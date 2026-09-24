from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.utils.text import slugify

from apps.core.validators import validate_string_list
from apps.projects.models import Project


class ProjectForm(forms.ModelForm):
    slug = forms.SlugField(
        required=False, max_length=50,
        help_text="Used in the public project link. Leave blank to generate from the title. Changing it changes the link.",
    )
    technologies = forms.CharField(
        required=False, widget=forms.Textarea(attrs={"rows": 4}),
        help_text="One technology per line. Up to 30 entries, 80 characters each.",
    )

    class Meta:
        model = Project
        fields = (
            "title", "slug", "category", "year", "summary", "description", "technologies",
            "image_url", "source_url", "live_url", "accent", "sort_order", "featured", "is_published",
        )
        labels = {
            "image_url": "Project image URL", "source_url": "Source / GitHub URL",
            "live_url": "Live / demo URL", "accent": "Fallback artwork color",
            "sort_order": "Display order", "featured": "Featured project", "is_published": "Published",
        }
        help_texts = {
            "image_url": "Use an HTTP or HTTPS image URL. Leave blank for the portfolio's built-in artwork. File uploads are not supported by this model.",
            "summary": "A short introduction for project cards (up to 300 characters).",
            "description": "Full project description. Plain text, up to 12,000 characters.",
            "sort_order": "Lower numbers appear first. Projects with the same order use their creation order.",
            "featured": "Include this project in Selected work when published.",
            "is_published": "Make this project visible on the public portfolio. Unchecked projects stay as private drafts.",
        }
        widgets = {
            "summary": forms.Textarea(attrs={"rows": 3}),
            "description": forms.Textarea(attrs={"rows": 7}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.is_bound:
            self.initial["technologies"] = "\n".join(self.instance.technologies or [])
        self.fields["year"].min_value = 1
        self.fields["year"].max_value = 9999
        self.fields["year"].widget.attrs.update(min=1, max=9999)
        for name in ("image_url", "source_url", "live_url"):
            self.fields[name].validators.append(URLValidator(schemes=["http", "https"]))
            self.fields[name].widget.attrs["placeholder"] = "https://"

    def clean_slug(self):
        slug = self.cleaned_data["slug"] or slugify(self.cleaned_data.get("title", ""))[:50]
        if not slug:
            raise forms.ValidationError("Enter a link slug using letters, numbers, hyphens or underscores.")
        return slug

    def clean_technologies(self):
        values = [line.strip() for line in self.cleaned_data["technologies"].splitlines() if line.strip()]
        try:
            validate_string_list(values)
        except ValidationError as error:
            raise forms.ValidationError("Enter up to 30 technologies, one per line, with at most 80 characters each.") from error
        return list(dict.fromkeys(values))

    def clean_year(self):
        year = self.cleaned_data["year"]
        if not 1 <= year <= 9999:
            raise forms.ValidationError("Enter a year between 1 and 9999.")
        return year
