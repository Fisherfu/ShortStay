from django import forms
from .models import Property, PropertyImage, Booking, CustomUser, RentalRequest, Message
from django.contrib.auth.forms import UserCreationForm


class PropertyForm(forms.ModelForm):
    """房源表單"""
    
    # 設施選項（多選）
    AMENITY_CHOICES = [
        ('wifi', 'WiFi'),
        ('air_conditioning', '空調'),
        ('heating', '暖氣'),
        ('kitchen', '廚房'),
        ('washing_machine', '洗衣機'),
        ('tv', '電視'),
        ('parking', '停車位'),
        ('elevator', '電梯'),
        ('balcony', '陽台'),
        ('pet_friendly', '允許寵物'),
    ]
    
    amenities = forms.MultipleChoiceField(
        choices=AMENITY_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='設施'
    )
    
    class Meta:
        model = Property
        fields = [
            'title', 'description', 'property_type',
            'city', 'district', 'address',
            'bedrooms', 'bathrooms', 'max_guests',
            'price_per_night', 'is_available', 'amenities'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'property_type': forms.Select(attrs={'class': 'form-select'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'district': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'bedrooms': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'bathrooms': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'max_guests': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'price_per_night': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'is_available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class PropertyImageForm(forms.ModelForm):
    """房源圖片表單"""
    class Meta:
        model = PropertyImage
        fields = ['image', 'is_cover', 'order']
        widgets = {
            'image': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'is_cover': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'value': 0}),
        }


class BookingForm(forms.ModelForm):
    """預訂表單"""
    class Meta:
        model = Booking
        fields = ['check_in', 'check_out', 'guests', 'notes']
        widgets = {
            'check_in': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'required': True
            }),
            'check_out': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'required': True
            }),
            'guests': forms.NumberInput(attrs={
                'min': 1,
                'class': 'form-control',
                'required': True
            }),
            'notes': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control',
                'placeholder': '有任何特殊需求嗎？（可選）'
            }),
        }
        labels = {
            'check_in': '入住日期',
            'check_out': '退房日期',
            'guests': '入住人數',
            'notes': '備註',
        }
    
    def __init__(self, property_obj, *args, **kwargs):
        """初始化表單，傳入房源對象"""
        self.property = property_obj
        super().__init__(*args, **kwargs)
    
    def clean_check_in(self):
        """驗證入住日期"""
        from datetime import date
        check_in = self.cleaned_data.get('check_in')
        
        if check_in < date.today():
            raise forms.ValidationError('入住日期不能早於今天')
        
        return check_in
    
    def clean(self):
        """整體表單驗證"""
        from datetime import date
        cleaned_data = super().clean()
        check_in = cleaned_data.get('check_in')
        check_out = cleaned_data.get('check_out')
        guests = cleaned_data.get('guests')
        
        # 驗證日期邏輯
        if check_in and check_out:
            if check_out <= check_in:
                raise forms.ValidationError('退房日期必須晚於入住日期')
            
            # 至少預訂一晚
            nights = (check_out - check_in).days
            if nights < 1:
                raise forms.ValidationError('至少需要預訂1晚')
            
            # 檢查日期是否有衝突
            conflicting_bookings = Booking.objects.filter(
                property=self.property,
                status__in=['pending', 'confirmed'],
                check_in__lt=check_out,
                check_out__gt=check_in
            )
            
            if conflicting_bookings.exists():
                raise forms.ValidationError('抱歉，選擇的日期已被預訂，請選擇其他日期')
        
        # 驗證人數
        if guests and guests > self.property.max_guests:
            raise forms.ValidationError(f'入住人數不能超過 {self.property.max_guests} 人')
        
        return cleaned_data

# 租客注册表单
class TenantRegisterForm(UserCreationForm):
    email = forms.EmailField(required=False, label='電子郵件（選填）')
    
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'password1', 'password2')
        labels = {
            'username': '用戶名',
            'password1': '密碼',
            'password2': '確認密碼',
        }
        help_texts = {
            'username': '只能包含字母和數字',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 添加Bootstrap样式
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
        
        # 简化密码要求（测试阶段）
        self.fields['password1'].help_text = '至少4個字符即可'
        self.fields['password2'].help_text = '請再次輸入密碼'
        
        # 移除Django默认的密码验证器
        self.fields['password1'].validators = []
        self.fields['password2'].validators = []
    
    def clean_password1(self):
        """自定义密码验证 - 只要求最少4位"""
        password = self.cleaned_data.get('password1')
        if len(password) < 4:
            raise forms.ValidationError('密碼至少需要4個字符')
        return password
    
    def clean_username(self):
        """验证用户名只包含字母和数字"""
        username = self.cleaned_data.get('username')
        if not username.isalnum():
            raise forms.ValidationError('用戶名只能包含字母和數字')
        return username
    
    def _post_clean(self):
        """覆盖父类方法，跳过Django内置的密码验证"""
        super(UserCreationForm, self)._post_clean()
        # 手动检查两次密码是否一致
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            self.add_error('password2', '兩次密碼輸入不一致')
    
    def save(self, commit=True):
        user = super(UserCreationForm, self).save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        user.email = self.cleaned_data.get('email', '')
        user.role = 'tenant'  # 默认为租客角色
        if commit:
            user.save()
        return user


class RentalRequestForm(forms.ModelForm):
    """租客需求表單"""
    
    # 設施選項（與房源相同的設施選項）
    AMENITY_CHOICES = [
        ('WiFi', 'WiFi'),
        ('空調', '空調'),
        ('暖氣', '暖氣'),
        ('洗衣機', '洗衣機'),
        ('廚房', '廚房'),
        ('電視', '電視'),
        ('停車位', '停車位'),
        ('電梯', '電梯'),
        ('陽台', '陽台'),
        ('寵物友善', '寵物友善'),
    ]
    
    desired_amenities = forms.MultipleChoiceField(
        choices=AMENITY_CHOICES,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False,
        label='期望設施'
    )
    
    class Meta:
        model = RentalRequest
        fields = ['title', 'description', 'property_type', 'preferred_city', 
                 'preferred_district', 'min_bedrooms', 'min_bathrooms', 
                 'max_guests', 'budget_range', 'move_in_date', 'rental_duration',
                 'desired_amenities']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '例如：尋找新竹市中心一房一廳'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 
                                                 'placeholder': '描述您的理想房源需求...'}),
            'property_type': forms.Select(attrs={'class': 'form-select'}),
            'preferred_city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '例如：新竹市'}),
            'preferred_district': forms.TextInput(attrs={'class': 'form-control', 
                                                        'placeholder': '例如：東區、北區（選填）'}),
            'min_bedrooms': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'min_bathrooms': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'max_guests': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'budget_range': forms.Select(attrs={'class': 'form-select'}),
            'move_in_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'rental_duration': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 
                                                       'placeholder': '例如：30（天）'}),
        }
        labels = {
            'title': '需求標題',
            'description': '需求描述',
            'property_type': '房源類型',
            'preferred_city': '偏好城市',
            'preferred_district': '偏好區域',
            'min_bedrooms': '最少臥室數',
            'min_bathrooms': '最少浴室數',
            'max_guests': '入住人數',
            'budget_range': '預算範圍',
            'move_in_date': '期望入住日期',
            'rental_duration': '租期（天）',
        }
    
    def clean_move_in_date(self):
        """驗證入住日期不能早於今天"""
        from datetime import date
        move_in_date = self.cleaned_data.get('move_in_date')
        
        if move_in_date and move_in_date < date.today():
            raise forms.ValidationError('期望入住日期不能早於今天')
        
        return move_in_date


class MessageForm(forms.ModelForm):
    """消息表單"""
    class Meta:
        model = Message
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': '在此輸入您的訊息...'
            })
        }
        labels = {
            'content': '訊息內容'
        }
