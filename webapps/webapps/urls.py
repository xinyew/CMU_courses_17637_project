"""webapps URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from dallf import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.gallery, name='home'),  # Temporary
    path('oauth/', include('social_django.urls', namespace='social')),
    path('console/', views.console, name='console'),
    path('gallery/', views.gallery, name='gallery'),
    path('favorite/', views.favorite_action, name='favorite'),
    path('label/', views.label_action, name='label'),
    path('my_profile/', views.my_profile, name='my_profile'),
    path('others_profile/', views.others_profile, name='others_profile'),
    path('discussion_board/', views.discussion_board, name='discussion_board'),
    path('logout/', views.logout_action, name='logout'),
    # API calls
    path('images/generate/', views.generate_action, name='generate'),
    # Testing
    path('testing/generate/', views.test_generate_action, name='test_generate')
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
