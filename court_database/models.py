from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
import datetime
import pytz

UserModel = get_user_model()


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


class CourtType(models.TextChoices):
    BG = 'BG', _('Bundesgericht')
    OG = 'OG', _('Oberlandesgericht')
    LG = 'LG', _('Landgericht')
    AG = 'AG', _('Amtsgericht')


class QualityChoices(models.IntegerChoices):
    Q1 = 1, _('Quality 1')
    Q2 = 2, _('Quality 2')
    Q3 = 3, _('Quality 3')
    Q4 = 4, _('Quality 4')
    Q5 = 5, _('Quality 5')


class RejectionReason(models.Model):
    name = models.CharField(verbose_name="Name", max_length=100)

    class Meta:
        verbose_name = "Ablehnungsgrund"
        verbose_name_plural = "Ablehnungsgründe"

    def __str__(self):
        return self.name


class CameraPerspective(models.Model):
    name = models.CharField(verbose_name="Name", max_length=100)

    class Meta:
        verbose_name = "Kameraperspektive"
        verbose_name_plural = "Kameraperspektiven"

    def __str__(self):
        return self.name


class ConferencingSoftware(models.Model):
    name = models.CharField(verbose_name="Name", max_length=100)

    class Meta:
        verbose_name = "Konferenz Software"
        verbose_name_plural = "Konferenz Software"

    def __str__(self):
        return self.name


class Address(models.Model):
    state = models.CharField(verbose_name="Staat", max_length=2, choices=States.choices)
    city = models.CharField(verbose_name="Ort", max_length=100, blank=True)
    postal_code = models.CharField(verbose_name="Postleitzahl", max_length=5, blank=True)
    street = models.CharField(verbose_name="Straße", max_length=100, blank=True)

    class Meta:
        verbose_name = "Adresse"
        verbose_name_plural = "Adressen"

    def __str__(self) -> str:
        return f"{self.state}, {self.postal_code} {self.city}, {self.street}"


class Court(models.Model):
    name = models.CharField(verbose_name="Name", max_length=200)
    type = models.TextField(verbose_name="Art", max_length=2, choices=CourtType.choices)
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

    class Meta:
        verbose_name = "Gericht"
        verbose_name_plural = "Gerichte"

    def get_absolute_url(self) -> str:
        return reverse("court-database-court-detail", args=[self.pk])

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
        return DetailedFeedback.objects.filter(court=self, disabled=False).exists()

    def detailed_feedbacks(self) -> ['DetailedFeedback']:
        return DetailedFeedback.objects.filter(court=self, disabled=False)

    def has_rejection_feedback(self) -> bool:
        return Feedback.objects.filter(court=self, provides_online_service=False, disabled=False).exists()

    def number_of_rejection_feedbacks(self) -> int:
        return Feedback.objects.filter(court=self, provides_online_service=False, disabled=False).count()

    def get_rejection_chart_data(self) -> list[list[str | int]]:
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

    def __str__(self) -> str:
        return self.name


class Feedback(models.Model):
    court = models.ForeignKey(verbose_name="Gericht", to=Court, on_delete=models.PROTECT)
    provides_online_service = models.BooleanField(verbose_name="Online Service gestattet")
    online_service_quality = models.IntegerField(verbose_name="Online Service Qualität", choices=QualityChoices.choices, null=True, blank=True)
    rejection_reason = models.ForeignKey(verbose_name="Ablehnungsgrund", to=RejectionReason, on_delete=models.PROTECT, null=True, blank=True)
    other_rejection_reason = models.TextField(verbose_name="Anderer Ablehnungsgrund", max_length=40, null=True, blank=True)
    creator_ip = models.GenericIPAddressField(verbose_name="IP Adresse")
    created_at = models.DateTimeField(verbose_name="Erstellungszeitpunkt", auto_now_add=True)
    disabled = models.BooleanField(verbose_name="Ausgeblendet", default=False)

    class Meta:
        verbose_name = "Feedback"
        verbose_name_plural = "Feedbacks"

    def created_at_localized(self) -> datetime.datetime:
        time_zone = pytz.timezone(settings.TIME_ZONE)
        return self.created_at.astimezone(time_zone)

    def local_time_to_str(self) -> str:
        local_time = self.created_at_localized()
        return local_time.strftime("%d.%m.%Y %H:%M:%S")

    def __str__(self) -> str:
        return f"{self.court.name} | {self.provides_online_service} | {self.online_service_quality if self.provides_online_service else self.rejection_reason.name if self.rejection_reason is not None else self.other_rejection_reason} | {self.local_time_to_str()}"


class DetailedFeedback(models.Model):
    user = models.ForeignKey(verbose_name="Benutzer", to=UserModel, on_delete=models.PROTECT)
    court = models.ForeignKey(verbose_name="Gericht", to=Court, on_delete=models.PROTECT)
    online_service_possible = models.BooleanField(verbose_name="Online Service möglich")
    camera_perspectives = models.ManyToManyField(verbose_name="Kameraperspektiven", to=CameraPerspective, blank=True)
    conferencing_software = models.ManyToManyField(verbose_name="Konferenzsoftware", to=ConferencingSoftware, blank=True)
    feedback = models.TextField(verbose_name="Feedback", blank=True)
    created_at = models.DateTimeField(verbose_name="Erstellungszeitpunkt", auto_now_add=True)
    disabled = models.BooleanField(verbose_name="Ausgeblendet", default=False)

    class Meta:
        verbose_name = "Detailliertes Feedback"
        verbose_name_plural = "Detaillierte Feedbacks"

    def created_at_localized(self) -> datetime.datetime:
        time_zone = pytz.timezone(settings.TIME_ZONE)
        if self.created_at is not None:
            return self.created_at.astimezone(time_zone)
        return datetime.datetime.now().astimezone(time_zone)

    def local_time_to_str(self) -> str:
        local_time = self.created_at_localized()
        return local_time.strftime("%d.%m.%Y %H:%M:%S")

    def online_service_possible_text(self) -> str:
        if self.online_service_possible:
            return "Ja"
        else:
            return "Nein"

    def camera_perspectives_text(self) -> str:
        return ", ".join([camera_perspective.name for camera_perspective in self.camera_perspectives.all()]) or "-"

    def conferencing_software_text(self) -> str:
        return ", ".join([conferencing_software.name for conferencing_software in self.conferencing_software.all()]) or "-"

    def __str__(self) -> str:
        return f"{self.user} | {self.court.name} | {self.online_service_possible} | {self.feedback} | {self.local_time_to_str()}"
