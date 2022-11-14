from django.urls import path
from dallf import views

urlpatterns = [
    path('console/', views.console, name='console'),
    path('favorite/', views.favorite_action, name='favorite')
]
