from django.urls import path

from . import views

app_name = "news"

urlpatterns = [
    path("news/", views.news_list, name="list"),
    path("news/<int:pk>/", views.news_detail, name="detail"),
    path("stories/", views.story_list, name="stories"),
    path("stories/<int:pk>/", views.story_detail, name="story_detail"),
]
