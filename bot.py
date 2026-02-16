from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)
import json, time, os, requests

print("FINAL SECURE WFD VERSION ACTIVE")

# ================= CONFIG =================
BOT_TOKEN = os.getenv("BOT_TOKEN")
FAUCETPAY_API = os.getenv("FAUCETPAY_API")

CLAIM_REWARD = 0.000045
COOLDOWN = 3600
MIN_WITHDRAW = 0.003
WITHDRAW_COOLDOWN = 86400

CHANNEL_USERNAME = "@litefaucet57"

FAUCETPAY_REGISTER = "https://faucetpay.io/?r=502868"
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


def create_user(uid):
    users[uid] = {
        "balance": 0,
        "last_claim": 0,
        "last_withdraw": 0,
        "fp_username": None,
        "waiting_username": False
    }
    save_users(users)


# ================= FAUCETPAY =================
def send_withdraw(username, amount):
    url = "https://faucetpay.io/api/v1/send"

    payload = {
        "api_key": FAUCETPAY_API,
        "amount": amount,
        "currency": "LTC",
        "to": username
    }

    try:
        response = requests.post(url, data=payload, timeout=15)
        result = response.json()

        if result.get("status") == 200:
            return True, result.get("message")
        else:
            return False, result.get("message")

    except Exception as e:
        return False, str(e)


# ================= UI =================
def main_menu_text():
    return (
        "🚀 LiteFaucetBot LIVE\n\n"
        "Coin: Litecoin (LTC)\n"
        f"Reward: {CLAIM_REWARD} LTC per claim\n"
        "Cooldown: 60 minutes\n"
        f"Min Withdraw: {MIN_WITHDRAW} LTC\n"
        "Withdraw: FaucetPay ONLY\n\n"
        "Status: GLOBAL 🌍"
    )

def main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 Claim LTC", callback_data="claim")],
        [InlineKeyboardButton("📊 Balance", callback_data="balance")],
        [InlineKeyboardButton("💸 Withdraw", callback_data="withdraw")],
        [InlineKeyboardButton("⚙️ Set FaucetPay Username", callback_data="setfp")],
        [InlineKeyboardButton("📜 Rules", callback_data="rules")]
    ])

def back_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")]
    ])


# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)

    if uid not in users:
        create_user(uid)

    await update.message.reply_text(
        main_menu_text(),
        reply_markup=main_keyboard()
    )


# ================= HANDLE TEXT INPUT =================
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)

    if uid not in users:
        create_user(uid)

    if users[uid]["waiting_username"]:
        username = update.message.text.strip()

        users[uid]["fp_username"] = username
        users[uid]["waiting_username"] = False
        save_users(users)

        await update.message.reply_text(
            f"✅ FaucetPay username saved:\n{username}"
        )


# ================= MENU =================
async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    uid = str(query.from_user.id)
    now = int(time.time())

    if uid not in users:
        create_user(uid)

    # CLAIM
    if query.data == "claim":

        if now - users[uid]["last_claim"] < COOLDOWN:
            remaining = (COOLDOWN - (now - users[uid]["last_claim"])) // 60
            await query.edit_message_text(
                f"⏳ Cooldown active.\nTry again in {remaining} minutes.",
                reply_markup=back_keyboard()
            )
            return

        users[uid]["balance"] += CLAIM_REWARD
        users[uid]["last_claim"] = now
        save_users(users)

        await query.edit_message_text(
            f"✅ Claim successful!\n+{CLAIM_REWARD} LTC added.",
            reply_markup=back_keyboard()
        )

    # BALANCE
    elif query.data == "balance":
        bal = users[uid]["balance"]
        await query.edit_message_text(
            f"💰 Your Balance:\n\n{bal:.6f} LTC",
            reply_markup=back_keyboard()
        )

    # SET FAUCETPAY USERNAME
    elif query.data == "setfp":
        users[uid]["waiting_username"] = True
        save_users(users)

        await query.edit_message_text(
            "Please send your FaucetPay username:",
            reply_markup=back_keyboard()
        )

    # WITHDRAW
    elif query.data == "withdraw":

        bal = users[uid]["balance"]

        if bal < MIN_WITHDRAW:
            await query.edit_message_text(
                f"❌ Minimum withdraw: {MIN_WITHDRAW} LTC\n"
                f"Your balance: {bal:.6f} LTC\n\n"
                "⚠️ FaucetPay account required for withdrawals.\n\n"
                "Don't have one yet?\n"
                f"Create your FREE account here:\n{FAUCETPAY_REGISTER}",
                reply_markup=back_keyboard()
            )
            return

        if now - users[uid]["last_withdraw"] < WITHDRAW_COOLDOWN:
            remaining = (WITHDRAW_COOLDOWN - (now - users[uid]["last_withdraw"])) // 3600
            await query.edit_message_text(
                f"⛔ Withdraw allowed once per 24 hours.\n"
                f"Try again in {remaining} hours.",
                reply_markup=back_keyboard()
            )
            return

        username = users[uid]["fp_username"]

        if not username:
            await query.edit_message_text(
                "⚠️ Please set your FaucetPay username first.\n\n"
                "Don't have a FaucetPay account?\n"
                f"Register here:\n{FAUCETPAY_REGISTER}",
                reply_markup=back_keyboard()
            )
            return

        success, message = send_withdraw(username, bal)

        if success:
            users[uid]["balance"] = 0
            users[uid]["last_withdraw"] = now
            save_users(users)

            await query.edit_message_text(
                f"✅ Withdraw successful!\n"
                f"Sent {bal:.6f} LTC to {username}",
                reply_markup=back_keyboard()
            )
        else:
            await query.edit_message_text(
                f"❌ Withdraw failed:\n{message}\n\n"
                "Need a FaucetPay account?\n"
                f"Register here:\n{FAUCETPAY_REGISTER}",
                reply_markup=back_keyboard()
            )

    # BACK TO MENU
    elif query.data == "menu":
        await query.edit_message_text(
            main_menu_text(),
            reply_markup=main_keyboard()
        )


# ================= MAIN =================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(menu))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("Bot running secure...")
    app.run_polling()


if __name__ == "__main__":
    main()
