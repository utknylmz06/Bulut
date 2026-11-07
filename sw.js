self.addEventListener('push', function(event) {
    let data = { title: 'J.A.R.V.I.S. Bildirimi', body: 'Sistemden yeni bir mesaj var!' };
    if (event.data) {
        try { data = JSON.parse(event.data.text()); } catch(e) { data.body = event.data.text(); }
    }
    const options = {
        body: data.body,
        icon: 'https://cdn-icons-png.flaticon.com/512/2092/2092663.png',
        vibrate: [200, 100, 200]
    };
    event.waitUntil(self.registration.showNotification(data.title, options));
});
