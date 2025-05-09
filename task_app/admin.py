from django.contrib import admin

from task_app.models import Comment, Task

# Register your models here.
admin.site.register(Task)
admin.site.register(Comment)