from django.db import models

from user_auth_app.models import Profile

# Create your models here.


class Board(models.Model):
    # id = models.BigAutoField(primary_key=True)
    title = models.CharField(max_length=255)
    owner_id = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="boards")
    members = models.ManyToManyField(Profile, blank=True,related_name="member_boards")
    tasks = models.ManyToManyField('task_app.Task', blank=True, related_name="board_tasks")

    class Meta:
        verbose_name = "Board"
        verbose_name_plural = "Boards"
        ordering = ["owner_id"]

    def __str__(self):
        return self.title