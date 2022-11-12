from django.shortcuts import render

# Create your views here.


def generate_action(request):
    if request.method == "GET":
        return render(request,
                      'dallf/image_generation_page.html',
                      {"prompt_input": ""})

    import replicate
    from PIL import Image
    import requests
    from io import BytesIO
    import os

    os.system('export REPLICATE_API_TOKEN=31a40836d77dc82f8a589ff6af1d2a4222eed801')
    context = {}

    if "prompt_input" not in request.POST or not request.POST["prompt_input"]:
        return render(request,
                      'dallf/image_generation_page.html',
                      {"prompt_input": ""})

    model = replicate.models.get("stability-ai/stable-diffusion")
    print(request.POST["prompt_input"])
    output = model.predict(prompt=request.POST["prompt_input"])
    response = requests.get(output[0])
    img = Image.open(BytesIO(response.content))
    img.save("dallf/static/dallf/tmp.png")
    context["img"] = "dallf/static/dallf/tmp.png"
    context["prompt_input"] = request.POST["prompt_input"]

    return render(request, 'dallf/image_generation_page.html', context)
