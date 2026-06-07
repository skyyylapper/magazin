# Словари переводов (RU и EN)
_ = {
    'ru': {
        'welcome': "Добро пожаловать в магазин!",
        'catalog': "🛍 Каталог",
        'balance': "💰 Баланс",
        'support': "🆘 Поддержка",
        'cart': "🛒 Корзина",
        'profile': "👤 Профиль",
        'referral': "👥 Реферальная система",
        # ... и так далее
    },
    'en': {
        'welcome': "Welcome to the shop!",
        'catalog': "🛍 Catalog",
        'balance': "💰 Balance",
        'support': "🆘 Support",
        'cart': "🛒 Cart",
        'profile': "👤 Profile",
        'referral': "👥 Referral system",
    }
}

def get_text(key: str, lang: str = 'ru') -> str:
    return _.get(lang, _['ru']).get(key, key)
