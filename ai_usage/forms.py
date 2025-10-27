from django import forms
from ai_usage.models import AIFeedback


class AIFeedbackForm(forms.ModelForm):
    def __init__(self, *args, **kwargs) -> None:
        court = kwargs.pop("court")
        user = kwargs.pop("user")
        super().__init__(*args, **kwargs)
        self.initial["court"] = court
        self.initial["user"] = user

    class Meta:
        model = AIFeedback
        fields = ["text", "court", "user", "usage_groups"]
        labels = {
            "text": "Information"
        }
        widgets = {
            "text": forms.Textarea(),
            "court": forms.HiddenInput(),
            "user": forms.HiddenInput()
        }
