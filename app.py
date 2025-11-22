# CƠM GÀ ƠI - WHATSAPP SALES AGENT (Complete Single File)
# Just copy this entire file to Railway and add environment variables!

import os
import requests
from flask import Flask, request
from datetime import datetime

app = Flask(__name__)

# Configuration from environment
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://cfeiyignthbejpwaruzk.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
WHATSAPP_PHONE_ID = os.getenv("WHATSAPP_PHONE_ID", "927300593790248")
WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
WEBHOOK_VERIFY_TOKEN = os.getenv("WEBHOOK_VERIFY_TOKEN", "ComGaOi2024SecureToken")

# Initialize Supabase with DEBUG
supabase = None
print("=" * 50)
print(f"[DEBUG] SUPABASE_URL: {SUPABASE_URL}")
print(f"[DEBUG] SUPABASE_KEY exists: {bool(SUPABASE_KEY)}")
print(f"[DEBUG] SUPABASE_KEY length: {len(SUPABASE_KEY) if SUPABASE_KEY else 0}")
print(f"[DEBUG] SUPABASE_KEY first 20 chars: {SUPABASE_KEY[:20] if SUPABASE_KEY else 'EMPTY'}")
print(f"[DEBUG] WEBHOOK_VERIFY_TOKEN: {WEBHOOK_VERIFY_TOKEN}")
print(f"[DEBUG] WHATSAPP_ACCESS_TOKEN exists: {bool(WHATSAPP_ACCESS_TOKEN)}")
print(f"[DEBUG] WHATSAPP_PHONE_ID: {WHATSAPP_PHONE_ID}")
print("=" * 50)

try:
    from supabase import create_client
    if SUPABASE_KEY:
        print(f"[DEBUG] Attempting to connect to Supabase...")
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✅ Supabase connected successfully!")
        
        # Test query
        try:
            test = supabase.table('menu_items').select('id').limit(1).execute()
            print(f"✅ Test query successful! Found {len(test.data)} items")
        except Exception as test_err:
            print(f"⚠️ Test query failed: {test_err}")
    else:
        print("❌ SUPABASE_KEY is EMPTY - check Railway environment variables!")
except Exception as e:
    print(f"❌ Supabase connection error: {e}")
    import traceback
    traceback.print_exc()

# Sales Agent Logic
PLATFORMS = {
    'befood': {'name': 'BeFood', 'url': 'https://begroup.onelink.me/ZOqn/cd7wxjq2', 'emoji': '🟢'},
    'shopeefood': {'name': 'ShopeeFood', 'url': 'https://shopeefood.vn/u/dU8yVzN', 'emoji': '🟠'},
    'xanhsm': {'name': 'Xanh SM', 'url': 'https://xanhsmngon.onelink.me/14WJ/91mmpf5n', 'emoji': '🟢'}
}

def send_whatsapp_message(to_phone, message_text):
    """Send a WhatsApp message via Meta's Cloud API"""
    if not WHATSAPP_ACCESS_TOKEN:
        print("⚠️ WHATSAPP_ACCESS_TOKEN not configured - cannot send message")
        return False
    
    url = f"https://graph.facebook.com/v17.0/{WHATSAPP_PHONE_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to_phone,
        "type": "text",
        "text": {"body": message_text}
    }
    
    try:
        print(f"[{datetime.utcnow().isoformat()}] 📤 Sending WhatsApp message to {to_phone}...")
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        print(f"[{datetime.utcnow().isoformat()}] ✅ Message sent successfully! Response: {response.json()}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"[{datetime.utcnow().isoformat()}] ❌ Failed to send WhatsApp message: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"[{datetime.utcnow().isoformat()}] Response body: {e.response.text}")
        return False

def detect_intent(message):
    msg = message.lower()
    if any(w in msg for w in ['menu', 'mon', 'co mon', 'an gi', 'món', 'ăn gì']): return 'menu_inquiry'
    if any(w in msg for w in ['gia', 'bao nhieu', 'price', 'giá', 'bao nhiêu']): return 'price_check'
    if any(w in msg for w in ['dat', 'order', 'mua', 'giao', 'đặt']): return 'order_intent'
    if any(w in msg for w in ['gio', 'mo cua', 'hours', 'giờ', 'mở cửa']): return 'hours_inquiry'
    if any(w in msg for w in ['dia chi', 'address', 'o dau', 'địa chỉ', 'ở đâu']): return 'location_inquiry'
    return 'general'

def get_menu_response():
    if not supabase:
        return "⚠️ Hệ thống đang bảo trì. Vui lòng thử lại sau!"
    
    try:
        result = supabase.table('menu_items').select('*').eq('available', True).execute()
        items = result.data if result.data else []
    except Exception as e:
        print(f"❌ Menu fetch error: {e}")
        items = []

    if not items:
        return "Menu chưa sẵn sàng. Vui lòng thử lại sau!"

    response = "📋 *MENU CƠM GÀ ƠI*\n\n"
    categories = {'com_ga': '🍗 CƠM GÀ', 'com_thit': '🥩 CƠM THỊT', 'do_uong': '🥤 ĐỒ UỐNG', 'side_dish': '🍲 MÓN PHỤ'}

    grouped = {}
    for item in items:
        cat = item.get('category', 'other')
        if cat not in grouped: grouped[cat] = []
        grouped[cat].append(item)

    for cat, items_list in grouped.items():
        response += f"\n*{categories.get(cat, cat.upper())}*\n"
        for item in items_list:
            price = f"{int(item['base_price']):,}đ" if item.get('base_price') else "Liên hệ"
            response += f"• {item['item_name']} - {price}\n"

    response += "\n📲 *ĐẶT NGAY:*\n"
    for p in PLATFORMS.values():
        response += f"{p['emoji']} {p['name']}: {p['url']}\n"
    return response

def handle_order_intent():
    response = "🛍️ *ĐẶT MÓN CƠM GÀ ƠI*\n\nBạn có thể đặt món qua:\n\n"
    for p in PLATFORMS.values():
        response += f"{p['emoji']} *{p['name']}*\n   {p['url']}\n\n"
    response += "Giao hàng: 30-45 phút"
    return response

def handle_greeting():
    return '''Xin chào! Chào mừng bạn đến Cơm Gà Ơi! 👋

Tôi có thể giúp bạn:
📋 Xem menu
💰 Hỏi giá món ăn
🛍️ Đặt món
📍 Thông tin liên hệ

Bạn muốn gì? Cứ hỏi nhé! 😊'''

def process_message(phone, message):
    # Log conversation
    if supabase:
        try:
            supabase.table('customer_conversations').insert({
                'customer_phone': phone, 'message_text': message,
                'message_type': 'incoming', 'created_at': datetime.utcnow().isoformat()
            }).execute()
        except Exception as e:
            print(f"⚠️ Log error: {e}")

    intent = detect_intent(message)

    if any(g in message.lower() for g in ['hi', 'hello', 'chao', 'chào', 'xin chào']):
        response = handle_greeting()
    elif intent == 'menu_inquiry':
        response = get_menu_response()
    elif intent == 'order_intent':
        response = handle_order_intent()
    elif intent == 'hours_inquiry':
        response = "⏰ *GIỜ MỞ CỬA*\n\nNhà hàng mở cửa 10:00 - 22:00 hàng ngáy!"
    elif intent == 'location_inquiry':
        response = "📍 *ĐỊA CHỈ*\n\nKiểm tra trên BeFood, ShopeeFood, Xanh SM!"
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
        except Exception as e:
            print(f"⚠️ Response log error: {e}")

    return response

# Flask Routes
@app.route('/')
def home():
    return {
        "status": "running",
        "service": "Com Ga Oi WhatsApp Sales Agent",
        "supabase_connected": supabase is not None,
        "whatsapp_phone_id": WHATSAPP_PHONE_ID,
        "whatsapp_configured": bool(WHATSAPP_ACCESS_TOKEN),
        "webhook_url": "/webhook/whatsapp"
    }

@app.route('/webhook/whatsapp', methods=['POST'])
def whatsapp_webhook():
    try:
        data = request.json
        print(f"[{datetime.utcnow().isoformat()}] 📥 Incoming webhook data: {data}")
        
        entry = data.get('entry', [{}])[0]
        changes = entry.get('changes', [{}])[0]
        value = changes.get('value', {})

        if 'messages' in value:
            message = value['messages'][0]
            customer_phone = message.get('from')
            text = message.get('text', {}).get('body', '')

            if customer_phone and text:
                print(f"[{datetime.utcnow().isoformat()}] 📨 Message from {customer_phone}: {text}")
                response = process_message(customer_phone, text)
                print(f"[{datetime.utcnow().isoformat()}] 📤 Response: {response[:100]}...")
                
                # Send response back via WhatsApp
                send_whatsapp_message(customer_phone, response)
                
                return {"status": "success"}, 200

        return {"status": "ok"}, 200
    except Exception as e:
        print(f"[{datetime.utcnow().isoformat()}] ❌ Webhook error: {e}")
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": str(e)}, 500

@app.route('/webhook/whatsapp', methods=['GET'])
def verify_webhook():
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    
    print("=" * 50)
    print(f"[WEBHOOK VERIFY] Mode: {mode}")
    print(f"[WEBHOOK VERIFY] Token received: '{token}'")
    print(f"[WEBHOOK VERIFY] Token expected: '{WEBHOOK_VERIFY_TOKEN}'")
    print(f"[WEBHOOK VERIFY] Challenge: {challenge}")
    print(f"[WEBHOOK VERIFY] Match: {token == WEBHOOK_VERIFY_TOKEN}")
    print(f"[WEBHOOK VERIFY] Token lengths - received: {len(token) if token else 0}, expected: {len(WEBHOOK_VERIFY_TOKEN)}")
    print("=" * 50)

    if mode == 'subscribe' and token == WEBHOOK_VERIFY_TOKEN:
        print(f"[{datetime.utcnow().isoformat()}] ✅ Webhook verified successfully!")
        return challenge, 200
    
    print(f"[{datetime.utcnow().isoformat()}] ❌ Webhook verification FAILED!")
    return 'Forbidden', 403

@app.route('/health')
def health():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "supabase": supabase is not None,
        "whatsapp_configured": bool(WHATSAPP_ACCESS_TOKEN)
    }

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    print(f"[{datetime.utcnow().isoformat()}] 🚀 Starting server on port {port}...")
    app.run(host='0.0.0.0', port=port)
