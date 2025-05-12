from django.urls import path

from task_app.api.views import AssignedToMeView, ReviewerView


urlpatterns = [
    path('assigned-to-me/', AssignedToMeView.as_view(), name="assigned-to-me"),
    path('reviewing/', ReviewerView.as_view(), name="reviewer"),
]