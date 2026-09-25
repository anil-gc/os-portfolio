"""Forms for the existing experience, education, and certificate records."""

from django import forms
from django.core.validators import MaxValueValidator, URLValidator

from apps.certificates.models import Certificate
from apps.education.models import Education
from apps.experience.models import Experience


class PublishedEntryForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        order = self.fields["sort_order"]
        order.label = "Display order"
        order.help_text = "Lower numbers appear first. Entries with the same order use their creation order."
        order.validators.append(MaxValueValidator(2147483647))
        order.widget.attrs["max"] = 2147483647
        self.fields["is_published"].label = "Published"
        self.fields["is_published"].help_text = "Show this entry on your public portfolio. Uncheck to keep it as a private draft."
        for field in self.fields.values():
            if isinstance(field, forms.DateField):
                field.widget = forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"})
        if "end_date" in self.fields:
            self.fields["end_date"].help_text = "Leave blank for an ongoing entry, shown as Present on your portfolio. Otherwise, use a date on or after the start date."

    @property
    def detail_fields(self):
        return [self[name] for name in self.fields if name not in ("sort_order", "is_published")]


class ExperienceForm(PublishedEntryForm):
    class Meta:
        model = Experience
        fields = ("role", "company", "location", "start_date", "end_date", "description", "sort_order", "is_published")
        labels = {"role": "Role / job title"}
        widgets = {"description": forms.Textarea(attrs={"rows": 6})}
        help_texts = {"description": "Describe your responsibilities and contributions. Plain text, up to 8,000 characters."}


class EducationForm(PublishedEntryForm):
    class Meta:
        model = Education
        fields = ("degree", "institution", "location", "start_date", "end_date", "description", "sort_order", "is_published")
        labels = {"degree": "Degree / qualification"}
        widgets = {"description": forms.Textarea(attrs={"rows": 6})}
        help_texts = {"description": "Optional details about your studies. Plain text, up to 8,000 characters."}


class CertificateForm(PublishedEntryForm):
    class Meta:
        model = Certificate
        fields = ("title", "issuer", "issued_date", "credential_url", "description", "sort_order", "is_published")
        labels = {"title": "Certificate name", "issuer": "Issuing organization", "issued_date": "Issue date", "credential_url": "Credential URL"}
        widgets = {"description": forms.Textarea(attrs={"rows": 5})}
        help_texts = {
            "credential_url": "Optional HTTP or HTTPS link to verify this credential.",
            "description": "Optional details about this certificate. Plain text, up to 4,000 characters.",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        field = self.fields["credential_url"]
        field.validators = [validator for validator in field.validators if not isinstance(validator, URLValidator)]
        field.validators.append(URLValidator(schemes=["http", "https"]))
        field.widget.attrs["placeholder"] = "https://"
