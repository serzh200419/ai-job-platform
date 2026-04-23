import logging

from django.db import transaction
from django.utils import timezone

from .openai_matcher import match_jobs

logger = logging.getLogger(__name__)

MAX_JOBS_TO_AI = 15
MATCH_CACHE_HOURS = 1   # minimum interval between AI calls (prevents spam)
STALE_HOURS = 24        # matches older than this are considered stale by callers


# ── Public helpers ────────────────────────────────────────────────────────────

def is_cache_fresh(user, max_age_hours: int = STALE_HOURS) -> bool:
    """
    Return True if the user has at least one match computed within max_age_hours.
    Cheap: single indexed query on (user, calculated_at).
    """
    from matching.models import JobMatch
    latest = JobMatch.objects.filter(user=user).order_by("-calculated_at").first()
    if not latest:
        logger.debug("Cache check for user %s: no matches exist", user.id)
        return False
    age_seconds = (timezone.now() - latest.calculated_at).total_seconds()
    fresh = age_seconds < max_age_hours * 3600
    logger.debug(
        "Cache check for user %s: age=%.0fm fresh=%s",
        user.id, age_seconds / 60, fresh,
    )
    return fresh


# ── Data builders ─────────────────────────────────────────────────────────────

def _build_candidate_data(user):
    """Serialize user profile, skills, experience, and education into user_profile dict."""
    p = user.profile if hasattr(user, "profile") else None

    return {
        "profession":       p.profession        if p else "",
        "summary":          p.summary           if p else "",
        "years_experience": p.years_experience  if p else 0,
        "desired_salary":   float(p.desired_salary) if (p and p.desired_salary) else None,
        "location":         p.location          if p else "",
        "skills": [
            {"name": s.skill_name, "level": s.skill_level}
            for s in user.skills.all()
        ],
        "experience": [
            {
                "company":     e.company,
                "position":    e.position,
                "description": e.description[:300],
            }
            for e in user.experience.all()
        ],
        "education": [
            {
                "degree": e.degree,
                "field":  e.field_of_study,
            }
            for e in user.education.all()
        ],
    }


def _build_jobs_data(jobs):
    """Serialize jobs into a compact list for the AI prompt."""
    result = []
    for job in jobs:
        result.append({
            "job_id": str(job.id),
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
    Rank jobs by relevance before sending to OpenAI. No hard exclusions.

    Scoring (descending priority):
      +3 per overlapping skill name          (primary signal)
      +2 per profession word in job title    (strong signal)
      +3 for matching location               (moderate)
      +2 for remote job type                 (moderate)
      +1 salary fit bonus                    (weak — only when both values present)

    Salary NEVER excludes a job. NULL salary is treated as neutral.
    Returns top MAX_JOBS_TO_AI jobs.
    """
    p = user.profile if hasattr(user, "profile") else None
    desired_salary  = p.desired_salary if p else None
    user_location   = p.location.lower() if (p and p.location) else ""
    profession_words = (
        {w for w in p.profession.lower().split() if len(w) > 2}
        if (p and p.profession) else set()
    )
    user_skills = {s.skill_name.lower() for s in user.skills.all()}

    scored = []
    for job in jobs:
        relevance = 0

        # Skills overlap (primary)
        job_skills = {s.skill_name.lower() for s in job.skills.all()}
        relevance += len(user_skills & job_skills) * 3

        # Title relevance (strong)
        if profession_words:
            title_words = set(job.title.lower().split())
            relevance += len(profession_words & title_words) * 2

        # Location / job type
        if job.job_type == "remote":
            relevance += 2
        elif user_location and job.location and user_location in job.location.lower():
            relevance += 3

        # Salary fit (weak bonus — only when both sides have a value)
        if desired_salary and job.salary_max and float(job.salary_max) >= float(desired_salary):
            relevance += 1

        scored.append((relevance, job))

    scored.sort(key=lambda x: x[0], reverse=True)
    kept = [job for _, job in scored[:MAX_JOBS_TO_AI]]
    logger.info("Pre-filter: %d jobs in, %d sent to AI (no salary exclusion)", len(jobs), len(kept))
    return kept


# ── Main entry point ──────────────────────────────────────────────────────────

def match_jobs_for_user(user_id, force: bool = False):
    """
    Run AI-based job matching for the given user and persist results.

    Args:
        user_id: Primary key of the User to match.
        force:   If True, bypass the MATCH_CACHE_HOURS guard and always call
                 OpenAI (used by the manual refresh endpoint).

    Returns:
        list[JobMatch]: Saved instances ordered by score desc.
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

    # ── Short-interval cache guard (prevents re-calling AI within MATCH_CACHE_HOURS) ──
    if not force:
        latest_match = JobMatch.objects.filter(user=user).order_by("-calculated_at").first()
        if latest_match:
            age_seconds = (timezone.now() - latest_match.calculated_at).total_seconds()
            if age_seconds < MATCH_CACHE_HOURS * 3600:
                logger.info(
                    "CACHE HIT (%.0fm old) for user %s — skipping AI call",
                    age_seconds / 60, user_id,
                )
                return list(JobMatch.objects.filter(user=user).order_by("-match_score"))

    jobs = _prefilter_jobs(user, jobs)

    if not jobs:
        logger.info("No jobs remain after pre-filter for user %s", user_id)
        return []

    # Build job_map immediately — same list that goes into the payload,
    # so validation never compares against a different set.
    job_map = {str(job.id): job for job in jobs}

    logger.info(
        "Candidate set job_ids: %s",
        list(job_map.keys()),
    )

    payload = {
        "user_profile": _build_candidate_data(user),
        "jobs":         _build_jobs_data(jobs),
    }

    logger.info("CACHE MISS — calling OpenAI for user %s with %d jobs", user_id, len(jobs))
    raw_results = match_jobs(payload)

    if not raw_results:
        logger.warning("OpenAI returned no results for user %s", user_id)
        return list(JobMatch.objects.filter(user=user).order_by("-match_score"))

    logger.info(
        "OpenAI returned job_ids: %s",
        [item["job_id"] for item in raw_results],
    )

    now = timezone.now()
    saved_matches = []
    saved_job_ids = []

    with transaction.atomic():
        for item in raw_results:
            job_id = item["job_id"]
            score  = item["match_score"]  # already 0-1, normalised by parser

            if job_id not in job_map:
                logger.warning(
                    "Returned job_id %s not in candidate set — skipping. "
                    "Candidate ids: %s",
                    job_id, list(job_map.keys()),
                )
                continue

            match, created = JobMatch.objects.update_or_create(
                user=user,
                job=job_map[job_id],
                defaults={
                    "match_score":   score,
                    "reason":        item["reason"],
                    "calculated_at": now,
                },
            )
            saved_matches.append(match)
            saved_job_ids.append(job_map[job_id].id)
            logger.debug("Saved match (%s): job=%s score=%.4f", "new" if created else "updated", job_id, score)

        # Remove stale matches for jobs no longer in the new result set
        stale = JobMatch.objects.filter(user=user).exclude(job__id__in=saved_job_ids)
        stale_count = stale.count()
        if stale_count:
            stale.delete()
            logger.info("Removed %d stale matches for user %s", stale_count, user_id)

    logger.info("Saved %d fresh matches for user %s", len(saved_matches), user_id)
    return saved_matches
