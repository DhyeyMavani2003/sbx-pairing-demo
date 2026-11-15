"""Tiny inventory module used to demo agent tooling."""
from dataclasses import dataclass


@dataclass
class Item:
    name: str
    price_cents: int
    quantity: int


def total_value(items: list[Item]) -> int:
    """Return the total stock value in cents."""
    return sum(item.price_cents * item.quantity for item in items)


def format_price(cents: int) -> str:
    return f"${cents / 100:.2f}"


def cheapest(items: list[Item]) -> Item:
    return min(items, key=lambda i: i.price_cents)
