from django.db import models, transaction
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from datetime import timedelta

# Create your models here.

# Users must wait until their previous generation has finished, or until
# GENERATION_DELAY seconds to generate again
GENERATION_DELAY_SECONDS = 10
GENERATION_DELAY = timedelta(seconds=GENERATION_DELAY_SECONDS)


def _last_generated_default():
    return timezone.now() - GENERATION_DELAY


class User(AbstractUser):
    bio = models.TextField(default="", max_length=100)
    profile_image = models.FileField(default="", upload_to='images/')
    # Prevent users from generating images too quickly.
    # default ensures user can always generate right away
    last_generated = models.DateTimeField(
        default=_last_generated_default)
    # Set to False when image generation is finished.
    generation_ongoing = models.BooleanField(default=False)

    def start_generation(self):
        """Call when generation starts to change User's state. May fail, raising
        RuntimeError.
        """
        with transaction.atomic():
            if self.is_generating():
                raise RuntimeError
            self.last_generated = timezone.now()
            self.generation_ongoing = True
            self.save()

    def finish_generation(self):
        """Call when generation finishes to change User's state
        """
        self.generation_ongoing = False
        self.save()

    def is_generating(self):
        """Whether user is currently generating. After GENERATION_DELAY seconds,
        we let the user generate again, even if a previous generation is still
        going.
        """
        return (
            self.generation_ongoing
            and timezone.now() - self.last_generated < GENERATION_DELAY
        )


class Label(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="labels")
    text = models.CharField(max_length=255)
    date_modified = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-date_modified',)
        constraints = [
            models.UniqueConstraint(fields=("user", "text"),
                                    name="unique_label_text"),
        ]


class UploadedImage(models.Model):
    file = models.FileField(null=True, upload_to='images/')
    favorited_by = models.ManyToManyField(User, related_name="favorites")
    labels = models.ManyToManyField(Label, related_name="image_set")
    prompt = models.TextField()
    user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="image_set"
    )
    date_created = models.DateTimeField(auto_now_add=True)
    published = models.BooleanField(default=False)

    class Meta:
        ordering = ('-date_created',)


class Comment(models.Model):
    # comment is made on a specific image
    image = models.ForeignKey(
        UploadedImage,
        on_delete=models.PROTECT,
        related_name="comments"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="comments")
    text = models.TextField()
    date_created = models.DateTimeField(auto_now_add=True)


class Reply(models.Model):
    # reply is made on a specific comment
    user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="replys")
    comment = models.ForeignKey(
        Comment,
        on_delete=models.CASCADE,
        related_name="replys")
    text = models.CharField(max_length=200)
    date_created = models.CharField(max_length=50)
