from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
import json, time, os

print("FINAL STABLE VERSION LIVE")

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


# ================= CHECK CHANNEL =================
async def is_joined(user_id, context):
    try:
        member = await context.bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False


# ================= MAIN MENU TEXT =================
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
        users[uid] = {
            "balance": 0,
            "last_claim": 0,
            "pending": False,
            "ref_by": None,
            "ref_earned": 0,
            "claimed_once": False
        }

        if context.args and context.args[0] != "reward":
            referrer = context.args[0]
            if referrer != uid and referrer in users:
                users[uid]["ref_by"] = referrer

        save_users(users)

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
        users[uid] = {
            "balance": 0,
            "last_claim": 0,
            "pending": False,
            "ref_by": None,
            "ref_earned": 0,
            "claimed_once": False
        }

    # ===== BACK TO MENU =====
    if query.data == "menu":
        await query.edit_message_text(
            main_menu_text(),
            reply_markup=main_keyboard()
        )

    # ===== CLAIM =====
    elif query.data == "claim":

        # CHECK CHANNEL
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

        last = users[uid]["last_claim"]

        if now - last < COOLDOWN:
            remaining = (COOLDOWN - (now - last)) // 60
            await query.edit_message_text(
                f"⏳ Cooldown active.\nTry again in {remaining} minutes.",
                reply_markup=back_keyboard()
            )
            return

        users[uid]["pending"] = True
        save_users(users)

        await query.edit_message_text(
            "🎁 Click below to watch ad and claim reward.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🎁 Watch Ad & Claim", url=AD_LINK)],
                [InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")]
            ])
        )

    # ===== BALANCE =====
    elif query.data == "balance":
        bal = users[uid]["balance"]
        await query.edit_message_text(
            f"💰 Your Balance:\n\n{bal:.6f} LTC",
            reply_markup=back_keyboard()
        )

    # ===== REFERRAL =====
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

    # ===== WITHDRAW =====
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

    # ===== RULES =====
    elif query.data == "rules":
        await query.edit_message_text(
            "📜 Rules:\n\n"
            "- One account per user\n"
            "- 60 minutes cooldown\n"
            "- Referral counts first claim only\n"
            "- Must join channel\n"
            "- Abuse = ban",
            reply_markup=back_keyboard()
        )


# ================= MAIN =================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(menu))

    print("Bot running...")
    app.run_polling()


if __name__ == "__main__":
    main()
    
