from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny
from .models import Project
from .serializers import ProjectSerializer


class ProjectListView(ListAPIView):
    permission_classes = (AllowAny,)
    authentication_classes = ()
    serializer_class = ProjectSerializer
    queryset = Project.objects.filter(is_published=True)
