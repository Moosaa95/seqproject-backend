#!/usr/bin/env python
"""
Quick script to create a default admin user.
Run this script from the backend directory: python create_admin_quick.py
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.contrib.auth.models import User


def create_default_admin():
    """Create a default admin user with predefined credentials"""

    # Default credentials
    username = "admin"
    email = "admin@seqprojects.com"
    password = "admin123"  # Change this in production!

    print("=" * 60)
    print("          SEQUOIA PROJECTS - QUICK ADMIN SETUP")
    print("=" * 60)
    print()

    # Check if user already exists
    if User.objects.filter(username=username).exists():
        print(f"❌ User '{username}' already exists!")
        print(f"\n💡 If you want to reset the password, delete the user first:")
        print(f"   python manage.py shell")
        print(f"   >>> from django.contrib.auth.models import User")
        print(f"   >>> User.objects.filter(username='{username}').delete()")
        print()
        return

    # Create the superuser
    user = User.objects.create_superuser(
        username=username,
        email=email,
        password=password
    )

    print("✅ Default admin user created successfully!")
    print()
    print("📝 Login Credentials:")
    print(f"   URL: http://localhost:3000/admin/login")
    print(f"   Username: {username}")
    print(f"   Password: {password}")
    print()
    print("⚠️  IMPORTANT: Change this password in production!")
    print()
    print("=" * 60)


if __name__ == "__main__":
    try:
        create_default_admin()
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        sys.exit(1)
