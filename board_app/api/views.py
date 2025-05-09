from rest_framework import generics
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from board_app.api.serializers import BoardSerializer
from board_app.models import Board


class BoardListView(generics.ListAPIView):
    serializer_class = BoardSerializer
    # permission_classes = [AllowAny]

    # def get(self, request, *args, **kwargs):
    #     serializer = self.get_serializer(data=request.data)
    #     token = serializer.validated_data["token"]

    #     example = 'Ok'
    #     return Response({
    #         "text": example
    #     })
