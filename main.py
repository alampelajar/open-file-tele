import asyncio
import html
import logging
import os
import re
import uuid
from pathlib import Path

from dotenv import load_dotenv
from telethon import TelegramClient, events
from telethon.errors import FloodWaitError

load_dotenv()

API_ID_VALUE = os.getenv("API_ID", "").strip()
API_HASH = os.getenv("API_HASH", "").strip()

if not API_ID_VALUE.isdigit() or not API_HASH:
    raise SystemExit(
        "API_ID/API_HASH belum diisi. Salin .env.example menjadi .env "
        "dan isi dari https://my.telegram.org"
    )

API_ID = int(API_ID_VALUE)
BASE_DIR = Path(__file__).resolve().parent
DOWNLOAD_DIR = BASE_DIR / "downloads"
DOWNLOAD_DIR.mkdir(exist_ok=True)

PREVIEW_LINES = 100
PREVIEW_MAX_CHARS = 2800
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
TELEGRAM_TEXT_LIMIT = 3900

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("telegram-open")

client = TelegramClient(
    str(BASE_DIR / "telegram_open_session"),
    API_ID,
    API_HASH,
)


def format_size(size: int) -> str:
    if size < 1024:
        return f"{size} B"
    if size < 1024**2:
        return f"{size / 1024:.1f} KB"
    return f"{size / (1024**2):.2f} MB"


def read_text_file(path: Path) -> str:
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="replace")


def build_preview(lines: list[str]) -> tuple[str, int]:
    """Return numbered preview text and the number of source lines shown."""
    output: list[str] = []
    used = 0
    shown = 0

    for number, line in enumerate(lines[:PREVIEW_LINES], start=1):
        numbered = f"{number:>4}. {line}"
        # Account for newline separators. Truncate a single very long line too.
        remaining = PREVIEW_MAX_CHARS - used
        if remaining <= 0:
            break

        if len(numbered) > remaining:
            if remaining > 8:
                numbered = numbered[: remaining - 3] + "..."
                output.append(numbered)
                shown += 1
            break

        output.append(numbered)
        used += len(numbered) + 1
        shown += 1

    return "\n".join(output), shown


@client.on(events.NewMessage(
    outgoing=True,
    pattern=re.compile(r"^\.open\s*$", re.IGNORECASE),
))
async def open_document(event):
    replied = await event.get_reply_message()
    if not replied:
        await event.reply(
            "Balas pesan yang berisi file <code>.txt</code> dengan "
            "<code>.open</code>.",
            parse_mode="html",
        )
        return

    document = getattr(replied, "document", None)
    if not document:
        await event.reply("Pesan yang dibalas bukan dokumen.")
        return

    file_name = next(
        (
            attr.file_name
            for attr in (document.attributes or [])
            if getattr(attr, "file_name", None)
        ),
        "document.txt",
    )

    if Path(file_name).suffix.lower() != ".txt":
        await event.reply("Format tidak didukung. Gunakan file .txt.")
        return

    if document.size and document.size > MAX_FILE_SIZE:
        await event.reply(
            f"File terlalu besar. Maksimal {format_size(MAX_FILE_SIZE)}."
        )
        return

    local_path = DOWNLOAD_DIR / f"{uuid.uuid4().hex}.txt"
    status = await event.reply("⏳ Sedang membuka file...")

    try:
        downloaded = await replied.download_media(file=str(local_path))
        if not downloaded:
            await status.edit("Gagal mengunduh file dari Telegram.")
            return

        path = Path(downloaded)
        if not path.is_file():
            await status.edit("File tidak ditemukan setelah diunduh.")
            return
        if path.stat().st_size > MAX_FILE_SIZE:
            await status.edit("File melewati batas ukuran 10 MB.")
            return

        content = read_text_file(path)
        lines = content.splitlines()
        line_count = len(lines)
        total_chars = len(content)
        preview, shown_lines = build_preview(lines)
        preview_chars = len(preview)
        safe_name = html.escape(Path(file_name).name)

        # Format metadata as a compact Info / Value table, similar to the example.
        metadata = (
            "<b>📂 Open</b>\n\n"
            "<pre>"
            "Info       | Value\n"
            "───────────┼────────────────────────\n"
            f"📄 File     | {safe_name}\n"
            f"📦 Ukuran   | {format_size(path.stat().st_size)}\n"
            f"🔢 Baris    | {line_count:,}\n"
            "🖥 Syntax   | text"
            "</pre>"
            f"\n🔖 Preview dipotong: {preview_chars:,} dari "
            f"{total_chars:,} karakter."
        )
        await status.edit(metadata, parse_mode="html")

        if not lines:
            await event.reply("📄 File kosong atau tidak memiliki teks.")
            return

        # Keep filename and preview in a separate, readable message.
        preview_message = (
            f"<b>📄 {safe_name}</b>\n"
            f"<pre>{html.escape(preview)}</pre>"
        )
        await event.reply(preview_message, parse_mode="html")

        if line_count > shown_lines:
            await event.reply(
                f"… Preview menampilkan {shown_lines} baris pertama "
                f"(maksimal {PREVIEW_LINES} baris dan "
                f"{PREVIEW_MAX_CHARS:,} karakter)."
            )

    except FloodWaitError as exc:
        logger.warning("Telegram meminta jeda %s detik.", exc.seconds)
        await status.edit(
            f"Terlalu banyak permintaan. Coba lagi dalam {exc.seconds} detik."
        )
    except Exception:
        logger.exception("Gagal memproses file.")
        await status.edit(
            "Terjadi kesalahan saat membaca file. Periksa log terminal."
        )
    finally:
        try:
            local_path.unlink(missing_ok=True)
        except OSError:
            logger.warning("Gagal menghapus file sementara.")


async def main():
    await client.start()
    me = await client.get_me()
    print("=" * 50)
    print("Telegram .open Userbot aktif")
    print(f"Akun: {me.first_name}")
    print(f"Username: @{me.username}" if me.username else "Username: -")
    print("Cara pakai: balas pesan dokumen TXT dengan .open")
    print("Tekan Ctrl+C untuk berhenti.")
    print("=" * 50)
    await client.run_until_disconnected()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nUserbot dihentikan.")
