from django.contrib.sitemaps import Sitemap
from django.urls import reverse


class AIUsageBasicSitemap(Sitemap):
    changefreq = "daily"

    def items(self):
        return ['ai-usage-root', 'ai-usage-faq', 'ai-usage-imprint']

    def location(self, item):
        return reverse(item)

    def priority(self, item):
        if item == 'ai-usage-root':
            return 1
        if item == 'ai-usage-faq':
            return 0.6
        if item == 'ai-usage-imprint':
            return 0.6
        return 0.5
