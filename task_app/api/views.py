from rest_framework import generics, status
from rest_framework.response import Response

from task_app.api.permissions import IsAssigneeAuthentication, IsReviewerAuthentication
from task_app.api.serializer import TaskSerializer
from task_app.models import Task
from user_auth_app.models import Profile


class AssignedToMeView(generics.GenericAPIView):
    serializer_class = TaskSerializer
    permission_classes = [IsAssigneeAuthentication]

    def get_object(self):
        user = self.request.user
        user_profile = Profile.objects.get(user=user)
        return user_profile

    def get(self, request, *args, **kwargs):
        profile = self.get_object()
        assigned_tasks = profile.assigned_tasks.all()
        tasks = []
        for assigned_task in assigned_tasks:
            tasks.append(Task.objects.get(pk=assigned_task.id))

        serializer = TaskSerializer(tasks, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ReviewerView(generics.GenericAPIView):
    serializer_class = TaskSerializer
    permission_classes = [IsReviewerAuthentication]

    def get_object(self):
        user = self.request.user
        user_profile = Profile.objects.get(user=user)
        return user_profile

    def get(self, request, *args, **kwargs):
        profile = self.get_object()
        reviewer_tasks = profile.reviewer_tasks.all()
        tasks = []
        for reviewer_task in reviewer_tasks:
            tasks.append(Task.objects.get(pk=reviewer_task.id))

        serializer = TaskSerializer(tasks, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
