from django.urls import path

from . import views

app_name = "feedback"

urlpatterns = [
    path("question/<str:fonctionnalite>/", views.question_active, name="question_active"),
    path("repondre/<uuid:question_id>/", views.repondre, name="repondre"),
]