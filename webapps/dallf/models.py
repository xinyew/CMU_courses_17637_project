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
    text = models.CharField(max_length=255)


class ImageGroup(models.Model):
    prompt = models.TextField()
    user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="image_group_set"
    )
    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-date_created',)


class UploadedImage(models.Model):
    file = models.FileField(null=True, upload_to='images/')
    favorited_by = models.ManyToManyField(User, related_name="favorites")
    labels = models.ManyToManyField(Label, related_name="image_set")
    group = models.ForeignKey(
        ImageGroup,
        on_delete=models.PROTECT,
        related_name="image_set")
    # prompt, user, date_created: go through imagegroup

    class Meta:
        ordering = ('group',)
