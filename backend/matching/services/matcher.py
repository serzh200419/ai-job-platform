import json
import logging
import time
from decimal import Decimal

import openai
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

MATCHING_PROMPT = """You are an expert job matching AI. Evaluate how well a candidate's profile matches each job posting.

Candidate Profile:
{candidate_json}

Jobs to evaluate:
{jobs_json}

Instructions:
- Compare skills overlap, years of experience, profession alignment, salary fit, and location/remote preferences.
- Score each job from 0 to 100 (100 = perfect match).
- Only include strong matches with a score >= 50.
- Return at most the top 5 jobs, sorted by score descending.
- For each match write a short reason (max 15 words) explaining why it is a good fit.

Return ONLY a valid JSON object in this exact format, no extra text:
{{
  "results": [
    {{"job_id": "<uuid>", "match_score": 85, "reason": "Strong Python/Django skills match; remote role fits location preference"}},
    {{"job_id": "<uuid>", "match_score": 72, "reason": "Relevant experience; salary range aligns with expectations"}}
  ]
}}
"""

MAX_JOBS_TO_AI = 15


def _build_candidate_data(user):
    """Serialize user profile, skills, and experience into a compact dict."""
    profile = {}
    if hasattr(user, "profile"):
        p = user.profile
        profile = {
            "profession": p.profession,
            "summary": p.summary,
            "years_experience": p.years_experience,
            "desired_salary": float(p.desired_salary) if p.desired_salary else None,
            "location": p.location,
        }

    skills = [
        {"name": s.skill_name, "level": s.skill_level}
        for s in user.skills.all()
    ]

    experience = [
        {
            "company": e.company,
            "position": e.position,
            "description": e.description[:300],
            "start_date": str(e.start_date),
            "end_date": str(e.end_date) if e.end_date else None,
        }
        for e in user.experience.all()
    ]

    return {
        "name": user.full_name,
        "profile": profile,
        "skills": skills,
        "experience": experience,
    }


def _build_jobs_data(jobs):
    """Serialize jobs into a compact list for the AI prompt."""
    result = []
    for job in jobs:
        result.append({
            "id": str(job.id),
            "title": job.title,
            "company": job.company.name,
            "description": job.description[:500],
            "requirements": job.requirements[:300] if job.requirements else "",
            "required_skills": [s.skill_name for s in job.skills.all()],
            "location": job.location,
            "job_type": job.job_type,
            "salary_min": float(job.salary_min) if job.salary_min else None,
            "salary_max": float(job.salary_max) if job.salary_max else None,
        })
    return result


def _prefilter_jobs(user, jobs):
    """
    Score and rank jobs by relevance before sending to OpenAI.

    Hard exclusion: salary_max < desired_salary * 0.7 (when both are set).
    Relevance scoring:
      +3 per overlapping skill name
      +2 per profession word found in job title
      +3 for location match, +2 for remote jobs
      +1 if job salary_max >= desired_salary (salary fits)

    Returns top MAX_JOBS_TO_AI jobs sorted by relevance descending.
    Ties preserve original fetch order (stable sort).
    """
    desired_salary = None
    user_location = ""
    profession_words: set = set()

    if hasattr(user, "profile"):
        p = user.profile
        if p.desired_salary:
            desired_salary = p.desired_salary
        if p.location:
            user_location = p.location.lower()
        if p.profession:
            profession_words = {w for w in p.profession.lower().split() if len(w) > 2}

    user_skills = {s.skill_name.lower() for s in user.skills.all()}
    salary_floor = desired_salary * Decimal("0.7") if desired_salary else None

    scored = []
    for job in jobs:
        # Hard exclusion
        if salary_floor and job.salary_max is not None and job.salary_max < salary_floor:
            continue

        relevance = 0

        # Skill overlap
        job_skills = {s.skill_name.lower() for s in job.skills.all()}
        relevance += len(user_skills & job_skills) * 3

        # Profession relevance (user profession words in job title)
        if profession_words:
            title_words = set(job.title.lower().split())
            relevance += len(profession_words & title_words) * 2

        # Location
        if job.job_type == "remote":
            relevance += 2
        elif user_location and job.location and user_location in job.location.lower():
            relevance += 3

        # Salary fit bonus
        if desired_salary and job.salary_max and float(job.salary_max) >= float(desired_salary):
            relevance += 1

        scored.append((relevance, job))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [job for _, job in scored[:MAX_JOBS_TO_AI]]


def call_openai_matching(prompt, max_retries=2):
    """
    Send the matching prompt to OpenAI and return the parsed results list.

    Returns:
        list[dict]: Each dict has "job_id" and "match_score" keys.

    Raises:
        openai.APIError: On unrecoverable API errors after retries.
        ValueError: If the response cannot be parsed as expected JSON.
    """
    client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

    for attempt in range(max_retries + 1):
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a job matching AI. Always respond with valid JSON only.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content
            data = json.loads(content)
            return data.get("results", [])

        except json.JSONDecodeError as exc:
            logger.warning("OpenAI JSON parse error (attempt %d/%d): %s", attempt + 1, max_retries + 1, exc)
            if attempt == max_retries:
                raise ValueError(f"OpenAI returned non-JSON response: {exc}") from exc

        except openai.RateLimitError:
            logger.warning("OpenAI rate limit hit (attempt %d/%d)", attempt + 1, max_retries + 1)
            if attempt == max_retries:
                raise
            time.sleep(2 ** attempt)

        except openai.APIError as exc:
            logger.error("OpenAI API error: %s", exc)
            raise

    return []


def match_jobs_for_user(user_id):
    """
    Run AI-based job matching for the given user and persist results.

    Steps:
      1. Load user profile, skills, and experience.
      2. Load the 20 most recent jobs with their skills.
      3. Build a structured prompt and call OpenAI.
      4. Parse the scored results and upsert JobMatch records.

    Args:
        user_id: The primary key of the User to match.

    Returns:
        list[JobMatch]: The saved/updated JobMatch instances, ordered by score desc.
    """
    from users.models import User
    from jobs.models import Job
    from matching.models import JobMatch

    user = (
        User.objects
        .select_related("profile")
        .prefetch_related("skills", "experience")
        .get(id=user_id)
    )

    jobs = list(
        Job.objects
        .select_related("company")
        .prefetch_related("skills")
        .order_by("-created_at")[:50]
    )

    if not jobs:
        logger.info("No jobs available to match for user %s", user_id)
        return []

    has_profile_data = (
        hasattr(user, "profile")
        and bool(user.profile.profession or user.profile.summary or user.profile.years_experience)
    )
    has_skills = user.skills.exists()
    has_experience = user.experience.exists()

    if not has_profile_data and not has_skills and not has_experience:
        logger.info("User %s has no profile data, skipping AI call", user_id)
        return []

    jobs = _prefilter_jobs(user, jobs)

    if not jobs:
        logger.info("No jobs remain after pre-filter for user %s", user_id)
        return []

    candidate_data = _build_candidate_data(user)
    jobs_data = _build_jobs_data(jobs)

    prompt = MATCHING_PROMPT.format(
        candidate_json=json.dumps(candidate_data, indent=2),
        jobs_json=json.dumps(jobs_data, indent=2),
    )

    logger.info("Calling OpenAI matching for user %s with %d jobs", user_id, len(jobs))
    raw_results = call_openai_matching(prompt)

    job_map = {str(job.id): job for job in jobs}
    saved_matches = []

    for item in raw_results:
        job_id = item.get("job_id")
        score = item.get("match_score")

        if not job_id or score is None:
            logger.warning("Skipping malformed result item: %s", item)
            continue

        if job_id not in job_map:
            logger.warning("Returned job_id %s not in candidate set, skipping", job_id)
            continue

        score = max(0.0, min(100.0, float(score))) / 100.0
        reason = str(item.get("reason", ""))[:500]

        match, created = JobMatch.objects.update_or_create(
            user=user,
            job=job_map[job_id],
            defaults={"match_score": score, "reason": reason, "calculated_at": timezone.now()},
        )
        saved_matches.append(match)
        logger.debug("%s match: job=%s score=%.1f", "Created" if created else "Updated", job_id, score)

    logger.info("Saved %d matches for user %s", len(saved_matches), user_id)
    return saved_matches
