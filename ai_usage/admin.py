from django.contrib import admin

from ai_usage.models import AIFeedback


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

admin.site.register(AIFeedback, AIFeedbackAdmin)