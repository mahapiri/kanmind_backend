from rest_framework import permissions


class BoardOwnerOrMemberAuthentication(permissions.BasePermission):
    message = "Not allowed to see boards"

    def has_object_permission(self, request, view, obj):
        user = request.user
        print(user)

        if not user.is_authenticated:
            return False
        
        is_owner = obj.owner_id == user
        is_member = user in obj.members.all()

        return is_owner or is_member

