#!/usr/bin/env python
"""
Script to create a superuser for the admin dashboard.
Run this script from the backend directory: python create_admin.py
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.contrib.auth.models import User


def create_admin_user():
    """Create an admin user if it doesn't exist"""

    # Admin user details
    username = input("Enter username (default: admin): ").strip() or "admin"
    email = input("Enter email (default: admin@seqprojects.com): ").strip() or "admin@seqprojects.com"

    # Check if user already exists
    if User.objects.filter(username=username).exists():
        print(f"\n❌ User '{username}' already exists!")
        update = input("Do you want to update the password? (yes/no): ").strip().lower()
        if update == "yes":
            user = User.objects.get(username=username)
            password = input("Enter new password: ").strip()
            user.set_password(password)
            user.is_staff = True
            user.is_superuser = True
            user.save()
            print(f"\n✅ Password updated for user '{username}'!")
            print(f"   Username: {username}")
            print(f"   Email: {user.email}")
        return

    # Create new user
    password = input("Enter password: ").strip()

    if not password:
        print("\n❌ Password cannot be empty!")
        return

    # Create the superuser
    user = User.objects.create_superuser(
        username=username,
        email=email,
        password=password
    )

    print("\n✅ Superuser created successfully!")
    print(f"   Username: {username}")
    print(f"   Email: {email}")
    print(f"   Password: {'*' * len(password)}")
    print("\n📝 You can now login at: http://localhost:3000/admin/login")


if __name__ == "__main__":
    print("=" * 60)
    print("          SEQUOIA PROJECTS - ADMIN USER CREATION")
    print("=" * 60)
    print()

    try:
        create_admin_user()
    except KeyboardInterrupt:
        print("\n\n❌ Operation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        sys.exit(1)

    print("\n" + "=" * 60)
