from django.contrib.auth import get_user_model
from django.db import models

from court_database.models import Court


UserModel = get_user_model()


class AIUsageGroup(models.Model):
    name = models.CharField(verbose_name="Name", unique=True, max_length=100)

    class Meta:
        verbose_name = "KI-Nutzergruppe"
        verbose_name_plural = "KI-Nutzergruppe"

    def __str__(self):
        return self.name


class AIFeedback(models.Model):
    court = models.ForeignKey(verbose_name="Gericht", to=Court, on_delete=models.PROTECT)
    text = models.TextField(verbose_name="Text", blank=False, null=False)
    user = models.ForeignKey(verbose_name="Benutzer", to=UserModel, on_delete=models.PROTECT, null=True)
    usage_groups = models.ManyToManyField(verbose_name="Nutzergruppen", to=AIUsageGroup, blank=True)

    class Meta:
        verbose_name = "KI Feedback"
        verbose_name_plural = "KI Feedbacks"

    def ai_usage_groups_string(self) -> str:
        names = [usage_group.name for usage_group in self.usage_groups.all()]
        return ", ".join(names)