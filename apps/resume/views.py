from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny
from .models import Resume
from .serializers import ResumeSerializer


class ResumeListView(ListAPIView):
    permission_classes = (AllowAny,)
    authentication_classes = ()
    serializer_class = ResumeSerializer
    queryset = Resume.objects.filter(is_published=True)
