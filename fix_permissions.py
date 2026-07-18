import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'short_stay.settings')
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

# Check current status
try:
    alan = User.objects.get(username='alan')
    fisher = User.objects.get(username='fisher')

    print(f'BEFORE:')
    print(f'  alan: is_superuser={alan.is_superuser}, role={alan.role}')
    print(f'  fisher: is_superuser={fisher.is_superuser}, role={fisher.role}')

    # Fix alan if needed
    if alan.is_superuser:
        print(f'\nFIXING: Setting alan.is_superuser to False')
        alan.is_superuser = False
        alan.is_staff = False
        alan.save()
        print('  alan updated!')
    else:
        print(f'\n  alan is already correct (not superuser)')

    # Ensure fisher is superuser
    if not fisher.is_superuser:
        print(f'\nFIXING: Setting fisher.is_superuser to True')
        fisher.is_superuser = True
        fisher.is_staff = True
        fisher.save()
        print('  fisher updated!')
    else:
        print(f'\n  fisher is already superuser')

    # Verify
    alan.refresh_from_db()
    fisher.refresh_from_db()
    print(f'\nAFTER:')
    print(f'  alan: is_superuser={alan.is_superuser}, role={alan.role}')
    print(f'  fisher: is_superuser={fisher.is_superuser}, role={fisher.role}')
    
except Exception as e:
    print(f'ERROR: {e}')
