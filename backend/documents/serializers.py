from rest_framework import serializers

from .models import CoverLetter, CVDocument


class CVDocumentSerializer(serializers.ModelSerializer):
    job_title = serializers.CharField(source="job.title", read_only=True, default=None)

    class Meta:
        model = CVDocument
        fields = (
            "id", "job", "job_title", "original_cv_path",
            "optimized_cv_path", "created_at",
        )
        read_only_fields = ("id", "optimized_cv_path", "created_at")


class CoverLetterSerializer(serializers.ModelSerializer):
    job_title = serializers.CharField(source="job.title", read_only=True)
    company_name = serializers.CharField(source="job.company.name", read_only=True)

    class Meta:
        model = CoverLetter
        fields = ("id", "job", "job_title", "company_name", "generated_text", "created_at")
        read_only_fields = ("id", "generated_text", "created_at")
