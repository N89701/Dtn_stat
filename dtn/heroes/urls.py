from django.urls import path

from .views import *  

app_name = 'posts'

urlpatterns = [
    path('', HeroList.as_view(), name='home'),
]