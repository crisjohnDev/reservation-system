from django.urls import path
from .views import availability, complete_reservation, login_view, dashboard, logout_view

from .views import (
    login_view,
    logout_view,
    dashboard,
    rooms_view,
    room_create,
    room_edit,
    room_delete,
    reservation_list,
    confirm_reservation,
    cancel_reservation,
    reservation_detail
)

urlpatterns = [
    path("", login_view, name="login"),
    path("login/", login_view, name="login"),
    path("dashboard/", dashboard, name="dashboard"),
    path("logout/", logout_view, name="logout"),
    path("rooms/", rooms_view, name="rooms"),
    path("rooms/create/", room_create, name="room_create"),
    path("rooms/<int:pk>/edit/", room_edit, name="room_edit"),
    path("rooms/<int:pk>/delete/", room_delete, name="room_delete"),
    path("reservations/", reservation_list, name="reservation_list"),
    path("reservations/<int:reservation_id>/confirm/", confirm_reservation, name="confirm_reservation"),
    path("reservations/<int:reservation_id>/cancel/", cancel_reservation, name="cancel_reservation"),
    path("reservations/<int:reservation_id>/", reservation_detail, name="reservation_detail"),
    path("reservations/<int:reservation_id>/complete/", complete_reservation, name="complete_reservation"),
    path("availability/", availability, name="availability"),
]