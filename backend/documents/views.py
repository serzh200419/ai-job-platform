from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import CoverLetter, CVDocument
from .serializers import CoverLetterSerializer, CVDocumentSerializer


class CVDocumentListCreateView(generics.ListCreateAPIView):
    serializer_class = CVDocumentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return CVDocument.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class CoverLetterListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        letters = CoverLetter.objects.filter(user=request.user)
        return Response(CoverLetterSerializer(letters, many=True).data)

    def post(self, request):
        serializer = CoverLetterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Placeholder generated text — replace with real AI generation
        generated = (
            f"Dear Hiring Manager,\n\n"
            f"I am writing to apply for the position at your company. "
            f"With my skills and experience, I am confident I would be a great fit.\n\n"
            f"Best regards."
        )

        cover = CoverLetter.objects.create(
            user=request.user,
            job=serializer.validated_data["job"],
            generated_text=generated,
        )
        return Response(CoverLetterSerializer(cover).data, status=status.HTTP_201_CREATED)
