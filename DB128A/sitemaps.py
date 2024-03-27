from django.contrib.sitemaps import Sitemap
from django.urls import reverse


class BasicSitemap(Sitemap):
    changefreq = "daily"

    def items(self):
        return ['court-database-root', 'faq', 'imprint']

    def location(self, item):
        return reverse(item)

    def priority(self, item):
        if item == 'court-database-root':
            return 1
        if item == 'faq':
            return 0.6
        if item == 'imprint':
            return 0.6
        return 0.5
