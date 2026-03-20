import logging
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler
from config.settings import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

# 로깅 설정
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

class TelegramManager:
    def __init__(self):
        self.application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
        self.bot = self.application.bot

    async def send_message(self, text, parse_mode='Markdown', reply_markup=None):
        """대표님께 메시지 발송"""
        return await self.bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=text,
            parse_mode=parse_mode,
            reply_markup=reply_markup
        )

    async def send_photo(self, photo_path, caption=None, reply_markup=None):
        """대표님께 이미지 발송"""
        with open(photo_path, 'rb') as photo:
            return await self.bot.send_photo(
                chat_id=TELEGRAM_CHAT_ID,
                photo=photo,
                caption=caption,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )

    async def build_approval_buttons(self, task_id):
        """승인/거절 버튼 생성"""
        keyboard = [
            [
                InlineKeyboardButton("✅ 승인", callback_data=f"approve_{task_id}"),
                InlineKeyboardButton("❌ 거절", callback_data=f"reject_{task_id}")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)

# 싱글톤 인스턴스 (옵션)
# manager = TelegramManager()
