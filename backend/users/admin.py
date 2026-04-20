from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Profile, User, UserEducation, UserExperience, UserSkill


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ("email",)
    list_display = ("email", "full_name", "is_active", "is_staff", "created_at")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal", {"fields": ("full_name", "phone")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
    )
    add_fieldsets = (
        (None, {"fields": ("email", "password1", "password2", "full_name")}),
    )
    search_fields = ("email", "full_name")
    filter_horizontal = ("groups", "user_permissions")


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "profession", "location", "years_experience")
    search_fields = ("user__email", "profession")


@admin.register(UserSkill)
class UserSkillAdmin(admin.ModelAdmin):
    list_display = ("user", "skill_name", "skill_level")
    list_filter = ("skill_level",)


@admin.register(UserEducation)
class UserEducationAdmin(admin.ModelAdmin):
    list_display = ("user", "institution", "degree", "start_date", "end_date")


@admin.register(UserExperience)
class UserExperienceAdmin(admin.ModelAdmin):
    list_display = ("user", "company", "position", "start_date", "end_date")
