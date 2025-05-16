from django.db import models

from user_auth_app.models import Profile


class Board(models.Model):
    """
    Board model representing a kanban/task board.
    Each board has an owner, a title, and optional members.
    """
    title = models.CharField(max_length=255)
    owner = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="board")
    members = models.ManyToManyField(Profile, blank=True, related_name="board_members")

    class Meta:
        verbose_name = "Board"
        verbose_name_plural = "Boards"
        ordering = ["owner"]

    def __str__(self):
        return self.title