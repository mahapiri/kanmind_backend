from django.contrib import admin

from task_app.models import Comment, Task

class TaskAdmin(admin.ModelAdmin):
    list_display = ['id', 'board_id', 'title', 'description', 'status', 'priority', 'all_assignees', 'all_reviewers', 'due_date', 'owner']

    def all_assignees(self, obj):
        ", ".join(assignee.fullname for assignee in obj.assignee.all())
    all_assignees.short_description = 'Assignees'
    def all_reviewers(self, obj):
        ", ".join(reviewer.fullname for reviewer in obj.reviewer.all())
    all_reviewers.short_description = 'Reviewers'

class CommentAdmin(admin.ModelAdmin):
    list_display = ['id', 'task_id', 'content', 'author_id', 'created_at']


admin.site.register(Task, TaskAdmin)
admin.site.register(Comment,CommentAdmin)