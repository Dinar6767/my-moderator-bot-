from aiocaptcha import CaptchaManager, SqliteCaptchaStorage, CaptchaOptions


def setup_captcha(dp):
    """Подключает капчу к диспетчеру.

    Вызывать ДО регистрации роутеров, чтобы капча перехватывала все сообщения
    новых пользователей.
    """
    storage = SqliteCaptchaStorage("captcha.sqlite3")

    options = CaptchaOptions(
        prompt_text="👋 Чтобы писать в чат, подтвердите, что вы человек: нажмите {target}",
        passed_text="✅ Проверка пройдена! Добро пожаловать.",
        pool=("🐶", "🐱", "🐭", "🐹", "🐰", "🦊", "🐻", "🐼"),
        choices=4,
        ttl_seconds=120,
    )

    captcha = CaptchaManager(storage=storage, options=options)
    captcha.setup(dp)