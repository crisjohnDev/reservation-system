from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from datetime import date
from .models import Room, Reservation

def login_view(request):

    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":

        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:

            # Only allow superusers
            if not user.is_superuser:
                return render(
                    request,
                    "login.html",
                    {
                        "error": "You do not have permission to access this system."
                    }
                )

            login(request, user)

            return redirect("dashboard")

        return render(
            request,
            "login.html",
            {
                "error": "Invalid username or password."
            }
        )

    return render(request, "login.html")


@login_required
def dashboard(request):

    # Extra protection
    if not request.user.is_superuser:
        return redirect("login")

    return render(request, "pages/dashboard.html")


@login_required
def rooms_view(request):

    if not request.user.is_superuser:
        return redirect("dashboard")

    rooms = Room.objects.all().order_by("name")

    context = {
        "rooms": rooms,

        "total_units": rooms.count(),

        "total_rooms": rooms.filter(
            type="ROOM"
        ).count(),

        "total_cottages": rooms.filter(
            type="COTTAGE"
        ).count(),

        "available_units": rooms.filter(
            status="AVAILABLE"
        ).count(),
    }

    return render(
        request,
        "pages/rooms.html",
        context
    )

@login_required
def room_create(request):

    if not request.user.is_superuser:
        return redirect("dashboard")

    if request.method == "POST":

        name = request.POST.get("name")
        room_type = request.POST.get("type")
        description = request.POST.get("description")
        price = request.POST.get("price")
        capacity = request.POST.get("capacity")
        status = request.POST.get("status")

        image = request.FILES.get("image")

        Room.objects.create(
            name=name,
            type=room_type,
            description=description,
            price=price,
            capacity=capacity,
            status=status,
            image=image,
        )

        return redirect("rooms")

    return render(
        request,
        "pages/room_form.html"
    )

@login_required
def room_edit(request, pk):

    if not request.user.is_superuser:
        return redirect("dashboard")

    room = get_object_or_404(
        Room,
        pk=pk
    )

    if request.method == "POST":

        room.name = request.POST.get("name")

        room.type = request.POST.get("type")

        room.description = request.POST.get(
            "description"
        )

        room.price = request.POST.get(
            "price"
        )

        room.capacity = request.POST.get(
            "capacity"
        )

        room.status = request.POST.get(
            "status"
        )

        image = request.FILES.get("image")

        if image:
            room.image = image

        room.save()

        return redirect("rooms")

    return render(
        request,
        "pages/room_form.html",
        {
            "room": room
        }
    )

@login_required
def room_delete(request, pk):

    if not request.user.is_superuser:
        return redirect("dashboard")

    room = get_object_or_404(
        Room,
        pk=pk
    )

    if request.method == "POST":

        room.delete()

        return redirect("rooms")

    return render(
        request,
        "pages/room_confirm_delete.html",
        {
            "room": room
        }
    )

@login_required
def reservation_list(request):

    if not request.user.is_authenticated:
        return redirect("login")

    if not request.user.is_superuser:
        return redirect("dashboard")

    reservations = (
        Reservation.objects
        .select_related("customer", "room")
        .order_by("-created_at")
    )

    pending_count = reservations.filter(
        status="PENDING"
    ).count()

    confirmed_count = reservations.filter(
        status="CONFIRMED"
    ).count()

    cancelled_count = reservations.filter(
        status="CANCELLED"
    ).count()

    return render(
        request,
        "reservations/list.html",
        {
            "reservations": reservations,
            "pending_count": pending_count,
            "confirmed_count": confirmed_count,
            "cancelled_count": cancelled_count,
        }
    )

@login_required
def confirm_reservation(request, reservation_id):

    if not request.user.is_authenticated:
        return redirect("login")

    if not request.user.is_superuser:
        return redirect("dashboard")

    if request.method == "POST":

        reservation = get_object_or_404(
            Reservation,
            id=reservation_id
        )

        reservation.status = "CONFIRMED"

        reservation.save()

    return redirect("reservation_list")

@login_required
def cancel_reservation(request, reservation_id):

    if not request.user.is_authenticated:
        return redirect("login")

    if not request.user.is_superuser:
        return redirect("dashboard")

    if request.method == "POST":

        reservation = get_object_or_404(
            Reservation,
            id=reservation_id
        )

        reservation.status = "CANCELLED"

        reservation.save()

    return redirect("reservation_list")


@login_required
def reservation_detail(request, reservation_id):

    if not request.user.is_authenticated:
        return redirect("login")

    if not request.user.is_superuser:
        return redirect("dashboard")

    reservation = get_object_or_404(
        Reservation.objects.select_related(
            "customer",
            "room"
        ),
        id=reservation_id
    )

    return render(
        request,
        "reservations/detail.html",
        {
            "reservation": reservation
        }
    )

@login_required
def complete_reservation(request, reservation_id):

    if not request.user.is_authenticated:
        return redirect("login")

    if not request.user.is_superuser:
        return redirect("dashboard")

    if request.method != "POST":
        return redirect("reservation_list")

    reservation = get_object_or_404(
        Reservation,
        id=reservation_id
    )

    # Only confirmed reservations can be completed
    if reservation.status != "CONFIRMED":
        return redirect(
            "reservation_detail",
            reservation_id=reservation.id
        )

    reservation.status = "COMPLETED"
    reservation.save()

    return redirect(
        "reservation_detail",
        reservation_id=reservation.id
    )

@login_required
def availability(request):

    check_in = request.GET.get("check_in")
    check_out = request.GET.get("check_out")

    rooms = Room.objects.all()

    reservations = Reservation.objects.filter(
        status__in=[
            "PENDING",
            "CONFIRMED",
        ]
    ).select_related(
        "room",
        "customer",
    ).order_by(
        "check_in"
    )

    available_rooms = rooms
    unavailable_rooms = Room.objects.none()

    searched = False

    # ==========================================
    # CHECK SELECTED DATES
    # ==========================================

    if check_in and check_out:

        searched = True

        try:

            check_in_date = date.fromisoformat(
                check_in
            )

            check_out_date = date.fromisoformat(
                check_out
            )

            # --------------------------------------
            # FIND ROOMS WITH OVERLAPPING RESERVATION
            # --------------------------------------

            unavailable_rooms = rooms.filter(
                reservation__status__in=[
                    "PENDING",
                    "CONFIRMED",
                ],
                reservation__check_in__lt=check_out_date,
                reservation__check_out__gt=check_in_date,
            ).distinct()

            # --------------------------------------
            # AVAILABLE
            # --------------------------------------

            available_rooms = rooms.exclude(
                id__in=unavailable_rooms.values_list(
                    "id",
                    flat=True
                )
            )

        except ValueError:

            searched = False

    # ==========================================
    # CALENDAR RESERVATIONS
    # ==========================================

    calendar_reservations = []

    for reservation in reservations:

        calendar_reservations.append({

            "id": reservation.id,

            "title": (
                f"{reservation.room.name} - "
                f"{reservation.customer.username}"
            ),

            "room": reservation.room.name,

            "customer": (
                reservation.customer.username
            ),

            "check_in": (
                reservation.check_in.isoformat()
            ),

            "check_out": (
                reservation.check_out.isoformat()
            ),

            "status": reservation.status,

        })

    # ==========================================
    # CONTEXT
    # ==========================================

    context = {

        "rooms": rooms,

        "available_rooms":
            available_rooms,

        "unavailable_rooms":
            unavailable_rooms,

        "check_in":
            check_in,

        "check_out":
            check_out,

        "searched":
            searched,

        "reservations":
            reservations,

        "calendar_reservations":
            calendar_reservations,

    }

    return render(
        request,
        "pages/availability.html",
        context
    )

def logout_view(request):

    logout(request)

    return redirect("login")