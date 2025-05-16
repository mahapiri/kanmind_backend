from rest_framework import generics, status
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import viewsets

from user_auth_app.models import Profile
from task_app.models import Comment, Task
from board_app.models import Board
from task_app.api.permissions import BoardOwnerOrMemberAuthentication, CommentIsBoardOwnerOrMemberAuthentication, CommentOwnerAuthentication, TaskOwnerOrBoardOwnerAuthentication, TaskOwnerOrBoardMemberAuthentication
from task_app.api.serializers import CommentSerializer, TaskSerializer


class AssignedToMeView(generics.GenericAPIView):
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        user = self.request.user
        profile = Profile.objects.get(user=user)
        return profile

    def get(self, request, *args, **kwargs):
        try:
            profile = self.get_object()
            assigned_tasks = profile.assigned_task.all()
            serializer = TaskSerializer(assigned_tasks, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception:
            return Response({"error": "An internal server error occurred!"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ReviewerView(generics.GenericAPIView):
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        user = self.request.user
        profile = Profile.objects.get(user=user)
        return profile

    def get(self, request, *args, **kwargs):
        try:
            profile = self.get_object()
            reviewer_tasks = profile.reviewer_task.all()
            serializer = TaskSerializer(reviewer_tasks, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception:
            return Response({"error": "An internal server error occurred!"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TaskView(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    queryset = Task.objects.all()

    def get_permissions(self):
        if self.request.method in ["PUT", "PATCH"]:
            permission_classes = [IsAuthenticated, TaskOwnerOrBoardMemberAuthentication]
        elif self.request.method == "DELETE":
            permission_classes = [IsAuthenticated, TaskOwnerOrBoardOwnerAuthentication]
        else:
            permission_classes = [IsAuthenticated, BoardOwnerOrMemberAuthentication]
        return [permission() for permission in permission_classes]

    def create(self, request, *args, **kwargs):
        user = request.user
        user_profile = Profile.objects.get(user=user)
        board_id = request.data.get("board")
        try:
            board = Board.objects.get(pk=board_id)
            assignees = self.get_profiles(board, board_id, self.request.data.get("assignee_id", []))
            reviewers = self.get_profiles(board, board_id, self.request.data.get("reviewer_id", []))

            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            task = serializer.save(owner=user_profile)

            self.create_profiles(assignees, task, "assignee")
            self.create_profiles(reviewers, task, "reviewer")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except ValidationError:
            return Response({"error": "Invalid request data"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            return Response({"error": "Internal Server error!"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        try:
            task = Task.objects.filter(pk=instance.pk)
            board_id = task[0].board.pk
            board = Board.objects.get(pk=board_id)
            assignees, reviewers = (self.get_profiles(board, board_id, self.request.data.get("assignee_id", [])), self.get_profiles(board, board_id, self.request.data.get("reviewer_id", [])))
            serializer = self.get_serializer(instance, data=request.data, partial=partial, context={"request": request})
            serializer.is_valid(raise_exception=True)
            task = serializer.save()
            clear_profiles = task.assignee.clear() and task.reviewer.clear()
            self.create_profiles(assignees, task, "assignee")
            self.create_profiles(reviewers, task, "reviewer")
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ValidationError:
            return Response({"error": "Invalid request data"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            return Response({"error": "Internal Server error!"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            self.perform_destroy(instance)
            return Response(None, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response({"error": f"Internal Server error!{e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def perform_destroy(self, instance):
        instance.delete()

    def get_profiles(self, board, board_id, profile_ids):
        if profile_ids and not isinstance(profile_ids, list):
            profile_ids = [profile_ids]
        elif profile_ids is None:
            profile_ids = []
        for profile_id in profile_ids:
            try:
                profile = Profile.objects.get(id=profile_id)
                is_board_member = board.owner == profile or profile.board_members.filter(
                    id=board_id).exists()
                if not is_board_member:
                    raise PermissionDenied("You are not a board member")
            except Profile.DoesNotExist:
                    raise NotFound("Profile was not found.")
        return profile_ids

    def create_profiles(self, profile_ids, task, field):
        for profile_id in profile_ids:
            try:
                profile = Profile.objects.get(id=profile_id)
                if field == "reviewer":
                    task.reviewer.add(profile)
                elif field == "assignee":
                    task.assignee.add(profile)
            except Profile.DoesNotExist:
                raise NotFound("Profile was not found.")


class CommentListView(viewsets.ModelViewSet):
    serializer_class = CommentSerializer

    def get_permissions(self):
        if self.request.method == "DELETE":
            permission_classes = [IsAuthenticated, CommentOwnerAuthentication]
        else:
            permission_classes = [IsAuthenticated, CommentIsBoardOwnerOrMemberAuthentication]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        task_id = self.kwargs.get("task_id")
        task = Task.objects.get(pk=task_id)
        queryset = task.comment.all()
        return queryset

    def get_object(self):
        comment_id = self.kwargs.get("comment_id")
        if comment_id:
            comment = Comment.objects.get(pk=comment_id)
        return comment

    def list(self, request, *args, **kwargs):
        try:
            queryset = self.get_queryset()
            serializer = CommentSerializer(queryset, many=True)
            if not serializer.data:
                return Response(None, status=status.HTTP_200_OK)
            else:
                return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception:
            return Response({"error": "Internal Server error!"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def create(self, request, *args, **kwargs):
        task_id = self.kwargs.get("task_id")
        comment_id = self.kwargs.get("comment_id")
        user = request.user
        try:
            user_profile = Profile.objects.get(user=user)
            task = Task.objects.get(pk=task_id)
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(task=task, author=user_profile)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except ValidationError:
            return Response({"error": "Invalid request data"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            return Response({"error": "Internal Server error!"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            self.perform_destroy(instance)
            return Response(None, status=status.HTTP_204_NO_CONTENT)
        except Exception:
            return Response({"error": f"Internal Server error!"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def perform_destroy(self, instance):
        instance.delete()
