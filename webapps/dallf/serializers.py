from rest_framework import serializers

from .models import UploadedImage, ImageGroup

# These are serializers from Django Rest Framework, which work much like Django
# forms and take similar arguments for customization. Outputs python
# dictionaries/JSON.

# Usage:
# https://www.django-rest-framework.org/tutorial/1-serialization/#working-with-serializers


class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = UploadedImage
        fields = '__all__'


class ImageGroupSerializer(serializers.ModelSerializer):
    image_set = ImageSerializer(many=True)  # output a nested list

    class Meta:
        model = ImageGroup
        fields = '__all__'
