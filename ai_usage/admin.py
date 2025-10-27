from django.contrib import admin

from ai_usage.models import AIUsageGroup, AIFeedback


class AIUsageGroupAdmin(admin.ModelAdmin):
    list_display = [
        "name"
    ]

    search_fields = [
        "name"
    ]


class AIFeedbackAdmin(admin.ModelAdmin):
    list_display = [
        "court"
    ]

    list_filter = [
        "court"
    ]

    search_fields = [
        "court__name"
    ]


admin.site.register(AIUsageGroup, AIUsageGroupAdmin)
admin.site.register(AIFeedback, AIFeedbackAdmin)