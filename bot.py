import os
import logging
import json
from typing import Dict, Any, Optional
from datetime import datetime

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    WebAppInfo,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove
)
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
    CallbackQueryHandler,
    ConversationHandler
)

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Токен бота
BOT_TOKEN = "8568340261:AAE18eYPuhqrDBkOhqnNJMHyURvEVedBxYA"

# Состояния для ConversationHandler
SELECTING_ACTION, TYPING_REFERRAL = range(2)


class FruNoBot:
    def __init__(self):
        self.user_data = {}

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик команды /start"""
        user = update.effective_user
        user_id = user.id

        # Первое сообщение - пост о возможностях бота (без Markdown)
        welcome_post = (
            "🌟 Что умеет этот бот?\n\n"
            "Добро пожаловать в FRUNO — сервис свежих орехов и сухофруктов!\n\n"
            "📦 Собирайте боксы по вашим предпочтениям\n"
            "🔄 Оформляйте подписку с выгодой до 15%\n"
            "🎁 Копите бонусы и оплачивайте ими заказы\n"
            "👥 Приглашайте друзей и получайте подарки\n"
            "📱 Удобное приложение прямо в Telegram\n\n"
            "Подписывайтесь на наш канал: @fruno_channel"
        )

        keyboard = [
            [InlineKeyboardButton("📱 Открыть приложение", web_app=WebAppInfo(url="https://gleb1.b3654yy2.beget.tech/"))],
            [InlineKeyboardButton("🎁 Получить 500 бонусов", callback_data="get_bonus")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            welcome_post,
            reply_markup=reply_markup
        )

    async def handle_web_app_data(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработка данных из Mini App"""
        try:
            data = json.loads(update.effective_message.web_app_data.data)
            user_id = update.effective_user.id

            # Обработка различных типов данных из Mini App
            action = data.get('action')

            if action == 'order_created':
                await self._handle_order_creation(update, context, data)
            elif action == 'subscription_created':
                await self._handle_subscription_creation(update, context, data)
            elif action == 'support_message':
                await self._handle_support_message(update, context, data)

        except Exception as e:
            logger.error(f"Error processing web app data: {e}")
            await update.message.reply_text("❌ Произошла ошибка при обработке данных")

    async def _handle_order_creation(self, update: Update, context: ContextTypes.DEFAULT_TYPE, data: Dict) -> None:
        """Обработка создания заказа из Mini App"""
        order_id = data.get('order_id')
        total_amount = data.get('total_amount')
        delivery_date = data.get('delivery_date')

        order_message = (
            "✅ Заказ создан!\n\n"
            f"📦 Номер заказа: #{order_id}\n"
            f"💰 Сумма: {total_amount} руб.\n"
            f"📅 Доставка: {delivery_date}\n\n"
            "Мы свяжемся с вами для подтверждения заказа."
        )

        await update.message.reply_text(order_message)

    async def _handle_subscription_creation(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                                            data: Dict) -> None:
        """Обработка создания подписки из Mini App"""
        subscription_type = data.get('type')
        discount = data.get('discount')
        next_delivery = data.get('next_delivery')

        subscription_message = (
            "🔄 Подписка оформлена!\n\n"
            f"📦 Тип: {subscription_type}\n"
            f"🎯 Скидка: {discount}%\n"
            f"📅 Следующая доставка: {next_delivery}\n\n"
            "Вы можете управлять подпиской в разделе «Мой аккаунт»"
        )

        await update.message.reply_text(subscription_message)

    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик нажатий на inline кнопки"""
        query = update.callback_query
        await query.answer()

        user_id = query.from_user.id

        if query.data == "get_bonus":
            await self._give_welcome_bonus(query, context)
        elif query.data == "open_app":
            await self._open_mini_app(query, context)
        elif query.data == "support":
            await self._handle_support_request(query, context)
        elif query.data == "check_order":
            await self._check_last_order(query, context)

    async def _give_welcome_bonus(self, query, context):
        """Выдача приветственных бонусов"""
        user_id = query.from_user.id

        # Проверяем, получал ли пользователь уже бонусы
        if user_id not in self.user_data:
            self.user_data[user_id] = {'bonuses': 500, 'bonus_received': True}

            bonus_message = (
                "🎉 Поздравляем!\n\n"
                "Вам начислено 500 бонусных рублей!\n\n"
                "Используйте их при оформлении первого заказа.\n"
                "1 бонус = 1 рубль скидки"
            )

            keyboard = [
                [InlineKeyboardButton("📱 Открыть приложение", web_app=WebAppInfo(url="https://gleb1.b3654yy2.beget.tech/"))]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_text(bonus_message, reply_markup=reply_markup)
        else:
            await query.edit_message_text(
                "❌ Вы уже получали приветственные бонусы"
            )

    async def _open_mini_app(self, query, context):
        """Открытие Mini App"""
        keyboard = [
            [InlineKeyboardButton("📱 Открыть FRUNO", web_app=WebAppInfo(url="https://gleb1.b3654yy2.beget.tech/"))]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            "Нажмите кнопку ниже чтобы открыть приложение:",
            reply_markup=reply_markup
        )

    async def _handle_support_request(self, query, context):
        """Обработка запроса в поддержку"""
        support_message = (
            "🛠 Служба поддержки FRUNO\n\n"
            "📧 Email: support@fruno.ru\n"
            "📞 Телефон: +7 (999) 123-45-67\n"
            "🕒 Время работы: 9:00-21:00\n\n"
            "Также вы можете написать нам прямо из приложения в разделе «Поддержка»"
        )

        await query.edit_message_text(support_message)

    async def _check_last_order(self, query, context):
        """Проверка последнего заказа"""
        order_info = "📦 Ваш последний заказ\n\nЗаказ №12345 от 2024-01-15\nСтатус: Доставлен\n\nИспользуйте приложение для просмотра полной истории."

        keyboard = [
            [InlineKeyboardButton("📱 Открыть приложение", web_app=WebAppInfo(url="https://gleb1.b3654yy2.beget.tech/"))]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(order_info, reply_markup=reply_markup)

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик текстовых сообщений"""
        message_text = update.message.text.lower()

        if any(word in message_text for word in ['привет', 'start', 'начать']):
            await self._send_welcome_message(update)
        elif any(word in message_text for word in ['бонус', 'bonus']):
            await self._send_bonus_info(update)
        elif any(word in message_text for word in ['заказ', 'order']):
            await self._send_order_info(update)
        elif any(word in message_text for word in ['поддержка', 'support']):
            await self._send_support_info(update)
        else:
            await self._send_default_response(update)

    async def _send_welcome_message(self, update):
        """Отправка приветственного сообщения"""
        welcome_text = (
            "👋 Добро пожаловать в FRUNO!\n\n"
            "Я помогу вам:\n"
            "• Собрать идеальный бокс орехов и сухофруктов\n"
            "• Оформить подписку с выгодой до 15%\n"
            "• Использовать бонусы и приглашать друзей\n\n"
            "Откройте приложение чтобы начать:"
        )

        keyboard = [
            [InlineKeyboardButton("📱 Открыть FRUNO", web_app=WebAppInfo(url="https://gleb1.b3654yy2.beget.tech/"))]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(welcome_text, reply_markup=reply_markup)

    async def _send_bonus_info(self, update):
        """Информация о бонусах"""
        bonus_text = (
            "🎁 Бонусная программа FRUNO\n\n"
            "• 500 бонусов за регистрацию\n"
            "• 5% от суммы каждого заказа\n"
            "• 500 бонусов за приглашенного друга\n"
            "• 1 бонус = 1 рубль\n\n"
            "Баланс бонусов и история доступны в приложении."
        )

        keyboard = [
            [InlineKeyboardButton("📱 Открыть приложение", web_app=WebAppInfo(url="https://gleb1.b3654yy2.beget.tech/"))]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(bonus_text, reply_markup=reply_markup)

    async def _send_order_info(self, update):
        """Информация о заказах"""
        order_text = (
            "📦 История заказов\n\n"
            "В приложении вы можете:\n"
            "• Посмотреть историю заказов\n"
            "• Повторить любой предыдущий заказ\n"
            "• Управлять активными подписками\n"
            "• Отслеживать статус доставки"
        )

        keyboard = [
            [InlineKeyboardButton("📱 Открыть приложение", web_app=WebAppInfo(url="https://gleb1.b3654yy2.beget.tech/"))]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(order_text, reply_markup=reply_markup)

    async def _send_support_info(self, update):
        """Информация о поддержке"""
        support_text = (
            "🛠 Служба поддержки\n\n"
            "📧 Email: support@fruno.ru\n"
            "📞 Телефон: +7 (999) 123-45-67\n"
            "🕒 Время работы: 9:00-21:00\n\n"
            "Для быстрой помощи используйте раздел «Поддержка» в приложении."
        )

        await update.message.reply_text(support_text)

    async def _send_default_response(self, update):
        """Ответ по умолчанию"""
        default_text = (
            "Я пока не умею отвечать на сложные вопросы 😊\n\n"
            "Лучше откройте приложение - там вы сможете:\n"
            "• Собрать бокс орехов и сухофруктов\n"
            "• Оформить заказ или подписку\n"
            "• Посмотреть бонусы и историю заказов\n"
            "• Написать в поддержку"
        )

        keyboard = [
            [InlineKeyboardButton("📱 Открыть FRUNO", web_app=WebAppInfo(url="https://gleb1.b3654yy2.beget.tech/"))]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(default_text, reply_markup=reply_markup)

    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик ошибок"""
        logger.error(msg="Exception while handling an update:", exc_info=context.error)

        # Уведомление пользователя об ошибке
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "❌ Произошла непредвиденная ошибка. Пожалуйста, попробуйте позже."
            )


def main() -> None:
    """Запуск бота"""
    bot = FruNoBot()

    # Создание Application
    application = Application.builder().token(BOT_TOKEN).build()

    # Добавление обработчиков
    application.add_handler(CommandHandler("start", bot.start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_message))
    application.add_handler(CallbackQueryHandler(bot.button_handler))

    # Обработчик данных из Web App
    application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, bot.handle_web_app_data))

    # Обработчик ошибок
    application.add_error_handler(bot.error_handler)

    # Запуск бота
    print("Бот FRUNO запущен...")
    application.run_polling()


if __name__ == "__main__":
    main()
