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

print("FINAL ULTRA SECURE V2 ACTIVE")

# ================= CONFIG =================
BOT_TOKEN = os.getenv("BOT_TOKEN")
FAUCETPAY_API = os.getenv("FAUCETPAY_API")

CLAIM_REWARD = 0.000045
REF_PERCENT = 0.07

COOLDOWN = 3600
MIN_WITHDRAW = 0.003

CHANNEL_USERNAME = "@litefaucet57"

AD_LINK = "https://free-faucet.github.io/ad.litebotmon/?uid="
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
        "fp_username": None,
        "waiting_username": False,
        "ref_by": None,
        "ref_earned": 0,
        "claimed_once": False,
        "pending_claim": False,
        "ad_click_time": 0   # TIMER ANTI INSTANT VERIFY
    }
    save_users(users)


# ================= CHANNEL CHECK =================
async def is_joined(user_id, bot):
    try:
        member = await bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False


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
        "Referral: 7% (first claim only)\n"
        "Cooldown: 60 minutes\n"
        f"Min Withdraw: {MIN_WITHDRAW} LTC\n"
        "Withdraw: FaucetPay ONLY\n\n"
        "Status: GLOBAL 🌍"
    )

def main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 Claim LTC", callback_data="claim")],
        [InlineKeyboardButton("📊 Balance", callback_data="balance")],
        [InlineKeyboardButton("👥 Referral", callback_data="referral")],
        [InlineKeyboardButton("💸 Withdraw", callback_data="withdraw")],
        [InlineKeyboardButton("⚙️ Set FaucetPay Username", callback_data="setfp")],
    ])

def back_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")]
    ])


# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    now = int(time.time())

    if uid not in users:
        create_user(uid)

    if context.args:
        arg = context.args[0]

        # ================= VERIFY CLAIM =================
        if arg.startswith("verify_"):
            verify_id = arg.split("_")[1]

            if verify_id == uid and users[uid]["pending_claim"]:

                # 🔒 15 SECOND MINIMUM STAY CHECK
                if now - users[uid]["ad_click_time"] < 15:
                    await update.message.reply_text(
                        "⚠️ Please stay on the advertisement page at least 15 seconds."
                    )
                    return

                # ⏳ COOLDOWN CHECK
                if now - users[uid]["last_claim"] < COOLDOWN:
                    await update.message.reply_text("⏳ Cooldown active.")
                    return

                users[uid]["balance"] += CLAIM_REWARD
                users[uid]["last_claim"] = now
                users[uid]["pending_claim"] = False

                # REF BONUS (FIRST CLAIM ONLY)
                if not users[uid]["claimed_once"]:
                    users[uid]["claimed_once"] = True
                    ref_id = users[uid]["ref_by"]
                    if ref_id and ref_id in users:
                        bonus = CLAIM_REWARD * REF_PERCENT
                        users[ref_id]["balance"] += bonus
                        users[ref_id]["ref_earned"] += bonus

                save_users(users)

                await update.message.reply_text(
                    f"✅ Claim successful!\n+{CLAIM_REWARD} LTC added.",
                    reply_markup=main_keyboard()
                )
                return

        # ================= REF SYSTEM =================
        if arg in users and arg != uid:
            users[uid]["ref_by"] = arg
            save_users(users)

    await update.message.reply_text(
        main_menu_text(),
        reply_markup=main_keyboard()
    )


# ================= HANDLE TEXT =================
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)

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

    # ================= CLAIM =================
    if query.data == "claim":

        if not await is_joined(query.from_user.id, context.bot):
            await query.edit_message_text(
                f"⚠️ You must join {CHANNEL_USERNAME} first!",
                reply_markup=back_keyboard()
            )
            return

        if now - users[uid]["last_claim"] < COOLDOWN:
            remaining = (COOLDOWN - (now - users[uid]["last_claim"])) // 60
            await query.edit_message_text(
                f"⏳ Cooldown active.\nTry again in {remaining} minutes.",
                reply_markup=back_keyboard()
            )
            return

        users[uid]["pending_claim"] = True
        users[uid]["ad_click_time"] = now  # START TIMER
        save_users(users)

        ad_url = f"{AD_LINK}{uid}"

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔗 View Advertisement", url=ad_url)],
            [InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")]
        ])

        await query.edit_message_text(
            "📢 Click the link below and stay at least 15 seconds.\n\n"
            "You will be redirected back automatically after finishing.",
            reply_markup=keyboard
        )

    # ================= BALANCE =================
    elif query.data == "balance":
        bal = users[uid]["balance"]
        await query.edit_message_text(
            f"💰 Your Balance:\n\n{bal:.6f} LTC",
            reply_markup=back_keyboard()
        )

    # ================= REFERRAL =================
    elif query.data == "referral":
        bot_username = (await context.bot.get_me()).username
        ref_link = f"https://t.me/{bot_username}?start={uid}"
        earned = users[uid]["ref_earned"]

        await query.edit_message_text(
            f"👥 Your Referral Link:\n{ref_link}\n\n"
            f"💰 Total Earned: {earned:.6f} LTC",
            reply_markup=back_keyboard()
        )

    # ================= SET USERNAME =================
    elif query.data == "setfp":
        users[uid]["waiting_username"] = True
        save_users(users)

        await query.edit_message_text(
            "Please send your FaucetPay username:",
            reply_markup=back_keyboard()
        )

    # ================= WITHDRAW =================
    elif query.data == "withdraw":

        bal = users[uid]["balance"]

        if bal < MIN_WITHDRAW:
            await query.edit_message_text(
                f"❌ Minimum withdraw: {MIN_WITHDRAW} LTC\n"
                f"Your balance: {bal:.6f} LTC\n\n"
                "Don't have a FaucetPay account?\n"
                f"Register here:\n{FAUCETPAY_REGISTER}",
                reply_markup=back_keyboard()
            )
            return

        username = users[uid]["fp_username"]

        if not username:
            await query.edit_message_text(
                "⚠️ Please set your FaucetPay username first.\n\n"
                f"Register here:\n{FAUCETPAY_REGISTER}",
                reply_markup=back_keyboard()
            )
            return

        success, message = send_withdraw(username, bal)

        if success:
            users[uid]["balance"] = 0
            save_users(users)

            await query.edit_message_text(
                f"✅ Withdraw successful!\n"
                f"Sent {bal:.6f} LTC to {username}",
                reply_markup=back_keyboard()
            )
        else:
            await query.edit_message_text(
                f"❌ Withdraw failed:\n{message}",
                reply_markup=back_keyboard()
            )

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

    print("Bot running ULTRA SECURE V2...")
    app.run_polling()


if __name__ == "__main__":
    main()
