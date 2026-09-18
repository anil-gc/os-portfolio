from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny
from .models import Certificate
from .serializers import CertificateSerializer


class CertificateListView(ListAPIView):
    permission_classes = (AllowAny,)
    authentication_classes = ()
    serializer_class = CertificateSerializer
    queryset = Certificate.objects.filter(is_published=True)
