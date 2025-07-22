from django.contrib.sitemaps import Sitemap
from .models import Court


class BasicSitemap(Sitemap):
    changefreq = "daily"

    def items(self):
        return ['video-conference-root', 'faq', 'imprint']

    def location(self, item):
        return reverse(item)

    def priority(self, item):
        if item == 'video-conference-root':
            return 1
        if item == 'faq':
            return 0.6
        if item == 'imprint':
            return 0.6
        return 0.5


class CourtSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.5

    def items(self):
        return Court.objects.all()
