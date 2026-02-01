from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class EmailNotificationService:
    """Service for sending email notifications"""

    @staticmethod
    def send_email(
        subject: str,
        recipient_list: List[str],
        html_content: str,
        text_content: Optional[str] = None,
        from_email: Optional[str] = None,
    ) -> bool:
        """
        Send an email with HTML content

        Args:
            subject: Email subject
            recipient_list: List of recipient email addresses
            html_content: HTML content of the email
            text_content: Plain text version (auto-generated from HTML if not provided)
            from_email: Sender email (uses DEFAULT_FROM_EMAIL if not provided)

        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        try:
            from_email = from_email or settings.DEFAULT_FROM_EMAIL
            text_content = text_content or strip_tags(html_content)

            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=from_email,
                to=recipient_list,
            )
            email.attach_alternative(html_content, "text/html")
            email.send()

            logger.info(f"Email sent successfully to {', '.join(recipient_list)}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            return False

    @classmethod
    def send_contact_inquiry_notification(cls, inquiry) -> bool:
        """Send notification to admin when contact inquiry is submitted"""
        subject = f"New Contact Inquiry: {inquiry.subject}"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #3a3a41; color: white; padding: 20px; text-align: center; }}
                .content {{ background-color: #f9f9f9; padding: 20px; }}
                .field {{ margin-bottom: 15px; }}
                .label {{ font-weight: bold; color: #3a3a41; }}
                .value {{ margin-top: 5px; }}
                .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>New Contact Inquiry</h2>
                </div>
                <div class="content">
                    <div class="field">
                        <div class="label">Name:</div>
                        <div class="value">{inquiry.name}</div>
                    </div>
                    <div class="field">
                        <div class="label">Email:</div>
                        <div class="value">{inquiry.email}</div>
                    </div>
                    <div class="field">
                        <div class="label">Phone:</div>
                        <div class="value">{inquiry.phone}</div>
                    </div>
                    <div class="field">
                        <div class="label">Subject:</div>
                        <div class="value">{inquiry.get_subject_display()}</div>
                    </div>
                    <div class="field">
                        <div class="label">Message:</div>
                        <div class="value">{inquiry.message}</div>
                    </div>
                    <div class="field">
                        <div class="label">Submitted:</div>
                        <div class="value">{inquiry.created_at.strftime('%B %d, %Y at %I:%M %p')}</div>
                    </div>
                </div>
                <div class="footer">
                    <p>Sequoia Projects - Real Estate Management System</p>
                </div>
            </div>
        </body>
        </html>
        """

        # Send to admin email
        admin_email = getattr(settings, 'ADMIN_EMAIL', settings.DEFAULT_FROM_EMAIL)
        return cls.send_email(subject, [admin_email], html_content)

    @classmethod
    def send_property_inquiry_notification(cls, inquiry) -> bool:
        """Send notification to agent/admin when property inquiry is submitted"""
        subject = f"New Property Inquiry: {inquiry.property.title}"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #3a3a41; color: white; padding: 20px; text-align: center; }}
                .content {{ background-color: #f9f9f9; padding: 20px; }}
                .property-info {{ background-color: #e8e8e8; padding: 15px; margin-bottom: 20px; border-radius: 5px; }}
                .field {{ margin-bottom: 15px; }}
                .label {{ font-weight: bold; color: #3a3a41; }}
                .value {{ margin-top: 5px; }}
                .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>New Property Inquiry</h2>
                </div>
                <div class="content">
                    <div class="property-info">
                        <h3>Property: {inquiry.property.title}</h3>
                        <p><strong>Location:</strong> {inquiry.property.location}</p>
                        <p><strong>Price:</strong> {inquiry.property.currency}{inquiry.property.price:,.2f}</p>
                        <p><strong>Type:</strong> {inquiry.property.type}</p>
                    </div>
                    <div class="field">
                        <div class="label">Inquirer Name:</div>
                        <div class="value">{inquiry.name}</div>
                    </div>
                    <div class="field">
                        <div class="label">Email:</div>
                        <div class="value">{inquiry.email}</div>
                    </div>
                    <div class="field">
                        <div class="label">Phone:</div>
                        <div class="value">{inquiry.phone}</div>
                    </div>
                    <div class="field">
                        <div class="label">Message:</div>
                        <div class="value">{inquiry.message}</div>
                    </div>
                    <div class="field">
                        <div class="label">Submitted:</div>
                        <div class="value">{inquiry.created_at.strftime('%B %d, %Y at %I:%M %p')}</div>
                    </div>
                </div>
                <div class="footer">
                    <p>Sequoia Projects - Real Estate Management System</p>
                </div>
            </div>
        </body>
        </html>
        """

        # Send to agent email if available, otherwise admin
        recipient_email = inquiry.property.agent.email if inquiry.property.agent else getattr(settings, 'ADMIN_EMAIL', settings.DEFAULT_FROM_EMAIL)
        return cls.send_email(subject, [recipient_email], html_content)

    @classmethod
    def send_booking_confirmation(cls, booking) -> bool:
        """Send booking confirmation email to customer"""
        subject = f"Booking Confirmation - {booking.property.title}"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #3a3a41; color: white; padding: 20px; text-align: center; }}
                .content {{ background-color: #f9f9f9; padding: 20px; }}
                .booking-info {{ background-color: #e8f5e9; padding: 15px; margin-bottom: 20px; border-radius: 5px; border-left: 4px solid #4caf50; }}
                .property-info {{ background-color: #e3f2fd; padding: 15px; margin-bottom: 20px; border-radius: 5px; }}
                .field {{ margin-bottom: 15px; }}
                .label {{ font-weight: bold; color: #3a3a41; }}
                .value {{ margin-top: 5px; }}
                .total {{ font-size: 24px; color: #4caf50; font-weight: bold; }}
                .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>✓ Booking Confirmed</h2>
                </div>
                <div class="content">
                    <p>Dear {booking.name},</p>
                    <p>Thank you for your booking! Your reservation has been confirmed.</p>

                    <div class="booking-info">
                        <h3>Booking Details</h3>
                        <p><strong>Booking ID:</strong> {booking.booking_id}</p>
                        <p><strong>Status:</strong> {booking.get_status_display()}</p>
                        <p><strong>Check-in:</strong> {booking.check_in.strftime('%B %d, %Y')}</p>
                        <p><strong>Check-out:</strong> {booking.check_out.strftime('%B %d, %Y')}</p>
                        <p><strong>Nights:</strong> {booking.nights}</p>
                        <p><strong>Guests:</strong> {booking.guests}</p>
                    </div>

                    <div class="property-info">
                        <h3>Property Details</h3>
                        <p><strong>{booking.property.title}</strong></p>
                        <p>{booking.property.location}</p>
                        <p>{booking.property.bedrooms} Bedrooms • {booking.property.bathrooms} Bathrooms</p>
                    </div>

                    <div class="field">
                        <div class="label">Total Amount:</div>
                        <div class="total">{booking.currency}{booking.total_amount:,.2f}</div>
                    </div>

                    {f'<div class="field"><div class="label">Special Requests:</div><div class="value">{booking.special_requests}</div></div>' if booking.special_requests else ''}

                    <p>If you have any questions, please don't hesitate to contact us.</p>
                </div>
                <div class="footer">
                    <p>Sequoia Projects - Real Estate Management System</p>
                    <p>Phone: +234 803 456 7890 | Email: info@seqprojects.com</p>
                </div>
            </div>
        </body>
        </html>
        """

        return cls.send_email(subject, [booking.email], html_content)

    @classmethod
    def send_booking_admin_notification(cls, booking) -> bool:
        """Send booking notification to admin"""
        subject = f"New Booking: {booking.property.title}"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #3a3a41; color: white; padding: 20px; text-align: center; }}
                .content {{ background-color: #f9f9f9; padding: 20px; }}
                .field {{ margin-bottom: 15px; }}
                .label {{ font-weight: bold; color: #3a3a41; }}
                .value {{ margin-top: 5px; }}
                .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>New Booking Received</h2>
                </div>
                <div class="content">
                    <h3>Booking #{booking.booking_id}</h3>
                    <div class="field">
                        <div class="label">Property:</div>
                        <div class="value">{booking.property.title} - {booking.property.location}</div>
                    </div>
                    <div class="field">
                        <div class="label">Guest Name:</div>
                        <div class="value">{booking.name}</div>
                    </div>
                    <div class="field">
                        <div class="label">Email:</div>
                        <div class="value">{booking.email}</div>
                    </div>
                    <div class="field">
                        <div class="label">Phone:</div>
                        <div class="value">{booking.phone}</div>
                    </div>
                    <div class="field">
                        <div class="label">Check-in - Check-out:</div>
                        <div class="value">{booking.check_in.strftime('%B %d, %Y')} - {booking.check_out.strftime('%B %d, %Y')}</div>
                    </div>
                    <div class="field">
                        <div class="label">Nights / Guests:</div>
                        <div class="value">{booking.nights} nights / {booking.guests} guests</div>
                    </div>
                    <div class="field">
                        <div class="label">Total Amount:</div>
                        <div class="value">{booking.currency}{booking.total_amount:,.2f}</div>
                    </div>
                    <div class="field">
                        <div class="label">Payment Status:</div>
                        <div class="value">{booking.payment_status}</div>
                    </div>
                    {f'<div class="field"><div class="label">Special Requests:</div><div class="value">{booking.special_requests}</div></div>' if booking.special_requests else ''}
                </div>
                <div class="footer">
                    <p>Sequoia Projects - Admin Notification</p>
                </div>
            </div>
        </body>
        </html>
        """

        admin_email = getattr(settings, 'ADMIN_EMAIL', settings.DEFAULT_FROM_EMAIL)
        return cls.send_email(subject, [admin_email], html_content)

    @classmethod
    def send_payment_confirmation(cls, payment) -> bool:
        """Send payment confirmation email to customer"""
        booking = payment.booking
        subject = f"Payment Confirmed - Booking {booking.booking_id}"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #4caf50; color: white; padding: 20px; text-align: center; }}
                .content {{ background-color: #f9f9f9; padding: 20px; }}
                .payment-info {{ background-color: #e8f5e9; padding: 15px; margin-bottom: 20px; border-radius: 5px; }}
                .field {{ margin-bottom: 15px; }}
                .label {{ font-weight: bold; color: #3a3a41; }}
                .value {{ margin-top: 5px; }}
                .amount {{ font-size: 28px; color: #4caf50; font-weight: bold; }}
                .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>✓ Payment Successful</h2>
                </div>
                <div class="content">
                    <p>Dear {booking.name},</p>
                    <p>Your payment has been successfully processed!</p>

                    <div class="payment-info">
                        <h3>Payment Details</h3>
                        <div class="field">
                            <div class="label">Amount Paid:</div>
                            <div class="amount">{payment.currency}{payment.amount:,.2f}</div>
                        </div>
                        <p><strong>Transaction Reference:</strong> {payment.transaction_reference}</p>
                        <p><strong>Payment Method:</strong> {payment.get_payment_method_display()}</p>
                        <p><strong>Payment Date:</strong> {payment.paid_at.strftime('%B %d, %Y at %I:%M %p') if payment.paid_at else 'N/A'}</p>
                    </div>

                    <h3>Booking Information</h3>
                    <p><strong>Booking ID:</strong> {booking.booking_id}</p>
                    <p><strong>Property:</strong> {booking.property.title}</p>
                    <p><strong>Location:</strong> {booking.property.location}</p>
                    <p><strong>Check-in:</strong> {booking.check_in.strftime('%B %d, %Y')}</p>
                    <p><strong>Check-out:</strong> {booking.check_out.strftime('%B %d, %Y')}</p>

                    <p>Thank you for choosing Sequoia Projects. We look forward to hosting you!</p>
                </div>
                <div class="footer">
                    <p>Sequoia Projects - Real Estate Management System</p>
                    <p>Phone: +234 803 456 7890 | Email: info@seqprojects.com</p>
                </div>
            </div>
        </body>
        </html>
        """

        return cls.send_email(subject, [booking.email], html_content)
