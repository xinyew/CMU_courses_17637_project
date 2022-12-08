from http import HTTPStatus
import json
import os
from django.http import HttpRequest, JsonResponse, HttpResponse, HttpResponseBadRequest
from django.shortcuts import render, redirect, get_object_or_404
from django.core.files.base import ContentFile
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST, require_http_methods
from django.contrib.auth import logout
from django.contrib.auth.views import logout_then_login
from django.conf import settings
from django.utils import timezone, dateformat
from django import forms

from rest_framework import serializers

from urllib.parse import urlparse
import requests

from .models import UploadedImage, Label, User, Comment, Reply


# Utility methods for generation


# Unused (fallback in case DallE fails)
def generate_stable_diffusion(request: HttpRequest):
    import replicate

    model = replicate.models.get("stability-ai/stable-diffusion")
    output = model.predict(prompt=request.POST["prompt_input"])
    return save_generated_images(request, output)


def generate_DallE(request):
    import openai
    import openai.error

    # response = openai.Image.create_edit(
    #     image=open("sunlit_lounge.png", "rb"),
    #     mask=open("mask.png", "rb"),
    #     prompt="A sunlit indoor lounge area with a pool containing a flamingo",
    #     n=1,
    #     size="1024x1024"
    # )
    try:
        response = openai.Image.create(
            prompt=request.POST["prompt_input"],
            n=int(request.POST["num_input"]),
            size=request.POST["size_input"],
        )
    except openai.error.OpenAIError:
        raise RuntimeError

    return save_generated_images(
        request,
        [image_obj['url'] for image_obj in response['data']])


def save_generated_images(request: HttpRequest, image_urls):
    group = []
    for image_url in image_urls:
        try:
            image_response = requests.get(image_url, timeout=10)
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
    return group


# Views


class GenerateParameterSerializer(serializers.Serializer):
    prompt_input = serializers.CharField()
    num_input = serializers.ChoiceField(choices=(1, 2, 3, 4))
    size_input = serializers.ChoiceField(
        choices=("256x256", "512x512", "1024x1024"))


@require_http_methods(["GET", "POST"])
@login_required
def console(request: HttpRequest):
    context = {
        "prompt_input": "",
        "favorites": request.user.favorites,
    }

    if request.method == "POST":
        try:
            GenerateParameterSerializer(data=request.POST) \
                .is_valid(raise_exception=True)
        except serializers.ValidationError as e:
            print(e)
            return HttpResponseBadRequest()

        try:
            request.user.start_generation()
        except RuntimeError:  # not a great name
            return HttpResponseBadRequest()

        recent_images = list(
            request.user.image_set.all()[:40]
        )
        try:
            last_generated_images = generate_DallE(request)
        except RuntimeError:
            return HttpResponseBadRequest()

        request.user.finish_generation()

        context['last_generated_images'] = last_generated_images
        context["recent_images"] = recent_images

        return render(request, 'dallf/console_generate.html', context)
    else:
        recent_images = list(
            request.user.image_set.all()[:40]
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


@require_GET
def gallery(request: HttpRequest):
    context = {}
    context["images"] = []
    for image in UploadedImage.objects.filter(published=True) \
                                      .order_by('?')[:10]:
        context["images"].append(image)
    return render(request, 'dallf/gallery.html', context)


class PublishParameterSerializer(serializers.Serializer):
    publish = serializers.BooleanField()


@require_POST
@login_required
def publish_unpublish_action(request: HttpRequest, image_id: int):
    image = get_object_or_404(UploadedImage, id=image_id)
    if not image.user == request.user:
        return HttpResponseBadRequest()
    try:
        serializer = PublishParameterSerializer(data=request.POST)
        serializer.is_valid(raise_exception=True)
    except serializers.ValidationError:
        return HttpResponseBadRequest()
    validated_data = serializer.validated_data
    image.published = validated_data["publish"]
    image.save()
    return HttpResponse(status=HTTPStatus.NO_CONTENT)


class FavoriteParameterSerializer(serializers.Serializer):
    favorite = serializers.BooleanField()


@require_POST
@login_required
def favorite_action(request: HttpRequest, image_id: int):
    image = get_object_or_404(UploadedImage, id=image_id)
    try:
        serializer = FavoriteParameterSerializer(data=request.POST)
        serializer.is_valid(raise_exception=True)
    except serializers.ValidationError:
        return HttpResponseBadRequest()
    validated_data = serializer.validated_data
    if validated_data["favorite"]:
        image.favorited_by.add(request.user)
    else:
        image.favorited_by.remove(request.user)
    return HttpResponse(status=HTTPStatus.NO_CONTENT)


@require_POST
@login_required
def label_action(request: HttpRequest, image_id: int):
    # TODO
    image = get_object_or_404(UploadedImage, id=image_id)
    label, _ = Label.objects.get_or_create(
        user=request.user, text=request.POST["label_name"])
    # get_or_create is atomic
    image.labels.add(label)
    return redirect('/dallf/console/')


@require_POST
@login_required
def logout_action(request: HttpRequest):
    logout(request)
    # Do this manually, because it seems to break otherwise due to redirection
    return redirect(settings.LOGIN_URL)


# TODO check validation for the below


@require_GET
@login_required
def my_profile(request):
    context = {}
    context["images"] = []
    for image in UploadedImage.objects.order_by('?')[:10]:
        context["images"].append(image)
    return render(request, 'dallf/my_profile.html', context)


@require_GET
@login_required
def others_profile(request):
    context = {}
    context["images"] = []
    for image in UploadedImage.objects.order_by('?')[:10]:
        context["images"].append(image)
    return render(request, 'dallf/others_profile.html', context)


@require_GET
@login_required
def discussion_board(request):
    context = {}
    context["images"] = []
    for image in UploadedImage.objects.order_by('?')[:10]:
        context["images"].append(image)
    return render(request, 'dallf/discussion_board.html', context)


@require_GET
@login_required
def get_profile_image(request, user_id):
    f = open(os.path.dirname(__file__) + '/static/dallf/not_found.jpg', 'rb')
    image = f.read()
    f.close()
    return HttpResponse(image, content_type="image/jpeg")


@require_GET
@login_required
def get_discussion(request, image_id):
    response_data = {}
    response_data['comments'] = []
    response_data['replies'] = []
    for comment in Comment.objects.get(pk=image_id):
        new_comment = {
            'id': comment.id,
            'text': comment.text,
            'user_id': comment.user.id,
            'first_name': comment.user.first_name,
            'last_name': comment.user.last_name,
            'date_created': comment.date_created
        }
        response_data['comments'].append(new_comment)
        for reply in comment.replys.all():
            new_reply = {
                'id': reply.id,
                'comment_id': comment.id,
                'text': reply.text,
                'user_id': reply.user.id,
                'first_name': reply.user.first_name,
                'last_name': reply.user.last_name,
                'date_created': reply.date_created
            }
            response_data['replies'].append(new_reply)

    response_json = json.dumps(response_data)
    return HttpResponse(response_json, content_type='application/json')


@require_GET
@login_required
def get_recent_activities(request, user_id):
    response_data = {}
    response_data['comments'] = []
    response_data['replies'] = []
    num_activities_found = 0
    for comment in Comment.objects.get(user=User.objects.get(pk=user_id)):
        new_comment = {
            'id': comment.id,
            'text': comment.text,
            'user_id': comment.user.id,
            'first_name': comment.user.first_name,
            'last_name': comment.user.last_name,
            'date_created': comment.date_created
        }
        response_data['comments'].append(new_comment)
        for reply in comment.replys.all():
            new_reply = {
                'id': reply.id,
                'comment_id': comment.id,
                'text': reply.text,
                'user_id': reply.user.id,
                'first_name': reply.user.first_name,
                'last_name': reply.user.last_name,
                'date_created': reply.date_created
            }
            response_data['replies'].append(new_reply)

    response_json = json.dumps(response_data)
    return HttpResponse(response_json, content_type='application/json')


@require_POST
@login_required
def post_new_comment(request):
    if 'discussion_reply_text' not in request.POST or not request.POST['discussion_reply_text']:
        return _my_json_error_response(
            message="You must enter something to comment",
            status=400)
    new_comment = Comment(
        text=request.POST['discussion_reply_text'],
        user=request.user,
        date_created=dateformat.format(timezone.localtime(), "n/j/Y g:i A"))
    new_comment.save()

    return get_discussion(request)


@require_POST
@login_required
def post_new_reply(request):
    if 'reply_text' not in request.POST or not request.POST['reply_text']:
        return _my_json_error_response(
            message="You must enter something to reply",
            status=400)

    if 'comment_id' not in request.POST or not request.POST['comment_id']:
        return _my_json_error_response(
            message="You must specify the comment id to reply",
            status=400)
    try:
        id = int(request.POST['comment_id'])
    except Exception:
        return _my_json_error_response("The comment id must be numeric", 400)
    if id > Comment.objects.all().order_by('-date_created')[0].id:
        return _my_json_error_response("The comment id does not exist", 400)

    comment = get_object_or_404(Comment, id=request.POST['comment_id'])
    new_reply = Reply(
        text=request.POST['reply_text'],
        user=request.user,
        comment=comment,
        date_created=dateformat.format(timezone.localtime(), "n/j/Y g:i A"))
    new_reply.save()


def _my_json_error_response(message, status):
    response_json = '{ "error": "' + message + '" }'
    print(status)
    return HttpResponse(
        response_json,
        content_type='application/json',
        status=status)
