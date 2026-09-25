from django import forms
from django.core.validators import MaxValueValidator

from apps.skills.models import Skill


class SkillForm(forms.ModelForm):
    class Meta:
        model = Skill
        fields = ("name", "category", "level", "sort_order", "is_published")
        labels = {"level": "Proficiency", "sort_order": "Display order", "is_published": "Published"}
        help_texts = {
            "category": "Choose an existing category or enter a new one. Skills are grouped by this name on your portfolio.",
            "sort_order": "Lower numbers appear first. Skills with the same order use their creation order, within each category.",
            "is_published": "Show this skill on your public portfolio. Uncheck to keep it as a private draft.",
        }
        widgets = {"category": forms.TextInput(attrs={"list": "skill-categories"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Keep values portable between the local SQLite and production database.
        self.fields["sort_order"].validators.append(MaxValueValidator(2147483647))
        self.fields["sort_order"].widget.attrs["max"] = 2147483647
        self.categories = Skill.objects.order_by("category").values_list("category", flat=True).distinct()
