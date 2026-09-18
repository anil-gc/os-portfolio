from django.db import models
from apps.core.content import PublishedContent
from apps.core.validators import validate_string_list


class Project(PublishedContent):
    title = models.CharField(max_length=160)
    slug = models.SlugField(unique=True)
    category = models.CharField(max_length=60)
    summary = models.CharField(max_length=300)
    description = models.TextField(max_length=12000)
    technologies = models.JSONField(default=list, blank=True, validators=[validate_string_list])
    year = models.PositiveSmallIntegerField()
    featured = models.BooleanField(default=False)
    accent = models.CharField(max_length=12, choices=[(c, c.title()) for c in ("blue", "green", "violet", "orange")], default="blue")
    image_url = models.URLField(blank=True)
    live_url = models.URLField(blank=True)
    source_url = models.URLField(blank=True)

    def __str__(self):
        return self.title
