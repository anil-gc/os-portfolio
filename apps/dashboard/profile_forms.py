"""The owner's existing profile and current resume, edited together."""

from django import forms
from django.core.validators import URLValidator

from apps.portfolio.models import Profile
from apps.resume.models import Resume


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = (
            "name", "headline", "location", "intro", "bio", "about", "email",
            "github_url", "linkedin_url", "avatar", "avatar_url", "available", "is_demo",
        )
        labels = {
            "headline": "Professional headline", "intro": "Hero heading",
            "bio": "Short introduction", "about": "About you",
            "avatar": "Profile photo", "avatar_url": "External photo URL",
            "github_url": "GitHub URL", "linkedin_url": "LinkedIn URL",
            "available": "Available for work", "is_demo": "Show sample-content labels",
        }
        help_texts = {
            "headline": "Shown beside your name in the sidebar, About, and resume.",
            "intro": "The main heading on Overview. Leave blank to use the existing default heading.",
            "bio": "Shown below your hero heading. Plain text, up to 2,000 characters.",
            "about": "Plain text, up to 8,000 characters. Separate paragraphs with a blank line.",
            "email": "Public contact email. Leave blank to hide it.",
            "avatar": "JPEG, PNG, or WebP. Up to 5 MB and 20 megapixels. No selection keeps the current photo.",
            "avatar_url": "Optional HTTP or HTTPS photo link. An uploaded photo takes priority; clear it to use this URL. Leave both empty for initials.",
            "github_url": "Optional HTTP or HTTPS link. Leave blank to hide it.",
            "linkedin_url": "Optional HTTP or HTTPS link. Leave blank to hide it.",
            "available": "Controls the availability status shown on your portfolio.",
            "is_demo": "Keep enabled while the portfolio contains sample personal credentials.",
        }
        widgets = {
            "intro": forms.Textarea(attrs={"rows": 2}),
            "bio": forms.Textarea(attrs={"rows": 4}),
            "about": forms.Textarea(attrs={"rows": 8}),
            "avatar": forms.ClearableFileInput(attrs={"accept": "image/jpeg,image/png,image/webp"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ("github_url", "linkedin_url", "avatar_url"):
            field = self.fields[name]
            field.validators = [v for v in field.validators if not isinstance(v, URLValidator)]
            field.validators.append(URLValidator(schemes=["https", "http"]))

    @property
    def sections(self):
        return [(title, [self[name] for name in names]) for title, names in (
            ("Basic information", ("name", "headline", "location")),
            ("Hero", ("intro", "bio")),
            ("About", ("about",)),
            ("Contact and social links", ("email", "github_url", "linkedin_url")),
        )]


class ProfileResumeForm(forms.ModelForm):
    class Meta:
        model = Resume
        fields = ("title", "summary", "file", "is_published")
        labels = {"title": "Resume title", "summary": "Resume summary", "file": "Resume PDF", "is_published": "Show resume publicly"}
        widgets = {
            "summary": forms.Textarea(attrs={"rows": 4}),
            "file": forms.ClearableFileInput(attrs={"accept": "application/pdf,.pdf"}),
        }
        help_texts = {
            "file": "PDF only, up to 5 MB. No selection keeps the current file. Without a file, visitors can print the existing resume page.",
            "is_published": "Uncheck to keep this resume private in the portfolio API.",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # A fresh profile need not have a resume. An entirely blank section is a no-op.
        if not self.instance.pk:
            self.fields["title"].required = False
            self.fields["summary"].required = False

    def clean(self):
        data = super().clean()
        if not self.instance.pk and any(data.get(key) for key in self.fields):
            for key in ("title", "summary"):
                if not data.get(key):
                    self.add_error(key, "Enter this field when adding a resume.")
        return data

    @property
    def should_save(self):
        return bool(self.instance.pk or any(self.cleaned_data.values()))
