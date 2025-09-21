from django.shortcuts import render
from django.http import HttpResponse


def home(request):
    """Basic home view"""
    return HttpResponse("Welcome to Smart School Management System!")