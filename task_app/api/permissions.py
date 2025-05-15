from rest_framework import permissions
from rest_framework.exceptions import AuthenticationFailed, NotFound

from board_app.models import Board
from user_auth_app.models import Profile


class BoardOwnerOrMemberAuthentication(permissions.BasePermission):

    def has_permission(self, request, view):
        user = request.user
        try:
            user_profile = Profile.objects.get(user=user)
            is_owner = Board.objects.filter(owner=user_profile).exists()
            is_member = user_profile.board_members.exists()

            if not (is_owner or is_member):
                raise AuthenticationFailed()
            return True
        except Profile.DoesNotExist:
            raise NotFound()


class TaskOwnerAuthentication(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user
        try:
            profile = Profile.objects.get(user=user)
            is_owner = profile.owned_task
            # if is_owner // FEHLT NOCH WAS bzgl welche task abgefragt werden um die korrekten anzuzeigen
            return is_owner
        except Profile.DoesNotExist:
            raise AuthenticationFailed()


class BoardOwnerAuthentication(permissions.BasePermission):
    # siehe noch board permissions.py auch hier muss noch geschaut werden ob er der owner ist
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False

        user = request.user
        try:
            user_profile = Profile.objects.get(user=user)
            is_owner = user_profile.boards.exists()
            return is_owner
        except Profile.DoesNotExist:
            return False
