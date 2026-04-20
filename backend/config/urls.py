from django.contrib import admin
from django.urls import include, path
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path("admin/", admin.site.urls),
    # Auth
    path("api/auth/", include("users.urls")),
    path("api/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    # Resources
    path("api/", include("jobs.urls")),
    path("api/chat/", include("chat.urls")),
    path("api/", include("documents.urls")),
    path("api/", include("matching.urls")),
]
