from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import QuerySet
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


UserModel = get_user_model()


class InvalidStateError(ValueError):
    pass


class States(models.TextChoices):
    BW = 'BW', _('Baden-Württemberg')
    BY = 'BY', _('Bayern')
    BE = 'BE', _('Berlin')
    BB = 'BB', _('Brandenburg')
    HB = 'HB', _('Bremen')
    HH = 'HH', _('Hamburg')
    HE = 'HE', _('Hessen')
    MV = 'MV', _('Mecklenburg-Vorpommern')
    NI = 'NI', _('Niedersachsen')
    NW = 'NW', _('Nordrhein-Westfalen')
    RP = 'RP', _('Rheinland-Pfalz')
    SL = 'SL', _('Saarland')
    SN = 'SN', _('Sachsen')
    ST = 'ST', _('Sachsen-Anhalt')
    SH = 'SH', _('Schleswig-Holstein')
    TH = 'TH', _('Thüringen')


class QualityChoices(models.IntegerChoices):
    Q1 = 1, _('Quality 1')
    Q2 = 2, _('Quality 2')
    Q3 = 3, _('Quality 3')
    Q4 = 4, _('Quality 4')
    Q5 = 5, _('Quality 5')


class CourtType(models.Model):
    name = models.CharField(verbose_name="Name", unique=True, max_length=100)
    api_user = models.ForeignKey(verbose_name="API Benutzer", to=UserModel, on_delete=models.PROTECT, null=True,
                                 blank=True, default=None)

    class Meta:
        verbose_name = "Gerichtsart"
        verbose_name_plural = "Gerichtsarten"

    def __str__(self):
        return self.name


class Address(models.Model):
    state = models.CharField(verbose_name="Staat", max_length=2, choices=States.choices)
    city = models.CharField(verbose_name="Ort", max_length=100, blank=True)
    postal_code = models.CharField(verbose_name="Postleitzahl", max_length=5, blank=True)
    street = models.CharField(verbose_name="Straße", max_length=100, blank=True)
    api_user = models.ForeignKey(verbose_name="API Benutzer", to=UserModel, on_delete=models.PROTECT, null=True,
                                 blank=True, default=None)

    class Meta:
        verbose_name = "Adresse"
        verbose_name_plural = "Adressen"

    def __str__(self) -> str:
        return f"{self.state}, {self.postal_code} {self.city}, {self.street}"


class Court(models.Model):
    name = models.CharField(verbose_name="Name", max_length=200, unique=True)
    type = models.ForeignKey(verbose_name="Art", to=CourtType, on_delete=models.PROTECT)
    address = models.ForeignKey(verbose_name="Adresse", to=Address, on_delete=models.PROTECT, null=True, blank=True)
    parent = models.ForeignKey(verbose_name="Übergeordnet", to="self", on_delete=models.PROTECT, null=True, blank=True)

    online_service_quality = models.FloatField(verbose_name="Online Service Qualität (Cache)", default=0.0)
    provides_online_service_yes_count = models.IntegerField(verbose_name="Online Service gestattet (Cache)", default=0)
    provides_online_service_no_count = models.IntegerField(verbose_name="Online Service nicht gestattet (Cache)",
                                                           default=0)
    provides_online_service_attr = models.BooleanField(verbose_name="Online Service gestattet (Bool Cache)",
                                                       default=False)
    online_service_possible_yes_count = models.IntegerField(verbose_name="Online Service möglich (Cache)", default=0)
    online_service_possible_no_count = models.IntegerField(verbose_name="Online Service nicht möglich (Cache)",
                                                           default=0)
    online_service_possible_attr = models.BooleanField(verbose_name="Online Service möglich (Bool Cache)",
                                                       default=False)
    api_user = models.ForeignKey(verbose_name="API Benutzer", to=UserModel, on_delete=models.PROTECT, null=True,
                                 blank=True, default=None)

    class Meta:
        verbose_name = "Gericht"
        verbose_name_plural = "Gerichte"

    def get_absolute_url(self) -> str:
        match settings.DB128A_CONTEXT:
            case 'video_conference':
                return reverse("video-conference-court-detail", args=[self.pk])
            case 'ai_usage':
                return reverse("ai-usage-court-detail", args=[self.pk])
        assert False

    def provides_online_service(self) -> bool:
        return self.provides_online_service_yes_count > self.provides_online_service_no_count

    def provides_online_service_yes_percentage(self) -> float:
        vote_count = self.provides_online_service_yes_count + self.provides_online_service_no_count
        if vote_count == 0:
            return 50
        return int(self.provides_online_service_yes_count / vote_count * 100)

    def provides_online_service_no_percentage(self) -> float:
        return 100 - self.provides_online_service_yes_percentage()

    def online_service_possible(self) -> bool:
        return self.online_service_possible_yes_count > self.online_service_possible_no_count

    def update_feedback_buffers(self):
        from video_conference.models import Feedback

        yes_count = 0
        no_count = 0
        quality_sum = 0
        quality_count = 0

        for feedback in Feedback.objects.filter(court=self.id, disabled=False):
            if feedback.provides_online_service:
                yes_count += 1
                if feedback.online_service_quality is not None:
                    quality_sum += feedback.online_service_quality
                    quality_count += 1
            else:
                no_count += 1

        self.provides_online_service_yes_count = yes_count
        self.provides_online_service_no_count = no_count
        self.provides_online_service_attr = self.provides_online_service()
        self.online_service_quality = quality_sum / quality_count if quality_count else 0

        self.save()

    def update_detailed_feedback_buffers(self):
        from video_conference.models import DetailedFeedback

        yes_count = 0
        no_count = 0

        for feedback in DetailedFeedback.objects.filter(court=self, disabled=False):
            if feedback.online_service_possible:
                yes_count += 1
            else:
                no_count += 1

        self.online_service_possible_yes_count = yes_count
        self.online_service_possible_no_count = no_count
        self.online_service_possible_attr = self.online_service_possible()

        self.save()

    def has_detailed_feedback(self) -> bool:
        from video_conference.models import DetailedFeedback

        return DetailedFeedback.objects.filter(court=self, disabled=False).exists()

    def detailed_feedbacks(self) -> QuerySet['DetailedFeedback']:
        from video_conference.models import DetailedFeedback

        return DetailedFeedback.objects.filter(court=self, disabled=False)

    def has_rejection_feedback(self) -> bool:
        from video_conference.models import Feedback

        return Feedback.objects.filter(court=self, provides_online_service=False, disabled=False).exists()

    def number_of_rejection_feedbacks(self) -> int:
        from video_conference.models import Feedback

        return Feedback.objects.filter(court=self, provides_online_service=False, disabled=False).count()

    def get_rejection_chart_data(self) -> list[list[str | int]]:
        from video_conference.models import Feedback

        rejection_chart_data = {
            "Grund": "Anzahl"
        }

        for rejection_reason in [feedback.rejection_reason for feedback in Feedback.objects.filter(court=self, provides_online_service=False, disabled=False)]:
            if rejection_reason is None:
                reason_name = "Sonstige"
            else:
                reason_name = rejection_reason.name

            if reason_name in rejection_chart_data:
                rejection_chart_data[reason_name] += 1
            else:
                rejection_chart_data[reason_name] = 1

        return [[reason, count] for reason, count in rejection_chart_data.items()]

    def has_ai_feedback(self) -> bool:
        from ai_usage.models import AIFeedback

        return AIFeedback.objects.filter(court=self).exists()

    def ai_feedbacks(self) -> QuerySet['AIFeedback']:
        from ai_usage.models import AIFeedback

        return AIFeedback.objects.filter(court=self)

    def ai_usage_groups(self) -> QuerySet['AIUsageGroup']:
        from ai_usage.models import AIUsageGroup
        return AIUsageGroup.objects.filter(aifeedback__court=self).distinct()

    def ai_usage_groups_string(self) -> str:
        names = [usage_group.name for usage_group in self.ai_usage_groups()]
        return ", ".join(names)

    def __str__(self) -> str:
        return self.name
