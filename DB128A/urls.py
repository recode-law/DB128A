"""
URL configuration for DB128A project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.shortcuts import render
from django.urls import path, include
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.sitemaps.views import sitemap
import sys

from django.views.generic import TemplateView, RedirectView

from .sitemaps import BasicSitemap
from court_database.sitemaps import CourtSitemap

urlpatterns = [
    path("", include("court_database.urls")),
    path("faq", TemplateView.as_view(template_name="DB128A/faq.html", extra_context={
        "title": "Fragen und Antworten"
    }), name="faq"),
    path("imprint", TemplateView.as_view(template_name="DB128A/imprint.html", extra_context={
        "title": "Impressum"
    }), name="imprint"),
    path("privacy", RedirectView.as_view(url="/static/privacy_statement.pdf"), name="privacy"),
    path("user_signup/", include("user_signup.urls")),
    path("admin/", admin.site.urls),
    path("login", LoginView.as_view(template_name="DB128A/login.html"), name="login"),
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
