from rest_framework import permissions

from board_app.models import Profile


class BoardOwnerOrMemberAuthentication(permissions.BasePermission):
    message = "Forbidden. You should be the owner or member of this board!"

    def has_object_permission(self, request, view, obj):
        user = request.user

        if not user.is_authenticated:
            return False

        user = Profile.objects.filter(user_id=user.id).first()

        is_owner = obj.owner_id == user
        is_member = user in obj.members.all()

        return is_owner or is_member


class BoardOwnerAuthentication(permissions.BasePermission):
    message = "Forbidden. You should be the owner of this board"

    def has_object_permission(self, request, view, obj):
        user = request.user

        if not user.is_authenticated:
            return False

        user = Profile.objects.filter(user_id=user.id).first()
        is_owner = obj.owner_id == user
        return is_owner
