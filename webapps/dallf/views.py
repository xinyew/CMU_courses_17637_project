from http import HTTPStatus
import json
import os
from django.http import HttpRequest, JsonResponse, HttpResponse, HttpResponseBadRequest, Http404
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

from .models import UploadedImage, Label, User, Comment, Reply, accessible_by


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
    return reversed(group)


# Views


class GenerateParameterSerializer(serializers.Serializer):
    prompt_input = serializers.CharField()
    num_input = serializers.ChoiceField(choices=(1, 2, 3, 4))
    size_input = serializers.ChoiceField(
        choices=("256x256", "512x512", "1024x1024"))


@require_GET
@login_required
def console(request: HttpRequest):
    context = {}

    recent_images = request.user.image_set.all()[:40]

    favorite_images = request.user.favorites.all()
    labeled_images = UploadedImage.objects.filter(labels__user=request.user)
    context["favorite_images"] = favorite_images
    context['labeled_images'] = labeled_images
    context["recent_images"] = recent_images

    # context['label_image_set'] = []
    # for label in request.user.labels.all():
    #     context['label_image_set'].append(label)

    # label = request.GET.get('label')
    # if label:
    #     try:
    #         context['label_image_set'] = \
    #             request.user.labels.get(text=label).image_set
    #     except Label.DoesNotExist:
    #         pass

    return render(request, 'dallf/console.html', context)


@require_POST
def console_generate(request: HttpRequest):
    context = {}

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

    # Evaluate this query early
    recent_images = list(
        request.user.image_set.all()[:40]
    )
    try:
        last_generated_images = generate_DallE(request)
    except RuntimeError:
        return HttpResponseBadRequest()

    request.user.finish_generation()

    favorite_images = request.user.favorites.all()
    labeled_images = UploadedImage.objects.filter(labels__user=request.user)
    context["favorite_images"] = favorite_images
    context['labeled_images'] = labeled_images
    context['last_generated_images'] = last_generated_images
    context["recent_images"] = recent_images

    return render(request, 'dallf/console_generate.html', context)


@require_GET
def console_get_favorites(request: HttpRequest):
    context = {}

    favorite_images = request.user.favorites.all()
    labeled_images = UploadedImage.objects.filter(labels__user=request.user)
    context["favorite_images"] = favorite_images
    context['labeled_images'] = labeled_images

    return render(request, 'dallf/console_get_favorites.html', context)


@require_GET
def console_get_labels(request: HttpRequest):
    context = {}

    labels = request.user.labels.all()
    context["labels"] = labels

    return render(request, 'dallf/console_get_labels.html', context)


@require_GET
def label_get_images(request: HttpRequest, label_id: int):
    print('here')
    context = {}

    label = get_object_or_404(request.user.labels, id=label_id)
    context["images"] = label.image_set.all()

    favorite_images = request.user.favorites.all()
    labeled_images = UploadedImage.objects.filter(labels__user=request.user)
    context["favorite_images"] = favorite_images
    context['labeled_images'] = labeled_images

    result = render(request, 'dallf/console_label_get_images.html', context)
    print(result)
    return result


@require_GET
def gallery(request: HttpRequest):
    context = {}
    context["images"] = \
        UploadedImage.objects.filter(published=True) \
        .order_by('?')[:10]
    return render(request, 'dallf/gallery.html', context)


class PublishParameterSerializer(serializers.Serializer):
    publish = serializers.BooleanField()


@require_POST
@login_required
def publish_unpublish_action(request: HttpRequest, image_id: int):
    image = get_object_or_404(UploadedImage, id=image_id, user=request.user)
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
    image = get_object_or_404(
        UploadedImage,
        accessible_by(request.user),
        id=image_id)
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


class LabelParameterSerializer(serializers.Serializer):
    label_name = serializers.CharField()
    set_label = serializers.BooleanField()


@require_POST
@login_required
def label_action(request: HttpRequest, image_id: int):
    image = get_object_or_404(
        UploadedImage,
        # accessible_by(request.user),
        id=image_id)
    try:
        serializer = LabelParameterSerializer(data=request.POST)
        serializer.is_valid(raise_exception=True)
    except serializers.ValidationError as e:
        return HttpResponseBadRequest()
    validated_data = serializer.validated_data
    if validated_data["set_label"]:
        label, created = Label.objects.get_or_create(
            user=request.user,
            text=validated_data["label_name"]
        )
        # get_or_create is atomic
        image.labels.add(label)
        if not created:
            label.save()  # update modified
    else:
        label = get_object_or_404(
            Label,
            user=request.user,
            text=validated_data["label_name"]
        )
        image.labels.remove(label)
        label.save()  # update modified

    context = {}
    context["label"] = label

    return render(request, 'dallf/console_single_label.html', context)


@require_POST
@login_required
def logout_action(request: HttpRequest):
    logout(request)
    # Do this manually, because it seems to break otherwise due to redirection
    return redirect(settings.LOGIN_URL)


# TODO check validation for the below


@login_required
def my_profile(request):
    if request.method == 'GET':
        context = {}
        context["recent_pubs"] = []
        published_num = 0
        for image in request.user.image_set.all():
            if image.published is True:
                published_num += 1
                context["recent_pubs"].append(image)
        context['published_num'] = published_num
        return render(request, 'dallf/my_profile.html', context)
    if request.POST['upload_bio']:
        request.user.bio = request.POST['upload_bio']
    if request.FILES['upload_photo']:
        request.user.profile_image = request.FILES['upload_photo']
        request.user.profile_image_type = request.FILES['upload_photo'].content_type

    request.user.save()
    return render(request, 'dallf/my_profile.html', {'user': request.user})


@require_GET
@login_required
def others_profile(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.user.id == user_id:
        return redirect('my_profile')
    context = {}
    context['user'] = user
    context["recent_pubs"] = []
    published_num = 0
    for image in user.image_set.all():
        if image.published is True:
            published_num += 1
            context["recent_pubs"].append(image)
    context['published_num'] = published_num
    return render(request, 'dallf/others_profile.html', context)


@login_required
def get_portrait(request, user_id):
    user = get_object_or_404(User, id=user_id)

    return HttpResponse(
        user.profile_image,
        content_type=user.profile_image_type)


@require_GET
@login_required
def discussion_board(request, image_id):
    context = {}
    image = get_object_or_404(
        UploadedImage,
        accessible_by(request.user),
        id=image_id)
    context["image"] = image
    return render(request, 'dallf/discussion_board.html', context)


@login_required
def get_discussion(request, image_id):
    response_data = {}
    response_data['comments'] = []
    response_data['replies'] = []
    for comment in Comment.objects.all():
        if comment.image.id != image_id:
            continue
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
    for comment in User.objects.get(id=user_id).comments.all():
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
def comment_new(request):
    if 'comment_text' not in request.POST or 'image_id' not in request.POST or \
            not request.POST['comment_text'] or not request.POST['image_id']:
        return _my_json_error_response(
            "You must enter something to comment.", status=400)

    try:
        id = int(request.POST['image_id'])
    except Exception:
        return _my_json_error_response("The image id must be numeric", 400)

    image = get_object_or_404(UploadedImage, id=id)
    if not image:
        return _my_json_error_response("The image id does not exist", 400)

    new_comment = Comment(
        image=image,
        text=request.POST['comment_text'],
        user=request.user,
        date_created=dateformat.format(timezone.localtime(), "n/j/Y g:i A"))
    new_comment.save()

    return get_discussion(request, id)


@require_POST
@login_required
def reply_new(request):
    if 'reply_text' not in request.POST or not request.POST['reply_text'] or \
            'comment_id' not in request.POST or not request.POST['comment_id']:
        return _my_json_error_response(
            "You must enter something to reply.", status=400)

    try:
        comment_id = int(request.POST['comment_id'])
    except Exception:
        return _my_json_error_response(
            "The comment id and comment id must be numeric", 400)

    comment = get_object_or_404(Comment, id=comment_id)
    if not comment:
        return _my_json_error_response("The comment id does not exist", 400)

    new_reply = Reply(
        text=request.POST['reply_text'],
        user=request.user,
        comment=comment,
        date_created=dateformat.format(timezone.localtime(), "n/j/Y g:i A"))
    new_reply.save()
    return get_discussion(request, int(request.POST['image_id']))


@require_POST
def follow_unfollow(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if user not in request.user.following.all():
        request.user.following.add(user)
    else:
        request.user.following.remove(user)
    response_data = {}
    response_data['following'] = user in request.user.following.all()
    response_data['following_num'] = user.following.count()
    response_json = json.dumps(response_data)

    print(response_data)
    return HttpResponse(response_json, content_type='application/json')


def _my_json_error_response(message, status):
    response_json = '{ "error": "' + message + '" }'
    print(response_json)
    print(status)
    return HttpResponse(
        response_json,
        content_type='application/json',
        status=status)
