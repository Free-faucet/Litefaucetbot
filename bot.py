from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
import json, time, os

print("FINAL DIRECT CLAIM VERSION ACTIVE")

# ================= CONFIG =================
BOT_TOKEN = os.getenv("BOT_TOKEN")
CLAIM_REWARD = 0.000045
COOLDOWN = 3600
MIN_WITHDRAW = 0.003
REF_PERCENT = 0.07

AD_LINK = "https://free-faucet.github.io/ad.litebotmon/"
CHANNEL_USERNAME = "@litefaucet57"
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


# ================= SECURITY =================
async def is_joined(user_id, context):
    try:
        member = await context.bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False


def create_user(uid):
    users[uid] = {
        "balance": 0,
        "last_claim": 0,
        "pending": False,
        "ref_by": None,
        "ref_earned": 0,
        "claimed_once": False
    }
    save_users(users)


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

        if context.args and context.args[0] != "reward":
            referrer = context.args[0]
            if referrer != uid and referrer in users:
                users[uid]["ref_by"] = referrer
                save_users(users)

    # ===== RETURN FROM AD =====
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

        if not users[uid]["claimed_once"] and users[uid]["ref_by"]:
            ref_id = users[uid]["ref_by"]
            if ref_id in users:
                ref_reward = CLAIM_REWARD * REF_PERCENT
                users[ref_id]["balance"] += ref_reward
                users[ref_id]["ref_earned"] += ref_reward

        users[uid]["claimed_once"] = True
        save_users(users)

        await update.message.reply_text(
            f"✅ Reward received!\n+{CLAIM_REWARD} LTC added."
        )
        return

    await update.message.reply_text(
        main_menu_text(),
        reply_markup=main_keyboard()
    )


# ================= MENU =================
async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    uid = str(query.from_user.id)
    now = int(time.time())

    if uid not in users:
        create_user(uid)

    if query.data == "menu":
        await query.edit_message_text(
            main_menu_text(),
            reply_markup=main_keyboard()
        )

    elif query.data == "claim":

        joined = await is_joined(uid, context)
        if not joined:
            await query.edit_message_text(
                "⚠️ You must join our channel first.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")],
                    [InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")]
                ])
            )
            return

        if now - users[uid]["last_claim"] < COOLDOWN:
            remaining = (COOLDOWN - (now - users[uid]["last_claim"])) // 60
            await query.edit_message_text(
                f"⏳ Cooldown active.\nTry again in {remaining} minutes.",
                reply_markup=back_keyboard()
            )
            return

        users[uid]["pending"] = True
        save_users(users)

        await query.edit_message_text(
            "🎁 Watch Ad & Claim\n\n"
            "🔒 Secure official faucet link\n"
            "You will be redirected safely.\n\n"
            "Click button below to continue:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🎁 Watch Ad & Claim", url=AD_LINK)],
                [InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")]
            ])
        )

    elif query.data == "balance":
        bal = users[uid]["balance"]
        await query.edit_message_text(
            f"💰 Your Balance:\n\n{bal:.6f} LTC",
            reply_markup=back_keyboard()
        )

    elif query.data == "referral":
        bot_username = (await context.bot.get_me()).username
        ref_link = f"https://t.me/{bot_username}?start={uid}"
        earned = users[uid]["ref_earned"]

        await query.edit_message_text(
            f"👥 Referral System\n\n"
            f"Your Link:\n{ref_link}\n\n"
            f"Earnings: {earned:.6f} LTC\n\n"
            "You earn 7% from first claim only.",
            reply_markup=back_keyboard()
        )

    elif query.data == "withdraw":
        bal = users[uid]["balance"]

        if bal < MIN_WITHDRAW:
            await query.edit_message_text(
                f"❌ Minimum withdraw: {MIN_WITHDRAW} LTC\n"
                f"Your balance: {bal:.6f} LTC",
                reply_markup=back_keyboard()
            )
            return

        await query.edit_message_text(
            "💸 FaucetPay withdrawal coming soon.",
            reply_markup=back_keyboard()
        )

    elif query.data == "rules":
        await query.edit_message_text(
            "📜 Rules:\n\n"
            "- One account per Telegram ID\n"
            "- 60 minutes cooldown\n"
            "- Referral counts first claim only\n"
            "- Must join channel\n"
            "- Abuse = permanent ban",
            reply_markup=back_keyboard()
        )


# ================= MAIN =================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(menu))

    print("Bot running stable...")
    app.run_polling()


if __name__ == "__main__":
    main()
                
