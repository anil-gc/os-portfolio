from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny
from .models import Education
from .serializers import EducationSerializer


class EducationListView(ListAPIView):
    permission_classes = (AllowAny,)
    authentication_classes = ()
    serializer_class = EducationSerializer
    queryset = Education.objects.filter(is_published=True)
