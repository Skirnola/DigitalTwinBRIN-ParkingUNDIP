const toggleCameraBtn = document.getElementById('toggleCameraBtn');
const cameraStream = document.getElementById('cameraStream');

let streamStarted = false;

toggleCameraBtn.addEventListener('click', async () => {
    if (!streamStarted) {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
            cameraStream.srcObject = stream;
            cameraStream.style.display = 'block';
            toggleCameraBtn.textContent = 'Click to Collapse';
            streamStarted = true;
        } catch (err) {
            alert('Gagal mengakses kamera: ' + err.message);
        }
    } else {
        const tracks = cameraStream.srcObject.getTracks();
        tracks.forEach(track => track.stop());
        cameraStream.srcObject = null;
        cameraStream.style.display = 'none';
        toggleCameraBtn.textContent = 'Click to Expand';
        streamStarted = false;
    }
});
