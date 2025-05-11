from django.db import models
from rest_framework import generics
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from board_app.api.permissions import BoardOwnerOrMemberAuthentication
from board_app.api.serializers import BoardSerializer
from board_app.models import Board
from task_app.models import Task
from user_auth_app.models import Profile


class BoardListView(generics.ListAPIView):
    serializer_class = BoardSerializer
    permission_classes = [BoardOwnerOrMemberAuthentication]

    def get(self, request):
        user = request.user
        profile = Profile.objects.filter(user=user).first()
        boards = Board.objects.filter(
            models.Q(owner_id=profile) | models.Q(members=profile)
        ).distinct()

        for board in boards:
            data = self.setBoardView(board)
        return Response(data)

    def setBoardView(self, board):
        tasks = Task.objects.filter(board=board)
        data = []
        data.append({
            "id": board.id,
            "title": board.title,
            "member_count": board.members.count(),
            "ticket_count": tasks.count(),
            "tasks_to_do_count": tasks.filter(status="to-do").count(),
            "tasks_high_prio_count": tasks.filter(priority="high").count(),
            "owner_id": board.owner_id.id,
        })
        return data
