from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from datetime import date
from .models import Room, Reservation, RoomMapPosition
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Sum, Count
import json
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.http import JsonResponse
from django.views.decorators.http import require_POST

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

    # ==========================================
    # SUPERUSER PROTECTION
    # ==========================================

    if not request.user.is_superuser:
        return redirect("login")


    # ==========================================
    # RESERVATION STATISTICS
    # ==========================================

    total_reservations = Reservation.objects.count()

    pending_reservations = Reservation.objects.filter(
        status="PENDING"
    ).count()

    confirmed_reservations = Reservation.objects.filter(
        status="CONFIRMED"
    ).count()

    completed_reservations = Reservation.objects.filter(
        status="COMPLETED"
    ).count()

    cancelled_reservations = Reservation.objects.filter(
        status="CANCELLED"
    ).count()


    # ==========================================
    # CUSTOMER COUNT
    # ==========================================

    total_customers = User.objects.filter(
        is_superuser=False,
        reservations__isnull=False
    ).distinct().count()


    # ==========================================
    # PAYMENT STATISTICS
    # ==========================================

    unpaid_payments = Reservation.objects.filter(
        payment_status="UNPAID"
    ).count()

    pending_payments = Reservation.objects.filter(
        payment_status="PENDING"
    ).count()

    paid_payments = Reservation.objects.filter(
        payment_status="PAID"
    ).count()

    rejected_payments = Reservation.objects.filter(
        payment_status="REJECTED"
    ).count()


    # ==========================================
    # TOTAL VERIFIED REVENUE
    # ==========================================

    total_revenue = (
        Reservation.objects
        .filter(payment_status="PAID")
        .aggregate(
            total=Sum("total_amount")
        )["total"]
        or 0
    )


    # ==========================================
    # RECENT RESERVATIONS
    # ==========================================

    recent_reservations = (
        Reservation.objects
        .select_related(
            "customer",
            "room"
        )
        .order_by("-created_at")[:5]
    )


    # ==========================================
    # CONTEXT
    # ==========================================

    context = {

        "total_reservations":
            total_reservations,

        "pending_reservations":
            pending_reservations,

        "confirmed_reservations":
            confirmed_reservations,

        "completed_reservations":
            completed_reservations,

        "cancelled_reservations":
            cancelled_reservations,

        "total_customers":
            total_customers,

        "unpaid_payments":
            unpaid_payments,

        "pending_payments":
            pending_payments,

        "paid_payments":
            paid_payments,

        "rejected_payments":
            rejected_payments,

        "total_revenue":
            total_revenue,

        "recent_reservations":
            recent_reservations,
    }


    return render(
        request,
        "pages/dashboard.html",
        context
    )


@login_required
def rooms_view(request):

    # Extra protection
    if not request.user.is_superuser:
        return redirect("login")

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

    # Extra protection
    if not request.user.is_superuser:
        return redirect("login")

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

    # Extra protection
    if not request.user.is_superuser:
        return redirect("login")

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

    # Extra protection
    if not request.user.is_superuser:
        return redirect("login")

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
        # Extra protection
    if not request.user.is_superuser:
        return redirect("login")

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
    # Extra protection
    if not request.user.is_superuser:
        return redirect("login")
    
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
        # Extra protection
    if not request.user.is_superuser:
        return redirect("login")

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


# ==========================================
# APPROVE PAYMENT
# ==========================================
@login_required
def approve_payment(request, reservation_id):
        # Extra protection
    if not request.user.is_superuser:
        return redirect("login")

    if request.method != "POST":
        return redirect("reservation_detail", reservation_id=reservation_id)

    reservation = get_object_or_404(
        Reservation,
        id=reservation_id
    )

    # --------------------------------------
    # CHECK RECEIPT
    # --------------------------------------

    if not reservation.payment_receipt:

        messages.error(
            request,
            "This reservation does not have a payment receipt."
        )

        return redirect(
            "reservation_detail",
            reservation_id=reservation.id
        )

    # --------------------------------------
    # APPROVE PAYMENT
    # --------------------------------------

    reservation.payment_status = "PAID"

    # --------------------------------------
    # CONFIRM RESERVATION
    # --------------------------------------

    reservation.status = "CONFIRMED"

    reservation.save(
        update_fields=[
            "payment_status",
            "status",
        ]
    )

    messages.success(
        request,
        f"Payment for Reservation #{reservation.id} "
        "has been approved."
    )

    return redirect(
        "reservation_detail",
        reservation_id=reservation.id
    )


# ==========================================
# REJECT PAYMENT
# ==========================================
@login_required
def reject_payment(request, reservation_id):

        # Extra protection
    if not request.user.is_superuser:
        return redirect("login")

    if request.method != "POST":
        return redirect("reservation_detail", reservation_id=reservation_id)

    reservation = get_object_or_404(
        Reservation,
        id=reservation_id
    )

    # --------------------------------------
    # CHECK RECEIPT
    # --------------------------------------

    if not reservation.payment_receipt:

        messages.error(
            request,
            "This reservation does not have a payment receipt."
        )

        return redirect(
            "reservation_detail",
            reservation_id=reservation.id
        )

    # --------------------------------------
    # REJECT PAYMENT
    # --------------------------------------

    reservation.payment_status = "REJECTED"

    reservation.save(
        update_fields=[
            "payment_status",
        ]
    )

    messages.warning(
        request,
        f"Payment for Reservation #{reservation.id} "
        "has been rejected."
    )

    return redirect(
        "reservation_detail",
        reservation_id=reservation.id
    )


# =========================================================
# PAYMENT LIST
# =========================================================
@login_required
def payment_list(request):
        # Extra protection
    if not request.user.is_superuser:
        return redirect("login")

    status = request.GET.get("status")

    reservations = (
        Reservation.objects
        .select_related("customer", "room")
        .order_by(
            "-payment_uploaded_at",
            "-created_at"
        )
    )

    if status in [
        "UNPAID",
        "PENDING",
        "PAID",
        "REJECTED",
    ]:

        reservations = reservations.filter(
            payment_status=status
        )

    return render(
        request,
        "payments/payment_list.html",
        {
            "reservations": reservations,
            "current_status": status,
        }
    )


# =========================================================
# PAYMENT DETAIL
# =========================================================
@login_required
def payment_detail(request, reservation_id):
    # Extra protection
    if not request.user.is_superuser:
        return redirect("login")
    reservation = get_object_or_404(
        Reservation.objects.select_related(
            "customer",
            "room"
        ),
        id=reservation_id
    )

    return render(
        request,
        "payments/payment_detail.html",
        {
            "reservation": reservation,
        }
    )


# =========================================================
# APPROVE PAYMENT
# =========================================================
@login_required
def approve_payment(request, reservation_id):
    # Extra protection
    if not request.user.is_superuser:
        return redirect("login")
    if request.method != "POST":
        return redirect("payment_detail", reservation_id=reservation_id)

    reservation = get_object_or_404(
        Reservation,
        id=reservation_id
    )

    # -----------------------------------------
    # CHECK RECEIPT
    # -----------------------------------------

    if not reservation.payment_receipt:

        messages.error(
            request,
            "This reservation does not have a payment receipt."
        )

        return redirect(
            "payment_detail",
            reservation_id=reservation_id
        )

    # -----------------------------------------
    # APPROVE PAYMENT
    # -----------------------------------------

    reservation.payment_status = "PAID"

    # Payment verified = reservation confirmed
    reservation.status = "CONFIRMED"

    reservation.save(
        update_fields=[
            "payment_status",
            "status",
        ]
    )

    messages.success(
        request,
        f"Payment for Reservation #{reservation.id} "
        "has been approved."
    )

    return redirect(
        "payment_detail",
        reservation_id=reservation_id
    )


# =========================================================
# REJECT PAYMENT
# =========================================================
@login_required
def reject_payment(request, reservation_id):
    # Extra protection
    if not request.user.is_superuser:
        return redirect("login")
    if request.method != "POST":
        return redirect("payment_detail", reservation_id=reservation_id)

    reservation = get_object_or_404(
        Reservation,
        id=reservation_id
    )

    # -----------------------------------------
    # REJECT PAYMENT
    # -----------------------------------------

    reservation.payment_status = "REJECTED"

    reservation.save(
        update_fields=[
            "payment_status",
        ]
    )

    messages.warning(
        request,
        f"Payment for Reservation #{reservation.id} "
        "has been rejected."
    )

    return redirect(
        "payment_detail",
        reservation_id=reservation_id
    )

@login_required
def customer_list(request):
    # Extra protection
    if not request.user.is_superuser:
        return redirect("login")
    customers = (
        User.objects
        .filter(is_staff=False)
        .order_by("-date_joined")
    )

    active_customers = customers.filter(
        is_active=True
    ).count()

    inactive_customers = customers.filter(
        is_active=False
    ).count()

    return render(
        request,
        "customers/customer_list.html",
        {
            "customers": customers,
            "active_customers": active_customers,
            "inactive_customers": inactive_customers,
        }
    )

@login_required
def customer_detail(request, customer_id):
    # Extra protection
    if not request.user.is_superuser:
        return redirect("login")
    customer = get_object_or_404(
        User,
        id=customer_id,
        is_staff=False
    )

    reservations = (
        Reservation.objects
        .filter(customer=customer)
        .select_related("room")
        .order_by("-created_at")
    )

    return render(
        request,
        "customers/customer_detail.html",
        {
            "customer": customer,
            "reservations": reservations,
        }
    )

@login_required
def reports(request):
    # Extra protection
    if not request.user.is_superuser:
        return redirect("login")
    # ==========================================
    # RESERVATION COUNTS
    # ==========================================

    total_reservations = Reservation.objects.count()

    pending_reservations = Reservation.objects.filter(
        status="PENDING"
    ).count()

    confirmed_reservations = Reservation.objects.filter(
        status="CONFIRMED"
    ).count()

    completed_reservations = Reservation.objects.filter(
        status="COMPLETED"
    ).count()

    cancelled_reservations = Reservation.objects.filter(
        status="CANCELLED"
    ).count()


    # ==========================================
    # PAYMENT COUNTS
    # ==========================================

    unpaid_payments = Reservation.objects.filter(
        payment_status="UNPAID"
    ).count()

    pending_payments = Reservation.objects.filter(
        payment_status="PENDING"
    ).count()

    paid_payments = Reservation.objects.filter(
        payment_status="PAID"
    ).count()

    rejected_payments = Reservation.objects.filter(
        payment_status="REJECTED"
    ).count()


    # ==========================================
    # REVENUE
    # ==========================================

    total_revenue = (
        Reservation.objects
        .filter(payment_status="PAID")
        .aggregate(
            total=Sum("total_amount")
        )["total"]
        or 0
    )


    # ==========================================
    # CUSTOMER COUNT
    # ==========================================

    total_customers = User.objects.filter(
        reservations__isnull=False
    ).distinct().count()


    # ==========================================
    # RECENT RESERVATIONS
    # ==========================================

    recent_reservations = (
        Reservation.objects
        .select_related(
            "customer",
            "room"
        )
        .order_by("-created_at")[:10]
    )


    # ==========================================
    # REVENUE BY ROOM
    # ==========================================

    revenue_by_room = (
        Reservation.objects
        .filter(
            payment_status="PAID"
        )
        .values(
            "room__name"
        )
        .annotate(
            total_revenue=Sum(
                "total_amount"
            ),
            reservation_count=Count("id")
        )
        .order_by("-total_revenue")
    )


    # ==========================================
    # CONTEXT
    # ==========================================

    context = {

        "total_reservations":
            total_reservations,

        "pending_reservations":
            pending_reservations,

        "confirmed_reservations":
            confirmed_reservations,

        "completed_reservations":
            completed_reservations,

        "cancelled_reservations":
            cancelled_reservations,

        "unpaid_payments":
            unpaid_payments,

        "pending_payments":
            pending_payments,

        "paid_payments":
            paid_payments,

        "rejected_payments":
            rejected_payments,

        "total_revenue":
            total_revenue,

        "total_customers":
            total_customers,

        "recent_reservations":
            recent_reservations,

        "revenue_by_room":
            revenue_by_room,
    }


    return render(
        request,
        "pages/reports.html",
        context
    )

@login_required
def mapping(request):

    rooms = (
        Room.objects
        .select_related("map_position")
        .all()
    )

    return render(
        request,
        "pages/mapping.html",
        {
            "rooms": rooms,
        }
    )

@login_required
def save_mapping(request):

    if not request.user.is_superuser:
        return JsonResponse(
            {
                "success": False,
                "message": "Permission denied."
            },
            status=403
        )


    if request.method != "POST":

        return JsonResponse(
            {
                "success": False,
                "message": "POST request required."
            },
            status=405
        )


    try:

        data = json.loads(
            request.body
        )

        positions = data.get(
            "positions",
            []
        )


    except json.JSONDecodeError:

        return JsonResponse(
            {
                "success": False,
                "message": "Invalid JSON data."
            },
            status=400
        )


    for position in positions:

        room_id = position.get(
            "room_id"
        )

        x = position.get(
            "x"
        )

        y = position.get(
            "y"
        )


        if room_id is None:
            continue


        try:

            x = float(x)
            y = float(y)

        except (
            TypeError,
            ValueError
        ):

            continue


        # Keep coordinates between 0 and 100

        x = max(
            0,
            min(100, x)
        )

        y = max(
            0,
            min(100, y)
        )


        room = get_object_or_404(
            Room,
            id=room_id
        )


        RoomMapPosition.objects.update_or_create(

            room=room,

            defaults={
                "x": x,
                "y": y,
            }

        )


    return JsonResponse(
        {
            "success": True,
            "message":
                "Mapping saved successfully."
        }
    )

@login_required
@require_POST
def save_room_map_position(request, room_id):

    try:
        data = json.loads(request.body)

        room = Room.objects.get(id=room_id)

        position, created = RoomMapPosition.objects.get_or_create(
            room=room
        )

        position.x = float(data.get("x", 0))
        position.y = float(data.get("y", 0))
        position.width = float(data.get("width", 10))
        position.height = float(data.get("height", 10))
        position.is_visible = bool(
            data.get("is_visible", True)
        )

        position.save()

        return JsonResponse({
            "success": True,
            "message": "Room position saved successfully."
        })

    except Room.DoesNotExist:

        return JsonResponse({
            "success": False,
            "message": "Room not found."
        }, status=404)

    except Exception as e:

        return JsonResponse({
            "success": False,
            "message": str(e)
        }, status=400)

def logout_view(request):

    logout(request)

    return redirect("login")