import re
from aiogram import BaseMiddleware
from aiogram.types import Message

SPAM_PATTERNS = [
    r"t\.me/\+",
    r"(?i)казино|casino|ставк[иа]",
    r"(?i)заработ[ао]к\s+от\s+\d+",
]


class AntiSpamMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: Message, data):
        if not isinstance(event, Message):
            return await handler(event, data)

        if not event.text:
            return await handler(event, data)

        # ЛОГ: показываем текст каждого сообщения
        print(f"[ANTISPAM] chat={event.chat.type} text={event.text!r}")

        for pattern in SPAM_PATTERNS:
            if re.search(pattern, event.text):
                print(f"[ANTISPAM] MATCH pattern={pattern}")
                try:
                    await event.delete()
                    print("[ANTISPAM] deleted")
                except Exception as e:
                    print(f"[ANTISPAM] delete failed: {e}")
                return

        return await handler(event, data)