from django.shortcuts import render
from django.core.files.base import ContentFile
from django.contrib.auth.decorators import login_required

from urllib.parse import urlparse
import requests

from .models import UploadedImage, ImageGroup, Label

# Create your views here.


def generate_stable_diffusion(request):
    import replicate

    model = replicate.models.get("stability-ai/stable-diffusion")
    output = model.predict(prompt=request.POST["prompt_input"])
    save_image_group(request, output)


def generate_DallE(request):
    import openai

    # response = openai.Image.create_edit(
    #     image=open("sunlit_lounge.png", "rb"),
    #     mask=open("mask.png", "rb"),
    #     prompt="A sunlit indoor lounge area with a pool containing a flamingo",
    #     n=1,
    #     size="1024x1024"
    # )
    response = openai.Image.create(
        prompt=request.POST["prompt_input"],
        n=int(request.POST["num_input"]),
        size=request.POST["size_input"]
    )
    save_image_group(request,
                     [image_obj['url'] for image_obj in response['data']])


def save_image_group(request, image_urls):
    group = ImageGroup(
        prompt=request.POST["prompt_input"],
        user=request.user
    )
    group.save()
    for image_url in image_urls:
        image_response = requests.get(image_url)
        img = UploadedImage(
            group=group,
        )
        img.file.save(
            name=urlparse(image_url).path.rsplit('/', 1)[-1],
            content=ContentFile(image_response.content)
        )
        # actually we don't need this line to save the object. Why?
        # img.save()


@login_required
def console(request):
    context = {
        "prompt_input": "",
        "favorites": request.user.favorites,
    }

    if request.method == "POST" and "prompt_input" in request.POST and request.POST[
            "prompt_input"]:
        generate_DallE(request)

        recent_groups = list(
            request.user.image_group_set.order_by('-date_created')[:5]
        )

        context["prompt_input"] = request.POST["prompt_input"]
        context["current_prompt"] = recent_groups[0]
        context["recent_images"] = []
        for group in recent_groups[1:]:
            for image in group.image_set.all():
                context["recent_images"].append(image)
    else:
        recent_groups = list(
            request.user.image_group_set.order_by('-date_created')[:5]
        )

        context["current_prompt"] = None
        if len(recent_groups) >= 1:
            context["recent_images"] = []
            for group in recent_groups[0:]:
                for image in group.image_set.all():
                    context["recent_images"].append(image)
        else:
            context["recent_images"] = []

        label = request.GET.get('label')
        if label:
            try:
                context['label_image_set'] = \
                    request.user.labels.get(text=label).image_set
            except Label.DoesNotExist:
                pass

    return render(request, 'dallf/console.html', context)


@login_required
def favorite_action(request):
    image = UploadedImage.objects.filter()
