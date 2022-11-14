from django.shortcuts import render
from django.core.files.base import ContentFile
from django.contrib.auth.decorators import login_required

from urllib.parse import urlparse
from PIL import Image
import requests
from io import BytesIO

from .models import UploadedImage, ImageGroup, Label

# Create your views here.


@login_required
def generate_action(request):
    if request.method == "GET":
        return render(request,
                      'dallf/image_generation_page.html',
                      {"prompt_input": ""})

    context = {}

    if "prompt_input" not in request.POST or not request.POST["prompt_input"]:
        return render(request,
                      'dallf/image_generation_page.html',
                      {"prompt_input": ""})

    generate_DallE(request)
    context["img"] = "dallf/static/dallf/tmp.png"
    context["prompt_input"] = request.POST["prompt_input"]

    return render(request, 'dallf/image_generation_page.html', context)


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
        print(image_url)
        img.file.save(
            name=urlparse(image_url).path.rsplit('/', 1)[-1],
            content=ContentFile(image_response.content)
        )


@login_required
def console(request):
    recent_groups = list(
        ImageGroup.objects.order_by('-date_created')[:5]
    )
    context = {
        'current_prompt': recent_groups[0] if len(recent_groups) >= 1 else None,
        'recent_prompts': recent_groups[1:] if len(recent_groups) >= 1 else None,
        'favorites': request.user.favorites,
    }
    label = request.GET.get('label')
    if label:
        try:
            context['label_image_set'] = \
                request.user.labels.get(text=label).image_set
        except Label.DoesNotExist:
            pass
    return render(request, 'dallf/console.html', context)
