from django.db import models
from django.contrib.auth.models import User
# Create your models here.
class Room(models.Model):

    TYPE_CHOICES = [
        ("ROOM", "Room"),
        ("COTTAGE", "Cottage"),
    ]

    STATUS_CHOICES = [
        ("AVAILABLE", "Available"),
        ("UNAVAILABLE", "Unavailable"),
        ("MAINTENANCE", "Maintenance"),
    ]

    name = models.CharField(
        max_length=150
    )

    type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default="ROOM"
    )

    description = models.TextField(
        blank=True
    )

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    capacity = models.PositiveIntegerField(
        default=1
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="AVAILABLE"
    )

    image = models.ImageField(
        upload_to="rooms/",
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return self.name


class Reservation(models.Model):

    PAYMENT_STATUS = [
        ("UNPAID", "Unpaid"),
        ("PENDING", "Payment Verification"),
        ("PAID", "Paid"),
        ("REJECTED", "Rejected"),
    ]

    STATUS = [
        ("PENDING", "Pending"),
        ("CONFIRMED", "Confirmed"),
        ("CANCELLED", "Cancelled"),
        ("COMPLETED", "Completed"),
    ]

    customer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="reservations"
    )

    room = models.ForeignKey(
        Room,
        on_delete=models.CASCADE
    )

    check_in = models.DateField()
    check_out = models.DateField()

    adults = models.PositiveIntegerField(default=1)
    children = models.PositiveIntegerField(default=0)

    special_request = models.TextField(
        blank=True,
        default=""
    )

    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS,
        default="PENDING"
    )

    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS,
        default="UNPAID"
    )

    payment_receipt = models.ImageField(
        upload_to="payment_receipts/",
        blank=True,
        null=True
    )

    payment_uploaded_at = models.DateTimeField(
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"Reservation #{self.id}"

class RoomMapPosition(models.Model):

    room = models.OneToOneField(
        Room,
        on_delete=models.CASCADE,
        related_name="map_position"
    )

    # Position as percentage of the map
    x = models.DecimalField(
        max_digits=6,
        decimal_places=3,
        default=0
    )

    y = models.DecimalField(
        max_digits=6,
        decimal_places=3,
        default=0
    )

    # Size as percentage of the map
    width = models.DecimalField(
        max_digits=6,
        decimal_places=3,
        default=8
    )

    height = models.DecimalField(
        max_digits=6,
        decimal_places=3,
        default=6
    )

    # Whether the room should appear on the map
    is_visible = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return f"{self.room.name} Map Position"