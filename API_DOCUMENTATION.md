# Sequoia Projects API Documentation

Complete API documentation for the apartment booking and payment system.

## Base URL

```
Development: http://localhost:8000/api/
Production: https://your-domain.com/api/
```

## Authentication

Most endpoints allow anonymous access for public users. Admin endpoints require authentication.

- **Admin Login**: `/admin/` (Django admin interface)
- **Admin-only endpoints**: Require staff/superuser authentication

---

## API Endpoints

### Health Check

#### GET /api/health/
Check if API is running.

**Response:**
```json
{
  "status": "healthy",
  "message": "Sequoia Projects API is running successfully",
  "timestamp": "2025-12-29T10:30:00Z"
}
```

---

## Properties

### List Properties

#### GET /api/properties/
Get all active properties with filtering, search, and pagination.

**Query Parameters:**
- `status` - Filter by status: `rent` or `sale`
- `type` - Filter by property type (e.g., "Apartment", "Villa")
- `entity` - Filter by managing entity
- `featured` - Filter featured properties: `true` or `false`
- `min_price` - Minimum price filter
- `max_price` - Maximum price filter
- `bedrooms` - Minimum number of bedrooms
- `bathrooms` - Minimum number of bathrooms
- `search` - Search in title, location, description, type, entity
- `ordering` - Sort by: `price`, `-price`, `created_at`, `-created_at`, `bedrooms`, `bathrooms`
- `page` - Page number (default: 1)
- `page_size` - Results per page (default: 10)

**Example Request:**
```
GET /api/properties/?status=rent&bedrooms=2&featured=true&ordering=-price
```

**Response:**
```json
{
  "count": 5,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "arusha-crescent",
      "title": "Executive 2-Bedroom Apartment",
      "location": "7 Arusha Crescent, Wuse Zone 1, Abuja",
      "price": "120000.00",
      "currency": "₦",
      "status": "rent",
      "type": "Apartment",
      "bedrooms": 2,
      "bathrooms": 4,
      "guests": 2,
      "featured": true,
      "primary_image": "http://localhost:8000/media/properties/2025/01/01/image.jpg",
      "agent": {
        "id": 1,
        "name": "Tijjani Musa",
        "phone": "(222) 456-8932",
        "mobile": "777 287 378 737",
        "email": "info@seqprojects.com",
        "skype": null
      }
    }
  ]
}
```

### Get Property Details

#### GET /api/properties/:id/
Get detailed information about a specific property.

**Response:**
```json
{
  "id": "arusha-101-spl-wuse",
  "title": "Arusha 101 by SPL - Premium Apartment",
  "location": "Arusha 101 by SPL, Wuse Zone 1, Abuja",
  "price": "75000.00",
  "currency": "₦",
  "status": "rent",
  "type": "Apartment",
  "area": null,
  "guests": 2,
  "bedrooms": 1,
  "bathrooms": 1,
  "living_rooms": 1,
  "garages": 1,
  "units": null,
  "description": "Experience ultimate comfort in the heart of Abuja...",
  "amenities": [
    "Fully Equipped Kitchen",
    "WiFi",
    "24/7 Electricity",
    "Water Supply",
    "Security",
    "Parking"
  ],
  "entity": "Arusha Property Management",
  "agent": {
    "id": 1,
    "name": "Tijjani Musa",
    "phone": "(222) 456-8932",
    "mobile": "777 287 378 737",
    "email": "info@seqprojects.com",
    "skype": null
  },
  "featured": true,
  "is_active": true,
  "available_from": null,
  "is_available": true,
  "images": [
    "http://localhost:8000/media/properties/2025/01/01/living-room.jpg",
    "http://localhost:8000/media/properties/2025/01/01/kitchen.jpg"
  ],
  "categorized_images": [
    {
      "category": "Living Room",
      "images": [
        "http://localhost:8000/media/properties/2025/01/01/living-room-1.jpg",
        "http://localhost:8000/media/properties/2025/01/01/living-room-2.jpg"
      ]
    },
    {
      "category": "Kitchen",
      "images": [
        "http://localhost:8000/media/properties/2025/01/01/kitchen.jpg"
      ]
    }
  ],
  "created_at": "2025-12-29T10:00:00Z",
  "updated_at": "2025-12-29T10:00:00Z"
}
```

### Check Property Availability

#### GET /api/properties/:id/availability/
Check if a property is available for specific dates.

**Query Parameters:**
- `check_in` - Check-in date (YYYY-MM-DD)
- `check_out` - Check-out date (YYYY-MM-DD)

**Example Request:**
```
GET /api/properties/arusha-101-spl-wuse/availability/?check_in=2025-01-15&check_out=2025-01-20
```

**Response:**
```json
{
  "available": true,
  "property_id": "arusha-101-spl-wuse",
  "check_in": "2025-01-15",
  "check_out": "2025-01-20"
}
```

---

## Bookings

### Create Booking

#### POST /api/bookings/
Create a new booking (reservation).

**Request Body:**
```json
{
  "property_id": "arusha-101-spl-wuse",
  "name": "John Doe",
  "email": "john@example.com",
  "phone": "+234 803 456 7890",
  "check_in": "2025-01-15",
  "check_out": "2025-01-20",
  "guests": 2,
  "special_requests": "Late check-in requested"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Booking created successfully",
  "booking": {
    "booking_id": "a1b2c3d4-5678-90ab-cdef-1234567890ab",
    "property": "arusha-101-spl-wuse",
    "property_details": {
      "id": "arusha-101-spl-wuse",
      "title": "Arusha 101 by SPL - Premium Apartment",
      "location": "Arusha 101 by SPL, Wuse Zone 1, Abuja",
      "price": "75000.00",
      "currency": "₦",
      "status": "rent",
      "type": "Apartment",
      "bedrooms": 1,
      "bathrooms": 1,
      "guests": 2,
      "featured": true,
      "primary_image": "http://localhost:8000/media/properties/image.jpg",
      "agent": {
        "id": 1,
        "name": "Tijjani Musa",
        "email": "info@seqprojects.com"
      }
    },
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "+234 803 456 7890",
    "check_in": "2025-01-15",
    "check_out": "2025-01-20",
    "guests": 2,
    "nights": 5,
    "total_amount": "375000.00",
    "currency": "₦",
    "status": "pending",
    "payment_status": "unpaid",
    "special_requests": "Late check-in requested",
    "created_at": "2025-12-29T10:30:00Z",
    "updated_at": "2025-12-29T10:30:00Z"
  }
}
```

**Validation Errors:**
```json
{
  "check_in": ["Check-in date cannot be in the past"],
  "check_out": ["Check-out date must be after check-in date"],
  "property_id": ["Property is already booked for selected dates"]
}
```

### Get Booking Details

#### GET /api/bookings/:booking_id/
Get details of a specific booking.

**Note**: Anyone can view booking details if they have the booking_id.

### Cancel Booking

#### POST /api/bookings/:booking_id/cancel/
Cancel a booking.

**Response:**
```json
{
  "success": true,
  "message": "Booking cancelled successfully",
  "booking": {
    "booking_id": "a1b2c3d4-5678-90ab-cdef-1234567890ab",
    "status": "cancelled"
  }
}
```

### List Bookings (Admin Only)

#### GET /api/bookings/
List all bookings (requires admin authentication).

**Query Parameters:**
- `status` - Filter by status: `pending`, `confirmed`, `cancelled`, `completed`
- `payment_status` - Filter by payment status
- `property_id` - Filter by property ID
- `email` - Filter by customer email

---

## Payments

### Create Payment

#### POST /api/payments/
Initiate a payment for a booking.

**Request Body:**
```json
{
  "booking_id": "a1b2c3d4-5678-90ab-cdef-1234567890ab",
  "amount": "375000.00",
  "currency": "₦",
  "payment_method": "paystack"
}
```

**Response:**
```json
{
  "payment_id": "b2c3d4e5-6789-01bc-def0-234567890abc",
  "booking": 1,
  "booking_details": {
    "booking_id": "a1b2c3d4-5678-90ab-cdef-1234567890ab",
    "property": "arusha-101-spl-wuse",
    "total_amount": "375000.00"
  },
  "amount": "375000.00",
  "currency": "₦",
  "payment_method": "paystack",
  "transaction_reference": null,
  "gateway_response": null,
  "status": "pending",
  "paid_at": null,
  "created_at": "2025-12-29T10:35:00Z",
  "updated_at": "2025-12-29T10:35:00Z"
}
```

### Verify Payment

#### POST /api/payments/:payment_id/verify/
Verify payment status with gateway.

**Response:**
```json
{
  "payment_id": "b2c3d4e5-6789-01bc-def0-234567890abc",
  "status": "successful",
  "amount": "375000.00",
  "currency": "₦",
  "transaction_reference": "PSK_abc123def456"
}
```

---

## Contact Inquiries

### Submit Contact Form

#### POST /api/contact-inquiries/
Submit a general contact form.

**Request Body:**
```json
{
  "name": "Jane Smith",
  "email": "jane@example.com",
  "phone": "+234 803 456 7891",
  "subject": "property",
  "message": "I'm interested in learning more about your properties in Wuse Zone 1."
}
```

**Subject Options:**
- `property` - Property Inquiry
- `management` - Property Management
- `construction` - Construction
- `consultancy` - Project Consultancy
- `airbnb` - Airbnb & Short-Let Services
- `other` - Other

**Response:**
```json
{
  "success": true,
  "message": "Thank you for contacting us. We will get back to you soon.",
  "inquiry_id": 1
}
```

---

## Property Inquiries

### Submit Property-Specific Inquiry

#### POST /api/property-inquiries/
Submit an inquiry for a specific property.

**Request Body:**
```json
{
  "property_id": "arusha-101-spl-wuse",
  "name": "Michael Johnson",
  "email": "michael@example.com",
  "phone": "+234 803 456 7892",
  "message": "Is this property available for long-term rent? What are the terms?"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Thank you for your inquiry. Our agent will contact you soon.",
  "inquiry_id": 1
}
```

---

## Agents

### List Agents

#### GET /api/agents/
Get list of all agents.

**Response:**
```json
{
  "count": 3,
  "results": [
    {
      "id": 1,
      "name": "Tijjani Musa",
      "phone": "(222) 456-8932",
      "mobile": "777 287 378 737",
      "email": "info@seqprojects.com",
      "skype": null
    }
  ]
}
```

### Get Agent Details

#### GET /api/agents/:id/
Get details of a specific agent.

---

## Error Responses

### Validation Error (400)
```json
{
  "field_name": ["Error message"]
}
```

### Not Found (404)
```json
{
  "detail": "Not found."
}
```

### Server Error (500)
```json
{
  "detail": "Internal server error."
}
```

---

## Integration Guide for Frontend

### 1. List Properties
```javascript
// Fetch all properties with filters
fetch('http://localhost:8000/api/properties/?status=rent&featured=true')
  .then(res => res.json())
  .then(data => {
    console.log(data.results); // Array of properties
  });
```

### 2. Get Property Details
```javascript
// Fetch single property
fetch('http://localhost:8000/api/properties/arusha-101-spl-wuse/')
  .then(res => res.json())
  .then(property => {
    console.log(property); // Property object with images, agent, etc.
  });
```

### 3. Create Booking
```javascript
// Create a new booking
fetch('http://localhost:8000/api/bookings/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    property_id: 'arusha-101-spl-wuse',
    name: 'John Doe',
    email: 'john@example.com',
    phone: '+234 803 456 7890',
    check_in: '2025-01-15',
    check_out: '2025-01-20',
    guests: 2
  })
})
  .then(res => res.json())
  .then(data => {
    if (data.success) {
      console.log('Booking created:', data.booking.booking_id);
      // Proceed to payment
    }
  })
  .catch(error => {
    console.error('Booking error:', error);
  });
```

### 4. Submit Contact Form
```javascript
// Submit contact inquiry
fetch('http://localhost:8000/api/contact-inquiries/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    name: 'Jane Smith',
    email: 'jane@example.com',
    phone: '+234 803 456 7891',
    subject: 'property',
    message: 'I would like more information about your properties.'
  })
})
  .then(res => res.json())
  .then(data => {
    if (data.success) {
      alert(data.message);
    }
  });
```

---

## Admin Panel

Access the Django admin panel at:
```
http://localhost:8000/admin/
```

**Features:**
- Manage properties, bookings, payments
- View and respond to inquiries
- Manage agents
- Upload property images
- Update booking and payment statuses
- Filter, search, and export data

---

## Next Steps

### 1. Payment Gateway Integration
To enable online payments, integrate with:
- **Paystack** (recommended for Nigerian market)
- **Flutterwave**

See `Set up payment gateway integration` todo item.

### 2. Email Notifications
Configure email service to send:
- Booking confirmations
- Payment receipts
- Inquiry acknowledgments

See `Add email notification service` todo item.

### 3. Production Deployment
- Set up PostgreSQL database
- Configure environment variables
- Enable HTTPS
- Set DEBUG=False
- Update ALLOWED_HOSTS and CORS_ALLOWED_ORIGINS

---

## Support

For issues or questions, contact the development team or file an issue in the repository.