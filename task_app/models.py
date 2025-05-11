from django.db import models

from user_auth_app.models import Profile

# Create your models here.
STATUS_CHOICES = {
    "to-do": "to-do",
    "in-progress": "in-progress",
    "review": "review",
    "done": "done"
}

STATUS_PRIORITY = {
    "low": "low",
    "mediium": "medium",
    "high": "high"
}

class Comment(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="comments")
    content = models.CharField(max_length=255)

    class Meta:
        verbose_name = "Comment"
        verbose_name_plural = "Comments"
        ordering = ["author"]
    
    def __str__(self):
        return f"{self.author} Comment: {self.content}"


class Task(models.Model):
    board = models.ForeignKey("board_app.Board", on_delete=models.CASCADE, related_name="tasks")
    title = models.CharField(max_length=255)
    description = models.TextField(max_length=500, blank=True)
    status = models.CharField(max_length=255, choices=STATUS_CHOICES)
    priority = models.CharField(max_length=255, choices=STATUS_PRIORITY)
    assignee = models.ManyToManyField(Profile, blank=True, related_name="assigned_tasks")
    reviewer = models.ManyToManyField(Profile, blank=True, related_name="reviewer_tasks")
    due_date = models.DateField()
    comment = models.ForeignKey(Comment, on_delete=models.SET_NULL, null=True, blank=True)
    owner_id = models.ManyToManyField(Profile, related_name="own_tasks")

    class Meta:
        verbose_name = "Task"
        verbose_name_plural = "Tasks"
        ordering = ["board"]
    
    def __str__(self):
        return self.title