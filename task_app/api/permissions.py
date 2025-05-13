from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from board_app.models import Board
from user_auth_app.models import Profile
from task_app.models import Task


class IsAssigneeAuthentication(IsAuthenticated):
    message = "Not authorized. You should be logged in to get the task!"

    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False

        user = request.user
        try:
            user_profile = Profile.objects.get(user=user)
            assigned_tasks = user_profile.assigned_tasks.all()
            view.assigned_tasks = assigned_tasks
            return True
        except Profile.DoesNotExist:
            return False


class IsReviewerAuthentication(IsAuthenticated):
    message = "Not authorized. You should be logged in to get the task!"

    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False

        user = request.user
        try:
            user_profile = Profile.objects.get(user=user)
            reviewer_tasks = user_profile.reviewer_tasks.all()
            view.reviewer_tasks = reviewer_tasks
            return True
        except Profile.DoesNotExist:
            return False


class isMemberOfBoardAuthentication(IsAuthenticated):
    message = "Not authorized. You should be logged in to get the task!"

    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False

        user = request.user
        try:
            user_profile = Profile.objects.get(user=user)
            is_owner = Board.objects.filter(owner_id=user_profile).exists()
            is_member = user_profile.member_boards.exists()

            return is_owner or is_member
        except Profile.DoesNotExist:
            return False

class isOwnerOfTask(IsAuthenticated):
    message = "Not authorized. You are not a member of this task"

    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        
        user = request.user
        try: 
            user_profile = Profile.objects.get(user=user)
            is_owner = user_profile.own_tasks.exists()
            return is_owner
        except Profile.DoesNotExist:
            return False
        
class isOwnerOfBoard(IsAuthenticated):
    message = "Not authorized. You are not a owner of the board"

    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        
        user = request.user
        try: 
            user_profile = Profile.objects.get(user=user)
            is_owner = user_profile.boards.exists()
            return is_owner
        except Profile.DoesNotExist:
            return False