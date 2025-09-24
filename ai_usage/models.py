from django.db import models

from court_database.models import Court


class AIFeedback(models.Model):
    court = models.ForeignKey(verbose_name="Gericht", to=Court, on_delete=models.PROTECT)
    text = models.TextField(verbose_name="Text", blank=False, null=False)

    class Meta:
        verbose_name = "KI Feedback"
        verbose_name_plural = "KI Feedbacks"