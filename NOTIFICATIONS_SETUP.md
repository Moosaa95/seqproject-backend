# Email Notifications Setup Guide

## Overview

The Sequoia Projects application now includes a comprehensive email notification system that sends automatic emails for:

1. **Contact Inquiries** - Notifies admin when someone submits a contact form
2. **Property Inquiries** - Notifies agent/admin when someone inquires about a property
3. **Bookings** - Sends confirmation to customer and notification to admin
4. **Payments** - Sends payment confirmation to customer after successful payment

## Configuration

### Development Mode (Console Email Backend)

By default, emails are printed to the console for testing. This is already configured in your `.env` file:

```env
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
DEFAULT_FROM_EMAIL=Sequoia Projects <noreply@seqprojects.com>
ADMIN_EMAIL=info@seqprojects.com
```

### Production Mode (SMTP Email Backend)

For production, you need to configure an SMTP server. Here's how to set up with Gmail:

#### Step 1: Enable 2-Factor Authentication on Gmail
1. Go to your Google Account settings
2. Navigate to Security
3. Enable 2-Step Verification

#### Step 2: Generate App Password
1. Go to https://myaccount.google.com/apppasswords
2. Select "Mail" and "Other (Custom name)"
3. Enter "Sequoia Projects" as the name
4. Copy the generated 16-character password

#### Step 3: Update .env File

```env
# Email Settings
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-16-char-app-password
DEFAULT_FROM_EMAIL=Sequoia Projects <noreply@seqprojects.com>
ADMIN_EMAIL=info@seqprojects.com
```

### Alternative Email Providers

#### SendGrid
```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=your-sendgrid-api-key
```

#### Mailgun
```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.mailgun.org
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=postmaster@your-domain.mailgun.org
EMAIL_HOST_PASSWORD=your-mailgun-password
```

## Email Templates

The system includes beautifully formatted HTML email templates for each notification type:

### 1. Contact Inquiry Notification
**Sent to:** Admin email (`ADMIN_EMAIL` in `.env`)
**Triggered when:** Someone submits the contact form
**Contains:** Name, email, phone, subject, message, timestamp

### 2. Property Inquiry Notification
**Sent to:** Property agent email (or admin if no agent)
**Triggered when:** Someone inquires about a specific property
**Contains:** Property details, inquirer information, message, timestamp

### 3. Booking Confirmation
**Sent to:** Customer email
**Triggered when:** A new booking is created
**Contains:** Booking ID, property details, check-in/out dates, total amount, special requests

### 4. Booking Admin Notification
**Sent to:** Admin email
**Triggered when:** A new booking is created
**Contains:** Full booking details including customer information

### 5. Payment Confirmation
**Sent to:** Customer email
**Triggered when:** Payment is successfully verified
**Contains:** Payment details, transaction reference, booking information

## Testing Email Notifications

### 1. Test in Development (Console)

With console backend enabled, emails will be printed to your terminal:

```bash
# Start the Django server
python manage.py runserver

# In another terminal, create a test inquiry
# Emails will appear in the server console
```

### 2. Test with Real Email (Production)

1. Update `.env` with your SMTP credentials
2. Restart the Django server
3. Submit a contact form or create a booking
4. Check your inbox for the email

### 3. Test Specific Notification

You can test notifications manually in Django shell:

```python
python manage.py shell

from api.models import ContactInquiry
from api.notifications import EmailNotificationService

# Create a test inquiry
inquiry = ContactInquiry.objects.create(
    name="Test User",
    email="test@example.com",
    phone="+234 803 123 4567",
    subject="property",
    message="I'm interested in your properties"
)

# Send test email
EmailNotificationService.send_contact_inquiry_notification(inquiry)
```

## Error Handling

The notification system is designed to be non-blocking:

- If email sending fails, the application continues to work normally
- Errors are logged but don't prevent the main operation (booking, inquiry, etc.)
- Check Django logs for email sending errors:

```bash
# View logs
tail -f logs/django.log
```

## Customization

### Modify Email Templates

Email templates are in `/home/moosa/Desktop/aminu/backend/api/notifications.py`

To customize:
1. Open `notifications.py`
2. Find the method for the email you want to customize (e.g., `send_booking_confirmation`)
3. Edit the HTML content in the `html_content` variable
4. Save and restart the server

### Change Admin Email

Update `ADMIN_EMAIL` in `.env`:

```env
ADMIN_EMAIL=your-admin@yourdomain.com
```

### Change From Email

Update `DEFAULT_FROM_EMAIL` in `.env`:

```env
DEFAULT_FROM_EMAIL=Your Company <noreply@yourdomain.com>
```

## Troubleshooting

### Emails Not Sending

1. **Check console output** - Look for error messages in terminal
2. **Verify credentials** - Ensure EMAIL_HOST_USER and EMAIL_HOST_PASSWORD are correct
3. **Check spam folder** - Gmail might flag your emails as spam initially
4. **Enable less secure apps** - If using regular Gmail password (not recommended)
5. **Check firewall** - Ensure port 587 (or 465) is not blocked

### Gmail Blocking Emails

If Gmail blocks your emails:
1. Use an App Password instead of your regular password
2. Visit https://accounts.google.com/DisplayUnlockCaptcha
3. Try sending again immediately after

### SendGrid/Mailgun Issues

1. Verify your API key is correct
2. Check your email sending limits
3. Ensure your domain is verified

## Production Checklist

Before deploying to production:

- [ ] Configure SMTP credentials in `.env`
- [ ] Test all email notifications
- [ ] Update `DEFAULT_FROM_EMAIL` to your company email
- [ ] Update `ADMIN_EMAIL` to receive admin notifications
- [ ] Set up email monitoring/logging
- [ ] Configure SPF and DKIM records for your domain (to prevent spam)
- [ ] Test with different email providers (Gmail, Outlook, etc.)

## Support

For issues or questions:
- Check Django logs for detailed error messages
- Review email backend configuration in `settings.py`
- Test with console backend first to isolate SMTP issues
- Contact support@seqprojects.com
