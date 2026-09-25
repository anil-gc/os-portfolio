from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.response import Response
from rest_framework import status
from .serializers import MessageSerializer


class MessageCreateView(CreateAPIView):
    authentication_classes = ()
    permission_classes = (AllowAny,)
    serializer_class = MessageSerializer
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = "contact"
    http_method_names = ["post", "options"]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        # Acknowledge receipt without returning message content or an internal ID.
        return Response({"detail": "Message received."}, status=status.HTTP_201_CREATED)
