from django.urls import path

from .views import (
    LoginView,
    MeView,
    ProfileView,
    RegisterView,
    UserEducationDetailView,
    UserEducationListCreateView,
    UserExperienceDetailView,
    UserExperienceListCreateView,
    UserSkillDetailView,
    UserSkillListCreateView,
)

urlpatterns = [
    # Auth
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("me/", MeView.as_view(), name="me"),
    # Profile
    path("profile/", ProfileView.as_view(), name="profile"),
    # Skills
    path("skills/", UserSkillListCreateView.as_view(), name="skills-list"),
    path("skills/<uuid:pk>/", UserSkillDetailView.as_view(), name="skills-detail"),
    # Education
    path("education/", UserEducationListCreateView.as_view(), name="education-list"),
    path("education/<uuid:pk>/", UserEducationDetailView.as_view(), name="education-detail"),
    # Experience
    path("experience/", UserExperienceListCreateView.as_view(), name="experience-list"),
    path("experience/<uuid:pk>/", UserExperienceDetailView.as_view(), name="experience-detail"),
]
