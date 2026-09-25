from django.shortcuts import get_object_or_404
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.projects.models import Project
from apps.projects.serializers import ProjectSerializer
from apps.skills.models import Skill
from apps.skills.serializers import SkillSerializer
from apps.experience.models import Experience
from apps.experience.serializers import ExperienceSerializer
from apps.education.models import Education
from apps.education.serializers import EducationSerializer
from apps.certificates.models import Certificate
from apps.certificates.serializers import CertificateSerializer
from apps.resume.models import Resume
from apps.resume.serializers import ResumeSerializer
from .models import Profile
from .serializers import ProfileSerializer


class SiteView(APIView):
    """Compose the public portfolio using each domain's own serializer."""

    permission_classes = (AllowAny,)
    authentication_classes = ()

    def get(self, request):
        context = {"request": request}
        data = {"profile": ProfileSerializer(get_object_or_404(Profile, pk=1), context=context).data}
        for key, model, serializer in (
            ("projects", Project, ProjectSerializer),
            ("skills", Skill, SkillSerializer),
            ("experience", Experience, ExperienceSerializer),
            ("education", Education, EducationSerializer),
            ("certificates", Certificate, CertificateSerializer),
        ):
            data[key] = serializer(model.objects.filter(is_published=True), many=True, context=context).data
        resume = Resume.objects.filter(is_published=True).first()
        data["resume"] = ResumeSerializer(resume, context=context).data if resume else None
        return Response(data, headers={"Cache-Control": "no-cache"})
