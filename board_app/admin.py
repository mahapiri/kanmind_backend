from django.contrib import admin

from board_app.models import Board

class BoardAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Board model.
    Customizes the display of boards in the Django admin interface.
    """
    list_display = ['id', 'title', 'owner', 'all_members']

    def all_members(self, obj):
        """
        Display all board members as a comma-separated string.
        
        Args:
            obj: The Board instance
            
        Returns:
            str: Comma-separated list of member fullnames
        """
        return ", ".join([member.fullname for member in obj.members.all()])
    all_members.short_description = 'Members'

# Register the Board model with the custom admin configuration
admin.site.register(Board, BoardAdmin)
