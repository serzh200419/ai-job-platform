from django.urls import path

from .views import CompanyListView, JobDetailView, JobListView

urlpatterns = [
    path("jobs/", JobListView.as_view(), name="jobs-list"),
    path("jobs/<uuid:pk>/", JobDetailView.as_view(), name="jobs-detail"),
    path("companies/", CompanyListView.as_view(), name="companies-list"),
]
