from django.contrib import admin
from django_object_actions import DjangoObjectActions, action

from .models import Address, Court, CourtType


class AddressAdmin(admin.ModelAdmin):
    list_display = [
        "state",
        "postal_code",
        "city",
        "street"
    ]

    list_filter = [
        "state"
    ]

    search_fields = [
        "city",
        "postal_code",
        "street"
    ]


class CourtAdmin(DjangoObjectActions, admin.ModelAdmin):
    @action(description="Caches Erneuern")
    def refresh_caches(self, request, courts):
        for court in courts:
            court.update_feedback_buffers()
            court.update_detailed_feedback_buffers()

    actions = ['refresh_caches']

    list_display = [
        "name",
        "type",
        "online_service_quality",
        "provides_online_service_yes_count",
        "provides_online_service_no_count",
        "provides_online_service_attr",
        "online_service_possible_yes_count",
        "online_service_possible_no_count",
        "online_service_possible_attr"
    ]

    list_filter = [
        "type",
        "online_service_quality",
        "provides_online_service_attr",
        "online_service_possible_attr"
    ]

    search_fields = [
        "name"
    ]


admin.site.register(Address, AddressAdmin)
admin.site.register(Court, CourtAdmin)
admin.site.register(CourtType)
