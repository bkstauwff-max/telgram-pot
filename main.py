import urllib.request
import urllib.parse
import urllib.error
import json
import time
import os

# بيانات البوت والقناة الخاصة بك
tok = "8595011585:AAGbgJvqvZK_Od5uFVmkiT4z58nPv4XSfDY"
cid = "-1002435545814"
msg_file = "last_msg.txt"
offset_file = "offset.txt"

def call(method, data=None):
    url = f"https://api.telegram.org/bot{tok}/{method}"
    try:
        if data:
            encoded_data = urllib.parse.urlencode(data).encode('utf-8')
            req = urllib.request.Request(url, data=encoded_data)
        else:
            req = urllib.request.Request(url)
        
        with urllib.request.urlopen(req, timeout=20) as response:
            return json.loads(response.read().decode('utf-8'))
            
    except urllib.error.HTTPError as e:
        try:
            err_body = e.read().decode('utf-8')
            print(f"⚠️ خطأ من تيليجرام في ({method}): {err_body}", flush=True)
            return json.loads(err_body)
        except Exception:
            return None
    except Exception as e:
        print(f"⚠️ خطأ اتصال في ({method}): {e}", flush=True)
        return None

def save_val(filename, val):
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(str(val).strip())
    except Exception as e:
        print(f"⚠️ خطأ في حفظ الملف {filename}: {e}", flush=True)

def load_val(filename):
    try:
        if os.path.exists(filename):
            with open(filename, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content.isdigit():
                    return int(content)
    except Exception:
        pass
    return None

def get_latest_channel_msg():
    offset = load_val(offset_file)
    params = {
        "timeout": 5,
        "allowed_updates": json.dumps(["channel_post", "edited_channel_post"])
    }
    if offset:
        params["offset"] = offset + 1

    res = call("getUpdates", params)
    latest_mid = None

    if res and res.get("ok"):
        updates = res.get("result", [])
        for u in updates:
            uid = u.get("update_id")
            if uid:
                save_val(offset_file, uid)
            
            post = u.get("channel_post") or u.get("edited_channel_post")
            if post and str(post.get("chat", {}).get("id")) == str(cid):
                latest_mid = post.get("message_id")

    if latest_mid:
        save_val(msg_file, latest_mid)
        print(f"🆕 تم التقاط رسالة جديدة بالقناة رقم: {latest_mid}", flush=True)
        return latest_mid

    return load_val(msg_file)

# تهيئة البوت وإلغاء أي ويب هوك قديم يمنع قراءة الرسائل
print("🔄 جاري تهيئة البوت...", flush=True)
call("deleteWebhook", {"drop_pending_updates": False})
print("🚀 بدأ تشغيل البوت بنجاح! سيتم تحديث التثبيت كل 6 دقائق...", flush=True)

while True:
    try:
        mid = get_latest_channel_msg()
        
        if mid:
            print(f"📌 جاري إلغاء التثبيت السابق وإعادة تثبيت الرسالة رقم {mid}...", flush=True)
            
            # 1. إلغاء تثبيت جميع الرسائل المثبتة حالياً
            call("unpinAllChatMessages", {"chat_id": cid})
            
            # 2. الانتظار ثانيتين لضمان استجابة سيرفرات تيليجرام للأمر كحدث جديد
            time.sleep(2)
            
            # 3. تثبيت الرسالة من جديد
            pin_res = call("pinChatMessage", {
                "chat_id": cid,
                "message_id": mid,
                "disable_notification": False
            })
            
            if pin_res and pin_res.get("ok"):
                print(f"✅ تم إعادة تثبيت الرسالة رقم ({mid}) بنجاح!", flush=True)
            else:
                print(f"❌ فشل تثبيت الرسالة ({mid}). الرد: {pin_res}", flush=True)
        else:
            print("⏳ لا توجد رسالة محفوظة حتى الآن. أرسل رسالة واحدة في القناة ليلتقطها البوت.", flush=True)

    except Exception as e:
        print(f"⚠️ خطأ غير متوقع في الدورة: {e}", flush=True)

    print("💤 الانتظار 6 دقائق (360 ثانية) قبل التحديث القادم...", flush=True)
    time.sleep(360)
