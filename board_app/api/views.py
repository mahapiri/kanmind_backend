from django.db import models
from django.http import Http404

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
        if self.request.method == "GET":
            return BoardReadSerializer
        elif self.request.method == "POST":
            return BoardWriteSerializer

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
            return Response({"error": f"An internal server error occurred!"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def set_board_view(self, board):
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
        members = data.get("members", [])
        if members and not isinstance(members, list):
            data["members"] = [members]
        elif members is None:
            data["members"] = []
        return data


class BoardDetailView(viewsets.ModelViewSet):
    queryset = Board.objects.all()

    def get_serializer_class(self):
        if self.request.method in ["PATCH", "PUT"]:
            return BoardUpdateSerializer
        return BoardSerializer

    def get_permissions(self):
        if self.action == "destroy":
            permission_classes = [IsAuthenticated, BoardOwnerAuthentication]
        else:
            permission_classes = [IsAuthenticated,
                                  BoardOwnerOrMemberAuthentication]
        return [permission() for permission in permission_classes]

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except NotFound:
            return Response({"error": "Board was not found"}, status=status.HTTP_404_NOT_FOUND)
        except AuthenticationFailed:
            return Response({"error": "Forbidden. You should be the owner or member of this board!"}, status=status.HTTP_401_UNAUTHORIZED)
        except Exception:
            return Response({"error": "Internal Server error!"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get_object(self):
        try:
            obj = super().get_object()
            return obj
        except (ObjectDoesNotExist, Http404):
            raise NotFound()

    def update(self, request, *args, **kwargs):
        try:
            partial = kwargs.get("partial", False)
            instance = self.get_object()
            members_data = request.data.get("members", [])
            serializer = BoardUpdateSerializer(instance, data=request.data, partial=partial, context={"request": request})
            if serializer.is_valid():
                board = serializer.save()
                valid_members, invalid_members = self.process_members_data(members_data, board)
                if invalid_members:
                    return Response({"error": "Some member are invalid.","invalid_members": invalid_members}, status=status.HTTP_400_BAD_REQUEST)
                board.members.set(valid_members)
                updated_serializer = BoardUpdateSerializer(board, context={"request": request})
                return Response(updated_serializer.data, status=status.HTTP_200_OK)
        except AuthenticationFailed:
            return Response({"error": "Forbidden. You should be the owner or member of this board!"}, status=status.HTTP_401_UNAUTHORIZED)
        except NotFound:
            return Response({"error": "Board was not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception:
            return Response({"error": "Internal Server error!"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def process_members_data(self, members_data, board):
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
            return valid_members, invalid_members

    def destroy(self, request, *args, **kwargs):
        try: 
            instance = self.get_object()
            self.perform_destroy(instance)
            return Response(None, status=status.HTTP_204_NO_CONTENT)
        except NotFound:
            return Response({"error": "Board was not found"}, status=status.HTTP_404_NOT_FOUND)
        except AuthenticationFailed:
            return Response({"error": "Forbidden. You should be the owner of this board!"}, status=status.HTTP_401_UNAUTHORIZED)
        except Exception:
            return Response({"error": "Internal Server error!"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def perform_destroy(self, instance):
        instance.delete()
