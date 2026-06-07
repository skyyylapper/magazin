def format_price(price_usdt: float, currency: str = 'USDT', rate: float = None) -> str:
    if currency == 'USDT':
        return f"{price_usdt:.2f} USDT"
    elif currency == 'RUB' and rate:
        return f"{price_usdt * rate:.2f} RUB"
    elif currency == 'USD' and rate:
        return f"{price_usdt * rate:.2f} USD"
    return f"{price_usdt:.2f} USDT"
