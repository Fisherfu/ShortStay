from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from datetime import date
from .models import Property, PropertyImage, Booking, RentalRequest, Message
from .forms import PropertyForm, PropertyImageForm, BookingForm, RentalRequestForm, MessageForm


# ==================== 租客功能（公開） ====================

def property_list(request):
    """公開房源列表（租客瀏覽）"""
    properties = Property.objects.filter(is_available=True).select_related('landlord').prefetch_related('images')
    
    # 搜索
    search = request.GET.get('search', '')
    if search:
        properties = properties.filter(
            Q(title__icontains=search) |
            Q(city__icontains=search) |
            Q(district__icontains=search) |
            Q(description__icontains=search)
        )
    
    # 城市篩選
    city = request.GET.get('city', '')
    if city:
        properties = properties.filter(city=city)
    
    # 房型篩選
    property_type = request.GET.get('property_type', '')
    if property_type:
        properties = properties.filter(property_type=property_type)
    
    # 價格範圍
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')
    if min_price:
        properties = properties.filter(price_per_night__gte=min_price)
    if max_price:
        properties = properties.filter(price_per_night__lte=max_price)
    
    # 人數篩選
    guests = request.GET.get('guests', '')
    if guests:
        properties = properties.filter(max_guests__gte=guests)
    
    # 排序
    sort = request.GET.get('sort', '-created_at')
    if sort in ['price_per_night', '-price_per_night', '-created_at', 'created_at']:
        properties = properties.order_by(sort)
    
    # 獲取所有可用城市（用於篩選下拉）
    cities = Property.objects.filter(is_available=True).values_list('city', flat=True).distinct()
    
    context = {
        'properties': properties,
        'cities': cities,
        'search': search,
        'city': city,
        'property_type': property_type,
        'min_price': min_price,
        'max_price': max_price,
        'guests': guests,
        'sort': sort,
    }
    return render(request, 'properties/property_list.html', context)


def property_detail(request, pk):
    """房源詳情頁面"""
    property_obj = get_object_or_404(Property, pk=pk, is_available=True)
    images = property_obj.images.all().order_by('order')
    
    context = {
        'property': property_obj,
        'images': images,
    }
    return render(request, 'properties/property_detail.html', context)


# ==================== 房東功能 ====================

@login_required
def landlord_properties(request):
    """房東的房源列表"""
    properties = Property.objects.filter(landlord=request.user).order_by('-created_at')
    context = {
        'properties': properties
    }
    return render(request, 'properties/landlord_properties.html', context)


@login_required
def property_add(request):
    """新增房源"""
    if request.method == 'POST':
        form = PropertyForm(request.POST)
        images = request.FILES.getlist('images')  # 獲取多個圖片文件
        
        if form.is_valid():
            property_obj = form.save(commit=False)
            property_obj.landlord = request.user
            
            # 處理設施（從表單選擇轉為列表）
            amenities = form.cleaned_data.get('amenities', [])
            property_obj.amenities = list(amenities)
            
            property_obj.save()
            
            # 處理上傳的圖片
            if images:
                for index, image_file in enumerate(images):
                    PropertyImage.objects.create(
                        property=property_obj,
                        image=image_file,
                        is_cover=(index == 0),  # 第一張設為封面
                        order=index
                    )
                messages.success(request, f'房源「{property_obj.title}」已成功創建，共上傳了 {len(images)} 張圖片！')
            else:
                messages.success(request, f'房源「{property_obj.title}」已成功創建！您可以稍後上傳圖片。')
            
            return redirect('landlord_properties')
    else:
        form = PropertyForm()
    
    context = {'form': form, 'is_new': True}
    return render(request, 'properties/property_form.html', context)


@login_required
def property_edit(request, pk):
    """編輯房源"""
    property_obj = get_object_or_404(Property, pk=pk, landlord=request.user)
    
    if request.method == 'POST':
        form = PropertyForm(request.POST, instance=property_obj)
        if form.is_valid():
            property_obj = form.save(commit=False)
            
            # 處理設施
            amenities = form.cleaned_data.get('amenities', [])
            property_obj.amenities = list(amenities)
            
            property_obj.save()
            messages.success(request, f'房源「{property_obj.title}」已更新！')
            return redirect('landlord_properties')
    else:
        # 初始化表單，預填設施
        initial_data = {
            'amenities': property_obj.amenities if property_obj.amenities else []
        }
        form = PropertyForm(instance=property_obj, initial=initial_data)
    
    # 獲取該房源的所有圖片
    images = property_obj.images.all()
    
    context = {
        'form': form,
        'property': property_obj,
        'images': images,
        'is_new': False,
    }
    return render(request, 'properties/property_form.html', context)


@login_required
def property_delete(request, pk):
    """刪除房源"""
    property_obj = get_object_or_404(Property, pk=pk, landlord=request.user)
    
    if request.method == 'POST':
        title = property_obj.title
        property_obj.delete()
        messages.success(request, f'房源「{title}」已刪除！')
        return redirect('landlord_properties')
    
    context = {'property': property_obj}
    return render(request, 'properties/property_confirm_delete.html', context)


@login_required
def property_upload_image(request, pk):
    """上傳房源圖片"""
    property_obj = get_object_or_404(Property, pk=pk, landlord=request.user)
    
    if request.method == 'POST':
        form = PropertyImageForm(request.POST, request.FILES)
        if form.is_valid():
            image = form.save(commit=False)
            image.property = property_obj
            image.save()
            messages.success(request, '圖片已上傳！')
            return redirect('property_edit', pk=pk)
    else:
        form = PropertyImageForm()
    
    context = {
        'form': form,
        'property': property_obj
    }
    return render(request, 'properties/property_upload_image.html', context)


@login_required
def property_delete_image(request, pk, image_id):
    """刪除房源圖片"""
    property_obj = get_object_or_404(Property, pk=pk, landlord=request.user)
    image = get_object_or_404(PropertyImage, pk=image_id, property=property_obj)
    
    if request.method == 'POST':
        image.delete()
        messages.success(request, '圖片已刪除！')
    
    return redirect('property_edit', pk=pk)


# ==================== 預訂功能 ====================

@login_required
def create_booking(request, property_id):
    """創建預訂"""
    property_obj = get_object_or_404(Property, pk=property_id, is_available=True)
    
    # 获取该房源的所有已确认和待确认的预订（用于前端显示，虽然现在用HTML5）
    from datetime import timedelta
    import json
    
    confirmed_bookings = Booking.objects.filter(
        property=property_obj,
        status__in=['confirmed', 'pending']
    ).values_list('check_in', 'check_out')
    
    # 生成已预订日期列表
    booked_dates = []
    for check_in, check_out in confirmed_bookings:
        current_date = check_in
        while current_date < check_out:
            booked_dates.append(current_date.strftime('%Y-%m-%d'))
            current_date += timedelta(days=1)
    
    if request.method == 'POST':
        form = BookingForm(property_obj, request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.property = property_obj
            booking.tenant = request.user
            
            # 后端验证：检查日期冲突
            conflicting_bookings = Booking.objects.filter(
                property=property_obj,
                status__in=['confirmed', 'pending'],
                check_in__lt=booking.check_out,
                check_out__gt=booking.check_in
            )
            
            if conflicting_bookings.exists():
                messages.error(request, '抱歉，您選擇的日期已被預訂，請選擇其他日期。')
                context = {
                    'property': property_obj,
                    'form': form,
                    'booked_dates': json.dumps(booked_dates),
                }
                return render(request, 'properties/booking_form.html', context)
            
            # 計算總價
            nights = (booking.check_out - booking.check_in).days
            booking.total_price = property_obj.price_per_night * nights
            
            booking.save()
            messages.success(request, f'預訂成功！您的預訂編號是：{booking.booking_number}')
            return redirect('booking_success', booking_id=booking.id)
    else:
        form = BookingForm(property_obj)
    
    context = {
        'form': form,
        'property': property_obj,
        'booked_dates': json.dumps(booked_dates),  # 保留以备将来使用
    }
    return render(request, 'properties/booking_form.html', context)


@login_required
def booking_success(request, booking_id):
    """預訂成功頁面"""
    booking = get_object_or_404(Booking, pk=booking_id, tenant=request.user)
    
    context = {
        'booking': booking,
    }
    return render(request, 'properties/booking_success.html', context)


@login_required
def my_bookings(request):
    """我的預訂列表（租客）"""
    bookings = Booking.objects.filter(tenant=request.user).select_related('property').order_by('-created_at')
    
    context = {
        'bookings': bookings,
    }
    return render(request, 'properties/my_bookings.html', context)


@login_required
def cancel_booking(request, booking_id):
    """取消預訂"""
    booking = get_object_or_404(Booking, pk=booking_id, tenant=request.user)
    
    if request.method == 'POST':
        if booking.status == 'pending':
            booking.status = 'cancelled'
            booking.save()
            messages.success(request, '預訂已取消')
        else:
            messages.error(request, '只有待確認的預訂可以取消')
    
    return redirect('my_bookings')


@login_required
def landlord_bookings(request):
    """房東的預訂管理"""
    # 獲取房東的所有房源
    properties = Property.objects.filter(landlord=request.user)
    
    # 獲取這些房源的所有預訂
    bookings = Booking.objects.filter(
        property__in=properties
    ).select_related('property', 'tenant').order_by('-created_at')
    
    # 篩選狀態
    status_filter = request.GET.get('status', '')
    if status_filter:
        bookings = bookings.filter(status=status_filter)
    
    context = {
        'bookings': bookings,
        'status_filter': status_filter,
    }
    return render(request, 'properties/landlord_bookings.html', context)


@login_required
def update_booking_status(request, booking_id):
    """更新預訂狀態（房東）"""
    booking = get_object_or_404(Booking, pk=booking_id, property__landlord=request.user)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in ['confirmed', 'cancelled']:
            booking.status = new_status
            booking.save()
            
            status_text = {'confirmed': '已確認', 'cancelled': '已取消'}
            messages.success(request, f'預訂狀態已更新為：{status_text[new_status]}')
    
    return redirect('landlord_bookings')


# ==================== 用户注册 ====================
def register(request):
    """租客注册"""
    if request.user.is_authenticated:
        # 已登录用户直接跳转首页
        return redirect('property_list')
    
    if request.method == 'POST':
        from .forms import TenantRegisterForm
        form = TenantRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            # 注册成功后自动登录
            from django.contrib.auth import login
            login(request, user)
            messages.success(request, f'歡迎加入 Short Stay！您已成功註冊為租客。')
            # 跳转到next参数指定的页面，或首页
            next_url = request.GET.get('next', 'property_list')
            return redirect(next_url)
    else:
        from .forms import TenantRegisterForm
        form = TenantRegisterForm()
    
    return render(request, 'properties/register.html', {'form': form})


# ==================== 租客需求功能 ====================

def rental_requests_list(request):
    """租客需求列表（公開）"""
    requests = RentalRequest.objects.filter(is_active=True).select_related('tenant').order_by('-created_at')
    
    # 搜索
    search = request.GET.get('search', '')
    if search:
        requests = requests.filter(
            Q(title__icontains=search) |
            Q(preferred_city__icontains=search) |
            Q(description__icontains=search)
        )
    
    # 城市篩選
    city = request.GET.get('city', '')
    if city:
        requests = requests.filter(preferred_city__icontains=city)
    
    # 預算篩選
    budget = request.GET.get('budget', '')
    if budget:
        requests = requests.filter(budget_range=budget)
    
    # 房型篩選
    property_type = request.GET.get('property_type', '')
    if property_type:
        requests = requests.filter(property_type=property_type)
    
    # 獲取所有可用城市
    cities = RentalRequest.objects.filter(is_active=True).values_list('preferred_city', flat=True).distinct()
    
    context = {
        'requests': requests,
        'cities': cities,
        'search': search,
        'city': city,
        'budget': budget,
        'property_type': property_type,
    }
    return render(request, 'properties/rental_requests_list.html', context)


def rental_request_detail(request, pk):
    """租客需求詳情頁面"""
    rental_request = get_object_or_404(RentalRequest, pk=pk, is_active=True)
    
    # 获取该需求的所有消息
    request_messages = rental_request.messages.all().select_related('sender', 'receiver')
    
    # 如果是租客查看自己的需求，标记消息为已读
    if request.user.is_authenticated and request.user == rental_request.tenant:
        request_messages.filter(receiver=request.user, is_read=False).update(is_read=True)
    
    # 处理消息发送
    message_form = None
    if request.user.is_authenticated:
        if request.method == 'POST':
            message_form = MessageForm(request.POST)
            if message_form.is_valid():
                message = message_form.save(commit=False)
                message.rental_request = rental_request
                message.sender = request.user
                message.receiver = rental_request.tenant  # 发给租客
                message.save()
                messages.success(request, '訊息已成功發送！')
                return redirect('rental_request_detail', pk=pk)
        else:
            message_form = MessageForm()
    
    context = {
        'request_obj': rental_request,
        'request_messages': request_messages,
        'message_form': message_form,
    }
    return render(request, 'properties/rental_request_detail.html', context)


@login_required
def create_rental_request(request):
    """創建租客需求"""
    # 只有租客可以創建需求
    if request.user.role != 'tenant':
        messages.error(request, '只有租客可以發布租屋需求')
        return redirect('rental_requests_list')
    
    if request.method == 'POST':
        form = RentalRequestForm(request.POST)
        if form.is_valid():
            rental_request = form.save(commit=False)
            rental_request.tenant = request.user
            
            # 處理期望設施
            amenities = form.cleaned_data.get('desired_amenities', [])
            rental_request.desired_amenities = list(amenities)
            
            rental_request.save()
            messages.success(request, f'需求「{rental_request.title}」已成功發布！')
            return redirect('my_rental_requests')
    else:
        form = RentalRequestForm()
    
    context = {'form': form, 'is_new': True}
    return render(request, 'properties/rental_request_form.html', context)


@login_required
def edit_rental_request(request, pk):
    """編輯租客需求"""
    rental_request = get_object_or_404(RentalRequest, pk=pk, tenant=request.user)
    
    if request.method == 'POST':
        form = RentalRequestForm(request.POST, instance=rental_request)
        if form.is_valid():
            rental_request = form.save(commit=False)
            
            # 處理期望設施
            amenities = form.cleaned_data.get('desired_amenities', [])
            rental_request.desired_amenities = list(amenities)
            
            rental_request.save()
            messages.success(request, f'需求「{rental_request.title}」已更新！')
            return redirect('my_rental_requests')
    else:
        # 初始化表單，預填設施
        initial_data = {
            'desired_amenities': rental_request.desired_amenities if rental_request.desired_amenities else []
        }
        form = RentalRequestForm(instance=rental_request, initial=initial_data)
    
    context = {
        'form': form,
        'request_obj': rental_request,
        'is_new': False,
    }
    return render(request, 'properties/rental_request_form.html', context)


@login_required
def delete_rental_request(request, pk):
    """刪除租客需求"""
    rental_request = get_object_or_404(RentalRequest, pk=pk, tenant=request.user)
    
    if request.method == 'POST':
        title = rental_request.title
        rental_request.delete()
        messages.success(request, f'需求「{title}」已刪除！')
        return redirect('my_rental_requests')
    
    context = {'request_obj': rental_request}
    return render(request, 'properties/rental_request_confirm_delete.html', context)


@login_required
def my_rental_requests(request):
    """我的需求列表（租客）"""
    requests = RentalRequest.objects.filter(tenant=request.user).order_by('-created_at')
    
    context = {
        'requests': requests,
    }
    return render(request, 'properties/my_rental_requests.html', context)
