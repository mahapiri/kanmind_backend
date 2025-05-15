from django.core.exceptions import BadRequest, FieldError
from rest_framework import generics, status
from rest_framework.exceptions import AuthenticationFailed, NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import viewsets

from user_auth_app.models import Profile
from task_app.models import Comment, Task
from board_app.models import Board
from task_app.api.permissions import BoardOwnerOrMemberAuthentication, TaskOwnerAuthentication, BoardOwnerAuthentication
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
        except AuthenticationFailed:
            return Response({"error": "Not authorized. You should be logged in to see the tasks!"}, status=status.HTTP_401_UNAUTHORIZED)
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
        except AuthenticationFailed:
            return Response({"error": "Not authorized. You should be logged in to see the tasks!"}, status=status.HTTP_401_UNAUTHORIZED)
        except Exception:
            return Response({"error": "An internal server error occurred!"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TaskView(viewsets.ModelViewSet):
    serializer_class = TaskSerializer

    def get_queryset(self):
        user = self.request.user
        user_profile = Profile.objects.get(user=user)
        owned_boards = Board.objects.filter(owner=user_profile)
        board_members = user_profile.board_members.all()
        boards = owned_boards | board_members
        queryset = Task.objects.filter(board__in=boards).distinct()
        return queryset

    def get_permissions(self):
        if self.request.method == "DELETE":
            permission_classes = [IsAuthenticated, TaskOwnerAuthentication, BoardOwnerAuthentication]
        else:
            permission_classes = [IsAuthenticated, BoardOwnerOrMemberAuthentication]
        return [permission() for permission in permission_classes]

    def create(self, request, *args, **kwargs):
        user = request.user
        user_profile = Profile.objects.get(user=user)
        board_id = request.data.get("board")
        try:
            board = Board.objects.get(pk=board_id)
            assignees = self.get_assignees(board, board_id)
            reviewers = self.get_reviewers(board, board_id)

            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            task = serializer.save(owner=user_profile)

            self.create_assignees(assignees, task)
            self.create_reviewers(reviewers, task)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Board.DoesNotExist:
            return Response({"error": "Board does not exist!"}, status=status.HTTP_404_NOT_FOUND)
        except NotFound:
            return Response({"error": "Profil was not found"}, status=status.HTTP_404_NOT_FOUND)
        except AuthenticationFailed:
            return Response({"error": "Forbidden. You should be the owner or member of this board!"}, status=status.HTTP_403_FORBIDDEN)
        except ValidationError:
            return Response({"error": "Invalid request data"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            return Response({"error": "Internal Server error!"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()

        # user = request.user
        # user_profile = Profile.objects.get(user=user)

        task = Task.objects.filter(pk=instance.pk)
        board_id = task[0].board.pk
        board = Board.objects.get(pk=board_id)

        assignees = self.request.data.get("assignee_id", [])
        if assignees and not isinstance(assignees, list):
            assignees = [assignees]
        elif not assignees:
            assignees = []

        for assignee in assignees:
            try:
                profile = Profile.objects.get(id=assignee)
                is_board_member = board.owner == profile or profile.board_members.filter(
                    id=board_id).exists()
                if not is_board_member:
                    return Response({
                        "error": f"Reviewer with ID {assignee} does not exist!"
                    }, status=status.HTTP_400_BAD_REQUEST)
            except Profile.DoesNotExist:
                return Response({
                    "error": f"Profile with ID {assignee} does not exist!"
                })

        reviewers = self.request.data.get("reviewer_id", [])
        if reviewers and not isinstance(reviewers, list):
            reviewers = [reviewers]

        for reviewer in reviewers:
            try:
                profile = Profile.objects.get(id=reviewer)
                is_board_member = board.owner == profile or profile.board_members.filter(
                    id=board_id).exists()
                if not is_board_member:
                    return Response({
                        "error": f"Reviewer with ID {reviewer} does not exist!"
                    }, status=status.HTTP_400_BAD_REQUEST)
            except Profile.DoesNotExist:
                return Response({
                    "error": f"Profile with ID {reviewer} does not exist!"
                })
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial, context={"request": request})
        serializer.is_valid(raise_exception=True)
        try:
            task = serializer.save()
        except Exception as e:
            return Response({
                "error": "Task was not found!"
            }, status=status.HTTP_404_NOT_FOUND)

        task.assignee.clear()
        for assignee in assignees:
            profile = Profile.objects.get(id=assignee)
            task.assignee.add(profile)

        task.reviewer.clear()
        for reviewer in reviewers:
            profile = Profile.objects.get(id=reviewer)
            all_reviewer = task.reviewer.all()
            all_reviewer.delete()
            task.reviewer.add(profile)

        # task.owner.add(user_profile)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(None, status=status.HTTP_204_NO_CONTENT)

    def perform_destroy(self, instance):
        instance.delete()
    
    def get_assignees(self, board, board_id):
        assignees = self.request.data.get("assignee_id", [])
        if assignees and not isinstance(assignees, list):
            assignees = [assignees]
        elif assignees is None:
            assignees = []
        for assignee in assignees:
            try:
                profile = Profile.objects.get(id=assignee)
                is_board_member = board.owner == profile or profile.board_members.filter(id=board_id).exists()
                if not is_board_member:
                    raise AuthenticationFailed()
            except Profile.DoesNotExist:
                raise NotFound()
        return assignees  
            
    def get_reviewers(self, board, board_id):
        reviewers = self.request.data.get("reviewer_id", [])
        if reviewers and not isinstance(reviewers, list):
            reviewers = [reviewers]
        elif reviewers is None:
            reviewers = []
        for reviewer in reviewers:
            try:
                profile = Profile.objects.get(id=reviewer)
                is_board_member = board.owner == profile or profile.board_members.filter(id=board_id).exists()
                if not is_board_member:
                    raise AuthenticationFailed()
            except Profile.DoesNotExist:
                raise NotFound() 
        return reviewers   
            
    def create_assignees(self, assignees, task):
        for assignee in assignees:
            # müssen member des boards sein
            profile = Profile.objects.get(id=assignee)
            task.assignee.add(profile)
    
    def create_reviewers(self, reviewers, task):
        for reviewer in reviewers:
            # müssen member des boards sein
            profile = Profile.objects.get(id=reviewer)
            task.assignee.add(profile)


class CommentListView(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    # permission_classes = [isMemberOfBoardAuthentication] /// isMemberOfBoardAuthentication

    def get_queryset(self):
        user = self.request.user
        user_profile = Profile.objects.get(user=user)
        owned_boards = Board.objects.filter(owner=user_profile)
        board_members = user_profile.board_members.all()
        boards = owned_boards | board_members
        comments = Comment.objects.filter(task__board__in=boards)
        return comments

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = CommentSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        user = request.user
        user_profile = Profile.objects.get(user=user)
        task_id = self.kwargs.get("pk")

        try:
            task = Task.objects.get(pk=task_id)
        except Task.DoesNotExist:
            return Response({
                "error": "The task does not exist!"
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        serializer.save(task=task, author=user_profile)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def get_object(self):
        comment_id = self.kwargs.get("comment_id")
        task_id = self.kwargs.get("pk")

        if comment_id:
            queryset = self.filter_queryset(self.get_queryset())
            obj = generics.get_object_or_404(
                queryset, pk=comment_id, task=task_id)

            self.check_object_permissions(self.request, obj)
            return obj
        return super().get_object()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(None, status=status.HTTP_204_NO_CONTENT)

    def perform_destroy(self, instance):
        instance.delete()
