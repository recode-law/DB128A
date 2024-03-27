from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import SignupRequest, User


class SignupRequestAdmin(admin.ModelAdmin):
    list_display = [
        "first_name",
        "last_name",
        "workplace",
        "email"
    ]

    list_filter = [
        "workplace"
    ]

    search_fields = [
        "first_name",
        "last_name",
        "workplace",
        "email"
    ]


admin.site.register(SignupRequest, SignupRequestAdmin)
admin.site.register(User, UserAdmin)
