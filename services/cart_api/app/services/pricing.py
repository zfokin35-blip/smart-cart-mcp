def recalc_total(items) -> float:
    return round(sum(i.qty * i.unit_price for i in items), 2)
