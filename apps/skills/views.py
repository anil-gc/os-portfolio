from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny
from .models import Skill
from .serializers import SkillSerializer


class SkillListView(ListAPIView):
    permission_classes = (AllowAny,)
    authentication_classes = ()
    serializer_class = SkillSerializer
    queryset = Skill.objects.filter(is_published=True)
