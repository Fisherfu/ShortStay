from django.urls import path
from . import views

urlpatterns = [
    # 租客功能（公開）
    path('', views.property_list, name='property_list'),
    path('property/<int:pk>/', views.property_detail, name='property_detail'),
    
    # 房東功能
    path('landlord/properties/', views.landlord_properties, name='landlord_properties'),
    path('landlord/properties/add/', views.property_add, name='property_add'),
    path('landlord/properties/<int:pk>/edit/', views.property_edit, name='property_edit'),
    path('landlord/properties/<int:pk>/delete/', views.property_delete, name='property_delete'),
    path('landlord/properties/<int:pk>/upload-image/', views.property_upload_image, name='property_upload_image'),
    path('landlord/properties/<int:pk>/delete-image/<int:image_id>/', views.property_delete_image, name='property_delete_image'),
    
    # 預訂功能
    path('property/<int:property_id>/book/', views.create_booking, name='create_booking'),
    path('booking/<int:booking_id>/success/', views.booking_success, name='booking_success'),
    path('my-bookings/', views.my_bookings, name='my_bookings'),
    path('booking/<int:booking_id>/cancel/', views.cancel_booking, name='cancel_booking'),
    path('landlord/bookings/', views.landlord_bookings, name='landlord_bookings'),
    path('landlord/bookings/<int:booking_id>/update/', views.update_booking_status, name='update_booking_status'),
    
    # 租客需求功能
    path('rental-requests/', views.rental_requests_list, name='rental_requests_list'),
    path('rental-requests/create/', views.create_rental_request, name='create_rental_request'),
    path('rental-requests/<int:pk>/', views.rental_request_detail, name='rental_request_detail'),
    path('rental-requests/<int:pk>/edit/', views.edit_rental_request, name='edit_rental_request'),
    path('rental-requests/<int:pk>/delete/', views.delete_rental_request, name='delete_rental_request'),
    path('my-rental-requests/', views.my_rental_requests, name='my_rental_requests'),
    
    # 用户注册
    path('register/', views.register, name='register'),
]
