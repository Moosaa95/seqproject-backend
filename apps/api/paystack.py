"""
Paystack Payment Integration Utility

This module handles all Paystack payment operations including:
- Initializing payments
- Verifying payment transactions
- Processing payment webhooks
"""

import os
import hmac
import hashlib
from decimal import Decimal
from typing import Dict, Any, Optional
from paystackapi.paystack import Paystack
from django.conf import settings
from .models import Payment, Booking
from .notifications import EmailNotificationService
import logging

logger = logging.getLogger(__name__)


class PaystackService:
    """Service class for Paystack payment operations"""

    def __init__(self):
        """Initialize Paystack client with secret key"""
        secret_key = getattr(settings, "PAYSTACK_SECRET_KEY", None)
        print("==========PAYSTACK SECRET KEY", secret_key)
        if not secret_key or secret_key == "sk_test_your_secret_key_here":
            raise Exception(
                "Paystack secret key not configured. Please set PAYSTACK_SECRET_KEY in settings."
            )

        self.paystack = Paystack(secret_key=secret_key)
        self.public_key = getattr(settings, "PAYSTACK_PUBLIC_KEY", "")
        self.callback_url = getattr(
            settings, "PAYSTACK_CALLBACK_URL", "http://localhost:3000/payment/verify"
        )

    def initialize_payment(
        self, booking: Booking, metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Initialize a payment transaction with Paystack

        Args:
            booking: Booking instance to create payment for
            metadata: Optional additional metadata for the transaction

        Returns:
            Dictionary containing authorization_url, access_code, and reference
        """
        # Convert amount to kobo (Paystack uses smallest currency unit)
        amount_kobo = int(booking.total_amount * 100)

        # Prepare payment data
        payment_data = {
            "email": booking.email,
            "amount": amount_kobo,
            "currency": "NGN" if booking.currency == "₦" else "USD",
            "callback_url": self.callback_url,
            "metadata": {
                "booking_id": str(booking.booking_id),
                "property_title": booking.property.title,
                "customer_name": booking.name,
                "check_in": str(booking.check_in),
                "check_out": str(booking.check_out),
                "nights": booking.nights,
                **(metadata or {}),
            },
        }

        try:
            # Initialize transaction with Paystack
            response = self.paystack.transaction.initialize(**payment_data)

            if response["status"]:
                data = response["data"]

                # Find and update existing pending payment or create new one
                payment = Payment.objects.filter(
                    booking=booking,
                    status='pending'
                ).first()

                if payment:
                    # Update existing pending payment
                    payment.transaction_reference = data["reference"]
                    payment.status = "processing"
                    payment.gateway_response = data
                    payment.save()
                else:
                    # Create new payment if none exists
                    payment = Payment.objects.create(
                        booking=booking,
                        amount=booking.total_amount,
                        currency=booking.currency,
                        payment_method="paystack",
                        transaction_reference=data["reference"],
                        status="processing",
                        gateway_response=data,
                    )

                return {
                    "success": True,
                    "payment_id": str(payment.id),
                    "authorization_url": data["authorization_url"],
                    "access_code": data["access_code"],
                    "reference": data["reference"],
                }
            else:
                return {
                    "success": False,
                    "message": response.get("message", "Failed to initialize payment"),
                }

        except Exception as e:
            return {
                "success": False,
                "message": f"Payment initialization failed: {str(e)}",
            }

    def verify_payment(self, reference: str) -> Dict[str, Any]:
        """
        Verify a payment transaction with Paystack

        Args:
            reference: Transaction reference to verify

        Returns:
            Dictionary containing verification status and payment details
        """
        try:
            # Verify transaction with Paystack
            response = self.paystack.transaction.verify(reference=reference)

            if response["status"]:
                data = response["data"]

                # Find payment in database
                try:
                    payment = Payment.objects.get(transaction_reference=reference)
                except Payment.DoesNotExist:
                    return {
                        "success": False,
                        "message": "Payment record not found in database",
                    }

                # Update payment status based on Paystack response
                if data["status"] == "success":
                    payment.status = "successful"
                    payment.paid_at = data.get("paid_at")
                    payment.gateway_response = data
                    payment.save()

                    # Update booking payment status
                    booking = payment.booking
                    booking.payment_status = "paid"
                    booking.status = "confirmed"
                    booking.save()

                    # Send payment confirmation email
                    try:
                        EmailNotificationService.send_payment_confirmation(payment)
                    except Exception as e:
                        logger.error(f"Failed to send payment confirmation email: {str(e)}")

                    return {
                        "success": True,
                        "message": "Payment verified successfully",
                        "payment_id": str(payment.id),
                        "booking_id": str(booking.booking_id),
                        "amount": float(payment.amount),
                        "currency": payment.currency,
                        "status": payment.status,
                    }
                elif data["status"] == "failed":
                    payment.status = "failed"
                    payment.gateway_response = data
                    payment.save()

                    return {
                        "success": False,
                        "message": "Payment failed",
                        "payment_id": str(payment.id),
                    }
                else:
                    # pending or other status
                    payment.gateway_response = data
                    payment.save()

                    return {
                        "success": False,
                        "message": f'Payment is {data["status"]}',
                        "payment_id": str(payment.id),
                        "status": data["status"],
                    }
            else:
                return {
                    "success": False,
                    "message": response.get("message", "Failed to verify payment"),
                }

        except Exception as e:
            return {
                "success": False,
                "message": f"Payment verification failed: {str(e)}",
            }

    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """
        Verify Paystack webhook signature

        Args:
            payload: Request body as bytes
            signature: X-Paystack-Signature header value

        Returns:
            True if signature is valid, False otherwise
        """
        secret_key = getattr(settings, "PAYSTACK_SECRET_KEY", "")

        # Compute HMAC hash
        computed_hash = hmac.new(
            secret_key.encode("utf-8"), payload, hashlib.sha512
        ).hexdigest()

        return hmac.compare_digest(computed_hash, signature)

    def process_webhook_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process Paystack webhook event

        Args:
            event_data: Webhook event data

        Returns:
            Dictionary containing processing result
        """
        event_type = event_data.get("event")
        data = event_data.get("data", {})

        if event_type == "charge.success":
            # Payment successful
            reference = data.get("reference")
            return self.verify_payment(reference)

        elif event_type == "charge.failed":
            # Payment failed
            reference = data.get("reference")
            try:
                payment = Payment.objects.get(transaction_reference=reference)
                payment.status = "failed"
                payment.gateway_response = data
                payment.save()

                return {"success": True, "message": "Payment failure recorded"}
            except Payment.DoesNotExist:
                return {"success": False, "message": "Payment record not found"}

        return {"success": True, "message": f"Event {event_type} received"}

    def get_public_key(self) -> str:
        """Get Paystack public key for frontend use"""
        return self.public_key


# Convenience function
def get_paystack_service() -> PaystackService:
    """Get or create PaystackService instance"""
    return PaystackService()
