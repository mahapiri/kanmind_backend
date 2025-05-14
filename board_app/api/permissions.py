from rest_framework import permissions
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.response import Response

from board_app.models import Profile


class BoardOwnerOrMemberAuthentication(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        user = request.user
        
        user = Profile.objects.filter(user=user).first()

        is_owner = obj.owner == user
        is_member = user in obj.board_members.all()

        if not (is_owner or is_member):
            raise AuthenticationFailed("Not authorized. You should be the owner or member of this board!")

        return True


class BoardOwnerAuthentication(permissions.BasePermission):
    message = "Forbidden. You should be the owner of this board"

    def has_object_permission(self, request, view, obj):
        user = request.user

        if not user.is_authenticated:
            return False

        user = Profile.objects.filter(user_id=user.id).first()
        is_owner = obj.owner_id == user
        return is_owner
