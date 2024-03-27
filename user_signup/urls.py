from django.urls import path
from django.views.generic import TemplateView

from .views import signup_request_create, SignupRequestListView, signup_request_accept, signup_request_reject, signup_request_verify, signup_request_send_mail

urlpatterns = [
    path("signup_request", signup_request_create, name="user-signup-request"),
    path("signup_request/success", TemplateView.as_view(template_name="user_signup/success.html"), name="user-signup-success"),
    path("signup_request/error", TemplateView.as_view(template_name="user_signup/error.html"), name="user-signup-error"),
    path("signup_request/list", SignupRequestListView.as_view(), name="user-signup-list"),
    path("signup_request/<int:sr_id>/accept", signup_request_accept, name="user-signup-accept"),
    path("signup_request/<int:sr_id>/reject", signup_request_reject, name="user-signup-reject"),
    path("signup_request/<int:sr_id>/send_mail", signup_request_send_mail, name="user-signup-send-mail"),
    path("signup_request/verify/<str:code>", signup_request_verify, name="user-signup-verify")
]
