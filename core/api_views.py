from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.utils.timezone import now
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from datetime import date
from django.db.models import Q
from .models import Room, Reservation

@api_view(["POST"])
def customer_register(request):

    username = request.data.get("username")
    email = request.data.get("email")
    password = request.data.get("password")

    if not username or not email or not password:

        return Response(
            {
                "success": False,
                "message": "Username, email, and password are required."
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    if User.objects.filter(username=username).exists():

        return Response(
            {
                "success": False,
                "message": "Username already exists."
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    if User.objects.filter(email=email).exists():

        return Response(
            {
                "success": False,
                "message": "Email already exists."
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    user = User.objects.create_user(
        username=username,
        email=email,
        password=password
    )

    return Response(
        {
            "success": True,
            "message": "Customer account created successfully.",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
            }
        },
        status=status.HTTP_201_CREATED
    )


@api_view(["POST"])
def customer_login(request):

    username = request.data.get("username")
    password = request.data.get("password")

    # ==========================================
    # CHECK REQUIRED FIELDS
    # ==========================================

    if not username or not password:

        return Response(
            {
                "success": False,
                "message": "Username and password are required."
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    # ==========================================
    # AUTHENTICATE USER
    # ==========================================

    user = authenticate(
        username=username,
        password=password
    )

    # ==========================================
    # INVALID LOGIN
    # ==========================================

    if user is None:

        return Response(
            {
                "success": False,
                "message": "Invalid username or password."
            },
            status=status.HTTP_401_UNAUTHORIZED
        )

    # ==========================================
    # PREVENT SUPERUSER LOGIN THROUGH CUSTOMER API
    # ==========================================

    if user.is_superuser:

        return Response(
            {
                "success": False,
                "message": "Superusers must use the admin login."
            },
            status=status.HTTP_403_FORBIDDEN
        )

    # ==========================================
    # GET OR CREATE TOKEN
    # ==========================================

    token, created = Token.objects.get_or_create(
        user=user
    )

    # ==========================================
    # LOGIN SUCCESS
    # ==========================================

    return Response(
        {
            "success": True,
            "message": "Login successful.",

            "token": token.key,

            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
            }
        },
        status=status.HTTP_200_OK
    )



@api_view(["GET"])
def room_list(request):

    rooms = Room.objects.all().order_by("-created_at")

    data = []

    for room in rooms:

        data.append({
            "id": room.id,
            "name": room.name,
            "type": room.type,
            "description": room.description,
            "price": str(room.price),
            "capacity": room.capacity,
            "status": room.status,

            "image": (
                request.build_absolute_uri(room.image.url)
                if room.image
                else None
            ),

            "created_at": room.created_at,
            "updated_at": room.updated_at,
        })

    return Response({
        "success": True,
        "rooms": data,
    })

@api_view(["GET"])
def room_detail(request, room_id):

    room = get_object_or_404(
        Room,
        id=room_id
    )

    return Response({
        "success": True,
        "room": {
            "id": room.id,
            "name": room.name,
            "type": room.type,
            "description": room.description,
            "price": str(room.price),
            "capacity": room.capacity,
            "status": room.status,

            "image": (
                request.build_absolute_uri(room.image.url)
                if room.image
                else None
            ),
        }
    })

@api_view(["POST"])
def create_reservation(request):

    # ==========================================
    # CHECK LOGIN
    # ==========================================

    if not request.user.is_authenticated:

        return Response(
            {
                "success": False,
                "message": "You must be logged in."
            },
            status=401
        )


    # ==========================================
    # GET DATA
    # ==========================================

    room_id = request.data.get("room_id")

    check_in = request.data.get("check_in")

    check_out = request.data.get("check_out")

    adults = request.data.get("adults", 1)

    children = request.data.get("children", 0)

    special_request = request.data.get(
        "special_request",
        ""
    )


    # ==========================================
    # REQUIRED FIELDS
    # ==========================================

    if not room_id:
        return Response(
            {
                "success": False,
                "message": "Room is required."
            },
            status=400
        )


    if not check_in or not check_out:
        return Response(
            {
                "success": False,
                "message":
                    "Check-in and check-out are required."
            },
            status=400
        )


    # ==========================================
    # GET ROOM
    # ==========================================

    room = get_object_or_404(
        Room,
        id=room_id
    )


    # ==========================================
    # CHECK ROOM STATUS
    # ==========================================

    if room.status != "AVAILABLE":

        return Response(
            {
                "success": False,
                "message":
                    "This room is currently unavailable."
            },
            status=400
        )


    # ==========================================
    # CONVERT DATES
    # ==========================================

    try:

        check_in_date = date.fromisoformat(
            check_in
        )

        check_out_date = date.fromisoformat(
            check_out
        )

    except ValueError:

        return Response(
            {
                "success": False,
                "message": "Invalid date format."
            },
            status=400
        )


    # ==========================================
    # CHECK DATE ORDER
    # ==========================================

    if check_out_date <= check_in_date:

        return Response(
            {
                "success": False,
                "message":
                    "Check-out must be after check-in."
            },
            status=400
        )


    # ==========================================
    # CHECK PAST DATE
    # ==========================================

    if check_in_date < date.today():

        return Response(
            {
                "success": False,
                "message":
                    "Check-in cannot be in the past."
            },
            status=400
        )


    # ==========================================
    # CHECK CAPACITY
    # ==========================================

    try:

        adults = int(adults)

        children = int(children)

    except (TypeError, ValueError):

        return Response(
            {
                "success": False,
                "message":
                    "Invalid guest count."
            },
            status=400
        )


    if adults < 1:

        return Response(
            {
                "success": False,
                "message":
                    "At least one adult is required."
            },
            status=400
        )


    total_guests = adults + children


    if total_guests > room.capacity:

        return Response(
            {
                "success": False,
                "message":
                    f"Maximum capacity is "
                    f"{room.capacity} guests."
            },
            status=400
        )


    # ==========================================
    # CHECK EXISTING RESERVATIONS
    # ==========================================

    overlapping_reservation = Reservation.objects.filter(
        room=room,
        status__in=[
            "PENDING",
            "CONFIRMED"
        ],
        check_in__lt=check_out_date,
        check_out__gt=check_in_date,
    ).exists()


    if overlapping_reservation:

        return Response(
            {
                "success": False,
                "message":
                    "This room is already reserved "
                    "for the selected dates."
            },
            status=400
        )


    # ==========================================
    # CALCULATE NIGHTS
    # ==========================================

    nights = (
        check_out_date - check_in_date
    ).days


    # ==========================================
    # CALCULATE TOTAL
    # ==========================================

    total_amount = (
        room.price * nights
    )


    # ==========================================
    # CREATE RESERVATION
    # ==========================================

    reservation = Reservation.objects.create(

        customer=request.user,

        room=room,

        check_in=check_in_date,

        check_out=check_out_date,

        adults=adults,

        children=children,

        special_request=special_request,

        total_amount=total_amount,

        status="PENDING",
    )


    # ==========================================
    # RESPONSE
    # ==========================================

    return Response(
        {
            "success": True,

            "message":
                "Reservation created successfully.",

            "reservation": {
                "id": reservation.id,

                "room": room.name,

                "check_in":
                    reservation.check_in,

                "check_out":
                    reservation.check_out,

                "adults":
                    reservation.adults,

                "children":
                    reservation.children,

                "nights":
                    nights,

                "total_amount":
                    str(reservation.total_amount),

                "status":
                    reservation.status,

                "created_at":
                    reservation.created_at,
            }
        },
        status=201
    )

@api_view(["GET"])
def my_reservations(request):

    if not request.user.is_authenticated:
        return Response(
            {
                "success": False,
                "message": "You must be logged in."
            },
            status=401
        )

    reservations = (
        Reservation.objects
        .filter(customer=request.user)
        .select_related("room")
        .order_by("-created_at")
    )

    data = []

    for reservation in reservations:

        data.append({
            "id": reservation.id,

            "room": {
                "id": reservation.room.id,
                "name": reservation.room.name,
                "type": reservation.room.type,
                "image": (
                    request.build_absolute_uri(
                        reservation.room.image.url
                    )
                    if reservation.room.image
                    else None
                ),
            },

            "check_in": reservation.check_in,
            "check_out": reservation.check_out,

            "adults": reservation.adults,
            "children": reservation.children,

            "special_request":
                reservation.special_request,

            "total_amount":
                str(reservation.total_amount),

            "status":
                reservation.status,

            "created_at":
                reservation.created_at,
        })

    return Response({
        "success": True,
        "reservations": data,
    })


@api_view(["POST"])
def upload_payment_receipt(request, reservation_id):

    # ==========================================
    # CHECK LOGIN
    # ==========================================

    if not request.user.is_authenticated:

        return Response(
            {
                "success": False,
                "message": "You must be logged in."
            },
            status=401
        )


    # ==========================================
    # GET RESERVATION
    # ==========================================

    try:

        reservation = Reservation.objects.get(
            id=reservation_id,
            customer=request.user
        )

    except Reservation.DoesNotExist:

        return Response(
            {
                "success": False,
                "message": "Reservation not found."
            },
            status=404
        )


    # ==========================================
    # CHECK STATUS
    # ==========================================

    if reservation.status == "CANCELLED":

        return Response(
            {
                "success": False,
                "message":
                    "This reservation has been cancelled."
            },
            status=400
        )


    # ==========================================
    # GET RECEIPT
    # ==========================================

    receipt = request.FILES.get(
        "payment_receipt"
    )


    if not receipt:

        return Response(
            {
                "success": False,
                "message":
                    "Payment receipt is required."
            },
            status=400
        )


    # ==========================================
    # CHECK FILE TYPE
    # ==========================================

    allowed_types = [
        "image/jpeg",
        "image/png",
        "image/webp"
    ]

    if receipt.content_type not in allowed_types:

        return Response(
            {
                "success": False,
                "message":
                    "Only JPG, PNG, or WEBP images are allowed."
            },
            status=400
        )


    # ==========================================
    # CHECK FILE SIZE
    # ==========================================

    if receipt.size > 5 * 1024 * 1024:

        return Response(
            {
                "success": False,
                "message":
                    "Receipt must be less than 5MB."
            },
            status=400
        )


    # ==========================================
    # SAVE RECEIPT
    # ==========================================

    reservation.payment_receipt = receipt

    reservation.payment_status = "PENDING"

    reservation.payment_uploaded_at = now()

    reservation.save(
        update_fields=[
            "payment_receipt",
            "payment_status",
            "payment_uploaded_at"
        ]
    )


    # ==========================================
    # RESPONSE
    # ==========================================

    return Response(
        {
            "success": True,

            "message":
                "Payment receipt uploaded successfully.",

            "reservation": {
                "id": reservation.id,

                "payment_status":
                    reservation.payment_status,

                "receipt":
                    request.build_absolute_uri(
                        reservation.payment_receipt.url
                    )
            }
        },
        status=200
    )


@api_view(["GET"])
def reservation_detail(request, reservation_id):

    # ==========================================
    # CHECK LOGIN
    # ==========================================

    if not request.user.is_authenticated:

        return Response(
            {
                "success": False,
                "message": "You must be logged in."
            },
            status=401
        )


    # ==========================================
    # GET RESERVATION
    # ==========================================

    try:

        reservation = (
            Reservation.objects
            .select_related("room")
            .get(
                id=reservation_id,
                customer=request.user
            )
        )

    except Reservation.DoesNotExist:

        return Response(
            {
                "success": False,
                "message": "Reservation not found."
            },
            status=404
        )


    # ==========================================
    # ROOM IMAGE
    # ==========================================

    room_image = None

    if reservation.room.image:

        room_image = request.build_absolute_uri(
            reservation.room.image.url
        )


    # ==========================================
    # CALCULATE NIGHTS
    # ==========================================

    nights = (
        reservation.check_out -
        reservation.check_in
    ).days


    # ==========================================
    # RESPONSE
    # ==========================================

    return Response(
        {
            "success": True,

            "reservation": {

                "id":
                    reservation.id,

                "room": {

                    "id":
                        reservation.room.id,

                    "name":
                        reservation.room.name,

                    "type":
                        reservation.room.type,

                    "image":
                        room_image,

                    "price":
                        str(
                            reservation.room.price
                        ),

                    "capacity":
                        reservation.room.capacity,

                },

                "check_in":
                    reservation.check_in,

                "check_out":
                    reservation.check_out,

                "adults":
                    reservation.adults,

                "children":
                    reservation.children,

                "special_request":
                    reservation.special_request,

                "nights":
                    nights,

                "total_amount":
                    str(
                        reservation.total_amount
                    ),

                "status":
                    reservation.status,

                "payment_status":
                    reservation.payment_status,

                "payment_receipt":
                    (
                        request.build_absolute_uri(
                            reservation.payment_receipt.url
                        )
                        if reservation.payment_receipt
                        else None
                    ),

                "payment_uploaded_at":
                    reservation.payment_uploaded_at,

                "created_at":
                    reservation.created_at,
            }
        },
        status=200
    )