from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from states.topup_states import ManualTopupState
from database import get_user, create_manual_topup
from send_integration import create_send_invoice
from utils.anti_spam import check_antispam, increment_invoice_count
from translations import get_text
from config import ADMIN_USERNAME, MANUAL_WALLET_ADDRESS

router = Router()

@router.callback_query(F.data == "topup")
async def topup_menu(callback: CallbackQuery, lang: str = 'ru'):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚡ Автоматически (через @send)", callback_data="auto_topup")],
        [InlineKeyboardButton(text="💳 Вручную (по адресу)", callback_data="manual_topup_start")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="profile")]
    ])
    await callback.message.edit_text(get_text('topup_choose_method', lang), reply_markup=kb)
    await callback.answer()

@router.callback_query(F.data == "auto_topup")
async def auto_topup_start(callback: CallbackQuery, state: FSMContext, lang: str = 'ru'):
    user_id = callback.from_user.id
    if not await check_antispam(user_id):
        await callback.answer(get_text('antispam_blocked', lang), show_alert=True)
        return
    await state.set_state(ManualTopupState.waiting_amount)
    await state.update_data(method='auto')
    await callback.message.edit_text(get_text('enter_topup_amount', lang))
    await callback.answer()

@router.callback_query(F.data == "manual_topup_start")
async def manual_topup_start(callback: CallbackQuery, state: FSMContext, lang: str = 'ru'):
    user_id = callback.from_user.id
    if not await check_antispam(user_id):
        await callback.answer(get_text('antispam_blocked', lang), show_alert=True)
        return
    await callback.message.edit_text(
        f"💳 {get_text('manual_topup_instruction', lang)}\n\n"
        f"`{MANUAL_WALLET_ADDRESS}`\n\n"
        f"{get_text('manual_topup_after_send', lang)}",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Я отправил", callback_data="manual_topup_submit")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="topup")]
        ])
    )
    await callback.answer()

@router.callback_query(F.data == "manual_topup_submit")
async def manual_topup_form(callback: CallbackQuery, state: FSMContext, lang: str = 'ru'):
    await callback.message.edit_text(get_text('enter_amount_usdt', lang))
    await state.set_state(ManualTopupState.waiting_amount)
    await callback.answer()

@router.message(ManualTopupState.waiting_amount)
async def process_amount(message: Message, state: FSMContext, lang: str = 'ru'):
    data = await state.get_data()
    method = data.get('method')
    try:
        amount = float(message.text.strip())
        if amount <= 0:
            raise ValueError
        if method == 'auto':
            user_id = message.from_user.id
            invoice_id, pay_url = await create_send_invoice(user_id, amount, "Пополнение баланса")
            if invoice_id:
                await message.answer(
                    f"💳 Счёт создан на сумму {amount} USDT.\n"
                    f"Ссылка для оплаты: {pay_url}\n\n"
                    "После оплаты баланс пополнится автоматически в течение 1-2 минут."
                )
                await increment_invoice_count(user_id)
            else:
                await message.answer("❌ Ошибка при создании счёта. Попробуйте позже.")
        else:
            await state.update_data(amount=amount)
            await message.answer(get_text('enter_txid', lang))
            await state.set_state(ManualTopupState.waiting_txid)
            return
        await state.clear()
    except ValueError:
        await message.answer(get_text('invalid_amount', lang))

@router.message(ManualTopupState.waiting_txid)
async def process_txid(message: Message, state: FSMContext, lang: str = 'ru'):
    txid = message.text.strip()
    data = await state.get_data()
    amount = data['amount']
    user_id = message.from_user.id
    await create_manual_topup(user_id, amount, MANUAL_WALLET_ADDRESS, txid)
    await increment_invoice_count(user_id)
    await message.answer(
        f"✅ Заявка на пополнение {amount} USDT создана.\n"
        f"Ожидайте проверки администратором (обычно до 24 часов).\n\n"
        f"По вопросам: @{ADMIN_USERNAME}"
    )
    await state.clear()
