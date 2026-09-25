import tempfile
from io import BytesIO

from PIL import Image
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError, transaction
from django.forms.models import model_to_dict
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from apps.portfolio.models import Profile
from apps.resume.models import Resume
from apps.dashboard.profile_forms import ProfileForm


def photo(name="portrait.png", fmt="PNG"):
    stream = BytesIO()
    Image.new("RGB", (32, 32), "#4278ab").save(stream, format=fmt)
    return SimpleUploadedFile(name, stream.getvalue(), content_type=f"image/{fmt.lower()}")


def pdf(name="cv.pdf"):
    return SimpleUploadedFile(name, b"%PDF-1.4\n1 0 obj<</Type /Catalog>>endobj\ntrailer<</Root 1 0 R>>\n%%EOF\n", content_type="application/pdf")


class ProfileEditorTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = get_user_model().objects.create_superuser("profile-owner")
        cls.editor = get_user_model().objects.create_user("profile-editor", is_staff=True)
        cls.profile = Profile.objects.create(
            name="Portfolio Owner", headline="Developer", bio="Original introduction",
            about="Original about", location="Test city", is_demo=False,
        )

    def setUp(self):
        media = tempfile.TemporaryDirectory()
        self.addCleanup(media.cleanup)
        settings = override_settings(MEDIA_ROOT=media.name)
        settings.enable()
        self.addCleanup(settings.disable)
        self.client.force_login(self.owner)
        self.url = reverse("dashboard:profile")
        self.public_url = reverse("v1:portfolio:site")

    def payload(self, **changes):
        self.profile.refresh_from_db()
        data = model_to_dict(self.profile, fields=ProfileForm.Meta.fields)
        data.pop("avatar")
        for field in ("available", "is_demo"):
            if not data[field]:
                data.pop(field)
        resume = Resume.objects.filter(is_published=True).first() or Resume.objects.first()
        if resume:
            data.update({"resume-title": resume.title, "resume-summary": resume.summary})
            if resume.is_published:
                data["resume-is_published"] = "on"
        data.update(changes)
        return data

    def grant(self, *names):
        self.editor.user_permissions.set(Permission.objects.filter(codename__in=names))
        self.client.force_login(self.editor)

    def test_anonymous_get_and_post_redirect(self):
        self.client.logout()
        for method in (self.client.get, self.client.post):
            self.assertEqual(method(self.url).status_code, 302)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.headline, "Developer")

    def test_nonstaff_and_permissionless_staff_cannot_get_or_post(self):
        for staff in (False, True):
            self.editor.is_staff = staff
            self.editor.save()
            self.client.force_login(self.editor)
            for method in (self.client.get, self.client.post):
                self.assertEqual(method(self.url, self.payload()).status_code, 403)

    def test_inactive_staff_cannot_update(self):
        self.owner.is_active = False
        self.owner.save()
        self.assertEqual(self.client.post(self.url, self.payload(headline="Blocked")).status_code, 302)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.headline, "Developer")

    def test_view_and_add_permissions_cannot_edit_existing_profile(self):
        for permission in ("view_profile", "add_profile"):
            self.grant(permission)
            self.assertEqual(self.client.post(self.url, self.payload()).status_code, 403)

    def test_editor_get_prefilled_private_page_and_navigation(self):
        response = self.client.get(self.url)
        self.assertContains(response, 'value="Portfolio Owner"')
        self.assertContains(response, "Original about")
        self.assertContains(response, 'enctype="multipart/form-data"')
        self.assertContains(response, 'href="/dashboard/profile/" aria-current="page"')
        self.assertIn("no-store", response.headers["Cache-Control"])
        self.assertNotContains(response, "Delete profile")

    def test_profile_change_permission_does_not_grant_resume_access(self):
        self.grant("change_profile")
        self.assertNotContains(self.client.get(self.url), 'name="resume-title"')
        self.assertEqual(self.client.post(self.url, self.payload(headline="Changed")).status_code, 302)
        self.assertEqual(self.client.post(self.url, self.payload(**{"resume-title": "Forged"})).status_code, 403)
        self.assertEqual(Resume.objects.count(), 0)

    def test_csrf_required(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.owner)
        self.assertEqual(client.post(self.url, self.payload()).status_code, 403)

    def test_full_profile_save_reaches_public_api(self):
        changes = dict(name="Updated Owner", headline="Updated headline", intro="Updated hero", bio="Updated introduction", about="Updated about", email="owner@example.com", github_url="https://github.com/example", linkedin_url="https://www.linkedin.com/in/example/", available="on")
        response = self.client.post(self.url, self.payload(**changes), follow=True)
        self.assertContains(response, "Profile changes saved")
        public = self.client.get(self.public_url).json()["profile"]
        for name, value in changes.items():
            self.assertEqual(public[name], True if name == "available" else value)
        self.assertEqual(public["location"], "Test city")
        self.assertEqual(Profile.objects.count(), 1)
        self.assertNotIn("id", public)
        self.assertNotIn("avatar", public)

    def test_optional_values_can_be_cleared(self):
        self.assertEqual(self.client.post(self.url, self.payload(about="", email="", location="", github_url="", linkedin_url="", avatar_url="")).status_code, 302)
        public = self.client.get(self.public_url).json()["profile"]
        for name in ("about", "email", "location", "github_url", "linkedin_url", "avatar_url"):
            self.assertEqual(public[name], "")

    def test_invalid_fields_show_errors_and_save_nothing(self):
        for changes in ({"name": ""}, {"headline": "a" * 161}, {"email": "invalid"}, {"github_url": "javascript:alert(1)"}, {"linkedin_url": "ftp://example.com"}, {"avatar_url": "not-a-url"}):
            with self.subTest(changes=changes):
                response = self.client.post(self.url, self.payload(**changes))
                self.assertEqual(response.status_code, 200)
                self.assertTrue(response.context["form"].errors)
                self.profile.refresh_from_db()
                self.assertEqual(self.profile.headline, "Developer")

    def test_content_is_escaped_in_editor(self):
        self.client.post(self.url, self.payload(about='<script>alert("x")</script>'))
        response = self.client.get(self.url)
        self.assertContains(response, "&lt;script&gt;")
        self.assertNotContains(response, '<script>alert("x")</script>')

    def test_empty_database_get_does_not_create_and_post_creates_singleton(self):
        Profile.objects.all().delete()
        self.grant("change_profile")
        self.assertEqual(self.client.get(self.url).status_code, 403)
        self.grant("add_profile")
        self.assertEqual(self.client.get(self.url).status_code, 200)
        self.assertEqual(Profile.objects.count(), 0)
        self.assertEqual(self.client.post(self.url, {"name": "Owner", "headline": "Headline", "bio": "Bio"}).status_code, 302)
        self.assertEqual(list(Profile.objects.values_list("pk", flat=True)), [1])
        self.assertEqual(self.client.post(self.url, {"name": "Overwrite"}).status_code, 403)

    def test_database_rejects_second_profile_id(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Profile.objects.create(pk=2, name="Other", headline="Other", bio="Other")

    def test_photo_upload_and_preservation(self):
        self.assertEqual(self.client.post(self.url, self.payload(avatar=photo())).status_code, 302)
        self.profile.refresh_from_db()
        path = self.profile.avatar.name
        self.assertTrue(self.profile.avatar.storage.exists(path))
        public = self.client.get(self.public_url).json()["profile"]
        self.assertEqual(public["avatar_url"], f"http://testserver/media/{path}")
        self.assertEqual(self.client.post(self.url, self.payload(headline="Unrelated edit")).status_code, 302)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.avatar.name, path)

    def test_jpeg_and_webp_uploads(self):
        for filename, fmt in (("photo.jpg", "JPEG"), ("photo.webp", "WEBP")):
            with self.subTest(fmt=fmt):
                self.assertEqual(self.client.post(self.url, self.payload(avatar=photo(filename, fmt))).status_code, 302)

    def test_bad_image_and_executable_extensions_rejected(self):
        for upload in (SimpleUploadedFile("bad.png", b"not an image"), photo("picture.exe"), photo("picture.gif", "GIF")):
            response = self.client.post(self.url, self.payload(avatar=upload))
            self.assertIn("avatar", response.context["form"].errors)
        self.profile.refresh_from_db()
        self.assertFalse(self.profile.avatar)

    def test_oversize_image_rejected(self):
        upload = photo()
        upload = SimpleUploadedFile("large.png", upload.read() + b"0" * (5 * 1024 * 1024))
        response = self.client.post(self.url, self.payload(avatar=upload))
        self.assertIn("avatar", response.context["form"].errors)

    def test_image_pixel_limit(self):
        stream = BytesIO()
        Image.new("1", (5000, 4001)).save(stream, format="PNG")
        response = self.client.post(self.url, self.payload(avatar=SimpleUploadedFile("large.png", stream.getvalue())))
        self.assertContains(response, "20 megapixels")

    def test_replacement_uses_new_filename_and_keeps_old_file(self):
        self.client.post(self.url, self.payload(avatar=photo()))
        self.profile.refresh_from_db()
        previous = self.profile.avatar.name
        self.client.post(self.url, self.payload(avatar=photo()))
        self.profile.refresh_from_db()
        self.assertNotEqual(previous, self.profile.avatar.name)
        self.assertTrue(self.profile.avatar.storage.exists(previous))

    def test_clear_uploaded_photo_uses_external_url_then_initials(self):
        self.client.post(self.url, self.payload(avatar=photo(), avatar_url="https://example.com/portrait.jpg"))
        self.assertIn("/media/profiles/", self.client.get(self.public_url).json()["profile"]["avatar_url"])
        self.client.post(self.url, self.payload(**{"avatar-clear": "on"}))
        self.assertEqual(self.client.get(self.public_url).json()["profile"]["avatar_url"], "https://example.com/portrait.jpg")
        self.client.post(self.url, self.payload(avatar_url=""))
        self.assertEqual(self.client.get(self.public_url).json()["profile"]["avatar_url"], "")

    def resume_payload(self, **changes):
        return self.payload(**{"resume-title": "My CV", "resume-summary": "My summary", "resume-is_published": "on", **changes})

    def test_resume_upload_public_link_and_preservation(self):
        self.assertEqual(self.client.post(self.url, self.resume_payload(**{"resume-file": pdf()})).status_code, 302)
        resume = Resume.objects.get()
        link = self.client.get(self.public_url).json()["resume"]["file_url"]
        self.assertEqual(link, f"http://testserver{resume.file.url}")
        previous = resume.file.name
        self.client.post(self.url, self.payload(headline="Only headline"))
        resume.refresh_from_db()
        self.assertEqual(resume.file.name, previous)
        self.assertEqual(resume.summary, "My summary")
        self.assertEqual(resume.title, "My CV")

    def test_resume_replacement_and_clear(self):
        self.client.post(self.url, self.resume_payload(**{"resume-file": pdf()}))
        old = self.client.get(self.public_url).json()["resume"]["file_url"]
        self.client.post(self.url, self.payload(**{"resume-file": pdf()}))
        new = self.client.get(self.public_url).json()["resume"]["file_url"]
        self.assertNotEqual(old, new)
        self.client.post(self.url, self.payload(**{"resume-file-clear": "on"}))
        self.assertIsNone(self.client.get(self.public_url).json()["resume"]["file_url"])

    def test_invalid_resume_prevents_profile_save(self):
        for upload in (pdf("cv.exe"), SimpleUploadedFile("fake.pdf", b"executable"), SimpleUploadedFile("truncated.pdf", b"%PDF-1.4"), SimpleUploadedFile("huge.pdf", b"%PDF-" + b"0" * (5 * 1024 * 1024) + b"%%EOF")):
            response = self.client.post(self.url, self.resume_payload(headline="Must not save", **{"resume-file": upload}))
            self.assertIn("file", response.context["resume_form"].errors)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.headline, "Developer")
        self.assertEqual(Resume.objects.count(), 0)

    def test_blank_resume_does_not_create_record(self):
        self.client.post(self.url, self.payload())
        self.assertEqual(Resume.objects.count(), 0)

    def test_partial_new_resume_returns_useful_errors(self):
        response = self.client.post(self.url, self.payload(**{"resume-file": pdf()}))
        self.assertIn("title", response.context["resume_form"].errors)
        self.assertIn("summary", response.context["resume_form"].errors)

    def test_reuses_existing_draft_without_publishing_implicitly(self):
        resume = Resume.objects.create(title="Draft", summary="Draft summary")
        self.client.post(self.url, self.payload(headline="Changed"))
        self.assertEqual(Resume.objects.count(), 1)
        self.assertIsNone(self.client.get(self.public_url).json()["resume"])
        resume.refresh_from_db()
        self.assertFalse(resume.is_published)

    def test_edits_public_resume_before_other_drafts(self):
        draft = Resume.objects.create(title="Draft", summary="Leave alone", sort_order=0)
        current = Resume.objects.create(title="Current", summary="Public", is_published=True, sort_order=5)
        self.client.post(self.url, self.payload(**{"resume-summary": "New public summary"}))
        current.refresh_from_db()
        draft.refresh_from_db()
        self.assertEqual(current.summary, "New public summary")
        self.assertEqual(draft.summary, "Leave alone")

    def test_resume_change_permission_required_for_existing_resume(self):
        Resume.objects.create(title="Current", summary="Summary")
        self.grant("change_profile", "add_resume")
        self.assertEqual(self.client.post(self.url, self.payload(**{"resume-title": "Forbidden"})).status_code, 403)
        self.grant("change_profile", "change_resume")
        self.assertEqual(self.client.post(self.url, self.payload(**{"resume-title": "Allowed"})).status_code, 302)

    def test_public_api_remains_read_only(self):
        self.assertEqual(self.client.post(self.public_url, {"headline": "Forged"}).status_code, 405)
