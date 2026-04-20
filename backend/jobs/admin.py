from django.contrib import admin

from .models import Company, Job, JobSkill


class JobSkillInline(admin.TabularInline):
    model = JobSkill
    extra = 1


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("name", "industry", "location", "created_at")
    search_fields = ("name", "industry")


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ("title", "company", "job_type", "location", "created_at")
    list_filter = ("job_type",)
    search_fields = ("title", "company__name")
    inlines = [JobSkillInline]
