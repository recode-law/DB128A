from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from .models import SignupRequest, User, PasswordResetRequest


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


@admin.action(description="Passwort reset E-Mail versenden")
def send_password_reset_mail(modeladmin, request, queryset):
    errors = []
    for user in queryset:
        try:
            reset_request = PasswordResetRequest.create_request(user)
            reset_request.send_mail(request)
        except ValueError as e:
            errors.append(str(e))

    messages.error(request, "\n".join(errors))


class UserAdmin(DjangoUserAdmin):
    actions = [send_password_reset_mail]


class PasswordResetRequestAdmin(admin.ModelAdmin):
    list_display = [
        "user"
    ]


admin.site.register(SignupRequest, SignupRequestAdmin)
admin.site.register(User, UserAdmin)
admin.site.register(PasswordResetRequest, PasswordResetRequestAdmin)
