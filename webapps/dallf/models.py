from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.


class User(AbstractUser):
    bio = models.TextField()
    profile_image = models.FileField(null=True, upload_to='images/')


class Label(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="labels")
    text = models.CharField()


class ImageGroup(models.Model):
    prompt = models.TextField()


class Image(models.Model):
    file = models.FileField(null=True, upload_to='images/')
    favorited_by = models.ManyToManyField(User, related_name="favorites")
    labels = models.ManyToManyField(Label, related_name="image_set")
    date_created = models.DateTimeField(auto_now_add=True)
    group = models.ForeignKey(
        ImageGroup,
        on_delete=models.PROTECT,
        related_name="image_set")
    # prompt: go through imagegroup
