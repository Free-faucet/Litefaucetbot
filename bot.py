from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
import json, time, os

# ================= CONFIG =================
BOT_TOKEN = os.getenv("BOT_TOKEN")
CLAIM_REWARD = 0.000045
COOLDOWN = 3600  # 60 minutes
MIN_WITHDRAW = 0.003
AD_LINK = "https://free-faucet.github.io/ad.litebotmon/"
# ==========================================

# ================= DATABASE =================
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
            "last_claim": 0,
            "pending": False
        }
        save_users(users)

    # ===== REWARD RETURN FROM AD =====
    if context.args and context.args[0] == "reward":

        if not users[uid]["pending"]:
            await update.message.reply_text("❌ No pending reward.")
            return

        now = int(time.time())
        if now - users[uid]["last_claim"] < COOLDOWN:
            await update.message.reply_text("⏳ Cooldown still active.")
            return

        users[uid]["balance"] += CLAIM_REWARD
        users[uid]["last_claim"] = now
        users[uid]["pending"] = False
        save_users(users)

        await update.message.reply_text(
            f"✅ Reward received!\n"
            f"+{CLAIM_REWARD} LTC added to your balance."
        )
        return

    keyboard = [
        [InlineKeyboardButton("💰 Claim LTC", callback_data="claim")],
        [InlineKeyboardButton("📊 Balance", callback_data="balance")],
        [InlineKeyboardButton("💸 Withdraw", callback_data="withdraw")],
        [InlineKeyboardButton("📜 Rules", callback_data="rules")]
    ]

    await update.message.reply_text(
        "🚀 LiteFaucetBot LIVE\n\n"
        "Coin: Litecoin (LTC)\n"
        "Reward: 0.000045 LTC per claim\n"
        "Cooldown: 60 minutes\n"
        "Min Withdraw: 0.003 LTC\n"
        "Withdraw: FaucetPay ONLY\n\n"
        "Status: GLOBAL 🌍",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ================= MENU =================
async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    uid = str(query.from_user.id)
    now = int(time.time())

    # ===== CLAIM =====
    if query.data == "claim":
        last = users[uid]["last_claim"]

        if now - last < COOLDOWN:
            remaining = (COOLDOWN - (now - last)) // 60
            await query.message.reply_text(
                f"⏳ Cooldown active.\nTry again in {remaining} minutes."
            )
            return

        users[uid]["pending"] = True
        save_users(users)

        await query.message.reply_text(
            "🔔 To receive your reward:\n\n"
            "1️⃣ Click the link below\n"
            "2️⃣ Watch the full ad\n"
            "3️⃣ Return to Telegram\n\n"
            f"{AD_LINK}"
        )

    # ===== BALANCE =====
    elif query.data == "balance":
        bal = users[uid]["balance"]
        await query.message.reply_text(f"💰 Your balance: {bal:.6f} LTC")

    # ===== WITHDRAW =====
    elif query.data == "withdraw":
        bal = users[uid]["balance"]

        if bal < MIN_WITHDRAW:
            await query.message.reply_text(
                f"❌ Minimum withdraw is {MIN_WITHDRAW} LTC\n"
                f"Your balance: {bal:.6f} LTC"
            )
            return

        await query.message.reply_text(
            "💸 Withdrawal system coming soon.\n"
            "FaucetPay integration will be enabled next update."
        )

    # ===== RULES =====
    elif query.data == "rules":
        await query.message.reply_text(
            "📜 Rules:\n"
            "- One account per user\n"
            "- 60 minutes cooldown\n"
            "- FaucetPay withdrawals only\n"
            "- Abuse or multi-account = ban"
        )

# ================= MAIN =================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(menu))

    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
