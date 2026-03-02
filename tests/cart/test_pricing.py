import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
module_path = ROOT / "services" / "cart_api" / "app" / "services" / "pricing.py"
spec = importlib.util.spec_from_file_location("pricing", module_path)
pricing = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pricing)


def test_recalc_total_rounding():
    class Item:
        def __init__(self, qty: int, unit_price: float):
            self.qty = qty
            self.unit_price = unit_price

    items = [Item(2, 10.105), Item(1, 5.0)]
    assert pricing.recalc_total(items) == 25.21
