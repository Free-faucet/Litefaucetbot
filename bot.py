import telebot, time, os
from database import *

# Token dari ENV (Render / hosting)
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 123456789  # ganti dengan Telegram ID kamu
COIN = "LTC"
CLAIM_REWARD = 0.001
REF_BONUS = 0.0005
CLAIM_INTERVAL = 3600  # 1 jam

bot = telebot.TeleBot(BOT_TOKEN)
db = load_db()

@bot.message_handler(commands=["start"])
def start(msg):
    uid = msg.from_user.id
    args = msg.text.split()
    user = get_user(db, uid)

    if len(args) > 1 and user["ref"] is None:
        user["ref"] = args[1]

    save_db(db)

    bot.send_message(uid,
        f"🚧 *LiteFaucetBot (BETA)*\n\n"
        f"💰 Reward masih *pending*\n"
        f"🕒 Claim tiap 1 jam\n"
        f"👥 Referral aktif\n\n"
        f"Gunakan /claim untuk mulai.",
        parse_mode="Markdown"
    )

@bot.message_handler(commands=["claim"])
def claim(msg):
    uid = msg.from_user.id
    user = get_user(db, uid)
    now = time.time()

    if now - user["last_claim"] < CLAIM_INTERVAL:
        sisa = int((CLAIM_INTERVAL - (now - user["last_claim"])) / 60)
        bot.send_message(uid, f"⏳ Tunggu {sisa} menit lagi.")
        return

    user["last_claim"] = now
    user["balance"] += CLAIM_REWARD

    # referral bonus
    if user["ref"] and user["ref"] in db:
        db[user["ref"]]["balance"] += REF_BONUS
        db[user["ref"]]["refs"] += 1

    save_db(db)

    bot.send_message(uid,
        f"✅ Claim sukses!\n"
        f"➕ {CLAIM_REWARD} {COIN} (pending)")

@bot.message_handler(commands=["balance"])
def balance(msg):
    user = get_user(db, msg.from_user.id)
    bot.send_message(msg.from_user.id,
        f"💰 Pending balance: {user['balance']} {COIN}")

@bot.message_handler(commands=["referral"])
def referral(msg):
    uid = msg.from_user.id
    bot.send_message(uid,
        f"👥 Referral link:\n"
        f"https://t.me/LiteFaucetBot?start={uid}\n\n"
        f"Total referral: {get_user(db, uid)['refs']}")

@bot.message_handler(commands=["stats"])
def stats(msg):
    if msg.from_user.id != ADMIN_ID:
        bot.send_message(msg.from_user.id, "❌ Hanya admin")
        return
    bot.send_message(msg.from_user.id,
        f"📊 Statistik Bot\n"
        f"👤 Total user: {len(db)}")

bot.infinity_polling()
