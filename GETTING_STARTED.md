# Getting Started with Sequoia Projects Backend

Complete apartment booking and payment backend built with Django REST Framework.

## Quick Start

### 1. Start the Development Server

```bash
cd /home/moosa/Desktop/aminu/backend
source ../venv/bin/activate
python manage.py runserver
```

The API will be available at:
- **API Base URL**: http://localhost:8000/api/
- **Admin Panel**: http://localhost:8000/admin/
- **Health Check**: http://localhost:8000/api/health/

### 2. Create Admin User

```bash
python manage.py createsuperuser
```

Follow the prompts to create an admin account.

### 3. Access Admin Panel

Visit http://localhost:8000/admin/ and login with your superuser credentials.

From the admin panel, you can:
- Add properties with images
- Manage agents
- View and manage bookings
- Process payments
- Handle customer inquiries

---

## Database Schema

### Models Created

1. **Agent** - Property agents/contacts
2. **Property** - Apartment listings with images
3. **PropertyImage** - Property photos (categorized)
4. **Booking** - Customer reservations
5. **Payment** - Payment transactions
6. **ContactInquiry** - General contact form submissions
7. **PropertyInquiry** - Property-specific inquiries

All models include proper validation, relationships, and timestamps.

---

## API Endpoints Overview

### Properties
- `GET /api/properties/` - List all properties (with filtering)
- `GET /api/properties/:id/` - Get property details
- `GET /api/properties/:id/availability/` - Check availability
- `POST /api/properties/` - Create property (admin)
- `PUT /api/properties/:id/` - Update property (admin)
- `DELETE /api/properties/:id/` - Delete property (admin)

### Bookings
- `POST /api/bookings/` - Create booking
- `GET /api/bookings/:id/` - Get booking details
- `POST /api/bookings/:id/cancel/` - Cancel booking
- `GET /api/bookings/` - List all bookings (admin)

### Payments
- `POST /api/payments/` - Create payment
- `POST /api/payments/:id/verify/` - Verify payment
- `GET /api/payments/` - List payments (admin)

### Contact & Inquiries
- `POST /api/contact-inquiries/` - Submit contact form
- `POST /api/property-inquiries/` - Submit property inquiry
- `GET /api/contact-inquiries/` - View inquiries (admin)
- `GET /api/property-inquiries/` - View inquiries (admin)

### Agents
- `GET /api/agents/` - List all agents
- `GET /api/agents/:id/` - Get agent details

See **API_DOCUMENTATION.md** for complete API reference with request/response examples.

---

## Integrating with Frontend

### Update Your Frontend API Base URL

In your frontend (`seqproject`), create an API client:

```typescript
// lib/api/client.ts
const API_BASE_URL = 'http://localhost:8000/api';

export async function fetchProperties(filters?: Record<string, string>) {
  const queryString = new URLSearchParams(filters).toString();
  const url = `${API_BASE_URL}/properties/${queryString ? '?' + queryString : ''}`;

  const response = await fetch(url);
  if (!response.ok) throw new Error('Failed to fetch properties');

  return response.json();
}

export async function createBooking(bookingData: {
  property_id: string;
  name: string;
  email: string;
  phone: string;
  check_in: string;
  check_out: string;
  guests: number;
}) {
  const response = await fetch(`${API_BASE_URL}/bookings/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(bookingData),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(JSON.stringify(error));
  }

  return response.json();
}

export async function submitContactForm(contactData: {
  name: string;
  email: string;
  phone: string;
  subject: string;
  message: string;
}) {
  const response = await fetch(`${API_BASE_URL}/contact-inquiries/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(contactData),
  });

  if (!response.ok) throw new Error('Failed to submit contact form');

  return response.json();
}
```

### Update Your Frontend Components

#### Replace `lib/data.ts` with API calls:

```typescript
// app/properties/page.tsx
import { fetchProperties } from '@/lib/api/client';

export default async function PropertiesPage() {
  const { results: properties } = await fetchProperties({ status: 'rent' });

  return (
    // Your JSX here using properties from API
  );
}
```

#### Update BookingModal component:

```typescript
// components/BookingModal.tsx
import { createBooking } from '@/lib/api/client';

const handleSubmit = async (e: React.FormEvent) => {
  e.preventDefault();

  try {
    const result = await createBooking({
      property_id: property.id,
      name: formData.name,
      email: formData.email,
      phone: formData.phone,
      check_in: formData.checkIn,
      check_out: formData.checkOut,
      guests: formData.guests,
    });

    if (result.success) {
      alert(`Booking created! Booking ID: ${result.booking.booking_id}`);
      // Redirect to payment page or show success
    }
  } catch (error) {
    alert('Failed to create booking: ' + error.message);
  }
};
```

#### Update Contact Page:

```typescript
// app/contact/page.tsx
import { submitContactForm } from '@/lib/api/client';

const handleSubmit = async (e: React.FormEvent) => {
  e.preventDefault();

  try {
    const result = await submitContactForm({
      name: formData.name,
      email: formData.email,
      phone: formData.phone,
      subject: formData.subject,
      message: formData.message,
    });

    if (result.success) {
      alert(result.message);
      // Reset form or show success message
    }
  } catch (error) {
    alert('Failed to submit contact form');
  }
};
```

---

## Adding Sample Data

### Option 1: Through Admin Panel

1. Login to http://localhost:8000/admin/
2. Create an Agent
3. Create Properties (assign agent, add amenities as JSON array)
4. Upload property images with categories

### Option 2: Using Django Shell

```bash
python manage.py shell
```

```python
from api.models import Agent, Property, PropertyImage

# Create an agent
agent = Agent.objects.create(
    name='Tijjani Musa',
    phone='(222) 456-8932',
    mobile='777 287 378 737',
    email='info@seqprojects.com'
)

# Create a property
property = Property.objects.create(
    id='arusha-101-spl-wuse',
    title='Arusha 101 by SPL - Premium Apartment',
    location='Arusha 101 by SPL, Wuse Zone 1, Abuja',
    price=75000,
    currency='₦',
    status='rent',
    type='Apartment',
    guests=2,
    bedrooms=1,
    bathrooms=1,
    living_rooms=1,
    garages=1,
    description='Experience ultimate comfort in the heart of Abuja...',
    amenities=['Fully Equipped Kitchen', 'WiFi', '24/7 Electricity', 'Security', 'Parking'],
    entity='Arusha Property Management',
    agent=agent,
    featured=True,
    is_active=True
)

print(f"Created property: {property.id}")
```

---

## Features Implemented

### Core Features
- ✅ Property management with images
- ✅ Booking system with date validation
- ✅ Booking availability checking
- ✅ Payment tracking
- ✅ Contact form handling
- ✅ Property-specific inquiries
- ✅ Agent management

### API Features
- ✅ RESTful API with Django REST Framework
- ✅ Advanced filtering (status, type, price range, bedrooms, etc.)
- ✅ Search functionality
- ✅ Pagination
- ✅ CORS configured for frontend integration
- ✅ Image upload handling
- ✅ Date validation
- ✅ Booking conflict detection

### Admin Features
- ✅ Comprehensive Django admin interface
- ✅ Inline image management
- ✅ Bulk editing capabilities
- ✅ Filtering and search
- ✅ Image previews
- ✅ Status management

---

## Next Steps

### 1. Payment Gateway Integration

Install payment gateway SDK:

```bash
# For Paystack (recommended for Nigerian market)
pip install paystackapi

# For Flutterwave
pip install flutterwaveng
```

Update `.env`:
```
PAYSTACK_SECRET_KEY=sk_test_your_secret_key
PAYSTACK_PUBLIC_KEY=pk_test_your_public_key
```

See `views.py` PaymentViewSet for TODO comments on payment integration.

### 2. Email Notifications

Configure email in `settings.py`:

```python
# Email configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = config('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = 'noreply@seqprojects.com'
```

Add to `.env`:
```
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

### 3. Production Deployment

#### Switch to PostgreSQL:

Update `.env`:
```
DB_ENGINE=django.db.backends.postgresql
DB_NAME=sequoia_db
DB_USER=sequoia_user
DB_PASSWORD=strong_password
DB_HOST=localhost
DB_PORT=5432
```

#### Production Settings:

Update `.env`:
```
DEBUG=False
SECRET_KEY=generate-a-new-strong-secret-key
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
CORS_ALLOWED_ORIGINS=https://your-frontend-domain.com
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

#### Collect Static Files:

```bash
python manage.py collectstatic
```

#### Deploy with Gunicorn:

```bash
pip install gunicorn
gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

---

## Troubleshooting

### Issue: ModuleNotFoundError

**Solution**: Ensure virtual environment is activated:
```bash
source ../venv/bin/activate
```

### Issue: Database errors

**Solution**: Run migrations:
```bash
python manage.py makemigrations
python manage.py migrate
```

### Issue: CORS errors from frontend

**Solution**: Update `.env` with your frontend URL:
```
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
```

### Issue: Image upload not working

**Solution**: Ensure media directory exists and check permissions:
```bash
mkdir -p media
chmod 755 media
```

---

## File Structure

```
backend/
├── api/                        # Main API app
│   ├── models.py              # Database models
│   ├── serializers.py         # DRF serializers
│   ├── views.py               # API views/viewsets
│   ├── urls.py                # API routing
│   ├── admin.py               # Admin configuration
│   └── migrations/            # Database migrations
├── config/                     # Project configuration
│   ├── settings.py            # Django settings
│   ├── urls.py                # Root URL configuration
│   └── wsgi.py                # WSGI configuration
├── media/                      # User-uploaded files
├── static/                     # Static files
├── .env                        # Environment variables (not in git)
├── .env.example               # Example environment file
├── .gitignore                 # Git ignore rules
├── manage.py                  # Django management script
├── requirements.txt           # Python dependencies
├── README.md                  # General README
├── API_DOCUMENTATION.md       # Complete API docs
└── GETTING_STARTED.md         # This file
```

---

## Support

For questions or issues:
- Check API_DOCUMENTATION.md for API reference
- Review Django admin at /admin/
- Check backend logs for errors
- Ensure all environment variables are set correctly

Happy coding! 🚀