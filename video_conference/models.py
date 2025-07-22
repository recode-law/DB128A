from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _
from court_database.models import Court
import datetime
import pytz


UserModel = get_user_model()


class QualityChoices(models.IntegerChoices):
    Q1 = 1, _('Quality 1')
    Q2 = 2, _('Quality 2')
    Q3 = 3, _('Quality 3')
    Q4 = 4, _('Quality 4')
    Q5 = 5, _('Quality 5')


class RejectionReason(models.Model):
    name = models.CharField(verbose_name="Name", unique=True, max_length=100)

    class Meta:
        verbose_name = "Ablehnungsgrund"
        verbose_name_plural = "Ablehnungsgründe"

    def __str__(self):
        return self.name


class CameraPerspective(models.Model):
    name = models.CharField(verbose_name="Name", unique=True, max_length=100)
    api_user = models.ForeignKey(verbose_name="API Benutzer", to=UserModel, on_delete=models.PROTECT, null=True,
                                 blank=True, default=None)

    class Meta:
        verbose_name = "Kameraperspektive"
        verbose_name_plural = "Kameraperspektiven"

    def __str__(self):
        return self.name


class ConferencingSoftware(models.Model):
    name = models.CharField(verbose_name="Name", unique=True, max_length=100)
    api_user = models.ForeignKey(verbose_name="API Benutzer", to=UserModel, on_delete=models.PROTECT, null=True,
                                 blank=True, default=None)

    class Meta:
        verbose_name = "Konferenz Software"
        verbose_name_plural = "Konferenz Software"

    def __str__(self):
        return self.name


class Feedback(models.Model):
    court = models.ForeignKey(verbose_name="Gericht", to=Court, on_delete=models.PROTECT)
    provides_online_service = models.BooleanField(verbose_name="Online Service gestattet")
    online_service_quality = models.IntegerField(verbose_name="Online Service Qualität", choices=QualityChoices.choices, null=True, blank=True)
    rejection_reason = models.ForeignKey(verbose_name="Ablehnungsgrund", to=RejectionReason, on_delete=models.PROTECT, null=True, blank=True)
    other_rejection_reason = models.TextField(verbose_name="Anderer Ablehnungsgrund", max_length=40, null=True, blank=True)
    creator_ip = models.GenericIPAddressField(verbose_name="IP Adresse", null=True, blank=True)
    created_at = models.DateTimeField(verbose_name="Erstellungszeitpunkt", auto_now_add=True)
    disabled = models.BooleanField(verbose_name="Ausgeblendet", default=False)
    api_user = models.ForeignKey(verbose_name="API Benutzer", to=UserModel, on_delete=models.PROTECT, null=True,
                                 blank=True, default=None)

    class Meta:
        verbose_name = "Feedback"
        verbose_name_plural = "Feedbacks"

    def created_at_localized(self) -> datetime.datetime:
        time_zone = pytz.timezone(settings.TIME_ZONE)
        return self.created_at.astimezone(time_zone)

    def local_time_to_str(self) -> str:
        local_time = self.created_at_localized()
        return local_time.strftime("%d.%m.%Y %H:%M:%S")

    def to_dict(self) -> dict:
        data = {
            "provides_online_service": self.provides_online_service,
            "online_service_quality": self.online_service_quality,
            "rejection_reason": None,
            "created_at": self.local_time_to_str()
        }

        if not self.provides_online_service:
            data["rejection_reason"] = self.rejection_reason.id if self.rejection_reason else -1

        return data

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
    from_api = models.BooleanField(verbose_name="Von API erstellt", default=False)

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

    def to_dict(self) -> dict:
        return {
            "online_service_possible": self.online_service_possible,
            "camera_perspectives": [camera_perspective.id for camera_perspective in self.camera_perspectives.all()],
            "conferencing_software": [conferencing_software.id for conferencing_software in self.conferencing_software.all()],
            "feedback": self.feedback,
            "created_at": self.local_time_to_str()
        }

    def __str__(self) -> str:
        return f"{self.user} | {self.court.name} | {self.online_service_possible} | {self.feedback} | {self.local_time_to_str()}"
