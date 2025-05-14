from rest_framework import permissions
from rest_framework.exceptions import AuthenticationFailed

from board_app.models import Profile


class BoardOwnerOrMemberAuthentication(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        user = request.user
        
        user = Profile.objects.filter(user=user).first()

        is_owner = obj.owner == user
        is_member = user in obj.members.all()

        if not (is_owner or is_member):
            raise AuthenticationFailed()
        return True


class BoardOwnerAuthentication(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        user = request.user

        user = Profile.objects.filter(user_id=user.id).first()
        is_owner = obj.owner == user

        if not is_owner:
            raise AuthenticationFailed()
        return is_owner
