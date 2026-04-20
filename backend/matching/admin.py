from django.contrib import admin

from .models import JobMatch


@admin.register(JobMatch)
class JobMatchAdmin(admin.ModelAdmin):
    list_display = ("user", "job", "match_score", "calculated_at")
    list_filter = ("match_score",)
    search_fields = ("user__email", "job__title")
