from django.urls import path
from dallf import views

urlpatterns = [
    path('console/', views.console, name='console'),
    path('gallery/', views.gallery, name='gallery'),
    path('my_profile/', views.my_profile, name='my_profile'),
    path('others_profile/', views.others_profile, name='others_profile'),
    path('discussion_board/', views.discussion_board, name='discussion_board'),
]
