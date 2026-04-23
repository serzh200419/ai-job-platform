import logging
from datetime import timedelta

from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import JobMatch
from .serializers import JobMatchSerializer
from .services.matcher import STALE_HOURS, is_cache_fresh, match_jobs_for_user

logger = logging.getLogger(__name__)


# ── Shared helper ─────────────────────────────────────────────────────────────

def _matches_response(user):
    """Serialize the current DB matches for a user into the standard response shape."""
    matches = (
        JobMatch.objects
        .filter(user=user)
        .select_related("job", "job__company")
        .prefetch_related("job__skills")
        .order_by("-match_score")
    )

    last_updated = None
    is_stale = True

    if matches.exists():
        latest = matches.order_by("-calculated_at").first()
        last_updated = latest.calculated_at.isoformat()
        is_stale = (timezone.now() - latest.calculated_at) > timedelta(hours=STALE_HOURS)

    return {
        "results": JobMatchSerializer(matches, many=True).data,
        "last_updated": last_updated,
        "is_stale": is_stale,
    }


# ── Recommended Jobs (cache-first, auto-trigger) ──────────────────────────────

class RecommendedJobsView(APIView):
    """
    GET /api/jobs/recommended/

    Cache-first recommended jobs for the authenticated user.

    - Fresh cache (< STALE_HOURS): return DB rows instantly (cache HIT).
    - Stale / empty: call OpenAI, save new matches, return results (cache MISS).
    - OpenAI failure: return previous matches if any; never fall back to all jobs.
    - No matches ever: return empty results with empty-state hint.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        if is_cache_fresh(user, max_age_hours=STALE_HOURS):
            logger.info("CACHE HIT — returning saved matches for user %s", user.id)
            return Response(_matches_response(user))

        logger.info("CACHE MISS — triggering AI matching for user %s", user.id)
        try:
            match_jobs_for_user(user.id)
        except Exception as exc:
            logger.error(
                "AI matching failed for user %s: %s", user.id, exc, exc_info=True,
            )
            # Graceful degradation: return whatever is in DB (may be empty)
            return Response(_matches_response(user))

        return Response(_matches_response(user))


class RecommendedJobsRefreshView(APIView):
    """
    POST /api/jobs/recommended/refresh/

    Force re-computation of matches, bypassing the short-interval cache guard.
    Useful for the manual "Refresh Matches" button.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            match_jobs_for_user(request.user.id, force=True)
        except Exception as exc:
            logger.error(
                "Forced AI matching failed for user %s: %s",
                request.user.id, exc, exc_info=True,
            )
            return Response(
                {"detail": "Matching service temporarily unavailable. Please try again."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response(_matches_response(request.user))


# ── Legacy endpoints (kept for backward compatibility) ────────────────────────

class JobMatchListView(APIView):
    """GET /api/matches/ — read-only DB view, no AI call."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(_matches_response(request.user))


class JobMatchRefreshView(APIView):
    """POST /api/matches/refresh/ — triggers AI, respects 1h cache."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            match_jobs_for_user(request.user.id)
        except Exception as exc:
            logger.error(
                "AI matching failed for user %s: %s",
                request.user.id, exc, exc_info=True,
            )
            return Response(
                {"detail": "Matching service temporarily unavailable. Please try again."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response(_matches_response(request.user))
