from rest_framework import serializers

from .models import JobMatch


class JobMatchSerializer(serializers.ModelSerializer):
    job = serializers.SerializerMethodField()

    class Meta:
        model = JobMatch
        fields = ("id", "job", "match_score", "reason", "calculated_at")
        read_only_fields = ("id", "calculated_at")

    def get_job(self, obj):
        return {
            "id": str(obj.job.id),
            "title": obj.job.title,
            "company": {
                "id": str(obj.job.company.id),
                "name": obj.job.company.name,
                "industry": obj.job.company.industry,
            },
            "salary": {"min": obj.job.salary_min, "max": obj.job.salary_max},
            "location": obj.job.location,
            "job_type": obj.job.job_type,
            "skills": [
                {"id": str(s.id), "skill_name": s.skill_name}
                for s in obj.job.skills.all()
            ],
            "created_at": obj.job.created_at.isoformat(),
        }
