import os
import time
import threading
from datetime import datetime, timedelta
import telebot
from telebot import types
from bot_data import *

BOT_TOKEN = "8303617404:AAG6wuiHY9ssxh1j3jXSoE1DNZ9ZaxYdWI8"
ADMIN_ID = 8917082487
BIKASH_NUMBER = "01909-492665"
POINTS_PER_TAKA = 1
RENEWAL_COST_PER_DAY = 20
WARNING_DAYS = 3

class _NoOpHandler:
    def message_handler(self, *args, **kwargs): return lambda fn: fn
    def callback_query_handler(self, *args, **kwargs): return lambda fn: fn
    def send_message(self, *args, **kwargs): return None
    def send_video(self, *args, **kwargs): return None
    def edit_message_text(self, *args, **kwargs): return None
    def answer_callback_query(self, *args, **kwargs): return None
    def infinity_polling(self, *args, **kwargs): return None

bot = telebot.TeleBot(BOT_TOKEN) if BOT_TOKEN else _NoOpHandler()
user_state = {}

def is_admin(tid): return tid == ADMIN_ID
def get_balance(tid): return 999999999 if is_admin(tid) else (get_bot_user(tid).get("points", 0) if get_bot_user(tid) else 0)
def get_balance_display(tid): return "♾️ Unlimited" if is_admin(tid) else get_balance(tid)

def safe_send(chat_id, text, **kwargs):
    try: return bot.send_message(chat_id, text, parse_mode='Markdown', **kwargs)
    except Exception as e: print(f"send error: {e}")

def safe_edit(chat_id, msg_id, text, **kwargs):
    try: return bot.edit_message_text(text, chat_id, msg_id, parse_mode='Markdown', **kwargs)
    except Exception as e: print(f"edit error: {e}")

def user_main_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add("🖥 File Server", "🚀 API Server", "🌐 HTML Server", "💎 My Points", "➕ Add Points", "📜 History")
    return kb

def admin_main_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add("📊 Statistics", "💰 Pending Verifications", "📦 Manage Plans", "🎥 Manage Videos", "👥 Users List", "🏠 User Mode")
    return kb

def welcome_text(tid): return f"🏠 *আলামিন হোস্টিং এ স্বাগতম!*\n\n💎 আপনার পয়েন্ট: *{get_balance_display(tid)}*\n\nনিচের বাটন থেকে কন্ট্রোল করুন:"
def admin_welcome_text(): return f"👨‍💼 *Admin Control Panel*\n\n💰 Pending Verifications: *{len(get_pending_transactions())}*\n\nনিচের বাটন থেকে কন্ট্রোল করুন:"

def send_category_panel(tid, category):
    cat_names = {"file": "🖥 File Server", "api": "🚀 API Server", "html": "🌐 HTML Server"}
    cat_label = cat_names[category]
    video = get_video(category)
    if video and video.get("file_id"):
        try: bot.send_video(tid, video["file_id"], caption=f"📹 *{cat_label}* — ব্যবহারবিধি", parse_mode='Markdown')
        except: pass

    kb = types.InlineKeyboardMarkup(row_width=1)
    for p in load_plans().get(category, []):
        if category == "file": label = f"{p['id']}. {p['name']} — {p['points']} pts — {p['days']}d\n   🖥 {p['ram']} | 💾 {p['disk']} | ⚙️ {p['cpu_limit']}%"
        elif category == "api": label = f"{p['id']}. {p['name']} — {p['points']} pts — {p['days']}d\n   📱 {p['max_apps']} apps | 🖥 {p['max_ram_mb']}MB | ⚙️ {p['max_cpu']} core"
        else: label = f"{p['id']}. {p['name']} — {p['points']} pts — {p['days']}d\n   🌐 {p['max_sites']} sites"
        kb.add(types.InlineKeyboardButton(label, callback_data=f"plan_{category}_{p['id']}"))
    safe_send(tid, f"🛒 *{cat_label} PLANS*\n\n💎 আপনার পয়েন্ট: *{get_balance_display(tid)}*\nনিচের প্ল্যান থেকে বেছে নিন:", reply_markup=kb)

@bot.message_handler(commands=['start'])
def cmd_start(message):
    tid = message.from_user.id
    if is_admin(tid): return safe_send(tid, admin_welcome_text(), reply_markup=admin_main_menu())
    if not get_bot_user(tid): create_bot_user(tid, message.from_user.username, message.from_user.first_name)
    safe_send(tid, welcome_text(tid), reply_markup=user_main_menu())

@bot.message_handler(func=lambda m: m.text in ["🖥 File Server", "🚀 API Server", "🌐 HTML Server"])
def handle_category(message):
    cat_map = {"🖥 File Server": "file", "🚀 API Server": "api", "🌐 HTML Server": "html"}
    send_category_panel(message.from_user.id, cat_map.get(message.text))

@bot.message_handler(func=lambda m: m.text == "💎 My Points")
def handle_my_points(message):
    tid = message.from_user.id
    user = get_bot_user(tid) or create_bot_user(tid, message.from_user.username, message.from_user.first_name)
    active = sum(1 for s in user.get("servers", []) if not s.get("deleted") and s.get("status") == "active")
    expired = sum(1 for s in user.get("servers", []) if not s.get("deleted") and s.get("status") == "expired")
    text = f"💎 *আপনার পয়েন্ট*\n\n━━━━━━━━━━━━━━\n💰 বর্তমান ব্যালেন্স: *{get_balance_display(tid)}*\n🖥 Active Servers: *{active}*\n⏰ Expired Servers: *{expired}*\n━━━━━━━━━━━━━━"
    safe_send(tid, text)

@bot.message_handler(func=lambda m: m.text == "➕ Add Points")
def handle_add_points(message):
    kb = types.InlineKeyboardMarkup(row_width=2)
    amounts = [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000]
    kb.add(*[types.InlineKeyboardButton(f"{a} pts — {a}৳", callback_data=f"buy_{a}") for a in amounts])
    safe_send(message.chat.id, "💳 *পয়েন্ট কিনুন*\n\n💰 *রেট:* 100 টাকা = 100 পয়েন্ট\n\nকত পয়েন্ট কিনতে চান?", reply_markup=kb)

@bot.message_handler(func=lambda m: m.text == "📜 History")
def handle_history(message):
    tid = message.from_user.id
    transactions = get_user_transactions(tid, limit=15)
    if not transactions: return safe_send(tid, "📜 *History*\n\nএখনো কোনো লেনদেন নেই।")
    user = get_bot_user(tid); servers_map = {s["server_id"]: s for s in user.get("servers", [])}
    safe_send(tid, f"📜 *সর্বশেষ ১৫টি লেনদেন*\n")
    for trx in transactions:
        trx_type = trx.get("type", ""); points = trx.get("points", 0); status = trx.get("status", "")
        if trx_type == "add_points":
            icon = "✅" if status == "approved" else "⏳" if status == "pending" else "❌"
            text = f"{icon} *+{points} points* (Bikash)\n🆔 TrxID: `{trx.get('bikash_trx_id', 'N/A')}`\nStatus: *{status.upper()}*"
        elif trx_type == "spend_server":
            text = f"🖥 *{points} points*\n📦 {trx.get('plan_name', 'Plan')}\n👤 `{trx.get('app_username', 'N/A')}`"
        else: text = f"📝 {trx_type} — {points} pts"
        kb = None
        if trx_type == "spend_server":
            sid = trx.get("server_id", "")
            if sid in servers_map:
                kb = types.InlineKeyboardMarkup(row_width=2)
                kb.add(types.InlineKeyboardButton("📋 Username", callback_data=f"copyuser_{sid}"), types.InlineKeyboardButton("🔑 Password", callback_data=f"copypwd_{sid}"))
        safe_send(tid, text, reply_markup=kb); time.sleep(0.2)

@bot.callback_query_handler(func=lambda c: c.data.startswith("buy_"))
def callback_buy(call):
    points = int(call.data.replace("buy_", "")); taka = points // POINTS_PER_TAKA
    user_state[call.from_user.id] = {"action": "awaiting_sender_number", "data": {"points": points, "taka": taka}}
    bot.answer_callback_query(call.id, "✅")
    safe_edit(call.message.chat.id, call.message.message_id, f"📱 *পেমেন্ট তথ্য*\n\n💰 Amount: *{taka}৳*\n📱 Bikash: `{BIKASH_NUMBER}`\n\n✅ টাকা পাঠিয়ে আপনার *Sender Number* পাঠান")

@bot.message_handler(func=lambda m: m.from_user.id in user_state and user_state[m.from_user.id].get("action") == "awaiting_sender_number")
def capture_sender(message):
    text = message.text.strip()
    if len(text) < 11: return safe_send(message.from_user.id, "⚠️ সঠিক নাম্বার দিন (১১ digit)")
    user_state[message.from_user.id]["data"]["sender_number"] = text
    user_state[message.from_user.id]["action"] = "awaiting_trx_id"
    safe_send(message.from_user.id, f"✅ নাম্বার সেভ হয়েছে।\nএখন *Transaction ID* পাঠান।")

@bot.message_handler(func=lambda m: m.from_user.id in user_state and user_state[m.from_user.id].get("action") == "awaiting_trx_id")
def capture_trxid(message):
    tid = message.from_user.id; text = message.text.strip()
    if len(text) < 4: return safe_send(tid, "⚠️ সঠিক TrxID দিন")
    data = user_state[tid]["data"]; points = data["points"]; sender_clean = ''.join(filter(str.isdigit, data["sender_number"]))[-11:]

    if is_trxid_used(text):
        safe_send(tid, f"❌ *এই TrxID আগে ব্যবহার হয়েছে!*"); del user_state[tid]; return

    # ম্যানুয়াল সিস্টেম: সরাসরি অ্যাডমিনের কাছে পাঠানো হচ্ছে
    trx = create_transaction(tid, "add_points", points, bikash_trx_id=text, sender_number=sender_clean, taka=data["taka"], status="pending")
    del user_state[tid]
    
    safe_send(tid, f"⏳ *ভেরিফাই হচ্ছে...*\nঅ্যাডমিন আপনার পেমেন্ট চেক করে অ্যাপ্রুভ করলে পয়েন্ট যোগ হবে।")
    notify_admin_verification(tid, trx)

@bot.callback_query_handler(func=lambda c: c.data.startswith("plan_"))
def callback_plan(call):
    tid = call.from_user.id; parts = call.data.split("_")
    if len(parts) != 3: return
    category, plan_id = parts[1], int(parts[2]); plan = get_plan(category, plan_id)
    if not plan: return
    if get_balance(tid) < plan["points"]: return bot.answer_callback_query(call.id, "❌ পর্যাপ্ত পয়েন্ট নেই", show_alert=True)
    
    kb = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("✅ Confirm", callback_data=f"confirm_{category}_{plan_id}"), types.InlineKeyboardButton("❌ Cancel", callback_data="cancel_plan"))
    bot.answer_callback_query(call.id)
    safe_edit(call.message.chat.id, call.message.message_id, f"🛒 *Confirm Order*\n🎯 {plan['name']}\n💰 Cost: {plan['points']} points\n\nনিশ্চিত করবেন?", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data == "cancel_plan")
def callback_cancel_plan(call):
    bot.answer_callback_query(call.id, "❌ Cancelled"); safe_edit(call.message.chat.id, call.message.message_id, "❌ *বাতিল*")

@bot.callback_query_handler(func=lambda c: c.data.startswith("confirm_"))
def callback_confirm(call):
    tid = call.from_user.id; parts = call.data.split("_")
    category, plan_id = parts[1], int(parts[2]); plan = get_plan(category, plan_id)
    bot.answer_callback_query(call.id, "⏳ তৈরি হচ্ছে...")
    safe_edit(call.message.chat.id, call.message.message_id, "⏳ *সার্ভার তৈরি হচ্ছে...*")
    if is_admin(tid): add_points(tid, 9999999)
    
    success, result = create_server_from_plan(tid, category, plan)
    if not success: return safe_edit(call.message.chat.id, call.message.message_id, f"❌ *ব্যর্থ:* {result}")

    kb = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("📋 Username", callback_data=f"copyuser_{result['server_id']}"), types.InlineKeyboardButton("🔑 Password", callback_data=f"copypwd_{result['server_id']}"))
    safe_edit(call.message.chat.id, call.message.message_id, f"🎉 *সার্ভার তৈরি!*\n👤 Username: `{result['username']}`\n🔑 Password: `{result['password']}`\n💰 New balance: {get_balance_display(tid)}", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("copyuser_") or c.data.startswith("copypwd_"))
def callback_copy(call):
    kind = "Username" if call.data.startswith("copyuser_") else "Password"; sid = call.data.split("_")[1]
    user = get_bot_user(call.from_user.id)
    for s in (user.get("servers", []) if user else []):
        if s.get("server_id") == sid:
            val = s.get("app_username") if kind == "Username" else s.get("app_password")
            safe_send(call.message.chat.id, f"📋 *{kind}:*\n`{val}`\n\n_টেক্সটে চাপ দিলেই কপি হবে_")
            return bot.answer_callback_query(call.id, "✅ Sent")
    bot.answer_callback_query(call.id, "❌ Not found")

# ---- Admin Section ----
def notify_admin_verification(tid, trx):
    user = get_bot_user(tid)
    kb = types.InlineKeyboardMarkup(row_width=2).add(types.InlineKeyboardButton("✅ Approve", callback_data=f"ap_{trx['id']}"), types.InlineKeyboardButton("❌ Reject", callback_data=f"rj_{trx['id']}"))
    safe_send(ADMIN_ID, f"💰 *NEW PAYMENT*\n👤 {user.get('first_name')} (`{tid}`)\n💎 {trx['points']} pts\n📱 `{trx.get('sender_number', 'N/A')}`\n🆔 `{trx.get('bikash_trx_id', 'N/A')}`", reply_markup=kb)

@bot.message_handler(func=lambda m: is_admin(m.from_user.id) and m.text == "📊 Statistics")
def admin_stats(message):
    users = load_bot_users(); trans = load_transactions()
    sold = sum(t.get("points", 0) for t in trans if t.get("type") == "add_points" and t.get("status") == "approved")
    pend = len([t for t in trans if t.get("type") == "add_points" and t.get("status") == "pending"])
    safe_send(message.chat.id, f"📊 *STATS*\n👥 Users: {len(users)}\n💰 Sold: {sold}৳\n⏳ Pending: {pend}")

@bot.message_handler(func=lambda m: is_admin(m.from_user.id) and m.text == "💰 Pending Verifications")
def admin_pending(message):
    pending = get_pending_transactions()
    if not pending: return safe_send(message.chat.id, "✅ *No pending*")
    for trx in pending[:10]:
        kb = types.InlineKeyboardMarkup(row_width=2).add(types.InlineKeyboardButton("✅ Approve", callback_data=f"ap_{trx['id']}"), types.InlineKeyboardButton("❌ Reject", callback_data=f"rj_{trx['id']}"))
        safe_send(message.chat.id, f"👤 `{trx['telegram_id']}`\n💎 {trx['points']} pts\n📱 `{trx.get('sender_number')}`\n🆔 `{trx.get('bikash_trx_id')}`", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("ap_"))
def callback_approve(call):
    if call.from_user.id != ADMIN_ID: return
    trx = get_transaction(call.data.replace("ap_", ""))
    if trx and trx.get("status") == "pending":
        add_points(trx["telegram_id"], trx["points"])
        update_transaction(trx["id"], status="approved")
        safe_send(trx["telegram_id"], f"✅ *পেমেন্ট সফল!*\n+{trx['points']} পয়েন্ট যোগ হয়েছে।", reply_markup=user_main_menu())
        bot.answer_callback_query(call.id, "✅ Approved")

@bot.callback_query_handler(func=lambda c: c.data.startswith("rj_"))
def callback_reject_menu(call):
    trx_id = call.data.replace("rj_", "")
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("ভুল TrxID", callback_data=f"rjr_{trx_id}_wrong"), types.InlineKeyboardButton("টাকা পাইনি", callback_data=f"rjr_{trx_id}_nomoney"))
    safe_send(call.message.chat.id, "❌ *Reject কারণ?*", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("rjr_"))
def callback_reject_confirm(call):
    parts = call.data.replace("rjr_", "").split("_"); trx_id = parts[0]
    reason = "ভুল TrxID" if parts[1] == "wrong" else "টাকা পাইনি"
    trx = get_transaction(trx_id)
    if trx and trx.get("status") == "pending":
        update_transaction(trx_id, status="rejected", reject_reason=reason)
        safe_send(trx["telegram_id"], f"❌ *ব্যর্থ*\nকারণ: {reason}")

@bot.message_handler(func=lambda m: is_admin(m.from_user.id) and m.text == "👥 Users List")
def admin_users_list(message):
    users = load_bot_users(); text = f"👥 *USERS ({len(users)})*\n\n"
    for u in list(users.values())[:30]: text += f"• `{u['telegram_id']}` — 💎{u.get('points', 0)}\n"
    safe_send(message.chat.id, text)

@bot.message_handler(func=lambda m: is_admin(m.from_user.id) and m.text == "🏠 User Mode")
def back_to_user(message): safe_send(message.chat.id, welcome_text(message.from_user.id), reply_markup=user_main_menu())

def start_bot():
    if not BOT_TOKEN: return
    print("🤖 Bot starting...")
    def send_startup():
        try: bot.send_message(ADMIN_ID, "🚀 *Bot Started!*")
        except: pass
    threading.Thread(target=send_startup, daemon=True).start()
    bot.infinity_polling(timeout=20, long_polling_timeout=20)

if __name__ == '__main__': start_bot()