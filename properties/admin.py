from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Property, PropertyImage, Booking, RentalRequest, Message


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """自定義用戶管理"""
    list_display = ('username', 'email', 'role', 'phone', 'is_staff', 'date_joined')
    list_filter = ('role', 'is_staff', 'is_active')
    search_fields = ('username', 'email', 'phone')
    
    fieldsets = UserAdmin.fieldsets + (
        ('額外資訊', {'fields': ('role', 'phone', 'avatar')}),
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('額外資訊', {'fields': ('role', 'phone')}),
    )


class PropertyImageInline(admin.TabularInline):
    """房源圖片內聯"""
    model = PropertyImage
    extra = 1
    fields = ('image', 'is_cover', 'order')


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    """房源管理"""
    list_display = ('title', 'landlord', 'property_type', 'city', 'district', 'price_per_night', 'is_available', 'created_at')
    list_filter = ('property_type', 'is_available', 'city', 'created_at')
    search_fields = ('title', 'description', 'city', 'district', 'address')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('基本資訊', {
            'fields': ('landlord', 'title', 'description', 'property_type')
        }),
        ('位置資訊', {
            'fields': ('city', 'district', 'address', 'latitude', 'longitude')
        }),
        ('房源詳情', {
            'fields': ('bedrooms', 'bathrooms', 'max_guests')
        }),
        ('價格和狀態', {
            'fields': ('price_per_night', 'is_available')
        }),
        ('設施', {
            'fields': ('amenities',)
        }),
        ('時間戳', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [PropertyImageInline]


@admin.register(PropertyImage)
class PropertyImageAdmin(admin.ModelAdmin):
    """房源圖片管理"""
    list_display = ('property', 'is_cover', 'order', 'uploaded_at')
    list_filter = ('is_cover', 'uploaded_at')
    search_fields = ('property__title',)


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    """預訂管理"""
    list_display = ('booking_number', 'property', 'tenant', 'check_in', 'check_out', 'guests', 'total_price', 'status', 'created_at')
    list_filter = ('status', 'check_in', 'created_at')
    search_fields = ('booking_number', 'property__title', 'tenant__username')
    readonly_fields = ('booking_number', 'created_at', 'updated_at')
    
    fieldsets = (
        ('預訂資訊', {
            'fields': ('booking_number', 'property', 'tenant')
        }),
        ('入住資訊', {
            'fields': ('check_in', 'check_out', 'guests')
        }),
        ('價格和狀態', {
            'fields': ('total_price', 'status')
        }),
        ('備註', {
            'fields': ('notes',)
        }),
        ('時間戳', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(RentalRequest)
class RentalRequestAdmin(admin.ModelAdmin):
    """租客需求管理"""
    list_display = ('title', 'tenant', 'preferred_city', 'budget_range', 'property_type', 'is_active', 'created_at')
    list_filter = ('is_active', 'property_type', 'budget_range', 'preferred_city', 'created_at')
    search_fields = ('title', 'description', 'tenant__username', 'preferred_city')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('基本資訊', {
            'fields': ('tenant', 'title', 'description', 'property_type', 'is_active')
        }),
        ('位置偏好', {
            'fields': ('preferred_city', 'preferred_district')
        }),
        ('房源需求', {
            'fields': ('min_bedrooms', 'min_bathrooms', 'max_guests')
        }),
        ('預算和時間', {
            'fields': ('budget_range', 'move_in_date', 'rental_duration')
        }),
        ('期望設施', {
            'fields': ('desired_amenities',)
        }),
        ('時間戳', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    """消息管理"""
    list_display = ('rental_request', 'sender', 'receiver', 'content_preview', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('content', 'sender__username', 'receiver__username')
    readonly_fields = ('created_at',)
    
    def content_preview(self, obj):
        """消息内容预览"""
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = '消息内容'
    
    fieldsets = (
        ('消息資訊', {
            'fields': ('rental_request', 'sender', 'receiver', 'content')
        }),
        ('狀態', {
            'fields': ('is_read',)
        }),
        ('時間戳', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
