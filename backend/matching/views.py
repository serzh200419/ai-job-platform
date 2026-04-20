import logging
from datetime import timedelta

from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import JobMatch
from .serializers import JobMatchSerializer
from .services.matcher import match_jobs_for_user

logger = logging.getLogger(__name__)

STALE_HOURS = 24


def _matches_response(user):
    """Build the standard matches payload for a given user."""
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


class JobMatchListView(APIView):
    """GET /api/matches/ — return cached matches instantly, no OpenAI call."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(_matches_response(request.user))


class JobMatchRefreshView(APIView):
    """POST /api/matches/refresh/ — trigger AI re-matching and return fresh results."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            match_jobs_for_user(request.user.id)
        except Exception as exc:
            logger.error(
                "AI matching failed for user %s: %s",
                request.user.id,
                exc,
                exc_info=True,
            )
            return Response(
                {"detail": "Matching service temporarily unavailable. Please try again."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response(_matches_response(request.user))
