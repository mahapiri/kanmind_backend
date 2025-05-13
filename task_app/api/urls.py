from django.urls import path

from task_app.api.views import AssignedToMeView, CommentListView, ReviewerView, TaskView


urlpatterns = [
    path('assigned-to-me/', AssignedToMeView.as_view(), name="assigned-to-me"),
    path('reviewing/', ReviewerView.as_view(), name="reviewer"),
    path('', TaskView.as_view({'post': 'create'}), name="tasks"),
    path('<int:pk>/', TaskView.as_view({'patch': 'partial_update', 'delete': 'destroy'}), name="tasks-detail"),
    path('<int:pk>/comments/', CommentListView.as_view({'get': 'list', 'post': 'create', 'delete': 'destroy'}), name="comments"),
]