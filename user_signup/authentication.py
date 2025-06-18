import base64

from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model, authenticate
from django.db import models
from django.http import HttpResponse

UserModel = get_user_model()


class EmailBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            user = UserModel.objects.get(models.Q(username__iexact=username) | models.Q(email__iexact=username))
        except UserModel.DoesNotExist:
            return None
        else:
            if user.check_password(password):
                return user
        return None


def basic_auth_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        auth_header = request.META.get("HTTP_AUTHORIZATION")
        if not auth_header or not auth_header.startswith("Basic "):
            response = HttpResponse("Unauthorized", status=401)
            response["WWW-Authenticate"] = 'Basic realm="API"'
            return response

        try:
            encoded_credentials = auth_header.split(" ", 1)[1].strip()
            decoded_credentials = base64.b64decode(encoded_credentials).decode("utf-8")
            username, password = decoded_credentials.split(":", 1)
        except Exception:
            response = HttpResponse("Invalid authentication header", status=401)
            response["WWW-Authenticate"] = 'Basic realm="API"'
            return response

        user = authenticate(request, username=username, password=password)
        if user is None:
            response = HttpResponse("Unauthorized", status=401)
            response["WWW-Authenticate"] = 'Basic realm="API"'
            return response

        request.user = user
        return view_func(request, *args, **kwargs)
    return _wrapped_view
