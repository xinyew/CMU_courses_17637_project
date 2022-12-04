from django.http import HttpRequest, JsonResponse
from django.shortcuts import render, redirect
from django.core.files.base import ContentFile
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST
from django.contrib.auth import logout
from django.contrib.auth.views import logout_then_login
from django.conf import settings

from urllib.parse import urlparse
import requests

from .models import UploadedImage, Label, User, GENERATION_TIMEOUT_SECONDS
from .serializers import ImageSerializer

# Fetching images once they're generated should not take a significant amount of
# time.
GET_IMAGE_TIMEOUT_SECONDS = 10


# Utility methods for generation


def generate_stable_diffusion(request: HttpRequest):
    import replicate

    request.user.start_generation()

    model = replicate.models.get("stability-ai/stable-diffusion")
    output = model.predict(prompt=request.POST["prompt_input"])
    return save_image_group(request, output)


def generate_DallE(request):
    import openai

    request.user.start_generation()

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
        size=request.POST["size_input"],
        request_timeout=GENERATION_TIMEOUT_SECONDS
    )
    return save_image_group(request,
                            [image_obj['url']
                             for image_obj in response['data']])


def save_image_group(request: HttpRequest, image_urls):
    group = []
    for image_url in image_urls:
        try:
            image_response = requests.get(
                image_url,
                timeout=GET_IMAGE_TIMEOUT_SECONDS)
        except requests.exceptions.Timeout:
            pass
        else:
            img = UploadedImage(
                prompt=request.POST["prompt_input"],
                user=request.user,
            )
            img.file.save(
                name=urlparse(image_url).path.rsplit('/', 1)[-1],
                content=ContentFile(image_response.content)
            )  # also saves img
            group.append(img)
    request.user.finish_generation()
    return group


# Views


@login_required
def console(request: HttpRequest):
    context = {
        "prompt_input": "",
        "favorites": request.user.favorites,
    }

    if request.method == "POST" and "prompt_input" in request.POST and request.POST[
            "prompt_input"]:
        generate_DallE(request)

        recent_images = list(
            request.user.image_set.order_by('-date_created')[:5]
        )
        context["prompt_input"] = request.POST["prompt_input"]
        context["recent_images"] = recent_images
    else:
        recent_images = list(
            request.user.image_set.order_by('-date_created')[:5]
        )
        context["recent_images"] = recent_images

    context['label_image_set'] = []
    for label in request.user.labels.all():
        context['label_image_set'].append(label)

    # label = request.GET.get('label')
    # if label:
    #     try:
    #         context['label_image_set'] = \
    #             request.user.labels.get(text=label).image_set
    #     except Label.DoesNotExist:
    #         pass

    return render(request, 'dallf/console.html', context)


def gallery(request: HttpRequest):
    context = {}
    context["images"] = []
    for image in UploadedImage.objects.order_by('?')[:10]:
        context["images"].append(image)
    return render(request, 'dallf/gallery.html', context)


@login_required
def favorite_action(request: HttpRequest):
    image = UploadedImage.objects.get(id=int(request.POST["image_id"]))
    image.favorited_by.add(request.user)
    return redirect('/dallf/console/')


@login_required
def label_action(request: HttpRequest):
    image = UploadedImage.objects.get(id=int(request.POST["image_id"]))
    label, _ = Label.objects.get_or_create(
        user=request.user, text=request.POST["label_name"])
    # get_or_create is atomic
    image.labels.add(label)
    return redirect('/dallf/console/')


@require_POST
@login_required
def generate_action(request: HttpRequest):
    group = generate_DallE(request)
    serializer = ImageSerializer(group, many=True)
    return JsonResponse(serializer.data)


@require_GET
@login_required
def test_generate_action(request: HttpRequest):
    group = request.user.image_set.all()[0]
    serializer = ImageSerializer(group, many=True)
    return JsonResponse(serializer.data)


@require_POST
@login_required
def logout_action(request: HttpRequest):
    logout(request)
    # Do this manually, because it seems to break otherwise due to redirection
    return redirect(settings.LOGIN_URL)


# TODO validation
# TODO exception handling for .get

@login_required
def my_profile(request):
    context = {}
    context["images"] = []
    for image in UploadedImage.objects.order_by('?')[:10]:
        context["images"].append(image)
    return render(request, 'dallf/my_profile.html', context)


@login_required
def others_profile(request):
    context = {}
    context["images"] = []
    for image in UploadedImage.objects.order_by('?')[:10]:
        context["images"].append(image)
    return render(request, 'dallf/others_profile.html', context)


@login_required
def discussion_board(request):
    context = {}
    context["images"] = []
    for image in UploadedImage.objects.order_by('?')[:10]:
        context["images"].append(image)
    return render(request, 'dallf/discussion_board.html', context)
