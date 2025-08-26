function updateClock() {
    try {
        const now = new Date();
        const options = {
            timeZone: 'Asia/Jakarta',
            hour: 'numeric',
            minute: '2-digit',
            hour12: true
        };
        const timeString = new Intl.DateTimeFormat('en-US', options).format(now);
        const currentTimeElement = document.getElementById('currentTime');
        if (currentTimeElement) {
            currentTimeElement.textContent = timeString;
        } else {
            console.error('Elemen currentTime tidak ditemukan');
        }
    } catch (error) {
        console.error('Kesalahan pembaruan jam:', error);
    }
}

// Jalankan sekali saat dimuat dan setiap detik
document.addEventListener('DOMContentLoaded', () => {
    updateClock();
    setInterval(updateClock, 1000);
});