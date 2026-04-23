from django.urls import path

from .views import (
    JobMatchListView,
    JobMatchRefreshView,
    RecommendedJobsView,
    RecommendedJobsRefreshView,
)

urlpatterns = [
    # Cache-first recommended jobs (new primary endpoint)
    path("jobs/recommended/", RecommendedJobsView.as_view(), name="recommended-jobs"),
    path("jobs/recommended/refresh/", RecommendedJobsRefreshView.as_view(), name="recommended-jobs-refresh"),

    # Legacy read-only endpoints (kept for backward compatibility)
    path("matches/", JobMatchListView.as_view(), name="matches-list"),
    path("matches/refresh/", JobMatchRefreshView.as_view(), name="matches-refresh"),
]
