import telebot
import requests
import time
import os
from threading import Thread
from flask import Flask

# ================= WEB SERVER (ALIVE) =================
app = Flask('')

@app.route('/')
def home():
    return "🚀 KKG ULTRA BOT IS ACTIVE"

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# ================= BOT CONFIG =================
API_TOKEN = '8399569164:AAFKEWRpao4oZgjer_BYZEBRZUt5wuiec-I'
MY_CHAT_ID = '-1003214557813'

GAME_RESULT_URL = "https://www.k082.com/m/lotto-thai-h5/lgw/draw/46402?page=0&size=50"

bot = telebot.TeleBot(API_TOKEN)

LAST_PREDICTED_ISSUE = None
LAST_PREDICTION = None

# ================= STATS =================
history_list = []
total_win = 0
total_lose = 0
current_streak = 0
max_win_streak = 0
max_lose_streak = 0

SUMMARY_INTERVAL = 10

# ================= UTILS =================
def get_size(num):
    try:
        val = int(num)
        return "SMALL" if val <= 4 else "BIG"
    except:
        return "SMALL"

# ================= FETCH DATA =================
def fetch_data():
    try:
        headers = {
            "Accept": "application/json, text/plain, */*",
            "Authorization": "a9f3bd7b-a421-403e-9d66-4997fb24800b",
            "Merchant": "kgmmkf7",
            "language": "EN",
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://www.k082.com/m/lotto-thai-h5/",
            "Origin": "https://www.k082.com"
        }

        r = requests.get(GAME_RESULT_URL, headers=headers, timeout=15)
        data = r.json()
        return data.get("content", [])[:10]
    except Exception as e:
        print("❌ Fetch Error:", e)
        return []

# ================= PREDICTION ENGINE =================
def pro_predict(results):
    if not results:
        return "SMALL", 50

    sizes = [get_size(x["winNo"]) for x in results]
    last_5 = "".join([s[0] for s in sizes[:5]][::-1])

    patterns = {
      "BSBSB": "SMALL", "SBSBS": "BIG", "SSBBS": "SMALL", "BBSSB": "BIG",
        "SSSBB": "BIG", "BBBSS": "SMALL", "BSSBS": "SMALL", "SBBSB": "BIG",
        "BSSSB": "SMALL", "SBBBS": "BIG", "SBBSS": "BIG", "BSSBB": "SMALL",
        "BBSBB": "SMALL", "SSBSS": "BIG", "SBBBB": "BIG", "BSSSS": "SMALL",
        "SSSSB": "SMALL", "BBBBS": "SMALL", "SSSBS": "SMALL", "BBBSB": "BIG",
        "SBSSB": "SMALL", "BSBBS": "BIG", "BBBBB": "BIG", "SSSSS": "SMALL"    }

    if last_5 in patterns:
        return patterns[last_5], 98

    return ("BIG" if sizes.count("BIG") <= 4 else "SMALL"), 75

# ================= SUMMARY =================
def send_last_10_summary():
    last10 = history_list[-SUMMARY_INTERVAL:]

    win = sum(1 for x in last10 if x["icon"] == "✅")
    lose = SUMMARY_INTERVAL - win
    rate = round((win / SUMMARY_INTERVAL) * 100, 1)

    msg = "📋 *LAST 10 ROUNDS SUMMARY*\n\n"
    msg += "`Issue | Pred | Result`\n"
    msg += "━━━━━━━━━━━━━━━\n"

    for h in last10:
        arrow = "B->B" if h["pred"] == "BIG" and h["actual"] == "BIG" else \
                "S->S" if h["pred"] == "SMALL" and h["actual"] == "SMALL" else \
                "B->S" if h["pred"] == "BIG" else "S->B"

        color = "🟢" if h["actual"] == "BIG" else "🔴"
        msg += f"`{h['issue']} | {arrow} | {color} {h['icon']}`\n"

    msg += "━━━━━━━━━━━━━━━\n"
    msg += f"✅ WIN: {win} | ❌ LOSE: {lose}\n"
    msg += f"📈 Rate: {rate}%\n"
                  
    bot.send_message(MY_CHAT_ID, msg, parse_mode="Markdown")

# ================= MAIN MONITOR =================
def start_monitoring():
    global LAST_PREDICTED_ISSUE, LAST_PREDICTION
    global total_win, total_lose, current_streak
    global max_win_streak, max_lose_streak

    print("✅ Monitoring Started...")

    while True:
        data = fetch_data()
        if not data:
            time.sleep(10)
            continue

        latest_issue = str(data[0]["numero"])

        # ===== RESULT CHECK =====
        if LAST_PREDICTED_ISSUE == latest_issue:
            actual = get_size(data[0]["winNo"])
            win = (actual == LAST_PREDICTION)
            icon = "✅" if win else "❌"

            if win:
                total_win += 1
                current_streak = current_streak + 1 if current_streak > 0 else 1
                max_win_streak = max(max_win_streak, current_streak)
            else:
                total_lose += 1
                current_streak = current_streak - 1 if current_streak < 0 else -1
                max_lose_streak = max(max_lose_streak, abs(current_streak))

            history_list.append({
                "issue": latest_issue,
                "pred": LAST_PREDICTION,
                "actual": actual,
                "icon": icon
            })

            bot.send_message(
                MY_CHAT_ID,
                f"📊 *RESULT*\nPeriod: `{latest_issue}`\n"
                f"Outcome: *{actual}* ({data[0]['winNo']}) {icon}",
                parse_mode="Markdown"
            )

            if len(history_list) % SUMMARY_INTERVAL == 0:
                send_last_10_summary()

            LAST_PREDICTED_ISSUE = None

        # ===== NEXT PREDICTION =====
        if LAST_PREDICTED_ISSUE is None:
            next_issue = str(int(latest_issue) + 1)
            pred, conf = pro_predict(data)

            msg = (
                   f"🔮 *KKG WINGO PRO SIGNAL *\n"
                f"᳀┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉᳀\n"
                f"🆔 Period: `{next_issue}`\n"
                f"🎯 Prediction: *{pred}*\n"
                f"🔥 Accuracy: `{conf}%` \n"
                f"📣 Note: 4 ဇဆောင်ပါ။🧠\n"
                f"👽 Developer: 𝙈𝙧. 𝐊 𝐄 𝐋 𝐕 𝐈 𝐍 🏈۞\n\n"
                f" 🛸 Stats: Waiting For Result...\n" f"᳀┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉᳀"
            )

            bot.send_message(MY_CHAT_ID, msg, parse_mode="Markdown")
            LAST_PREDICTED_ISSUE = next_issue
            LAST_PREDICTION = pred

        time.sleep(5)

# ================= START =================
if __name__ == "__main__":
    try:
        bot.send_message(MY_CHAT_ID, "🚀 KKG ULTRA BOT STARTED (PRO VERSION READY TO START !)")
    except:
        print("❌ Telegram Error")

    Thread(target=run_web_server).start()
    start_monitoring()