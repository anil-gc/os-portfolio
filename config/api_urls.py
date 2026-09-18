from django.urls import include, path

app_name = "v1"

urlpatterns = [
    path("core/", include("apps.core.urls", namespace="core")),
    path("portfolio/", include("apps.portfolio.urls", namespace="portfolio")),
    path("projects/", include("apps.projects.urls", namespace="projects")),
    path("skills/", include("apps.skills.urls", namespace="skills")),
    path("experience/", include("apps.experience.urls", namespace="experience")),
    path("certificates/", include("apps.certificates.urls", namespace="certificates")),
    path("education/", include("apps.education.urls", namespace="education")),
    path("contact/", include("apps.contact.urls", namespace="contact")),
    path("resume/", include("apps.resume.urls", namespace="resume")),
]
