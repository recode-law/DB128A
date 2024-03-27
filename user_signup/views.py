import requests
from base64 import b64decode

from django.conf import settings
from django.core.exceptions import PermissionDenied

from django.core.mail import mail_admins
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import get_user_model
from django.shortcuts import render
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.html import format_html
from django.views.generic import ListView
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.contrib.auth.password_validation import validate_password

from .models import SignupRequest
from helper.helper import is_member


User = get_user_model()


def signup_request_create(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        workplace = request.POST.get('workplace')
        email = request.POST.get('email')

        signup_request = SignupRequest(first_name=first_name, last_name=last_name, workplace=workplace, email=email)

        try:
            validate_email(email)
        except ValidationError:
            return render(request, "user_signup/signup_request_create.html", {
                "captcha_public_key": settings.USER_SIGNUP_CAPTCHA_PUBLIC_KEY,
                "title": "Registrierungsformular",
                "mail_error": "Ungültige E-Mail Adresse"
            })

        if not passes_friendly_captcha_check(request.POST.get("frc-captcha-solution")):
            raise PermissionDenied()

        signup_request.save()
        return HttpResponseRedirect(reverse("user-signup-success"))

    return render(request, "user_signup/signup_request_create.html", {
        "captcha_public_key": settings.USER_SIGNUP_CAPTCHA_PUBLIC_KEY,
        "title": "Registrierungsformular"
    })


class SignupRequestListView(UserPassesTestMixin, LoginRequiredMixin, ListView):
    template_name = "user_signup/signup_request_list.html"
    paginate_by = 20
    model = SignupRequest

    def test_func(self):
        return is_member(self.request.user, "Verifizierer")

    def get_queryset(self):
        name = self.request.GET.get("name")
        if name:
            object_list = self.model.objects.filter(name__icontains=name)
        else:
            object_list = self.model.objects.all()
        return object_list

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Accountanfragen"
        return context


@login_required
@user_passes_test(lambda user: is_member(user, "Verifizierer"))
def signup_request_accept(request, sr_id):
    signup_request = SignupRequest.objects.get(pk=sr_id)
    signup_request.accept()
    return HttpResponseRedirect(reverse("user-signup-list"))


@login_required
@user_passes_test(lambda user: is_member(user, "Verifizierer"))
def signup_request_reject(request, sr_id):
    signup_request = SignupRequest.objects.get(pk=sr_id)
    signup_request.reject()
    return HttpResponseRedirect(reverse("user-signup-list"))


def signup_request_verify(request, code):
    try:
        free_text = b64decode(code.encode()).decode()
        username = free_text.split("_$_")[0]
        user = User.objects.get(username=username)
        signup_request = SignupRequest.objects.get(user=user)
        if signup_request.verification_code == code:
            if request.method == "POST":
                password = request.POST.get("password")

                try:
                    validate_password(password)
                except ValidationError as e:
                    return render(request, "user_signup/create_password.html", {
                        "username": username,
                        "title": "Passworterstellung",
                        "pv_error": format_html("<br>".join(e.messages))
                    })

                password_repeat = request.POST.get("passwordRepeat")

                if password != password_repeat:
                    return render(request, "user_signup/create_password.html", {
                        "username": username,
                        "title": "Passworterstellung",
                        "pv_error": "Die Passwörter stimmen nicht überein!"
                    })

                user.set_password(password)
                user.is_active = True
                user.save()
                signup_request.delete()
                return HttpResponseRedirect(reverse("login"))
            return render(request, "user_signup/create_password.html", {
                "user": user,
                "title": "Passworterstellung"
            })
    except (UnicodeDecodeError, IndexError, SignupRequest.DoesNotExist):
        pass

    return HttpResponseRedirect("/")


def passes_friendly_captcha_check(captcha_token) -> bool:
    response = requests.post("https://api.friendlycaptcha.com/api/v1/siteverify", data={
        "secret": settings.USER_SIGNUP_CAPTCHA_SECRET_KEY,
        "solution": captcha_token
    })
    response_data = response.json()
    # return True so that checks succeed if something goes wrong internally
    if response.status_code != 200:
        mail_admins("There was an error with friendlycaptcha.", str(response_data))
        return True
    return response_data["success"]
