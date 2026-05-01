import json
import logging

from django.conf import settings
from openai import OpenAI

from .law_rag import build_law_context

logger = logging.getLogger(__name__)

client = OpenAI(api_key=settings.OPENAI_API_KEY)

_FALLBACK = "AI service temporarily unavailable."


# ── Data helpers ──────────────────────────────────────────────────────────────

def _fetch_user_data(user):
    from users.models import Profile, UserEducation, UserExperience, UserSkill

    profile    = Profile.objects.filter(user=user).first()
    skills     = list(UserSkill.objects.filter(user=user))
    experience = list(UserExperience.objects.filter(user=user))
    education  = list(UserEducation.objects.filter(user=user))

    return profile, skills, experience, education


def _build_user_profile(user) -> dict:
    """
    Builds a fully-keyed user_profile dict aligned with the OpenAI hosted
    prompt schema.  Every field is present and typed; lists are never None.
    """
    if user is None:
        return _empty_user_profile()

    profile, skills, experience, education = _fetch_user_data(user)

    return {
        "profession":       profile.profession       if profile else "",
        "summary":          profile.summary          if profile else "",
        "years_experience": profile.years_experience if profile else 0,
        "desired_salary":   (
            float(profile.desired_salary) if profile and profile.desired_salary is not None else None
        ),
        "location":         profile.location         if profile else "",
        "skills": [
            {"name": s.skill_name, "level": s.skill_level}
            for s in skills
        ],
        "experience": [
            {
                "company":    e.company,
                "position":   e.position,
                "description": e.description,
                "start_date": str(e.start_date),
                "end_date":   str(e.end_date) if e.end_date else None,
            }
            for e in experience
        ],
        "education": [
            {
                "institution":   edu.institution,
                "degree":        edu.degree,
                "field_of_study": edu.field_of_study,
                "start_date":    str(edu.start_date),
                "end_date":      str(edu.end_date) if edu.end_date else None,
            }
            for edu in education
        ],
    }


def _empty_user_profile() -> dict:
    return {
        "profession":       "",
        "summary":          "",
        "years_experience": 0,
        "desired_salary":   None,
        "location":         "",
        "skills":           [],
        "experience":       [],
        "education":        [],
    }


# ── Job description builder ───────────────────────────────────────────────────

def _build_job_description(job_id) -> str:
    if not job_id:
        return ""

    from jobs.models import Job, JobSkill

    try:
        job = Job.objects.get(id=job_id)
    except Job.DoesNotExist:
        logger.warning("Job %s not found — omitting job_description", job_id)
        return ""

    skills_text = ", ".join(
        JobSkill.objects.filter(job=job).values_list("skill_name", flat=True)
    )
    return (
        f"Title: {job.title}\n"
        f"Description: {job.description}\n"
        f"Requirements: {job.requirements}\n"
        f"Skills: {skills_text}"
    )


# ── Profile summary generation ────────────────────────────────────────────────

def generate_profile_summary(user) -> str:
    profile, skills, experience, _ = _fetch_user_data(user)

    lines = []
    if profile:
        if profile.profession:
            lines.append(f"Profession: {profile.profession}")
        if profile.years_experience:
            lines.append(f"Years of experience: {profile.years_experience}")
        if profile.location:
            lines.append(f"Location: {profile.location}")
        if profile.summary:
            lines.append(f"Summary: {profile.summary}")
    if skills:
        lines.append("Skills: " + ", ".join(s.skill_name for s in skills[:10]))
    if experience:
        lines.append(
            "Experience: "
            + "; ".join(f"{e.position} at {e.company}" for e in experience[:3])
        )

    if not lines:
        logger.debug("No profile data for user %s — skipping summary generation", user.id)
        return ""

    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You write concise professional summaries of job candidates.",
                },
                {
                    "role": "user",
                    "content": (
                        "Summarize this candidate professionally in 2-3 sentences:\n\n"
                        + "\n".join(lines)
                    ),
                },
            ],
            max_tokens=150,
            temperature=0.3,
        )
        return resp.choices[0].message.content.strip()

    except Exception as exc:
        logger.warning("Could not generate profile summary for user %s: %s", user.id, exc)
        return ""


# ── Main entry point ──────────────────────────────────────────────────────────

def generate_ai_reply(user, message: str, session=None, job_id=None) -> str:
    message = (message or "").strip()
    if not message:
        return "Please enter a valid message."

    if not settings.OPENAI_CHAT_PROMPT_ID:
        logger.warning("OPENAI_CHAT_PROMPT_ID is not set — returning fallback")
        return _FALLBACK

    user_profile    = _build_user_profile(user)
    job_description = _build_job_description(job_id)

    if not isinstance(user_profile, dict):
        raise ValueError("user_profile must be a dict")

    # Cache a prose summary on the session (first message only)
    if session is not None and not session.profile_summary:
        summary = generate_profile_summary(user)
        if summary:
            session.profile_summary = summary
            session.save(update_fields=["profile_summary"])
            logger.info("Cached profile summary for session %s", session.id)

    profile_summary = (
        session.profile_summary
        if session and session.profile_summary
        else user_profile.get("profession", "")
    )

    law_context = build_law_context(message)

    # The Responses API treats any plain dict as a typed content-part and
    # requires a "type" field.  Serialising to a JSON string avoids that
    # validation entirely while keeping the full structured data readable
    # by the hosted prompt template.
    user_profile_str = json.dumps(user_profile, ensure_ascii=False)

    print("OPENAI PAYLOAD:", {
        "user_question":   message,
        "profile_summary": profile_summary,
        "user_profile":    user_profile,
    })

    try:
        response = client.responses.create(
            # input carries the actual user message — this is the only reliable
            # way to populate the user turn; variable substitution does not reach
            # the user turn in the stored prompt
            input=message,
            prompt={
                "id": settings.OPENAI_CHAT_PROMPT_ID,
                "variables": {
                    "user_question":   message,
                    "profile_summary": profile_summary or "",
                    "user_profile":    user_profile_str,
                    "job_description": job_description or "",
                    "law_context":     law_context or "",
                },
            },
        )
        return response.output_text

    except Exception as exc:
        logger.error("OpenAI error in generate_ai_reply: %s", exc, exc_info=True)
        return _FALLBACK
