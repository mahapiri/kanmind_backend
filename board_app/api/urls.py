from django.urls import path
from rest_framework.routers import DefaultRouter

from board_app.api.views import BoardDetailView, BoardListView


urlpatterns = [
    path('', BoardListView.as_view(), name="boards"),
    path('<int:pk>/', BoardDetailView.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name="board-detail"),
]