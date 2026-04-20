from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ChatMessage, ChatSession
from .serializers import (
    ChatSessionListSerializer,
    ChatSessionSerializer,
    SendMessageSerializer,
)


class ChatSessionCreateView(APIView):
    """POST /api/chat/session/ — create a new session."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        session = ChatSession.objects.create(user=request.user)
        return Response(ChatSessionSerializer(session).data, status=status.HTTP_201_CREATED)

    def get(self, request):
        sessions = ChatSession.objects.filter(user=request.user)
        return Response(ChatSessionListSerializer(sessions, many=True).data)


class ChatSessionDetailView(APIView):
    """GET /api/chat/<session_id>/ — retrieve session with all messages."""
    permission_classes = [IsAuthenticated]

    def get(self, request, session_id):
        session = get_object_or_404(ChatSession, id=session_id, user=request.user)
        return Response(ChatSessionSerializer(session).data)


class ChatMessageCreateView(APIView):
    """POST /api/chat/message/ — send a message and get an AI reply."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SendMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        session = get_object_or_404(
            ChatSession,
            id=serializer.validated_data["session_id"],
            user=request.user,
        )

        # Save user message
        user_msg = ChatMessage.objects.create(
            session=session,
            sender=ChatMessage.Sender.USER,
            message=serializer.validated_data["message"],
        )

        # Placeholder AI response — replace with real AI integration
        ai_reply = ChatMessage.objects.create(
            session=session,
            sender=ChatMessage.Sender.AI,
            message="I'm processing your request. AI integration coming soon.",
        )

        from .serializers import ChatMessageSerializer
        return Response(
            {
                "user_message": ChatMessageSerializer(user_msg).data,
                "ai_message": ChatMessageSerializer(ai_reply).data,
            },
            status=status.HTTP_201_CREATED,
        )
