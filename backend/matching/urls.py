from django.urls import path

from .views import JobMatchListView, JobMatchRefreshView

urlpatterns = [
    path("matches/", JobMatchListView.as_view(), name="matches-list"),
    path("matches/refresh/", JobMatchRefreshView.as_view(), name="matches-refresh"),
]
