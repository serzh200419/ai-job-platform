"""
OpenAI Chat Completions integration for job matching.

Public interface:
    match_jobs(payload) -> list[dict]

payload structure:
    {
        "candidate": { ...profile/skills/experience dict... },
        "jobs":      [ ...list of job dicts with real UUID job_id fields... ]
    }

Output contract per item:
    {"job_id": str, "match_score": float (0-1), "reason": str}
"""
import json
import logging
import re
import time

import openai
from django.conf import settings

logger = logging.getLogger(__name__)

# ── Configuration ─────────────────────────────────────────────────────────────

OPENAI_TIMEOUT = 30.0
MAX_RETRIES    = 2
MODEL          = "gpt-4o-mini"

_RETRYABLE = (
    openai.RateLimitError,
    openai.APIConnectionError,
    openai.APITimeoutError,
    openai.InternalServerError,
)

# ── System prompt ─────────────────────────────────────────────────────────────

_SYSTEM_PROMPT = """\
You are a job-matching assistant. You receive a candidate's user_profile and a list of jobs.

Each job has a "job_id" field containing a UUID from the database. You MUST return it verbatim.

Scoring priorities (use all available signals):
1. Skills overlap — compare user_profile.skills vs job.required_skills (PRIMARY)
2. Job title relevance — match user_profile.profession to job.title (VERY STRONG)
3. Experience fit — use user_profile.experience and years_experience
4. Location & job type — remote is broadly compatible; prefer location match
5. Salary — OPTIONAL weak signal only; if salary_min or salary_max is null, ignore salary entirely

Rules:
- Score each job 0–100. Include jobs with score >= 20, ordered descending.
- Salary MUST NOT exclude any job. A null salary is neutral.
- Return the job_id field EXACTLY as given — never shorten, modify, or replace with "job-1" etc.

Output format — return ONLY this JSON, no markdown, no extra keys:
{
  "matches": [
    {"job_id": "<exact UUID from input>", "score": <0-100>, "reason": "<1-2 sentences>"},
    ...
  ]
}

CRITICAL: copy every job_id character-for-character from the input. Never invent IDs.\
"""


# ── Public function ───────────────────────────────────────────────────────────

def match_jobs(payload: dict, max_retries: int = MAX_RETRIES) -> list[dict]:
    """
    Score jobs against a candidate profile using OpenAI Chat Completions.

    Returns:
        list of dicts: [{"job_id": str, "match_score": float (0-1), "reason": str}, ...]

    Raises:
        ValueError: misconfiguration or unparseable response.
        openai.APIError: non-retryable API error, or retries exhausted.
    """
    api_key = getattr(settings, "OPENAI_API_KEY", "") or ""
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not configured in settings.")

    client   = openai.OpenAI(api_key=api_key, timeout=OPENAI_TIMEOUT)
    jobs     = payload.get("jobs", [])
    job_count = len(jobs)

    valid_ids = {str(j["job_id"]) for j in jobs if "job_id" in j}

    logger.info(
        "Sending to OpenAI (%s): %d jobs | user_profile keys: %s",
        MODEL, job_count, list(payload.get("user_profile", {}).keys()),
    )
    logger.debug("Valid job_ids in payload: %s", sorted(valid_ids))

    user_profile_json = json.dumps(payload.get("user_profile", {}), ensure_ascii=False)
    jobs_json         = json.dumps(jobs, ensure_ascii=False)

    user_message = f"USER_PROFILE:\n{user_profile_json}\n\nJOBS:\n{jobs_json}"

    last_exc: Exception | None = None

    for attempt in range(max_retries + 1):
        t0 = time.perf_counter()
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user",   "content": user_message},
                ],
                temperature=0.1,
                response_format={"type": "json_object"},
            )
            latency = time.perf_counter() - t0
            logger.info(
                "OpenAI response in %.2fs (attempt %d/%d) | tokens: %s",
                latency, attempt + 1, max_retries + 1,
                getattr(response.usage, "total_tokens", "?"),
            )

            raw_text = response.choices[0].message.content or ""
            logger.info("Raw OpenAI output (first 1000): %.1000s", raw_text)

            return _parse_response(raw_text, valid_ids)

        except _RETRYABLE as exc:
            latency = time.perf_counter() - t0
            last_exc = exc
            logger.warning(
                "OpenAI transient %s after %.2fs (attempt %d/%d): %s",
                type(exc).__name__, latency, attempt + 1, max_retries + 1, exc,
            )
            if attempt < max_retries:
                backoff = 2 ** attempt
                logger.info("Retrying in %ds…", backoff)
                time.sleep(backoff)

        except openai.APIError as exc:
            latency = time.perf_counter() - t0
            logger.error("OpenAI non-retryable error after %.2fs: %s", latency, exc, exc_info=True)
            raise

    assert last_exc is not None
    raise last_exc


# ── Helpers ───────────────────────────────────────────────────────────────────

_FENCE_RE = re.compile(r"```(?:json)?\s*([\s\S]*?)\s*```", re.IGNORECASE)


def _strip_markdown(text: str) -> str:
    m = _FENCE_RE.search(text)
    return m.group(1) if m else text.strip()


def _is_schema_response(data: dict) -> bool:
    return "type" in data and "properties" in data


def _parse_response(raw_text: str, valid_ids: set | None = None) -> list[dict]:
    """
    Parse and validate OpenAI output.

    valid_ids: set of job_id strings that were sent to the model.
               Items with IDs outside this set are logged and discarded.
    """
    cleaned = _strip_markdown(raw_text)

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        logger.error("OpenAI returned non-JSON. Raw (first 500): %.500s", raw_text)
        raise ValueError(f"OpenAI response is not valid JSON: {exc}") from exc

    if isinstance(data, dict) and _is_schema_response(data):
        logger.error(
            "OpenAI returned a JSON Schema definition instead of match data. Keys: %s",
            list(data.keys()),
        )
        raise ValueError("OpenAI returned a schema definition instead of match results.")

    if isinstance(data, list):
        results = data
    elif isinstance(data, dict):
        results = data.get("matches") or data.get("results") or []
        if not results:
            logger.error(
                "OpenAI dict has no usable array. Keys: %s | Response: %.500s",
                list(data.keys()), cleaned,
            )
            return []
    else:
        logger.error("Unexpected top-level JSON type: %s", type(data).__name__)
        return []

    validated = []
    skipped   = 0

    for item in results:
        if not isinstance(item, dict):
            skipped += 1
            continue

        job_id = str(item.get("job_id", "")).strip()
        score  = item.get("score") if item.get("score") is not None else item.get("match_score")

        if not job_id or score is None:
            logger.warning("Skipping item missing job_id or score: %s", item)
            skipped += 1
            continue

        # Reject hallucinated IDs before they reach the DB layer
        if valid_ids is not None and job_id not in valid_ids:
            logger.warning(
                "OpenAI returned hallucinated job_id %r — not in candidate set. "
                "Valid sample: %s",
                job_id, sorted(valid_ids)[:5],
            )
            skipped += 1
            continue

        try:
            score_float = max(0.0, min(100.0, float(score))) / 100.0
        except (TypeError, ValueError):
            logger.warning("Skipping item with non-numeric score=%s: %s", score, item)
            skipped += 1
            continue

        validated.append({
            "job_id":      job_id,
            "match_score": score_float,
            "reason": str(item.get("reason", ""))[:500],
        })

    if skipped:
        logger.warning("Parser skipped %d/%d items", skipped, len(results))

    if results and not validated:
        logger.error(
            "OpenAI returned %d items but 0 passed validation. First item: %s",
            len(results), results[0],
        )
    else:
        logger.info("Parsed %d valid matches (%d skipped)", len(validated), skipped)

    return validated
