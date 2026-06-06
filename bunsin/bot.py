"""
분신 봇 — 텔레그램 ⇄ 판단엔진 v1 ⇄ SQLite 큐

쓰는 법:
  - 그냥 파편을 텍스트로 던지면  → 분신이 점수 매겨 큐에 넣고 즉시 회신
  - /now    → 지금 할 거 1개 + 이유
  - /queue  → 점수순 전체 큐
  - /brief  → 아침 브리핑
  - /done <id>  → 완료 처리
  - /cut  <id>  → 손으로 컷
"""

import asyncio
import os

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

import db
import engine

OWNER_CHAT_ID = os.environ.get("OWNER_CHAT_ID")  # 비우면 누구나 사용 가능(비권장)

TAG_EMOJI = {"딜": "💼", "사업": "🚀", "공모전": "🏆", "본업": "🏢", "기타": "📌"}


def _owner_only(update: Update) -> bool:
    if not OWNER_CHAT_ID:
        return True
    return str(update.effective_chat.id) == str(OWNER_CHAT_ID)


def _line(row) -> str:
    emoji = TAG_EMOJI.get(row["tag"], "📌")
    auto = " 🔧자동화먼저" if row["auto"] else ""
    return f"{emoji} <b>{row['title']}</b>  ({row['score']}점·{row['tag']}){auto}\n    └ {row['reason']}"


async def on_fragment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _owner_only(update):
        return
    fragment = update.message.text.strip()
    if not fragment:
        return

    await context.bot.send_chat_action(update.effective_chat.id, "typing")
    try:
        item = await asyncio.to_thread(engine.evaluate, fragment)
    except Exception as e:  # noqa: BLE001
        await update.message.reply_text(f"⚠️ 판단 실패: {e}")
        return

    item_id = db.add(item, fragment)

    if item["cut"]:
        gate = "복리로 안 쌓임" if item["gate_a"] == "cut" else "나 없으면 못 굴러감"
        await update.message.reply_text(
            f"🚫 컷 (#{item_id}) — {gate}\n    └ {item['reason']}",
            parse_mode=ParseMode.HTML,
        )
        return

    top = db.top()
    auto = " 🔧(자동화 먼저 깔고)" if item["auto"] else ""
    msg = (
        f"✅ 큐에 넣음 #{item_id} — {item['score']}점·{item['tag']}{auto}\n"
        f"    └ {item['reason']}\n\n"
        f"👑 지금 TOP: {_line(top)}"
    )
    await update.message.reply_text(msg, parse_mode=ParseMode.HTML)


async def cmd_now(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _owner_only(update):
        return
    top = db.top()
    if not top:
        await update.message.reply_text("큐 비었음. 파편 던지면 채워짐.")
        return
    await update.message.reply_text(
        f"👉 지금 이거:\n\n{_line(top)}", parse_mode=ParseMode.HTML
    )


async def cmd_queue(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _owner_only(update):
        return
    rows = db.open_queue()
    if not rows:
        await update.message.reply_text("큐 비었음.")
        return
    body = "\n".join(f"#{r['id']}  {_line(r)}" for r in rows)
    await update.message.reply_text(f"📋 <b>현재 큐</b> (점수순)\n\n{body}", parse_mode=ParseMode.HTML)


async def cmd_brief(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _owner_only(update):
        return
    rows = db.open_queue(limit=5)
    if not rows:
        await update.message.reply_text("☀️ 오늘 큐 비었음. 깨끗한 출발.")
        return
    body = "\n".join(f"{i+1}. {_line(r)}" for i, r in enumerate(rows))
    await update.message.reply_text(
        f"☀️ <b>아침 브리핑</b> — 오늘 이 순서로\n\n{body}\n\n"
        f"먼저 1번부터. /now 로 언제든 다시 확인.",
        parse_mode=ParseMode.HTML,
    )


async def _mark_cmd(update, context, status, verb):
    if not _owner_only(update):
        return
    if not context.args:
        await update.message.reply_text(f"사용법: /{verb} <번호>")
        return
    try:
        item_id = int(context.args[0].lstrip("#"))
    except ValueError:
        await update.message.reply_text("번호는 숫자로.")
        return
    ok = db.mark(item_id, status)
    await update.message.reply_text(
        f"{'✅ 완료' if status == 'done' else '🚫 컷'} 처리: #{item_id}" if ok else f"#{item_id} 못 찾음."
    )


async def cmd_done(update, context):
    await _mark_cmd(update, context, "done", "done")


async def cmd_cut(update, context):
    await _mark_cmd(update, context, "cut", "cut")


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👑 분신 가동.\n\n"
        "그냥 파편을 던져. (예: '레드문 CB 만기 체크')\n"
        "→ 점수 매겨 큐에 넣고 TOP 알려줌.\n\n"
        "/now 지금 할 거 · /queue 전체 큐 · /brief 아침 브리핑\n"
        "/done <번호> 완료 · /cut <번호> 컷\n\n"
        f"네 chat_id: {update.effective_chat.id}  (← .env의 OWNER_CHAT_ID 에 넣어 잠가)"
    )


def main():
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    db.init()
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("now", cmd_now))
    app.add_handler(CommandHandler("queue", cmd_queue))
    app.add_handler(CommandHandler("brief", cmd_brief))
    app.add_handler(CommandHandler("done", cmd_done))
    app.add_handler(CommandHandler("cut", cmd_cut))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_fragment))
    print("분신 봇 가동 중… (Ctrl+C 로 종료)")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
