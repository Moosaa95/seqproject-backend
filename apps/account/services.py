from django.core.mail import send_mail
from django.conf import settings


class EmailService:
    """
    Service class to handle email sending operations.
    """

    @staticmethod
    def send_otp_email(email, otp_code, purpose):
        """
        Send OTP email to the user.

        Args:
            email (str): User's email address
            otp_code (str): The OTP code to send
            purpose (str): Purpose of the OTP (signup, login, reset)

        Returns:
            bool: True if email sent successfully, False otherwise
        """
        subject_map = {
            'signup': 'Verify Your Email - Signup',
            'login': 'Your Login Verification Code',
            'reset': 'Password Reset Verification Code'
        }

        subject = subject_map.get(purpose, 'Email Verification Code')

        message = f"""
Hello,

Your verification code is: {otp_code}

This code will expire in 10 minutes.

If you didn't request this code, please ignore this email.

Best regards,
Sequoia Projects Team
        """

        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
            return True
        except Exception as e:
            print(f"Error sending email: {str(e)}")
            return False

    @staticmethod
    def send_welcome_email(email, first_name, password):
        """
        Send welcome email to newly created staff user with their credentials.

        Args:
            email (str): User's email address
            first_name (str): User's first name
            password (str): Auto-generated password

        Returns:
            bool: True if email sent successfully, False otherwise
        """
        subject = "Welcome to Sequoia Projects - Your Account Details"

        message = f"""
Hello {first_name},

Your staff account has been created for Sequoia Projects.

Here are your login credentials:
Email: {email}
Password: {password}

For security reasons, you will be required to change your password when you first log in.

Please log in at: {getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')}/admin/login

If you did not expect this email, please contact the administrator.

Best regards,
Sequoia Projects Team
        """

        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
            return True
        except Exception as e:
            print(f"Error sending welcome email: {str(e)}")
            return False

    @staticmethod
    def send_password_changed_email(email, first_name):
        """
        Send confirmation email after password is changed.

        Args:
            email (str): User's email address
            first_name (str): User's first name

        Returns:
            bool: True if email sent successfully, False otherwise
        """
        subject = "Password Changed Successfully - Sequoia Projects"

        message = f"""
Hello {first_name},

Your password has been successfully changed.

If you did not make this change, please contact the administrator immediately.

Best regards,
Sequoia Projects Team
        """

        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
            return True
        except Exception as e:
            print(f"Error sending password changed email: {str(e)}")
            return False
