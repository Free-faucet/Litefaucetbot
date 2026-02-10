import os, json, time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext

BOT_TOKEN = os.getenv("BOT_TOKEN")

users = {}

def start(update: Update, context: CallbackContext):
    uid = str(update.effective_user.id)
    if uid not in users:
        users[uid] = {"balance": 0, "last": 0}

    keyboard = [
        [InlineKeyboardButton("💰 Claim", callback_data="claim")],
        [InlineKeyboardButton("📊 Balance", callback_data="balance")]
    ]

    update.message.reply_text(
        "LiteFaucetBot hidup ✅",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def menu(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    uid = str(query.from_user.id)
    now = int(time.time())

    if query.data == "claim":
        users[uid]["balance"] += 0.000045
        users[uid]["last"] = now
        query.message.reply_text("✅ Claim sukses")

    elif query.data == "balance":
        query.message.reply_text(f"Balance: {users[uid]['balance']} LTC")

def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(menu))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
