from database.models import add_warning

MAX_WARNINGS = 3


async def warn_user(user_id: int) -> tuple[int, bool]:
    count = await add_warning(user_id)
    return count, count >= MAX_WARNINGS