import os
import re
import sys
import asyncio
import importlib
import subprocess
from main import OWNER_ID 
from pyrogram.types import Message
from pyrogram import Client, filters
from pyrogram import Client, filters
from typing import Dict, Literal, TypedDict, Optional

URL_RE = re.compile(r"https?://\S+")
REPO_DIR = os.path.dirname(os.path.abspath(__file__))
UPSTREAM_REPO = "https://github.com/Sanchit0102/multifunction.git"
UPSTREAM_BRANCH = "main"

class Cover(TypedDict):
    kind: Literal["file_id", "url"]
    value: str

class PendingVideo(TypedDict):
    video_id: str
    caption: Optional[str]

cover_store: Dict[int, Cover] = {}
pending_video: Dict[int, PendingVideo] = {}


@Client.on_message(filters.command("start"))
async def start_cmd(client, message):
    await message.reply_text("Bot online.")

@Client.on_message(filters.command("reload") & filters.user(OWNER_ID))
async def reload_cmd(client, message):
    msg = await message.reply_text("Syncing from upstream...")

    # Ensure upstream exists
    subprocess.run(
        ["git", "remote", "add", "upstream", UPSTREAM_REPO],
        cwd=REPO_DIR,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    try:
        subprocess.run(
            ["git", "fetch", "upstream"],
            check=True,
            cwd=REPO_DIR,
        )

        subprocess.run(
            ["git", "reset", "--hard", f"upstream/{UPSTREAM_BRANCH}"],
            check=True,
            cwd=REPO_DIR,
        )

    except subprocess.CalledProcessError as e:
        await msg.edit_text(f"Git sync failed:\n{e}")
        return

    reloaded = 0
    for name, module in list(sys.modules.items()):
        file = getattr(module, "__file__", None)
        if not file:
            continue

        try:
            if os.path.commonpath([REPO_DIR, file]) == REPO_DIR:
                importlib.reload(module)
                reloaded += 1
        except:
            pass

    await msg.edit_text(
        "Upstream update applied\n"
        f"Modules reloaded: {reloaded}"
    )


@app.on_message(filters.command("show_cover"))
async def show_cover(_, message: Message):
    user_id = message.from_user.id
    if user_id not in cover_store:
        return await message.reply_text("No cover saved.")
    await app.send_photo(message.chat.id, cover_store[user_id]["value"])

@app.on_message(filters.command("del_cover"))
async def del_cover(_, message: Message):
    cover_store.pop(message.from_user.id, None)
    await message.reply_text("Cover deleted.")

@app.on_message(filters.video))
async def on_video(_, message: Message):
    user_id = message.from_user.id
    video_id = message.video.file_id
    caption = message.caption or ""

    if user_id in cover_store:
        await app.send_video(
            message.chat.id,
            video=video_id,
            cover=cover_store[user_id]["value"],
            caption=caption,
            supports_streaming=True
        )
    else:
        pending_video[user_id] = {"video_id": video_id, "caption": caption}
        await message.reply_text("Send cover image or URL.")

@app.on_message(filters.photo))
async def on_photo(_, message: Message):
    user_id = message.from_user.id
    file_id = message.photo[-1].file_id
    cover_store[user_id] = {"kind": "file_id", "value": file_id}

    if user_id in pending_video:
        pv = pending_video.pop(user_id)
        await app.send_video(
            message.chat.id,
            video=pv["video_id"],
            cover=file_id,
            caption=pv["caption"],
            supports_streaming=True
        )
    else:
        await message.reply_text("Cover saved.")

@app.on_message(filters.text & ~filters.command))
async def on_text(_, message: Message):
    m = URL_RE.search(message.text or "")
    if not m:
        return

    url = m.group(0)
    user_id = message.from_user.id
    cover_store[user_id] = {"kind": "url", "value": url}

    if user_id in pending_video:
        pv = pending_video.pop(user_id)
        await app.send_video(
            message.chat.id,
            video=pv["video_id"],
            cover=url,
            caption=pv["caption"],
            supports_streaming=True
        )
    else:
        await message.reply_text("Cover URL saved.")
