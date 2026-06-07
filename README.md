# Telegram Shop Bot with @send and referral system

## Setup
1. Create virtual environment: `python -m venv venv`
2. Activate: `source venv/bin/activate` (Windows: `venv\Scripts\activate`)
3. Install: `pip install -r requirements.txt`
4. Copy `.env.example` to `.env` and fill in tokens, API keys, admin IDs, etc.
5. Run: `python main.py`

## Features
- User bot: catalog, cart, balance, referral (50% of deposit), auto topup via @send, manual topup with admin approval.
- Admin bot: manage products, users, partners, manual topups, withdrawal requests.
- Partner bot: view own earnings, referral link, request withdrawal.
- Antispam, multi-currency (USDT/RUB/USD), bilingual (RU/EN).
