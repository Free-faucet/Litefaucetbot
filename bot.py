from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
import json, time, os

print("FINAL VERSION REF SYSTEM ACTIVE")

# ================= CONFIG =================
BOT_TOKEN = os.getenv("BOT_TOKEN")
CLAIM_REWARD = 0.000045
COOLDOWN = 3600
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

    # Register new user
    if uid not in users:
        users[uid] = {
            "balance": 0,
            "last_claim": 0,
            "pending": False,
            "ref_by": None,
            "ref_earned": 0,
            "claimed_once": False
        }

        # Referral system
        if context.args:
            referrer = context.args[0]
            if referrer != uid and referrer in users:
                users[uid]["ref_by"] = referrer

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

        # Give reward
        users[uid]["balance"] += CLAIM_REWARD
        users[uid]["last_claim"] = now
        users[uid]["pending"] = False

        # Referral reward (ONLY first claim)
        if not users[uid]["claimed_once"] and users[uid]["ref_by"]:
            ref_id = users[uid]["ref_by"]
            ref_reward = CLAIM_REWARD * REF_PERCENT

            users[ref_id]["balance"] += ref_reward
            users[ref_id]["ref_earned"] += ref_reward

        users[uid]["claimed_once"] = True
        save_users(users)

        await update.message.reply_text(
            f"✅ Reward received!\n"
            f"+{CLAIM_REWARD} LTC added."
        )
        return

    # Main Menu
    keyboard = [
        [InlineKeyboardButton("💰 Claim LTC", callback_data="claim")],
        [InlineKeyboardButton("📊 Balance", callback_data="balance")],
        [InlineKeyboardButton("👥 Referral", callback_data="referral")],
        [InlineKeyboardButton("💸 Withdraw", callback_data="withdraw")],
        [InlineKeyboardButton("📜 Rules", callback_data="rules")]
    ]

    await update.message.reply_text(
        "🚀 LiteFaucetBot LIVE\n\n"
        "Coin: Litecoin (LTC)\n"
        "Reward: 0.000045 LTC per claim\n"
        "Referral: 7% (first claim only)\n"
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

    # CLAIM
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
            "1️⃣ Click link\n"
            "2️⃣ Watch full ad\n"
            "3️⃣ Return to Telegram\n\n"
            f"{AD_LINK}"
        )

    # BALANCE
    elif query.data == "balance":
        bal = users[uid]["balance"]
        await query.message.reply_text(f"💰 Balance: {bal:.6f} LTC")

    # REFERRAL
    elif query.data == "referral":
        bot_username = (await context.bot.get_me()).username
        ref_link = f"https://t.me/{bot_username}?start={uid}"
        earned = users[uid]["ref_earned"]

        await query.message.reply_text(
            f"👥 Your Referral Link:\n{ref_link}\n\n"
            f"Referral Earnings: {earned:.6f} LTC\n\n"
            "You earn 7% when your referral claims first time."
        )

    # WITHDRAW
    elif query.data == "withdraw":
        bal = users[uid]["balance"]

        if bal < MIN_WITHDRAW:
            await query.message.reply_text(
                f"❌ Minimum withdraw: {MIN_WITHDRAW} LTC\n"
                f"Your balance: {bal:.6f} LTC"
            )
            return

        await query.message.reply_text(
            "💸 FaucetPay withdrawal coming soon."
        )

    # RULES
    elif query.data == "rules":
        await query.message.reply_text(
            "📜 Rules:\n"
            "- One account per user\n"
            "- 60 minutes cooldown\n"
            "- Referral only counts first claim\n"
            "- Abuse = ban"
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
