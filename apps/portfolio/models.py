from django.db import models

from apps.core.models import TimeStampedModel


class Profile(TimeStampedModel):
    id = models.PositiveSmallIntegerField(primary_key=True, default=1, editable=False)
    name = models.CharField(max_length=100)
    headline = models.CharField(max_length=160)
    location = models.CharField(max_length=160, blank=True)
    intro = models.CharField(max_length=200, blank=True)
    bio = models.TextField(max_length=2000)
    about = models.TextField(max_length=8000, blank=True)
    email = models.EmailField(blank=True)
    github_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)
    avatar_url = models.URLField(blank=True)
    available = models.BooleanField(default=False)
    is_demo = models.BooleanField(default=True, help_text="Keep enabled until all sample credentials and content have been replaced.")

    class Meta:
        constraints = [
            models.CheckConstraint(condition=models.Q(id=1), name="portfolio_single_profile"),
        ]

    def __str__(self):
        return self.name
