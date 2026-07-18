from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class CustomUser(AbstractUser):
    """自定義用戶模型，支持房東、租客、管理員角色"""
    USER_ROLES = [
        ('landlord', '房東'),
        ('tenant', '租客'),
        ('admin', '管理員')
    ]
    
    role = models.CharField('角色', max_length=20, choices=USER_ROLES, default='tenant')
    phone = models.CharField('電話', max_length=20, blank=True)
    avatar = models.ImageField('頭像', upload_to='avatars/', blank=True, null=True)
    created_at = models.DateTimeField('註冊時間', auto_now_add=True)
    
    class Meta:
        verbose_name = '用戶'
        verbose_name_plural = '用戶'
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


class Property(models.Model):
    """房源模型"""
    PROPERTY_TYPES = [
        ('entire', '整套房'),
        ('private', '獨立房間'),
        ('shared', '共享房間')
    ]
    
    landlord = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='properties', verbose_name='房東')
    title = models.CharField('房源標題', max_length=200)
    description = models.TextField('房源描述')
    property_type = models.CharField('房源類型', max_length=20, choices=PROPERTY_TYPES, default='entire')
    
    # 位置資訊
    city = models.CharField('城市', max_length=100)
    district = models.CharField('區域', max_length=100)
    address = models.CharField('地址', max_length=255)
    latitude = models.DecimalField('緯度', max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField('經度', max_digits=9, decimal_places=6, null=True, blank=True)
    
    # 房源詳情
    bedrooms = models.IntegerField('臥室數', validators=[MinValueValidator(0)])
    bathrooms = models.IntegerField('浴室數', validators=[MinValueValidator(0)])
    max_guests = models.IntegerField('最大入住人數', validators=[MinValueValidator(1)])
    
    # 價格和狀態
    price_per_night = models.DecimalField('每晚價格', max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    is_available = models.BooleanField('是否可用', default=True)
    
    # 設施（JSON 存儲）
    amenities = models.JSONField('設施', default=list, blank=True)  # ['WiFi', '空調', '洗衣機', '廚房', '停車位', ...]
    
    # 時間戳
    created_at = models.DateTimeField('創建時間', auto_now_add=True)
    updated_at = models.DateTimeField('更新時間', auto_now=True)
    
    class Meta:
        verbose_name = '房源'
        verbose_name_plural = '房源'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.city}"


class PropertyImage(models.Model):
    """房源圖片模型"""
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='images', verbose_name='房源')
    image = models.ImageField('圖片', upload_to='properties/')
    is_cover = models.BooleanField('是否為封面圖', default=False)
    order = models.IntegerField('排序', default=0)
    uploaded_at = models.DateTimeField('上傳時間', auto_now_add=True)
    
    class Meta:
        verbose_name = '房源圖片'
        verbose_name_plural = '房源圖片'
        ordering = ['order', '-uploaded_at']
    
    def __str__(self):
        return f"{self.property.title} - 圖片 {self.order}"


class Booking(models.Model):
    """預訂模型"""
    BOOKING_STATUS = [
        ('pending', '待確認'),
        ('confirmed', '已確認'),
        ('cancelled', '已取消'),
        ('completed', '已完成')
    ]
    
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='bookings', verbose_name='房源')
    tenant = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='bookings', verbose_name='租客')
    
    # 預訂日期
    check_in = models.DateField('入住日期')
    check_out = models.DateField('退房日期')
    guests = models.IntegerField('入住人數', validators=[MinValueValidator(1)])
    
    # 價格和狀態
    total_price = models.DecimalField('總價格', max_digits=10, decimal_places=2)
    status = models.CharField('預訂狀態', max_length=20, choices=BOOKING_STATUS, default='pending')
    
    # 預訂編號
    booking_number = models.CharField('預訂編號', max_length=50, unique=True, editable=False)
    
    # 備註
    notes = models.TextField('備註', blank=True)
    
    # 時間戳
    created_at = models.DateTimeField('創建時間', auto_now_add=True)
    updated_at = models.DateTimeField('更新時間', auto_now=True)
    
    class Meta:
        verbose_name = '預訂'
        verbose_name_plural = '預訂'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.booking_number} - {self.property.title}"
    
    def save(self, *args, **kwargs):
        if not self.booking_number:
            # 生成預訂編號：BOOK + 時間戳
            from datetime import datetime
            self.booking_number = f"BOOK{datetime.now().strftime('%Y%m%d%H%M%S')}"
        super().save(*args, **kwargs)
    
    def get_nights(self):
        """計算住宿天數"""
        return (self.check_out - self.check_in).days


class RentalRequest(models.Model):
    """租客房源需求模型"""
    BUDGET_RANGES = [
        ('0-1000', 'NT$0 - NT$1,000'),
        ('1000-2000', 'NT$1,000 - NT$2,000'),
        ('2000-3000', 'NT$2,000 - NT$3,000'),
        ('3000-5000', 'NT$3,000 - NT$5,000'),
        ('5000+', 'NT$5,000+'),
    ]
    
    PROPERTY_TYPES = Property.PROPERTY_TYPES  # 重用房源類型
    
    tenant = models.ForeignKey(CustomUser, on_delete=models.CASCADE, 
                              related_name='rental_requests', verbose_name='租客')
    title = models.CharField('需求標題', max_length=200)
    description = models.TextField('需求描述')
    property_type = models.CharField('房源類型', max_length=20, choices=PROPERTY_TYPES)
    
    # 位置偏好
    preferred_city = models.CharField('偏好城市', max_length=100)
    preferred_district = models.CharField('偏好區域', max_length=100, blank=True)
    
    # 房源需求
    min_bedrooms = models.IntegerField('最少臥室數', validators=[MinValueValidator(0)], default=1)
    min_bathrooms = models.IntegerField('最少浴室數', validators=[MinValueValidator(0)], default=1)
    max_guests = models.IntegerField('入住人數', validators=[MinValueValidator(1)])
    
    # 預算和時間
    budget_range = models.CharField('預算範圍', max_length=20, choices=BUDGET_RANGES)
    move_in_date = models.DateField('期望入住日期', null=True, blank=True)
    rental_duration = models.IntegerField('租期（天）', validators=[MinValueValidator(1)], 
                                         null=True, blank=True, help_text='預計租住天數')
    
    # 期望設施
    desired_amenities = models.JSONField('期望設施', default=list, blank=True)
    
    # 狀態
    is_active = models.BooleanField('是否有效', default=True)
    
    # 時間戳
    created_at = models.DateTimeField('創建時間', auto_now_add=True)
    updated_at = models.DateTimeField('更新時間', auto_now=True)
    
    class Meta:
        verbose_name = '租客需求'
        verbose_name_plural = '租客需求'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.tenant.username}"


class Message(models.Model):
    """租客需求留言模型"""
    rental_request = models.ForeignKey(RentalRequest, on_delete=models.CASCADE, 
                                      related_name='messages', verbose_name='相關需求')
    sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE, 
                              related_name='sent_messages', verbose_name='發送者')
    receiver = models.ForeignKey(CustomUser, on_delete=models.CASCADE, 
                                related_name='received_messages', verbose_name='接收者')
    content = models.TextField('消息内容')
    is_read = models.BooleanField('是否已讀', default=False)
    created_at = models.DateTimeField('發送時間', auto_now_add=True)
    
    class Meta:
        verbose_name = '消息'
        verbose_name_plural = '消息'
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.sender.username} -> {self.receiver.username}: {self.content[:20]}"
