from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from datetime import timedelta

# Create your models here.

# Users must wait at least GENERATION_DELAY to generate again
GENERATION_DELAY_SECONDS = 10
GENERATION_DELAY = timedelta(seconds=GENERATION_DELAY_SECONDS)
# Time until a generation is considered failed
GENERATION_TIMEOUT_SECONDS = 60
GENERATION_TIMEOUT = timedelta(seconds=GENERATION_TIMEOUT_SECONDS)


def _last_generated_default():
    return timezone.now() - GENERATION_DELAY


class User(AbstractUser):
    bio = models.TextField(default="")
    profile_image = models.FileField(default="", upload_to='images/')
    # Prevent users from generating images too quickly.
    # default ensures user can always generate right away
    last_generated = models.DateTimeField(
        default=_last_generated_default)
    # Set to False when image generation is finished.
    generation_ongoing = models.BooleanField(default=False)

    # TODO start_generation could fail, need to include can_generate() check in
    # a transaction
    def start_generation(self):
        """Call when generation starts to change User's state
        """
        self.last_generated = timezone.now()
        self.generation_ongoing = True

    def finish_generation(self):
        """Call when generation finishes to change User's state
        """
        self.generation_ongoing = False

    def is_generating(self):
        return (
            self.generation_ongoing
            and timezone.now() - self.last_generated < GENERATION_TIMEOUT
        )

    def can_generate(self):
        """Returns True if the user is allowed to generate.

        Currently, a user can generate while another set of images is still
        generating, as long as they don't generate within GENERATION_DELAY
        seconds.
        """
        return timezone.now() - self.last_generated >= GENERATION_DELAY


class Label(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="labels")
    text = models.CharField(max_length=255)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("user", "text"),
                                    name="unique_label_text"),
        ]


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
