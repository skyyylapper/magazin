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

'ru': {
    ...
    'topup_choose_method': "Выберите способ пополнения:",
    'enter_topup_amount': "Введите сумму в USDT:",
    'manual_topup_instruction': "Отправьте USDT (TRC20) на адрес:",
    'manual_topup_after_send': "После отправки нажмите «Я отправил» и укажите сумму и хэш транзакции.",
    'enter_amount_usdt': "Введите сумму в USDT:",
    'enter_txid': "Введите хэш транзакции (TXID):",
    'invalid_amount': "❌ Некорректная сумма. Введите число больше 0.",
    'manual_topup_created': "✅ Заявка на пополнение {amount} USDT создана.\nОжидайте проверки.",
    'support_contact': "По вопросам: @{username}",
    'antispam_blocked': "⛔ Вы создали слишком много заявок. Попробуйте позже.",
},
'en': {
    ...
    'topup_choose_method': "Choose top-up method:",
    'enter_topup_amount': "Enter amount in USDT:",
    'manual_topup_instruction': "Send USDT (TRC20) to address:",
    'manual_topup_after_send': "After sending, press 'I sent' and enter amount and transaction hash.",
    'enter_amount_usdt': "Enter amount in USDT:",
    'enter_txid': "Enter transaction hash (TXID):",
    'invalid_amount': "❌ Invalid amount. Enter a number greater than 0.",
    'manual_topup_created': "✅ Top-up request for {amount} USDT created.\nWait for admin check.",
    'support_contact': "Contact: @{username}",
    'antispam_blocked': "⛔ You have created too many requests. Try later.",
}

def get_text(key: str, lang: str = 'ru') -> str:
    return _.get(lang, _['ru']).get(key, key)
