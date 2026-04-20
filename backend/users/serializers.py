from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Profile, UserEducation, UserExperience, UserSkill

User = get_user_model()


# ── Auth ──────────────────────────────────────────────────────────────────────

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ("email", "password")

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "email", "full_name", "phone", "is_active", "created_at", "updated_at")
        read_only_fields = ("id", "is_active", "created_at", "updated_at")


# ── Profile ───────────────────────────────────────────────────────────────────

class ProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Profile
        fields = (
            "id", "user", "profession", "summary",
            "years_experience", "desired_salary", "location", "created_at",
        )
        read_only_fields = ("id", "created_at")


# ── Skills ────────────────────────────────────────────────────────────────────

class UserSkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSkill
        fields = ("id", "skill_name", "skill_level")
        read_only_fields = ("id",)


# ── Education ─────────────────────────────────────────────────────────────────

class UserEducationSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserEducation
        fields = ("id", "institution", "degree", "field_of_study", "start_date", "end_date")
        read_only_fields = ("id",)


# ── Experience ────────────────────────────────────────────────────────────────

class UserExperienceSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserExperience
        fields = ("id", "company", "position", "description", "start_date", "end_date")
        read_only_fields = ("id",)
