from rest_framework import permissions
from rest_framework.exceptions import NotFound

from board_app.models import Profile


class BoardOwnerOrMemberAuthentication(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        user = request.user

        try:
            user = Profile.objects.filter(user=user).first()
            is_owner = obj.owner == user
            is_member = user in obj.members.all()

            if not (is_owner or is_member):
                return False
            return True
        except Profile.DoesNotExist:
            raise NotFound("Profile was not found.")


class BoardOwnerAuthentication(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        user = request.user

        try:
            user = Profile.objects.filter(user_id=user.id).first()
            is_owner = obj.owner == user

            if not is_owner:
                return False
            return True
        except Profile.DoesNotExist:
            raise NotFound("Profile was not found.")
