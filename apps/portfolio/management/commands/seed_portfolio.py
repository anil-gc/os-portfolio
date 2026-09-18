import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.projects.models import Project
from apps.skills.models import Skill
from apps.experience.models import Experience
from apps.education.models import Education
from apps.certificates.models import Certificate
from apps.resume.models import Resume
from apps.portfolio.models import Profile


class Command(BaseCommand):
    help = "Load a sample portfolio JSON into an empty portfolio. Never overwrite existing content."

    def add_arguments(self, parser):
        parser.add_argument("path", type=Path)

    @transaction.atomic
    def handle(self, *args, **options):
        if Profile.objects.exists():
            raise CommandError("A portfolio already exists. Seed skipped to preserve your content.")
        try:
            data = json.loads(options["path"].read_text(encoding="utf-8"))
            profile = Profile(**data["profile"])
            profile.full_clean()
            profile.save()
            for key, model in (
                ("projects", Project), ("skills", Skill), ("experience", Experience),
                ("education", Education), ("certificates", Certificate),
            ):
                for index, values in enumerate(data[key]):
                    record = model(**values, sort_order=index, is_published=True)
                    record.full_clean()
                    record.save()
            if data.get("resume"):
                values = {k: v for k, v in data["resume"].items() if k != "file_url"}
                record = Resume(**values, is_published=True)
                record.full_clean()
                record.save()
        except (OSError, ValueError, KeyError, TypeError) as exc:
            raise CommandError(f"Invalid portfolio seed: {exc}") from exc
        self.stdout.write(self.style.SUCCESS("Sample portfolio created. Edit it in Django admin."))
