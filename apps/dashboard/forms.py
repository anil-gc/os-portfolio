from django.contrib.auth.forms import AuthenticationForm


class StaffAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update(
            {"placeholder": "Your username", "autocapitalize": "none", "spellcheck": "false"}
        )
        self.fields["password"].widget.attrs["placeholder"] = "Your password"

    def confirm_login_allowed(self, user):
        # Use the same message for invalid credentials, inactive and non-staff accounts.
        if not user.is_active or not user.is_staff:
            raise self.get_invalid_login_error()
