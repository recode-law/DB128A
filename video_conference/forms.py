from django import forms
from video_conference.models import DetailedFeedback


class DetailedFeedbackForm(forms.ModelForm):
    def __init__(self, *args, **kwargs) -> None:
        court = kwargs.pop("court")
        user = kwargs.pop("user")
        super().__init__(*args, **kwargs)
        self.initial["court"] = court
        self.initial["user"] = user

    class Meta:
        model = DetailedFeedback
        fields = ["online_service_possible", "camera_perspectives", "conferencing_software", "feedback", "court", "user"]
        labels = {
            "online_service_possible": "Technische Ausstattung vorhanden?",
            "feedback": "Information zu diesem Gericht"
        }
        widgets = {
            "camera_perspectives": forms.CheckboxSelectMultiple(),
            "conferencing_software": forms.CheckboxSelectMultiple(),
            "court": forms.HiddenInput(),
            "user": forms.HiddenInput()
        }

    def clean(self):
        cleaned_data = super(DetailedFeedbackForm, self).clean()

        if cleaned_data["online_service_possible"]:
            if cleaned_data["camera_perspectives"].count() == 0:
                self.add_error("camera_perspectives", "Es muss ein Wert ausgewählt werden")
            if cleaned_data["conferencing_software"].count() == 0:
                self.add_error("conferencing_software", "Es muss ein Wert ausgewählt werden")

        return cleaned_data
