from django.contrib import admin

from .models import (Feedback, DetailedFeedback, CameraPerspective, ConferencingSoftware,
                     RejectionReason)

@admin.action(description="IP Adressen löschen")
def reset_ip_addresses(modeladmin, request, queryset):
    queryset.update(creator_ip=None)

class FeedbackAdmin(admin.ModelAdmin):
    list_display = [
        "court",
        "provides_online_service",
        "online_service_quality",
        "rejection_reason",
        "other_rejection_reason",
        "creator_ip",
        "api_user",
        "created_at",
        "disabled"
    ]

    list_filter = [
        "court",
        "provides_online_service",
        "online_service_quality",
        "rejection_reason",
        "creator_ip",
        "api_user",
        "disabled"
    ]

    search_fields = [
        "court__name",
        "online_service_quality",
        "rejection_reason",
        "other_rejection_reason",
        "creator_ip",
        "api_user"
    ]

    actions = [reset_ip_addresses]

class DetailedFeedbackAdmin(admin.ModelAdmin):
    list_display = [
        "court",
        "online_service_possible",
        "feedback",
        "user",
        "created_at",
        "disabled"
    ]

    list_filter = [
        "user",
        "court",
        "online_service_possible",
        "disabled"
    ]

    search_fields = [
        "court__name",
        "user__username",
        "feedback"
    ]

admin.site.register(Feedback, FeedbackAdmin)
admin.site.register(DetailedFeedback, DetailedFeedbackAdmin)
admin.site.register(CameraPerspective)
admin.site.register(ConferencingSoftware)
admin.site.register(RejectionReason)
