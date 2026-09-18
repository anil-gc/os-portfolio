from django.db import models
from apps.core.content import PublishedContent


class Skill(PublishedContent):
    name = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=80)
    level = models.CharField(max_length=40, choices=[(v, v) for v in ("Learning", "Proficient", "Advanced")], default="Proficient")

    def __str__(self):
        return self.name
