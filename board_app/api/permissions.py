from rest_framework import permissions
from rest_framework.exceptions import NotFound

from board_app.models import Profile


class BoardOwnerOrMemberAuthentication(permissions.BasePermission):
    """
    Permission class that allows access to board owners and board members.
    Used for operations that should be accessible to both owners and members,
    such as viewing board details or tasks.
    """

    def has_object_permission(self, request, view, obj):
        """
        Check if the user is either the board owner or a board member.
        """
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
    """
    Permission class that only allows access to board owners.
    Used for operations that should be restricted to board owners only,
    such as deleting a board or changing ownership.
    """

    def has_object_permission(self, request, view, obj):
        """
        Check if the user is the board owner.
        """
        user = request.user

        try:
            user = Profile.objects.filter(user=user).first()
            is_owner = obj.owner == user

            if not is_owner:
                return False
            return True
        except Profile.DoesNotExist:
            raise NotFound("Profile was not found.")
