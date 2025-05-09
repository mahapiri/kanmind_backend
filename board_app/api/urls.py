from django.urls import path

from board_app.api.views import BoardListView


urlpatterns = [
    path('', BoardListView.as_view(), name="boards"),
]