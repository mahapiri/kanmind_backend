from django.urls import path

from board_app.api.views import BoardDetailView, BoardListView

# Retrieve, update, partially update and delete a specific board
# Maps HTTP methods to ViewSet actions:
# - GET: retrieve (get board details)
# - PUT: update (full update of board)
# - PATCH: partial_update (partial update of board)
# - DELETE: destroy (delete board)
urlpatterns = [
    path("", BoardListView.as_view(), name="boards"),
    path("<int:pk>/", BoardDetailView.as_view({
        "get": "retrieve", 
        "put": "update",
        "patch": "partial_update", 
        "delete": "destroy"}), name="board-detail"),
]
