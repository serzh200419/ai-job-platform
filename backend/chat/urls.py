from django.urls import path

from .views import ChatMessageCreateView, ChatSessionCreateView, ChatSessionDetailView

urlpatterns = [
    path("session/", ChatSessionCreateView.as_view(), name="chat-session"),
    path("<uuid:session_id>/", ChatSessionDetailView.as_view(), name="chat-detail"),
    path("message/", ChatMessageCreateView.as_view(), name="chat-message"),
]
