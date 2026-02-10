from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
import json, time, os

# ================= CONFIG =================
BOT_TOKEN = "ISI_TOKEN_BOT_KAMU"
CLAIM_REWARD = 0.000045
COOLDOWN = 3600  # 1 hour
AD_BASE_URL = "https://ISI_LINK_IKLAN_KAMU/ad?uid="
# ==========================================

# Load users
def load_users():
    if not os.path.exists("users.json"):
        return {}
    with open("users.json", "r") as f:
        return json.load(f)

def save_users(data):
    with open("users.json", "w") as f:
        json.dump(data, f)

users = load_users()

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)

    if uid not in users:
        users[uid] = {
            "balance": 0,
            "last_claim": 0
        }
        save_users(users)

    keyboard = [
        [InlineKeyboardButton("💰 Claim LTC", callback_data="claim")],
        [InlineKeyboardButton("📊 Balance", callback_data="balance")],
        [InlineKeyboardButton("📜 Rules", callback_data="rules")]
    ]

    await update.message.reply_text(
        "🚀 Welcome to LiteFaucetBot\n\n"
        "Earn free Litecoin every hour.\n"
        "Complete a short ad to claim.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ================= MENU =================
async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    uid = str(query.from_user.id)
    now = int(time.time())

    if query.data == "claim":
        last = users[uid]["last_claim"]

        if now - last < COOLDOWN:
            remaining = COOLDOWN - (now - last)
            minutes = remaining // 60
            await query.message.reply_text(
                f"⏳ Cooldown active.\nTry again in {minutes} minutes."
            )
            return

        ad_link = AD_BASE_URL + uid
        await query.message.reply_text(
            "🔔 Complete this ad to receive your reward:\n\n"
            f"{ad_link}"
        )

    elif query.data == "balance":
        bal = users[uid]["balance"]
        await query.message.reply_text(f"💰 Your balance: {bal} LTC")

    elif query.data == "rules":
        await query.message.reply_text(
            "📜 Rules:\n"
            "- 1 account per user\n"
            "- Cooldown: 60 minutes\n"
            "- FaucetPay only (later)\n"
            "- Abuse = ban"
        )

# ================= CALLBACK (MANUAL TEST) =================
async def reward(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    users[uid]["balance"] += CLAIM_REWARD
    users[uid]["last_claim"] = int(time.time())
    save_users(users)

    await update.message.reply_text(
        f"✅ Reward added!\nYou received {CLAIM_REWARD} LTC"
    )

# ================= MAIN =================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reward", reward))  # sementara manual
    app.add_handler(CallbackQueryHandler(menu))

    app.run_polling()

if __name__ == "__main__":
    main()

