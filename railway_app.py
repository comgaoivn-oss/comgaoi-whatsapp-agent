# CƠM GÀ ƠI - WHATSAPP SALES AGENT (Complete Single File)
# Just copy this entire file to Railway and add environment variables!

import os
from flask import Flask, request
from datetime import datetime

app = Flask(__name__)

# Configuration from environment
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://cfeiyignthbejpwaruzk.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
WHATSAPP_PHONE_ID = os.getenv("WHATSAPP_PHONE_ID", "927300593790248")
WEBHOOK_VERIFY_TOKEN = os.getenv("WEBHOOK_VERIFY_TOKEN", "ComGaOi2024SecureToken")

# Initialize Supabase
supabase = None
try:
    from supabase import create_client
    if SUPABASE_KEY:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✅ Supabase connected!")
except Exception as e:
    print(f"❌ Supabase error: {e}")

# Sales Agent Logic
PLATFORMS = {
    'befood': {'name': 'BeFood', 'url': 'https://begroup.onelink.me/ZOqn/cd7wxjq2', 'emoji': '🟢'},
    'shopeefood': {'name': 'ShopeeFood', 'url': 'https://shopeefood.vn/u/dU8yVzN', 'emoji': '🟠'},
    'xanhsm': {'name': 'Xanh SM', 'url': 'https://xanhsmngon.onelink.me/14WJ/91mmpf5n', 'emoji': '🟢'}
}

def detect_intent(message):
    msg = message.lower()
    if any(w in msg for w in ['menu', 'mon', 'co mon', 'an gi']): return 'menu_inquiry'
    if any(w in msg for w in ['gia', 'bao nhieu', 'price']): return 'price_check'
    if any(w in msg for w in ['dat', 'order', 'mua', 'giao']): return 'order_intent'
    if any(w in msg for w in ['gio', 'mo cua', 'hours']): return 'hours_inquiry'
    if any(w in msg for w in ['dia chi', 'address', 'o dau']): return 'location_inquiry'
    return 'general'

def get_menu_response():
    try:
        result = supabase.table('menu_items').select('*').eq('available', True).execute()
        items = result.data if result.data else []
    except:
        items = []

    if not items:
        return "Menu chua san sang. Vui long thu lai sau!"

    response = "📋 *MENU COM GA OI*\n\n"
    categories = {'com_ga': '🍗 COM GA', 'com_thit': '🥩 COM THIT', 'do_uong': '🥤 DO UONG', 'side_dish': '🍲 MON PHU'}

    grouped = {}
    for item in items:
        cat = item.get('category', 'other')
        if cat not in grouped: grouped[cat] = []
        grouped[cat].append(item)

    for cat, items_list in grouped.items():
        response += f"\n*{categories.get(cat, cat.upper())}*\n"
        for item in items_list:
            price = f"{int(item['base_price']):,}d" if item.get('base_price') else "Lien he"
            response += f"• {item['item_name']} - {price}\n"

    response += "\n📲 *DAT NGAY:*\n"
    for p in PLATFORMS.values():
        response += f"{p['emoji']} {p['name']}: {p['url']}\n"
    return response

def handle_order_intent():
    response = "🛍️ *DAT MON COM GA OI*\n\nBan co the dat mon qua:\n\n"
    for p in PLATFORMS.values():
        response += f"{p['emoji']} *{p['name']}*\n   {p['url']}\n\n"
    response += "Giao hang: 30-45 phut"
    return response

def handle_greeting():
    return '''Xin chao! Chao mung ban den Com Ga Oi! 👋

Toi co the giup ban:
📋 Xem menu
💰 Hoi gia mon an
🛍️ Dat mon
📍 Thong tin lien he

Ban muon gi? Cu hoi nhe! 😊'''

def process_message(phone, message):
    # Log conversation
    if supabase:
        try:
            supabase.table('customer_conversations').insert({
                'customer_phone': phone, 'message_text': message,
                'message_type': 'incoming', 'created_at': datetime.utcnow().isoformat()
            }).execute()
        except: pass

    intent = detect_intent(message)

    if any(g in message.lower() for g in ['hi', 'hello', 'chao']):
        response = handle_greeting()
    elif intent == 'menu_inquiry':
        response = get_menu_response()
    elif intent == 'order_intent':
        response = handle_order_intent()
    elif intent == 'hours_inquiry':
        response = "⏰ *GIO MO CUA*\n\nNha hang mo cua 10:00 - 22:00 hang ngay!"
    elif intent == 'location_inquiry':
        response = "📍 *DIA CHI*\n\nKiem tra tren BeFood, ShopeeFood, Xanh SM!"
    else:
        response = handle_greeting()

    # Log response
    if supabase:
        try:
            supabase.table('customer_conversations').insert({
                'customer_phone': phone, 'message_text': response,
                'message_type': 'outgoing', 'intent': intent,
                'responded': True, 'created_at': datetime.utcnow().isoformat()
            }).execute()
        except: pass

    return response

# Flask Routes
@app.route('/')
def home():
    return {
        "status": "running",
        "service": "Com Ga Oi WhatsApp Sales Agent",
        "supabase_connected": supabase is not None,
        "whatsapp_phone_id": WHATSAPP_PHONE_ID,
        "webhook_url": "/webhook/whatsapp"
    }

@app.route('/webhook/whatsapp', methods=['POST'])
def whatsapp_webhook():
    try:
        data = request.json
        entry = data.get('entry', [{}])[0]
        changes = entry.get('changes', [{}])[0]
        value = changes.get('value', {})

        if 'messages' in value:
            message = value['messages'][0]
            customer_phone = message.get('from')
            text = message.get('text', {}).get('body', '')

            if customer_phone and text:
                response = process_message(customer_phone, text)
                print(f"[{datetime.utcnow().isoformat()}] Response to {customer_phone}: {response[:50]}...")
                return {"status": "success"}, 200

        return {"status": "ok"}, 200
    except Exception as e:
        print(f"[{datetime.utcnow().isoformat()}] Webhook error: {e}")
        return {"status": "error", "message": str(e)}, 500

@app.route('/webhook/whatsapp', methods=['GET'])
def verify_webhook():
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')

    if mode == 'subscribe' and token == WEBHOOK_VERIFY_TOKEN:
        print(f"[{datetime.utcnow().isoformat()}] ✅ Webhook verified!")
        return challenge, 200
    return 'Forbidden', 403

@app.route('/health')
def health():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "supabase": supabase is not None
    }

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    print(f"[{datetime.utcnow().isoformat()}] 🚀 Starting server on port {port}...")
    app.run(host='0.0.0.0', port=port)
