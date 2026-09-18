from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny
from rest_framework.throttling import ScopedRateThrottle
from .serializers import MessageSerializer


class MessageCreateView(CreateAPIView):
    authentication_classes = ()
    permission_classes = (AllowAny,)
    serializer_class = MessageSerializer
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = "contact"
    http_method_names = ["post", "options"]
