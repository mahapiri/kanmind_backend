from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework.authtoken.models import Token
from rest_framework.response import Response

from board_app.admin import Board
from task_app.api.serializer import TaskSerializer
from user_auth_app.api.serializers import MemberSerializer
from user_auth_app.models import Profile


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
        fields = ['title', 'members']

    def create(self, validated_data):
        owner = validated_data.pop('owner', None)
        members = validated_data.pop('members', [])
        filtered_members = [
            member for member in members if member.id != owner.id]
        try:
            board = Board.objects.create(owner=owner, **validated_data)
            board.members.set(filtered_members)
            return board
        except Exception as e:
            raise serializers.ValidationError({"error": f"Internal Server error!"})


class BoardSerializer(serializers.ModelSerializer):
    tasks = TaskSerializer(many=True, read_only=True)
    members = MemberSerializer(many=True, read_only=True)

    class Meta:
        model = Board
        fields = ['id', 'title', 'owner', 'members', 'tasks']


class BoardUpdateSerializer(serializers.ModelSerializer):
    owner_data = serializers.SerializerMethodField(read_only=True)
    members_data = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Board
        fields = ['id', 'title', 'owner_data', 'members_data']

    def get_owner_data(self, obj):
        try:
            owner_user = obj.owner_id
            user_profile = User.objects.get(pk=owner_user.id)
            owner_profile = Profile.objects.get(user=user_profile)

            return {
                'id': owner_profile.id,
                'email': user_profile.email,
                'fullname': owner_profile.fullname
            }
        except Profile.DoesNotExist:
            return None


    def get_members_data(self, obj):
        return [{
            'id': member.id,
            'email': member.user.email,
            'fullname': member.fullname
        } for member in obj.members.all()]