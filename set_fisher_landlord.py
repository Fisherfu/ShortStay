from properties.models import CustomUser

# 设置fisher为房东
try:
    user = CustomUser.objects.get(username='fisher')
    user.role = 'landlord'
    user.save()
    print(f"✅ 成功：用户 {user.username} (ID: {user.id}) 已设置为房东角色")
    print(f"   角色: {user.get_role_display()}")
except CustomUser.DoesNotExist:
    print("❌ 错误：找不到用户 'fisher'")
except Exception as e:
    print(f"❌ 错误：{e}")
