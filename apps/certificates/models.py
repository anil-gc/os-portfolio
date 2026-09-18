from django.db import models
from apps.core.content import PublishedContent


class Certificate(PublishedContent):
    title = models.CharField(max_length=160)
    issuer = models.CharField(max_length=160)
    issued_date = models.DateField()
    credential_url = models.URLField(blank=True)
    description = models.TextField(max_length=4000, blank=True)

    def __str__(self):
        return self.title
