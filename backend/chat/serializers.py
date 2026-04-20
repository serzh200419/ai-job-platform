from rest_framework import serializers

from .models import ChatMessage, ChatSession


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ("id", "sender", "message", "created_at")
        read_only_fields = ("id", "created_at")


class ChatSessionSerializer(serializers.ModelSerializer):
    messages = ChatMessageSerializer(many=True, read_only=True)

    class Meta:
        model = ChatSession
        fields = ("id", "started_at", "messages")
        read_only_fields = ("id", "started_at")


class ChatSessionListSerializer(serializers.ModelSerializer):
    message_count = serializers.IntegerField(source="messages.count", read_only=True)
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = ChatSession
        fields = ("id", "started_at", "message_count", "last_message")

    def get_last_message(self, obj):
        msg = obj.messages.last()
        if msg:
            return {"sender": msg.sender, "message": msg.message[:100], "created_at": msg.created_at}
        return None


class SendMessageSerializer(serializers.Serializer):
    session_id = serializers.UUIDField()
    message = serializers.CharField(min_length=1)
