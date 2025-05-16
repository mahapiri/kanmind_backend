from django.db import models
from django.http import Http404

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import generics, status
from rest_framework import viewsets
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import AuthenticationFailed, NotFound
from rest_framework.fields import ObjectDoesNotExist
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import viewsets

from user_auth_app.models import Profile
from board_app.models import Board
from task_app.models import Task
from board_app.api.permissions import BoardOwnerAuthentication, BoardOwnerOrMemberAuthentication
from board_app.api.serializers import BoardReadSerializer, BoardSerializer, BoardUpdateSerializer, BoardWriteSerializer


class BoardListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        # Dynamic serializer selection based on HTTP method
        if self.request.method == "GET":
            return BoardReadSerializer
        elif self.request.method == "POST":
            return BoardWriteSerializer

    @extend_schema(
        summary="List user boards",
        description="Returns all boards where the user is either owner or member",
        tags=["Board"],
        responses={
            200: BoardReadSerializer(many=True),
            500: OpenApiResponse(description="Internal server error"),
        }
    )
    def get(self, request):
        try:
            user = request.user
            profile = Profile.objects.filter(user=user).first()
            boards = Board.objects.filter(
                models.Q(owner=profile) | models.Q(members=profile)
            ).distinct()

            response_data = [self.set_board_view(board) for board in boards]
            response_serializer = BoardReadSerializer(response_data, many=True)
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        except Exception:
            return Response({"error": "An internal server error occurred!"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def set_board_view(self, board):
        """
        Transform board object into API response format
        """
        tasks = Task.objects.filter(board=board)
        return {
            "id": board.id,
            "title": board.title,
            "member_count": board.members.count(),
            "ticket_count": tasks.count(),
            "tasks_to_do_count": tasks.filter(status="to-do").count(),
            "tasks_high_prio_count": tasks.filter(priority="high").count(),
            "owner_id": board.owner.id,
        }

    @extend_schema(
        summary="Create new board",
        description="Creates a new board with the authenticated user as owner",
        tags=["Board"],
        request=BoardWriteSerializer,
        responses={
            201: BoardReadSerializer,
            400: OpenApiResponse(description="Invalid request data or user profile not found"),
            500: OpenApiResponse(description="Internal server error")
        }
    )
    def post(self, request):
        data = request.data.copy()
        data = self.validate_members(data)
        serializer = self.get_serializer(
            data=data, context={"request": request})
        user_id = self.get_user_from_token(request)
        profile = Profile.objects.filter(user_id=user_id).first()
        if not profile:
            return Response({"error": "No profile found for the user."}, status=status.HTTP_400_BAD_REQUEST)
        if serializer.is_valid():
            board = serializer.save(owner=profile)
            response_data = self.set_board_view(board)
            response_serializer = BoardReadSerializer(response_data)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get_user_from_token(self, request):
        """
        Extract user ID from token
        """
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Token "):
            raise AuthenticationFailed("No valid Token found!")

        token_key = auth_header.split("Token ")[1]
        try:
            token = Token.objects.get(key=token_key)
            return token.user_id
        except Token.DoesNotExist:
            raise AuthenticationFailed("Invalid Token!")

    def validate_members(self, data):
        # Helper to ensure members is always a list
        members = data.get("members", [])
        if members and not isinstance(members, list):
            data["members"] = [members]
        elif members is None:
            data["members"] = []
        return data


class BoardDetailView(viewsets.ModelViewSet):
    """
    ViewSet for managing board details with CRUD operations.
    Handles GET, PUT, PATCH and DELETE methods for boards.
    """
    queryset = Board.objects.all()

    def get_serializer_class(self):
        """
        Returns appropriate serializer based on request method.
        Uses BoardUpdateSerializer for update operations.
        """
        if self.request.method in ["PATCH", "PUT"]:
            return BoardUpdateSerializer
        return BoardSerializer

    def get_permissions(self):
        """
        Assigns permissions based on the action:
        - BoardOwnerAuthentication for delete operations
        - BoardOwnerOrMemberAuthentication for other operations
        Both require user authentication first
        """
        if self.action == "destroy":
            permission_classes = [IsAuthenticated, BoardOwnerAuthentication]
        else:
            permission_classes = [IsAuthenticated,
                                  BoardOwnerOrMemberAuthentication]
        return [permission() for permission in permission_classes]

    @extend_schema(
        summary="Get board details",
        description="Retrieves details of a specific board",
        tags=["Board"],
        responses={
            200: BoardSerializer,
            403: OpenApiResponse(description="Not owner or member of board"),
            404: OpenApiResponse(description="Board not found"),
            500: OpenApiResponse(description="Internal server error")
        }
    )
    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except NotFound:
            return Response({"error": "Board was not found"}, status=status.HTTP_404_NOT_FOUND)
        except AuthenticationFailed:
            return Response({"error": "Forbidden. You should be the owner or member of this board!"}, status=status.HTTP_403_FORBIDDEN)
        except Exception:
            return Response({"error": "Internal Server error!"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get_object(self):
        """
        Override get_object to handle not found errors consistently.
        Translates Django's ObjectDoesNotExist and Http404 to NotFound.
        """
        try:
            obj = super().get_object()
            return obj
        except (ObjectDoesNotExist, Http404):
            raise NotFound()

    @extend_schema(
        summary="Update board",
        description="Updates board information including members list",
        tags=["Board"],
        request=BoardUpdateSerializer,
        responses={
            200: BoardUpdateSerializer,
            400: OpenApiResponse(description="Invalid members data"),
            404: OpenApiResponse(description="Board not found"),
            500: OpenApiResponse(description="Internal server error")
        }
    )
    def update(self, request, *args, **kwargs):
        """
        Update a board with PUT/PATCH methods.
        Handles member validation and updates board-member relationships.
        """
        try:
            partial = kwargs.get("partial", False)
            instance = self.get_object()
            data = request.data.copy()
            data, members_data = self.validate_members(data)
            serializer = BoardUpdateSerializer(instance, data=data, partial=partial, context={"request": request})
            if serializer.is_valid():
                board = serializer.save()
                valid_members, invalid_members = self.process_members_data(members_data, board)
                if invalid_members:
                    return Response({"error": "Some member are invalid.","invalid_members": invalid_members}, status=status.HTTP_400_BAD_REQUEST)
                if valid_members is not None: 
                    board.members.set(valid_members)
                else: 
                    board.members.clear()
                updated_serializer = BoardUpdateSerializer(board, context={"request": request})
                return Response(updated_serializer.data, status=status.HTTP_200_OK)
        except NotFound:
            return Response({"error": "Board was not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": f"Internal Server error!{e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def validate_members(self, data):
        """
        Ensures members data is always in list format.
        """
        members = data.get("members", [])
        if members and not isinstance(members, list):
            data["members"] = [members]
        elif members is None:
            data["members"] = []
        return data, data["members"]
    
    def process_members_data(self, members_data, board):
        """
        Processes member IDs to valid Profile objects.
        Ensures board owner isn't added as a member.
        
        Args:
            members_data: List of member IDs
            board: Board instance
            
        Returns:
            tuple: (valid member profiles, invalid member IDs)
        """
        valid_members = []
        invalid_members = []
        if members_data is not None:
            for member_id in members_data:
                try:
                    profile = Profile.objects.get(id=member_id)
                    if profile != board.owner:
                        valid_members.append(profile)
                    else:
                        invalid_members.append(member_id)
                except ObjectDoesNotExist:
                    invalid_members.append(member_id)
        else: 
            valid_members = None    
        return valid_members, invalid_members

    @extend_schema(
        summary="Delete board",
        description="Permanently removes a board",
        tags=["Board"],
        responses={
            204: OpenApiResponse(description="Board successfully deleted"),
            404: OpenApiResponse(description="Board not found"),
            500: OpenApiResponse(description="Internal server error")
        }
    )
    def destroy(self, request, *args, **kwargs):
        """
        Delete a board.
        Only board owners can perform this action.
        """
        try: 
            instance = self.get_object()
            self.perform_destroy(instance)
            return Response(None, status=status.HTTP_204_NO_CONTENT)
        except NotFound:
            return Response({"error": "Board was not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception:
            return Response({"error": "Internal Server error!"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def perform_destroy(self, instance):
        """
        Perform the deletion of the board instance.
        """
        instance.delete()
