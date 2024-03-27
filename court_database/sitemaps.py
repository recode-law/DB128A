from django.contrib.sitemaps import Sitemap
from .models import Court


class CourtSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.5

    def items(self):
        return Court.objects.all()
