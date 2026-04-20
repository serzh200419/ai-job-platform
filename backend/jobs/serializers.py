from rest_framework import serializers

from .models import Company, Job, JobSkill


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ("id", "name", "industry", "description", "location", "website", "created_at")
        read_only_fields = ("id", "created_at")


class JobSkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobSkill
        fields = ("id", "skill_name")
        read_only_fields = ("id",)


class JobSerializer(serializers.ModelSerializer):
    company = CompanySerializer(read_only=True)
    salary = serializers.SerializerMethodField()
    skills = JobSkillSerializer(many=True, read_only=True)

    class Meta:
        model = Job
        fields = (
            "id", "title", "company", "description", "requirements",
            "salary", "location", "job_type", "skills", "created_at",
        )
        read_only_fields = ("id", "created_at")

    def get_salary(self, obj):
        return {"min": obj.salary_min, "max": obj.salary_max}


class JobListSerializer(serializers.ModelSerializer):
    """Lighter serializer for list views — no full description."""
    company = serializers.SerializerMethodField()
    salary = serializers.SerializerMethodField()

    class Meta:
        model = Job
        fields = ("id", "title", "company", "salary", "location", "job_type", "created_at")

    def get_company(self, obj):
        return {"id": obj.company.id, "name": obj.company.name, "industry": obj.company.industry}

    def get_salary(self, obj):
        return {"min": obj.salary_min, "max": obj.salary_max}
