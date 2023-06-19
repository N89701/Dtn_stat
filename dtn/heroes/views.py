from django.shortcuts import render
from django.http import HttpResponse
from django.views.generic import ListView
from .models import Hero, Appearance

class HeroList(ListView):
    model = Hero
    template_name = "heroes/index.html"
