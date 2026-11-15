import pytest

from inventory import Item, cheapest, format_price, total_value


def test_total_value():
    items = [Item("mug", 1250, 4), Item("pen", 199, 10)]
    assert total_value(items) == 6990


def test_format_price():
    assert format_price(6990) == "$69.90"


def test_cheapest_empty_raises_value_error():
    with pytest.raises(ValueError):
        cheapest([])
