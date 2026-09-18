from django.core.exceptions import ValidationError
from django.db import models
from apps.core.content import PublishedContent


class Education(PublishedContent):
    degree = models.CharField(max_length=160)
    institution = models.CharField(max_length=160)
    location = models.CharField(max_length=160, blank=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    description = models.TextField(max_length=8000, blank=True)

    class Meta(PublishedContent.Meta):
        abstract = False
        verbose_name_plural = "education"
        constraints = [models.CheckConstraint(condition=models.Q(end_date__isnull=True) | models.Q(end_date__gte=models.F("start_date")), name="education_valid_dates")]

    def clean(self):
        if self.end_date and self.start_date and self.end_date < self.start_date:
            raise ValidationError({"end_date": "End date cannot precede the start date."})

    def __str__(self):
        return f"{self.degree}, {self.institution}"
