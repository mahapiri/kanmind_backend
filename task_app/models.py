from django.db import models

from user_auth_app.models import Profile

STATUS_CHOICES = {
    "to-do": "to-do",
    "in-progress": "in-progress",
    "review": "review",
    "done": "done"
}

STATUS_PRIORITY = {
    "low": "low",
    "medium": "medium",
    "high": "high"
}


class Task(models.Model):
    board = models.ForeignKey(
        "board_app.Board", on_delete=models.CASCADE, related_name="task")
    title = models.CharField(max_length=255)
    description = models.TextField(max_length=500, blank=True)
    status = models.CharField(max_length=255, choices=STATUS_CHOICES)
    priority = models.CharField(max_length=255, choices=STATUS_PRIORITY)
    assignee = models.ManyToManyField(
        Profile, blank=True, related_name="assigned_task")
    reviewer = models.ManyToManyField(
        Profile, blank=True, related_name="reviewer_task")
    due_date = models.DateField()
    owner = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="owned_task")

    class Meta:
        verbose_name = "Task"
        verbose_name_plural = "Tasks"
        ordering = ["board"]

    def __str__(self):
        return self.title


class Comment(models.Model):
    task = models.ForeignKey(
        Task, on_delete=models.CASCADE, related_name="comment")
    created_at = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name="comment_author")
    content = models.CharField(max_length=255)

    class Meta:
        verbose_name = "Comment"
        verbose_name_plural = "Comments"
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.author} Comment: {self.content}"
