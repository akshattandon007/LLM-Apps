"""Data models for MoveMate — multi-agent relocation assistant."""

from dataclasses import dataclass, field
from typing import Optional
from datetime import date


@dataclass
class MoveDetails:
    """User-provided details about the move."""
    current_zip: str
    new_zip: str
    move_date: date
    household_size: str  # studio, 1br, 2br, 3br, house
    is_renting: bool
    current_address: Optional[str] = None
    new_address: Optional[str] = None


@dataclass
class UtilityInfo:
    """Utility setup/cancellation recommendations."""
    electric: list[str] = field(default_factory=list)
    gas: list[str] = field(default_factory=list)
    water: list[str] = field(default_factory=list)
    internet: list[str] = field(default_factory=list)
    trash: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


@dataclass
class AddressChangeInfo:
    """Entities to notify about address change."""
    government: list[str] = field(default_factory=list)
    financial: list[str] = field(default_factory=list)
    subscriptions: list[str] = field(default_factory=list)
    insurance: list[str] = field(default_factory=list)
    other: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


@dataclass
class CostEstimate:
    """Estimated moving costs breakdown."""
    truck_rental: float = 0.0
    moving_supplies: float = 0.0
    movers: float = 0.0
    security_deposit: float = 0.0
    cleaning: float = 0.0
    travel: float = 0.0
    other: float = 0.0
    total: float = 0.0
    notes: list[str] = field(default_factory=list)
    buffer_percent: float = 15.0


@dataclass
class NeighborhoodInfo:
    """Research about the new neighborhood."""
    nearby_amenities: list[str] = field(default_factory=list)
    transit_options: list[str] = field(default_factory=list)
    grocery_stores: list[str] = field(default_factory=list)
    parks_greenspace: list[str] = field(default_factory=list)
    schools_nearby: list[str] = field(default_factory=list)
    weather_summary: str = ""
    notes: list[str] = field(default_factory=list)


@dataclass
class TimelineEntry:
    """A single timeline item."""
    week: str
    tasks: list[str] = field(default_factory=list)
    category: str = "general"


@dataclass
class Playbook:
    """The complete relocation playbook — output of the orchestrator."""
    move_details: MoveDetails
    utilities: UtilityInfo = field(default_factory=UtilityInfo)
    address_changes: AddressChangeInfo = field(default_factory=AddressChangeInfo)
    costs: CostEstimate = field(default_factory=CostEstimate)
    neighborhood: NeighborhoodInfo = field(default_factory=NeighborhoodInfo)
    timeline: list[TimelineEntry] = field(default_factory=list)

    def to_markdown(self) -> str:
        """Render the playbook as formatted Markdown."""
        lines = []
        lines.append(f"# 📦 MoveMate Relocation Playbook")
        lines.append(f"")
        lines.append(f"**Moving on:** {self.move_details.move_date}")
        lines.append(f"**From:** {self.move_details.current_zip or self.move_details.current_address or 'N/A'}")
        lines.append(f"**To:** {self.move_details.new_zip or self.move_details.new_address or 'N/A'}")
        lines.append(f"**Household:** {self.move_details.household_size}")
        lines.append(f"")
        lines.append(f"---")
        lines.append(f"")

        # Utilities
        lines.append(f"## ⚡ Utility Setup & Cancellation")
        for label, items in [
            ("Electric", self.utilities.electric),
            ("Gas", self.utilities.gas),
            ("Water/Sewer", self.utilities.water),
            ("Internet/Cable", self.utilities.internet),
            ("Trash/Recycling", self.utilities.trash),
        ]:
            if items:
                lines.append(f"**{label}:**")
                for item in items:
                    lines.append(f"- {item}")
                lines.append(f"")
        if self.utilities.notes:
            for n in self.utilities.notes:
                lines.append(f"> 💡 {n}")
            lines.append(f"")

        # Address changes
        lines.append(f"## 📬 Address Change Checklist")
        for label, items in [
            ("Government", self.address_changes.government),
            ("Financial", self.address_changes.financial),
            ("Subscriptions", self.address_changes.subscriptions),
            ("Insurance", self.address_changes.insurance),
            ("Other", self.address_changes.other),
        ]:
            if items:
                lines.append(f"**{label}:**")
                for item in items:
                    lines.append(f"- {item}")
                lines.append(f"")
        if self.address_changes.notes:
            for n in self.address_changes.notes:
                lines.append(f"> 💡 {n}")
            lines.append(f"")

        # Cost estimate
        lines.append(f"## 💰 Cost Estimate")
        lines.append(f"")
        cost_items = [
            ("Truck Rental", self.costs.truck_rental),
            ("Moving Supplies", self.costs.moving_supplies),
            ("Movers/Labor", self.costs.movers),
            ("Security Deposit", self.costs.security_deposit),
            ("Cleaning", self.costs.cleaning),
            ("Travel", self.costs.travel),
            ("Other", self.costs.other),
        ]
        subtotal = sum(v for _, v in cost_items)
        for label, amount in cost_items:
            if amount > 0:
                lines.append(f"| **{label}** | ${amount:,.0f} |")
        lines.append(f"| --- | --- |")
        lines.append(f"| **Subtotal** | **${subtotal:,.0f}** |")
        lines.append(f"| **Buffer ({self.costs.buffer_percent:.0f}%)** | **${subtotal * self.costs.buffer_percent / 100:,.0f}** |")
        lines.append(f"| **Total Estimate** | **${subtotal * (1 + self.costs.buffer_percent/100):,.0f}** |")
        lines.append(f"")
        if self.costs.notes:
            for n in self.costs.notes:
                lines.append(f"> 💡 {n}")
            lines.append(f"")

        # Neighborhood
        lines.append(f"## 🏘️ Neighborhood Snapshot")
        if self.neighborhood.nearby_amenities:
            lines.append(f"**Amenities nearby:**")
            for a in self.neighborhood.nearby_amenities:
                lines.append(f"- {a}")
            lines.append(f"")
        if self.neighborhood.grocery_stores:
            lines.append(f"**Grocery:**")
            for g in self.neighborhood.grocery_stores:
                lines.append(f"- {g}")
            lines.append(f"")
        if self.neighborhood.transit_options:
            lines.append(f"**Transit:**")
            for t in self.neighborhood.transit_options:
                lines.append(f"- {t}")
            lines.append(f"")
        if self.neighborhood.parks_greenspace:
            lines.append(f"**Parks & Green Space:**")
            for p in self.neighborhood.parks_greenspace:
                lines.append(f"- {p}")
            lines.append(f"")
        if self.neighborhood.schools_nearby:
            lines.append(f"**Schools:**")
            for s in self.neighborhood.schools_nearby:
                lines.append(f"- {s}")
            lines.append(f"")
        if self.neighborhood.notes:
            for n in self.neighborhood.notes:
                lines.append(f"> 💡 {n}")
            lines.append(f"")

        # Timeline
        lines.append(f"## 📅 Moving Timeline")
        for entry in self.timeline:
            lines.append(f"### {entry.week}")
            for task in entry.tasks:
                lines.append(f"- [ ] {task}")
            lines.append(f"")

        lines.append(f"---")
        lines.append(f"*Generated by MoveMate — your multi-agent relocation assistant*")
        lines.append(f"")

        return "\n".join(lines)