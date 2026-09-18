from django.core.validators import FileExtensionValidator
from django.db import models
from apps.core.content import PublishedContent
from apps.core.validators import validate_resume_size


class Resume(PublishedContent):
    title = models.CharField(max_length=160)
    summary = models.TextField(max_length=4000)
    file = models.FileField(upload_to="resumes/%Y/%m/", blank=True, validators=[FileExtensionValidator(["pdf"]), validate_resume_size])

    def __str__(self):
        return self.title
