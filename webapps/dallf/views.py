from django.shortcuts import render


from PIL import Image
import requests
from io import BytesIO

# Create your views here.


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
    image_url = output[0]
    image_response = requests.get(image_url)
    img = Image.open(BytesIO(image_response.content))
    img.save("dallf/static/dallf/tmp.png")


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
    image_url = response['data'][0]['url']
    image_response = requests.get(image_url)
    img = Image.open(BytesIO(image_response.content))
    img.save("dallf/static/dallf/tmp.png")
