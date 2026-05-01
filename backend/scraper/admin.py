from django.contrib import admin
from .models import ScrapeJob


@admin.register(ScrapeJob)
class ScrapeJobAdmin(admin.ModelAdmin):
    list_display  = ("url", "status", "attempts", "created_at", "processed_at")
    list_filter   = ("status",)
    search_fields = ("url", "error")
    readonly_fields = ("created_at", "processed_at")
