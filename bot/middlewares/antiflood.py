import time
from collections import defaultdict
from aiogram import BaseMiddleware
from aiogram.types import Message


class AntiFloodMiddleware(BaseMiddleware):
    def __init__(self, max_messages: int = 5, window: int = 10):
        self.max_messages = max_messages
        self.window = window
        self.history: dict[int, list[float]] = defaultdict(list)

    async def __call__(self, handler, event: Message, data):
        if not isinstance(event, Message) or event.chat.type == "private":
            return await handler(event, data)

        user_id = event.from_user.id
        now = time.time()
        self.history[user_id] = [t for t in self.history[user_id] if now - t < self.window]

        if len(self.history[user_id]) >= self.max_messages:
            try:
                await event.delete()
            except Exception:
                pass
            return

        self.history[user_id].append(now)
        return await handler(event, data)