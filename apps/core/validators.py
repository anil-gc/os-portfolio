from django.core.exceptions import ValidationError
from PIL import Image, UnidentifiedImageError
import warnings


def validate_string_list(value):
    if not isinstance(value, list) or len(value) > 30 or any(
        not isinstance(item, str) or not item.strip() or len(item) > 80 for item in value
    ):
        raise ValidationError("Enter a JSON list of up to 30 nonempty strings, each up to 80 characters.")


def validate_resume_size(value):
    if value.size > 5 * 1024 * 1024:
        raise ValidationError("Resume files must be 5 MB or smaller.")


def validate_profile_image(value):
    if value.size > 5 * 1024 * 1024:
        raise ValidationError("Profile photos must be 5 MB or smaller.")
    was_closed = value.closed
    try:
        value.open("rb")
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            picture = Image.open(value)
            if picture.format not in ("JPEG", "PNG", "WEBP"):
                raise ValidationError("Choose a JPEG, PNG, or WebP photo.")
            if picture.width * picture.height > 20_000_000:
                raise ValidationError("Profile photos must be 20 megapixels or smaller.")
            picture.verify()
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError, Image.DecompressionBombWarning):
        raise ValidationError("Choose a valid JPEG, PNG, or WebP photo.")
    finally:
        if was_closed:
            value.close()
        else:
            value.seek(0)


def validate_resume_pdf(value):
    """Check the file signature as well as the extension and size validators."""
    was_closed = value.closed
    try:
        value.open("rb")
        header = value.read(5)
        value.seek(max(0, value.size - 1024))
        trailer = value.read()
        if header != b"%PDF-" or b"%%EOF" not in trailer:
            raise ValidationError("Choose a valid PDF document.")
    finally:
        if was_closed:
            value.close()
        else:
            value.seek(0)
