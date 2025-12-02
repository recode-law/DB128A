from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.shortcuts import render
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path, include
from django.views.generic import TemplateView, RedirectView

from court_database.sitemaps import CourtSitemap
from .sitemaps import AIUsageBasicSitemap
from .views import CourtListView, CourtDetailView, CreateAIFeedbackFormView

urlpatterns = [
    path("", CourtListView.as_view(), name="ai-usage-root"),
    path("court/<int:pk>", CourtDetailView.as_view(), name="ai-usage-court-detail"),
    path("court/<int:court_id>/feedback", CreateAIFeedbackFormView.as_view(), name="ai-usage-court-feedback"),
    path("faq", TemplateView.as_view(template_name="ai_usage/faq.html", extra_context={
        "title": "Fragen und Antworten"
    }), name="ai-usage-faq"),
    path("sources", TemplateView.as_view(template_name="ai_usage/sources.html", extra_context={
        "title": "Quellen"
    }), name="ai-usage-sources"),
    path("imprint", TemplateView.as_view(template_name="ai_usage/imprint.html", extra_context={
        "title": "Impressum"
    }), name="ai-usage-imprint"),
    path("privacy", RedirectView.as_view(url="/static/privacy_statement.pdf"), name="ai-usage-privacy"),
    path("user_signup/", include("user_signup.urls")),
    path("admin/", admin.site.urls),
    path("login", LoginView.as_view(template_name="video_conference/login.html"), name="login"),
    path("logout", LogoutView.as_view(), name="logout"),
    path("sitemap.xml", sitemap, {"sitemaps": {
        "basics": AIUsageBasicSitemap,
        "courts": CourtSitemap
    }}, name="django.contrib.sitemaps.views.sitemap")
]


admin.site.site_header = "KI-vor-Gericht.de Administration"
admin.site.site_title = "KI-vor-Gericht.de Administration"


def handler403(request, exception):
    return render(request, "DB128A/403.html", status=403)


def handler404(request, exception):
    return render(request, "DB128A/404.html", status=404)


def handler500(request):
    type_, value, traceback = sys.exc_info()
    return render(request, "DB128A/500.html", {"error": value}, status=500)
