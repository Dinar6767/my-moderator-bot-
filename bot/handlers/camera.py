"""
Камера наблюдения внутри бота. Только для владельца (ADMIN_IDS).

ВАЖНО: камера есть только у устройства, где запущен бот.
- Бот на ноутбуке → камера ноутбука работает.
- Бот на Railway → камеры нет, команды ответят об этом.

Команды:
    /shot            — фото с камеры
    /clip [секунды]  — видео (по умолчанию 10 сек)
    /cam_on          — включить наблюдение (тревоги при движении)
    /cam_off         — выключить
    /cam_status      — статус
"""
import os
import threading
import time
import datetime

import requests
from aiogram import Router, F
from aiogram.filters import Command, CommandObject
from aiogram.types import BufferedInputFile, FSInputFile, Message

from bot.keyboards.inline import camera_menu
from core.config import (
    ADMIN_IDS,
    BOT_TOKEN,
    CAMERA_SOURCE,
    CAMERA_MIN_AREA,
    CAMERA_SENSITIVITY,
    CAMERA_COOLDOWN,
    CAMERA_CLIP_SECONDS,
)

try:
    import cv2
except ImportError:
    cv2 = None

router = Router()
private = F.chat.type == "private"

MIN_AREA = CAMERA_MIN_AREA
SENSITIVITY = CAMERA_SENSITIVITY

_stop_event = threading.Event()
_thread: threading.Thread | None = None
_owner_id: int | None = None


def _tg_post(method: str, **data):
    return requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/{method}",
        data=data, timeout=30,
    )


def _watch_worker() -> None:
    """Фоновое наблюдение: детекция движения -> фото + видео владельцу."""
    global _owner_id
    cap = cv2.VideoCapture(CAMERA_SOURCE)
    if not cap.isOpened():
        _tg_post("sendMessage", chat_id=_owner_id,
                 text="❌ Камера не открылась. Проверь CAMERA_SOURCE в настройках.")
        return

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    prev = None
    last_alert = 0.0

    while not _stop_event.is_set():
        ok, frame = cap.read()
        if not ok:
            time.sleep(1)
            continue

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)

        if prev is not None:
            diff = cv2.absdiff(prev, gray)
            thresh = cv2.threshold(diff, SENSITIVITY, 255, cv2.THRESH_BINARY)[1]
            thresh = cv2.dilate(thresh, None, iterations=2)
            contours, _ = cv2.findContours(
                thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )
            motion = any(cv2.contourArea(c) > MIN_AREA for c in contours)

            if motion and time.time() - last_alert > CAMERA_COOLDOWN:
                last_alert = time.time()
                stamp = datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")

                ok_j, buf = cv2.imencode(".jpg", frame)
                if ok_j:
                    requests.post(
                        f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto",
                        data={"chat_id": _owner_id,
                              "caption": f"⚠️ <b>Движение!</b>\n{stamp}",
                              "parse_mode": "HTML"},
                        files={"photo": ("cam.jpg", buf.tobytes(), "image/jpeg")},
                        timeout=15,
                    )

                clip_path = f"alert_{datetime.datetime.now():%Y%m%d_%H%M%S}.mp4"
                writer = cv2.VideoWriter(
                    clip_path, cv2.VideoWriter_fourcc(*"mp4v"), 20, (width, height)
                )
                start = time.time()
                while time.time() - start < CAMERA_CLIP_SECONDS \
                        and not _stop_event.is_set():
                    ok_f, f2 = cap.read()
                    if not ok_f:
                        break
                    writer.write(f2)
                writer.release()
                try:
                    with open(clip_path, "rb") as f:
                        requests.post(
                            f"https://api.telegram.org/bot{BOT_TOKEN}/sendVideo",
                            data={"chat_id": _owner_id,
                                  "caption": f"🎥 Клип с тревоги\n{stamp}",
                                  "parse_mode": "HTML"},
                            files={"video": ("alert.mp4", f, "video/mp4")},
                            timeout=90,
                        )
                except Exception:
                    pass
                finally:
                    if os.path.exists(clip_path):
                        os.remove(clip_path)

        prev = gray
        time.sleep(0.02)

    cap.release()


def _is_owner(message: Message) -> bool:
    return message.from_user.id in ADMIN_IDS


async def _need_cv2(message: Message) -> bool:
    if cv2 is None:
        await message.answer(
            "❌ OpenCV не установлен. Выполни: <code>pip install opencv-python</code>"
        )
        return False
    return True


# ---------- Команды ----------

@router.message(Command("cam_on"))
async def cmd_cam_on(message: Message):
    if not _is_owner(message):
        return
    if not await _need_cv2(message):
        return
    global _thread, _owner_id
    if _thread is not None and _thread.is_alive():
        await message.answer("🛡 Наблюдение уже включено.", reply_markup=camera_menu())
        return
    _owner_id = message.chat.id
    _stop_event.clear()
    _thread = threading.Thread(target=_watch_worker, daemon=True)
    _thread.start()
    await message.answer(
        "🛡 <b>Наблюдение включено.</b>\n\nПри движении сюда будут приходить "
        "фото и видеоклипы.\n/cam_off — выключить.",
        reply_markup=camera_menu(),
    )


@router.message(Command("cam_off"))
async def cmd_cam_off(message: Message):
    if not _is_owner(message):
        return
    _stop_event.set()
    await message.answer("🛑 Наблюдение выключено.", reply_markup=camera_menu())


@router.message(Command("shot"))
async def cmd_shot(message: Message):
    if not _is_owner(message):
        return
    if not await _need_cv2(message):
        return
    cap = cv2.VideoCapture(CAMERA_SOURCE)
    if not cap.isOpened():
        await message.answer("❌ Камера не открылась. Проверь CAMERA_SOURCE.")
        return
    ok, frame = cap.read()
    cap.release()
    if not ok:
        await message.answer("❌ Не удалось получить кадр.")
        return
    ok_j, buf = cv2.imencode(".jpg", frame)
    await message.answer_photo(
        BufferedInputFile(buf.tobytes(), filename="cam.jpg"),
        caption="📷 Фото с камеры",
    )


@router.message(Command("clip"))
async def cmd_clip(message: Message, command: CommandObject):
    if not _is_owner(message):
        return
    if not await _need_cv2(message):
        return
    seconds = 10
    if command.args and command.args.strip().isdigit():
        seconds = min(60, max(1, int(command.args.strip())))

    cap = cv2.VideoCapture(CAMERA_SOURCE)
    if not cap.isOpened():
        await message.answer("❌ Камера не открылась. Проверь CAMERA_SOURCE.")
        return
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    path = f"clip_{datetime.datetime.now():%Y%m%d_%H%M%S}.mp4"
    writer = cv2.VideoWriter(path, cv2.VideoWriter_fourcc(*"mp4v"), 20, (width, height))
    start = time.time()
    while time.time() - start < seconds:
        ok, frame = cap.read()
        if not ok:
            break
        writer.write(frame)
    writer.release()
    cap.release()
    await message.answer_video(FSInputFile(path), caption=f"🎥 Видео {seconds} сек")
    if os.path.exists(path):
        os.remove(path)


@router.message(Command("cam_status"))
async def cmd_cam_status(message: Message):
    if not _is_owner(message):
        return
    state = "включено 🛡" if (_thread and _thread.is_alive()) else "выключено"
    cam = "веб-камера (0)" if CAMERA_SOURCE == 0 else str(CAMERA_SOURCE)
    await message.answer(
        f"📷 <b>Статус камеры</b>\n\n"
        f"Источник: {cam}\n"
        f"Наблюдение: {state}\n"
        f"Чувствительность: {SENSITIVITY}\n"
        f"Мин. размер объекта: {MIN_AREA} px\n"
        f"Клип при тревоге: {CAMERA_CLIP_SECONDS} сек"
    )


# ---------- Кнопки меню ----------

@router.message(F.text == "📷 Камера", private)
async def btn_camera(message: Message):
    if not _is_owner(message):
        await message.answer("❌ Только для владельца бота.")
        return
    if not await _need_cv2(message):
        return
    await message.answer(
        "📷 <b>Камера наблюдения</b>\n\nРаботает, пока бот запущен на этом "
        "устройстве. Выберите действие:",
        reply_markup=camera_menu(),
    )


@router.message(F.text == "📷 Фото", private)
async def btn_shot(message: Message):
    await cmd_shot(message)


@router.message(F.text == "🎥 Видео", private)
async def btn_clip(message: Message):
    fake_command = CommandObject(prefix="/", command="clip", mention=None, args="10")
    await cmd_clip(message, fake_command)


@router.message(F.text == "🛡 Вкл. наблюдение", private)
async def btn_cam_on(message: Message):
    await cmd_cam_on(message)


@router.message(F.text == "🛑 Выкл. наблюдение", private)
async def btn_cam_off(message: Message):
    await cmd_cam_off(message)


@router.message(F.text == "ℹ️ Статус камеры", private)
async def btn_cam_status(message: Message):
    await cmd_cam_status(message)
