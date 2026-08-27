from django.contrib import admin

from content.models import AggregatedContent


@admin.register(AggregatedContent)
class AggregatedContentAdmin(admin.ModelAdmin):
    list_display = ("id", "created_at", "updated_at", "created_by", "updated_by")
    ordering = ("-created_at",)
    readonly_fields = ("id", "created_at", "updated_at", "deleted_at")
