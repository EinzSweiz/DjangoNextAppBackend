from django.urls import path
from . import api

urlpatterns = [
    path('all/<str:pk>', api.get_reviews_api, name='api_get_reviews'),
    path('create/<str:pk>', api.create_reviews_api, name='api_create_review'),
]