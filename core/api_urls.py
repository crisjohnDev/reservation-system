from django.urls import path

from .api_views import (
    customer_register,
    customer_login,
    room_list,
    room_detail,
    create_reservation,
    my_reservations,
    upload_payment_receipt,
    reservation_detail
    
)


urlpatterns = [

    # ==========================================
    # CUSTOMER
    # ==========================================

    path(
        "register/",
        customer_register,
        name="customer_register"
    ),

    path(
        "login/",
        customer_login,
        name="customer_login"
    ),


    # ==========================================
    # ROOMS
    # ==========================================

    path(
        "rooms/",
        room_list,
        name="room_list"
    ),

    path(
        "rooms/<int:room_id>/",
        room_detail,
        name="room_detail"
    ),


    # ==========================================
    # RESERVATIONS
    # ==========================================

    # GET - customer's reservations
    path(
        "reservations/",
        my_reservations,
        name="my_reservations"
    ),

    # POST - create reservation
    path(
        "reservations/create/",
        create_reservation,
        name="create_reservation"
    ),

    # GET - single reservation
    path(
        "reservations/<int:reservation_id>/",
        reservation_detail,
        name="reservation_detail"
    ),

    # POST - upload payment receipt
    path(
        "reservations/<int:reservation_id>/upload-receipt/",
        upload_payment_receipt,
        name="upload_payment_receipt"
    ),

]