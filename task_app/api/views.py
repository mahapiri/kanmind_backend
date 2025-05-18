from drf_spectacular.utils import OpenApiResponse, extend_schema
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
    """
    View to list all tasks assigned to the current authenticated user.
    Returns a list of Task objects where the current user is assigned.
    """
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        user = self.request.user
        profile = Profile.objects.get(user=user)
        return profile

    @extend_schema(
        summary="Get tasks assigned to me",
        description="Returns all tasks that are assigned to the current authenticated user",
        tags=["Task"],
        responses={
            200: TaskSerializer(many=True),
            500: OpenApiResponse(description="Internal server error")
        }
    )
    def get(self, request, *args, **kwargs):
        try:
            profile = self.get_object()
            assigned_tasks = profile.assigned_task.all()
            serializer = TaskSerializer(assigned_tasks, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception:
            return Response({"error": "An internal server error occurred!"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ReviewerView(generics.GenericAPIView):
    """
    View to list all tasks where the current authenticated user is a reviewer.
    Returns Task objects associated with the user as a reviewer.
    """
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        """
        Retrieve the Profile object for the current user.

        Returns:
            Profile: The user's profile object

        Raises:
            Profile.DoesNotExist: If profile doesn't exist for user
        """
        user = self.request.user
        profile = Profile.objects.get(user=user)
        return profile

    @extend_schema(
        summary="Get tasks to review",
        description="Returns all tasks where the current authenticated user is assigned as a reviewer",
        tags=["Task"],
        responses={
            200: TaskSerializer(many=True),
            500: OpenApiResponse(description="Internal server error")
        }
    )
    def get(self, request, *args, **kwargs):
        try:
            profile = self.get_object()
            reviewer_tasks = profile.reviewer_task.all()
            serializer = TaskSerializer(reviewer_tasks, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception:
            return Response({"error": "An internal server error occurred!"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TaskView(viewsets.ModelViewSet):
    """
    ViewSet for managing task operations.
    Provides CRUD functionality for tasks with appropriate permissions.
    """
    serializer_class = TaskSerializer
    queryset = Task.objects.all()

    def get_permissions(self):
        """
        Determines the permissions required based on the HTTP method.

        - PUT/PATCH: Task owner or board member
        - DELETE: Task owner or board owner
        - Others: Board owner or member

        Returns:
            list: Instantiated permission classes
        """
        if self.request.method in ["PUT", "PATCH"]:
            permission_classes = [IsAuthenticated, TaskOwnerOrBoardMemberAuthentication]
        elif self.request.method == "DELETE":
            permission_classes = [IsAuthenticated, TaskOwnerOrBoardOwnerAuthentication]
        else:
            permission_classes = [IsAuthenticated, BoardOwnerOrMemberAuthentication]
        return [permission() for permission in permission_classes]

    @extend_schema(
        summary="Create a new task",
        description="Creates a task with optional assignees and reviewers",
        tags=["Task"],
        responses={
            201: TaskSerializer,
            400: OpenApiResponse(description="Invalid request data"),
            500: OpenApiResponse(description="Internal server error")
        }
    )
    def create(self, request, *args, **kwargs):
        user = request.user
        user_profile = Profile.objects.get(user=user)
        board_id = request.data.get("board")
        try:
            board = Board.objects.get(pk=board_id)
            print(board)
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
        except PermissionDenied as e:
            return Response({"error": f"{e}"}, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            return Response({"error": f"Internal Server error!{e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @extend_schema(
        summary="Update a task",
        description="Updates task details including assignees and reviewers",
        tags=["Task"],
        responses={
            200: TaskSerializer,
            400: OpenApiResponse(description="Invalid request data"),
            500: OpenApiResponse(description="Internal server error")
        }
    )
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        try:
            task = Task.objects.get(pk=instance.pk)
            board_id = task.board.pk
            board = Board.objects.get(pk=board_id)
            assignee_ids = self.get_profiles(board, board_id, request.data.get("assignee_id", []))
            reviewer_ids = self.get_profiles(board, board_id, request.data.get("reviewer_id", []))
            task.assignee.clear()
            task.reviewer.clear()
            serializer = self.get_serializer(instance, data=request.data, partial=partial, context={"request": request})
            serializer.is_valid(raise_exception=True)
            updated_task = serializer.save()
            self.create_profiles(assignee_ids, updated_task, "assignee")
            self.create_profiles(reviewer_ids, updated_task, "reviewer")
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ValidationError:
            return Response({"error": "Invalid request data"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            return Response({"error": "Internal Server error!"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @extend_schema(
        summary="Delete a task",
        description="Permanently removes a task",
        tags=["Task"],
        responses={
            204: OpenApiResponse(description="Task successfully deleted"),
            500: OpenApiResponse(description="Internal server error")
        }
    )
    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            self.perform_destroy(instance)
            return Response(None, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response({"error": f"Internal Server error!{e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def perform_destroy(self, instance):
        """
        Perform the deletion of the task instance.
        """
        instance.delete()

    def get_profiles(self, board, board_id, profile_ids):
        """
        Validate that profile IDs belong to board members.
        """
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
                    raise PermissionDenied(f"{profile.fullname} is not a board member")
            except Profile.DoesNotExist:
                raise NotFound("Profile was not found.")
        return profile_ids

    def create_profiles(self, profile_ids, task, field):
        """
        Add profiles to task as assignees or reviewers.
        """
        profiles = []
        for profile_id in profile_ids:
            try:
                profile = Profile.objects.get(id=profile_id)
                profiles.append(profile)
            except Profile.DoesNotExist:
                raise NotFound("Profile was not found.")
        if field == "reviewer":
            task.reviewer.set(profiles)
        elif field == "assignee":
            task.assignee.set(profiles)
        return profiles

class CommentListView(viewsets.ModelViewSet):
    """
    ViewSet for managing comments on tasks.
    Provides CRUD operations for comments with appropriate permissions based on user roles.
    """
    serializer_class = CommentSerializer

    def get_permissions(self):
        """
        Determine permissions based on the request method.
        """
        if self.request.method == "DELETE":
            permission_classes = [IsAuthenticated, CommentOwnerAuthentication]
        else:
            permission_classes = [IsAuthenticated, CommentIsBoardOwnerOrMemberAuthentication]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """
        Get all comments for a specific task.
        """
        task_id = self.kwargs.get("task_id")
        task = Task.objects.get(pk=task_id)
        queryset = task.comment.all()
        return queryset

    def get_object(self):
        """
        Get a specific comment by ID.
        """
        comment_id = self.kwargs.get("comment_id")
        if comment_id:
            comment = Comment.objects.get(pk=comment_id)
        return comment

    @extend_schema(
        summary="List comments for a task",
        description="Returns all comments associated with a specific task",
        tags=["Comment"],
        responses={
            200: CommentSerializer(many=True),
            500: OpenApiResponse(description="Internal server error")
        }
    )
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

    @extend_schema(
        summary="Create a comment",
        description="Creates a new comment on a specific task",
        tags=["Comment"],
        responses={
            201: CommentSerializer,
            400: OpenApiResponse(description="Invalid request data"),
            500: OpenApiResponse(description="Internal server error")
        }
    )
    def create(self, request, *args, **kwargs):
        task_id = self.kwargs.get("task_id")
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

    @extend_schema(
        summary="Delete a comment",
        description="Permanently removes a comment",
        tags=["Comment"],
        responses={
            204: OpenApiResponse(description="Comment successfully deleted"),
            500: OpenApiResponse(description="Internal server error")
        }
    )
    def destroy(self, request, *args, **kwargs):
        """
        Perform the deletion of the comment instance.
        """
        try:
            instance = self.get_object()
            self.perform_destroy(instance)
            return Response(None, status=status.HTTP_204_NO_CONTENT)
        except Exception:
            return Response({"error": f"Internal Server error!"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def perform_destroy(self, instance):
        instance.delete()
