"""Appointment booking logic for home service professionals.

In production this would integrate with calendar APIs (Google Calendar, Calendly)
and CRM systems (ServiceTitan, Housecall Pro). The mock generates confirmations.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from src.service_db import get_pro_by_name

# Track booked appointments in memory
_booked_appointments: list[dict] = []


def _generate_time_slots(pro_name: str, date_str: str | None = None) -> list[dict]:
    """Generate available time slots for a given pro and date.

    Returns 30-minute slots during business hours (8 AM – 6 PM).
    Emergency pros get after-hours slots too.
    """
    pro = get_pro_by_name(pro_name)
    if pro is None:
        return []

    if date_str:
        try:
            base_date = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            return []
    else:
        base_date = datetime.now() + timedelta(days=1)

    # Business hours
    slots = []
    for hour in range(8, 18):
        for minute in (0, 30):
            slot_time = base_date.replace(hour=hour, minute=minute)
            if slot_time < datetime.now():
                continue
            slots.append({
                "date": slot_time.strftime("%Y-%m-%d"),
                "time": slot_time.strftime("%I:%M %p").lstrip("0").lower(),
                "datetime": slot_time.isoformat(),
                "available": True,
            })

    # After-hours for emergency pros
    if pro.available_now:
        for hour in range(18, 22):
            slot_time = base_date.replace(hour=hour, minute=0)
            if slot_time < datetime.now():
                continue
            slots.append({
                "date": slot_time.strftime("%Y-%m-%d"),
                "time": slot_time.strftime("%I:%M %p").lstrip("0").lower(),
                "datetime": slot_time.isoformat(),
                "available": True,
                "emergency": True,
            })

    return slots


def get_available_slots(pro_name: str, date_str: str | None = None) -> list[dict]:
    """Get available appointment slots for a professional."""
    return _generate_time_slots(pro_name, date_str)


def book_appointment(pro_name: str, time_slot: str, date_str: str | None = None) -> dict:
    """Book an appointment with a professional at a given time.

    Args:
        pro_name: Name of the professional.
        time_slot: Time string like "9:00 am" or "14:00".
        date_str: Optional date string YYYY-MM-DD. Defaults to tomorrow.

    Returns:
        Booking confirmation dict.
    """
    pro = get_pro_by_name(pro_name)
    if pro is None:
        return {
            "success": False,
            "error": f"Professional '{pro_name}' not found.",
        }

    # Parse the time_slot
    try:
        # Try HH:MM format first
        parsed_time = datetime.strptime(time_slot.strip(), "%H:%M")
    except ValueError:
        try:
            # Try 12-hour format
            parsed_time = datetime.strptime(time_slot.strip().lower(), "%I:%M %p")
        except ValueError:
            try:
                parsed_time = datetime.strptime(time_slot.strip().lower(), "%I:%M%p")
            except ValueError:
                return {
                    "success": False,
                    "error": f"Invalid time format: '{time_slot}'. Use HH:MM (24h) or HH:MM AM/PM.",
                }

    if date_str is None:
        date_str = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

    appointment_datetime = f"{date_str}T{parsed_time.strftime('%H:%M:%S')}"

    confirmation = {
        "success": True,
        "confirmation_number": f"HF-{uuid.uuid4().hex[:8].upper()}",
        "professional": pro.name,
        "company": pro.company,
        "service_types": [st.value for st in pro.service_types],
        "appointment_date": date_str,
        "appointment_time": parsed_time.strftime("%I:%M %p").lstrip("0").lower(),
        "appointment_datetime": appointment_datetime,
        "status": "confirmed",
        "notes": "Please confirm 24 hours before the appointment. Cancellations within 2 hours may incur a fee.",
    }

    _booked_appointments.append(confirmation)
    return confirmation


def list_appointments(pro_name: str | None = None) -> list[dict]:
    """List all booked appointments, optionally filtered by professional."""
    if pro_name:
        return [a for a in _booked_appointments if a["professional"] == pro_name]
    return list(_booked_appointments)