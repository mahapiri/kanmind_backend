from django.db import models
from rest_framework import generics, status
from rest_framework import permissions
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import AuthenticationFailed, MethodNotAllowed
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from board_app.api.permissions import BoardOwnerOrMemberAuthentication
from board_app.api.serializers import BoardReadSerializer, BoardWriteSerializer
from board_app.models import Board
from task_app.models import Task
from user_auth_app.models import Profile


class BoardListView(generics.ListAPIView):
    def get_permissions(self):
        if self.request.method == "GET":
            permission_classes = [BoardOwnerOrMemberAuthentication]
        elif self.request.method == "POST":
            permission_classes = [IsAuthenticated]
        else:
            raise MethodNotAllowed(self.request.method,
                                   detail="Only Get and Post are supported")
        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        if self.request.method == "GET":
            return BoardReadSerializer
        elif self.request.method == "POST":
            return BoardWriteSerializer
        else:
            raise MethodNotAllowed(self.request.method,
                                   detail="Only GET and POST are supported")

    def get(self, request):
        user = request.user
        profile = Profile.objects.filter(user=user).first()
        boards = Board.objects.filter(
            models.Q(owner_id=profile) | models.Q(members=profile)
        ).distinct()

        data = [self.set_board_view(board) for board in boards]
        return Response(data)

    def set_board_view(self, board):
        tasks = Task.objects.filter(board=board)
        return {
            "id": board.id,
            "title": board.title,
            "member_count": board.members.count(),
            "ticket_count": tasks.count(),
            "tasks_to_do_count": tasks.filter(status="to-do").count(),
            "tasks_high_prio_count": tasks.filter(priority="high").count(),
            "owner_id": board.owner_id.id,
        }

    def post(self, request):
        serializer = self.get_serializer(
            data=request.data, context={'request': request})
        user_id = self.get_user_from_token(request)
        profile = Profile.objects.filter(user_id=user_id).first()
        if not profile:
            return Response({"error": "No profile found for the user."}, status=status.HTTP_400_BAD_REQUEST)
        if serializer.is_valid():
            board = serializer.save(owner=profile)
            board_data = self.set_board_view(board)
            return Response(board_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get_user_from_token(self, request):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Token '):
            raise AuthenticationFailed("No valid Token found!")

        token_key = auth_header.split('Token ')[1]
        try:
            token = Token.objects.get(key=token_key)
            return token.user_id
        except Token.DoesNotExist:
            raise AuthenticationFailed("Invalid Token!")
