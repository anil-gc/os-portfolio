from django.core.exceptions import ValidationError


def validate_string_list(value):
    if not isinstance(value, list) or len(value) > 30 or any(
        not isinstance(item, str) or not item.strip() or len(item) > 80 for item in value
    ):
        raise ValidationError("Enter a JSON list of up to 30 nonempty strings, each up to 80 characters.")


def validate_resume_size(value):
    if value.size > 5 * 1024 * 1024:
        raise ValidationError("Resume files must be 5 MB or smaller.")
