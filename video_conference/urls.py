from video_conference.views import (CourtListView, CourtDetailView, submit_positive_feedback, submit_negative_feedback,
                                    CreateDetailedFeedbackFormView, APIInfoView, rest_api_court, rest_api_court_search,
                                    rest_api_court_percentage, rest_api_court_detail, rest_api_court_type, rest_api_state,
                                    rest_api_court_feedback, rest_api_court_detailed_feedback, rest_api_rejection_reason,
                                    rest_api_camera_perspective, rest_api_conferencing_software)

from django.contrib import admin
from django.shortcuts import render
from django.urls import path, include
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.sitemaps.views import sitemap
import sys

from django.views.generic import TemplateView, RedirectView

from .sitemaps import BasicSitemap, CourtSitemap

urlpatterns = [
    path("", CourtListView.as_view(), name="video-conference-root"),
    path("court/<int:pk>", CourtDetailView.as_view(), name="video-conference-court-detail"),
    path("court/<int:court_id>/good", submit_positive_feedback, name="video-conference-good-feedback"),
    path("court/<int:court_id>/bad", submit_negative_feedback, name="video-conference-bad-feedback"),
    path("court/<int:court_id>/feedback", CreateDetailedFeedbackFormView.as_view(), name="video-conference-create-detailed-feedback"),
    path("api_info", APIInfoView.as_view(), name="video-conference-api-info"),
    path("api/v1/court", rest_api_court, name="video-conference-restapi-court"),
    path("api/v1/court/search", rest_api_court_search, name="video-conference-restapi-court-search"),
    path("api/v1/court/percentage", rest_api_court_percentage, name="video-conference-restapi-court-percentage"),
    path("api/v1/court/detail", rest_api_court_detail, name="video-conference-restapi-court-detail"),
    path("api/v1/court_type", rest_api_court_type, name="video-conference-restapi-court-type"),
    path("api/v1/state", rest_api_state, name="video-conference-restapi-state"),
    path("api/v1/feedback", rest_api_court_feedback, name="video-conference-restapi-feedback"),
    path("api/v1/feedback/detailed", rest_api_court_detailed_feedback, name="video-conference-restapi-detailed-feedback"),
    path("api/v1/feedback/rejection_reason", rest_api_rejection_reason, name="video-conference-restapi-rejection-reason"),
    path("api/v1/feedback/camera_perspective", rest_api_camera_perspective, name="video-conference-restapi-camera-perspective"),
    path("api/v1/feedback/conferencing_software", rest_api_conferencing_software, name="video-conference-restapi-conferencing-software"),
    path("faq", TemplateView.as_view(template_name="video_conference/faq.html", extra_context={
        "title": "Fragen und Antworten"
    }), name="video-conference-faq"),
    path("imprint", TemplateView.as_view(template_name="video_conference/imprint.html", extra_context={
        "title": "Impressum"
    }), name="video-conference-imprint"),
    path("privacy", RedirectView.as_view(url="/static/privacy_statement.pdf"), name="video-conference-privacy"),
    path("user_signup/", include("user_signup.urls")),
    path("admin/", admin.site.urls),
    path("login", LoginView.as_view(template_name="video_conference/login.html"), name="login"),
    path("logout", LogoutView.as_view(), name="logout"),
    path("sitemap.xml", sitemap, {"sitemaps": {
        "basics": BasicSitemap,
        "courts": CourtSitemap
    }}, name="django.contrib.sitemaps.views.sitemap")
]


admin.site.site_header = "Videoverhandlung.de Administration"
admin.site.site_title = "Videoverhandlung.de Administration"


def handler403(request, exception):
    return render(request, "DB128A/403.html", status=403)


def handler404(request, exception):
    return render(request, "DB128A/404.html", status=404)


def handler500(request):
    type_, value, traceback = sys.exc_info()
    return render(request, "DB128A/500.html", {"error": value}, status=500)
