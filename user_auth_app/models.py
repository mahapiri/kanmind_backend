from tabnanny import verbose
from django.contrib.auth.models import User
from django.db import models

# Create your models here.
class Profile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="profile")
    fullname = models.CharField(max_length=255)
    
    class Meta:
        verbose_name = "Profile"
        verbose_name_plural = "Profiles"
        ordering = ["fullname"]
    
    def __str__(self):
        return self.fullname
