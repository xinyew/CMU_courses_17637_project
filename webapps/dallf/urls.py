from django.urls import path
from dallf import views

urlpatterns = [
    path('generate', views.generate_action, name='generate'),
]