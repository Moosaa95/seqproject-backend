from django.contrib.auth.models import BaseUserManager


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("the email field must be set")

        print("Extra fields")
        print(extra_fields)
        email = self.normalize_email(
            email
        )  # Normalize the email address by lowercasing the domain part of it.
        email = email.lower()
        user = self.model(email=email, **extra_fields)  # Create a new user model
        user.set_password(password)  # Set the password for the user
        user.save(using=self._db)  # Save the user model
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        return self.create_user(email, password, **extra_fields)

    def create_staffuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", False)

        return self.create_user(email, password, **extra_fields)
