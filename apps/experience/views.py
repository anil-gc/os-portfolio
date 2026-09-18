from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny
from .models import Experience
from .serializers import ExperienceSerializer


class ExperienceListView(ListAPIView):
    permission_classes = (AllowAny,)
    authentication_classes = ()
    serializer_class = ExperienceSerializer
    queryset = Experience.objects.filter(is_published=True)
