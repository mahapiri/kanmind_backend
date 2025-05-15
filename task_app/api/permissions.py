from rest_framework import permissions
from rest_framework.exceptions import AuthenticationFailed, NotFound

from board_app.models import Board
from task_app.models import Task
from user_auth_app.models import Profile


class BoardOwnerOrMemberAuthentication(permissions.BasePermission):

    def has_permission(self, request, view):
        board_id = request.data.get('board')
        user = request.user
        try:
            user_profile = Profile.objects.get(user=user)
            board = Board.objects.get(pk=board_id)
            is_owner = board.owner == user_profile
            is_member = user_profile in board.members.all()

            if not (is_owner or is_member):
                raise AuthenticationFailed()
            return True
        except Board.DoesNotExist:
            raise NotFound()


class TaskOwnerOrMemberAuthentication(permissions.BasePermission):

    def has_permission(self, request, view):
        user = request.user
        try:
            profile = Profile.objects.get(user=user)
            task_id = view.kwargs.get("pk")
            task = Task.objects.get(id=task_id)
            if not task:
                raise NotFound()
            is_owner = task.owner == profile
            is_member = profile in task.board.members.all()
            if not (is_owner or is_member):
                raise AuthenticationFailed()
            return True
        except Profile.DoesNotExist:
            raise NotFound()
        

class TaskOwnerAuthentication(permissions.BasePermission):

    def has_permission(self, request, view):
        user = request.user
        try:
            profile = Profile.objects.get(user=user)
            task_id = view.kwargs.get("pk")
            task = Task.objects.get(id=task_id)
            if not task:
                raise NotFound()
            is_owner = task.owner == profile
            if not is_owner:
                raise AuthenticationFailed()
            return True
        except Profile.DoesNotExist:
            raise NotFound()



class BoardOwnerAuthentication(permissions.BasePermission):
    
    def has_permission(self, request, view):
        user = request.user
        try:
            user_profile = Profile.objects.get(user=user)
            task_id = view.kwargs.get("pk")
            task = Task.objects.get(id=task_id)
            board = task.board
            is_board_owner = board.owner == user_profile
            if not is_board_owner:
                raise AuthenticationFailed
            return True
        except Profile.DoesNotExist:
            return False
