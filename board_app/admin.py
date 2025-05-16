from django.contrib import admin

from board_app.models import Board

class BoardAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'owner', 'all_members']

    def all_members(self, obj):
        return ", ".join([member.fullname for member in obj.members.all()])
    all_members.short_description = 'Members'


admin.site.register(Board, BoardAdmin)
