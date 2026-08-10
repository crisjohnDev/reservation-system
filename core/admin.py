from django.contrib import admin

# Register your models here.
from .models import Room, Reservation


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "type",
        "price",
        "capacity",
        "status",
        "created_at",
    )

    list_filter = (
        "type",
        "status",
    )

    search_fields = (
        "name",
        "description",
    )


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "customer",
        "room",
        "check_in",
        "check_out",
        "adults",
        "children",
        "total_amount",
        "status",
        "created_at",
    )

    list_filter = (
        "status",
        "check_in",
        "check_out",
    )

    search_fields = (
        "customer__username",
        "customer__email",
        "room__name",
    )

    ordering = (
        "-created_at",
    )