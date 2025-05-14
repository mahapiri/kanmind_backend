from django.contrib.auth.models import User

from rest_framework import serializers
from rest_framework.exceptions import NotFound

from user_auth_app.models import Profile
from board_app.admin import Board
from task_app.api.serializers import TaskSerializer
from user_auth_app.api.serializers import MemberSerializer


class BoardReadSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    member_count = serializers.IntegerField()
    ticket_count = serializers.IntegerField()
    tasks_to_do_count = serializers.IntegerField()
    tasks_high_prio_count = serializers.IntegerField()
    owner_id = serializers.IntegerField()


class BoardWriteSerializer(serializers.ModelSerializer):
    members = serializers.PrimaryKeyRelatedField(
        queryset=Profile.objects.all(),
        many=True,
        required=False,
        error_messages={
            "does_not_exist": "Member with ID {pk_value} does not exist!"
        }
    )

    class Meta:
        model = Board
        fields = ["title", "members"]

    def create(self, validated_data):
        owner = validated_data.pop("owner", None)
        members = validated_data.pop("members", [])
        filtered_members = [
            member for member in members if member.id != owner.id]
        try:
            board = Board.objects.create(owner=owner, **validated_data)
            board.members.set(filtered_members)
            return board
        except Exception as e:
            raise serializers.ValidationError(
                {"error": f"Internal Server error!"})


class BoardSerializer(serializers.ModelSerializer):
    tasks = serializers.SerializerMethodField(read_only=True)
    members = serializers.SerializerMethodField(read_only=True)
    owner_id = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Board
        fields = ["id", "title", "owner_id", "members", "tasks"]

    def get_owner_id(self, obj):
        return obj.id

    def get_members(self, obj):
        if obj.members.exists():
            return MemberSerializer(obj.members.all(), many=True).data
        else:
            return None

    def get_tasks(self, obj):
        if obj.task.exists():
            return TaskSerializer(obj.task.all(), many=True).data
        else:
            return None


class BoardUpdateSerializer(serializers.ModelSerializer):
    owner_data = serializers.SerializerMethodField(read_only=True)
    members_data = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Board
        fields = ["id", "title", "owner_data", "members_data"]

    def get_owner_data(self, obj):
        try:
            profile = obj.owner
            user = User.objects.get(pk=profile.user_id)
            profile = Profile.objects.get(user=user)

            return {
                "id": profile.id,
                "email": user.email,
                "fullname": profile.fullname
            }
        except Profile.DoesNotExist:
            raise NotFound()

    def get_members_data(self, obj):
        members_data = []
        for member in obj.members.all():
            if member:
                members_data.append({
                    "id": member.id,
                    "email": member.user.email,
                    "fullname": member.fullname
                })
        return members_data if members_data else None
