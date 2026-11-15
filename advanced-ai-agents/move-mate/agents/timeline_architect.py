"""Timeline Architect Agent — generates a comprehensive moving timeline."""

from models import MoveDetails, TimelineEntry
from datetime import date, timedelta


def run(details: MoveDetails) -> list[TimelineEntry]:
    """Build a week-by-week moving timeline leading up to and after move day."""
    timeline = []
    move = details.move_date

    # 8 weeks before
    timeline.append(TimelineEntry(
        week=f"8 Weeks Before ({_fmt_week_range(move, -8)})",
        category="planning",
        tasks=[
            "Set a moving budget",
            "Research moving companies and get 3 quotes",
            "Decide: DIY vs full-service moving",
            "Start decluttering — sell/donate items you don't need",
            "Notify landlord/property manager of move-out date",
        ],
    ))

    # 6 weeks before
    timeline.append(TimelineEntry(
        week=f"6 Weeks Before ({_fmt_week_range(move, -6)})",
        category="planning",
        tasks=[
            "Book moving truck or movers",
            "Start collecting moving supplies (boxes, tape, markers)",
            "Measure furniture for new space",
            "Begin using up freezer/ pantry food",
            "Check new address for parking/permit requirements",
        ],
    ))

    # 4 weeks before
    timeline.append(TimelineEntry(
        week=f"4 Weeks Before ({_fmt_week_range(move, -4)})",
        category="admin",
        tasks=[
            "File USPS change of address (mail forwarding)",
            "Schedule utility disconnection at old address",
            "Schedule utility connection at new address",
            "Notify banks and credit cards of address change",
            "Book time off work if needed",
            "Arrange pet/child care for moving day",
        ],
    ))

    # 2 weeks before
    timeline.append(TimelineEntry(
        week=f"2 Weeks Before ({_fmt_week_range(move, -2)})",
        category="packing",
        tasks=[
            "Start packing non-essential items (seasonal clothes, decor, books)",
            "Label all boxes by room and contents",
            "Notify remaining subscriptions/services",
            "Make a first-night box (essentials, meds, chargers, toiletries)",
            "Arrange elevator/stair access if moving to/from apartment",
        ],
    ))

    # 1 week before
    timeline.append(TimelineEntry(
        week=f"1 Week Before ({_fmt_week_range(move, -1)})",
        category="packing",
        tasks=[
            "Finish packing everything except daily essentials",
            "Defrost and clean refrigerator/freezer",
            "Take photos of empty rooms for security deposit documentation",
            "Confirm all utility appointments",
            "Disconnect and prepare appliances (washer, dryer, TV mounts)",
            "Pack a 'move-day kit' with snacks, water, paper plates, hand sanitizer",
        ],
    ))

    # Move day
    timeline.append(TimelineEntry(
        week=f"Move Day — {move.strftime('%B %d, %Y')}",
        category="moving",
        tasks=[
            "Wake up early — take final meter readings (gas, electric, water)",
            "Do final walk-through of old home — check all closets, cabinets",
            "Load truck in order: heavy items first, light/irregular last",
            "Keep essential documents and valuables with YOU (not in the truck)",
            "Clean old home as needed for deposit return",
            "Drop keys off with landlord/agent",
            "Arrive at new home — inspect for damage before unloading",
            "Unload room by room — label temporarily if helpers/direction unclear",
            "Set up beds first! You'll thank yourself at the end of the day.",
            "Plug in refrigerator and set up basic kitchen",
        ],
    ))

    # 1 week after
    timeline.append(TimelineEntry(
        week=f"1 Week After ({_fmt_week_range(move, 1)})",
        category="settling",
        tasks=[
            "Unpack kitchen and bathroom essentials",
            "Update driver's license / state ID address",
            "Register to vote at new address",
            "Find nearest pharmacy, urgent care, grocery store",
            "Set up internet and TV at new home",
            "Change garage door codes / re-key locks if needed",
        ],
    ))

    # 2 weeks after
    timeline.append(TimelineEntry(
        week=f"2 Weeks After ({_fmt_week_range(move, 2)})",
        category="settling",
        tasks=[
            "Unpack remaining boxes (don't let them sit!)",
            "Update auto insurance with new garaging address",
            "Set up recurring trash/recycling pickup",
            "Explore the neighborhood — find favorite coffee shop, gym, park",
            "Update emergency contact info with employer/school",
            "Submit change of address to remaining services",
            "Schedule annual furnace/AC maintenance if applicable",
        ],
    ))

    return timeline


def _fmt_week_range(move: date, offset_weeks: int) -> str:
    """Format a readable date range for a given week offset from move date."""
    start = move + timedelta(weeks=offset_weeks)
    end = start + timedelta(days=6)
    return f"{start.strftime('%b %d')} – {end.strftime('%b %d, %Y')}"