from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

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
