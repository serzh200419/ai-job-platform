from django.urls import path

from .views import CoverLetterListCreateView, CVDocumentListCreateView

urlpatterns = [
    path("cv/", CVDocumentListCreateView.as_view(), name="cv-list"),
    path("cover-letter/", CoverLetterListCreateView.as_view(), name="cover-letter-list"),
]
