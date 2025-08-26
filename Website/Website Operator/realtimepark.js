<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Digital Parking Dashboard</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            color: darkslategrey;
            overflow-x: hidden;
        }

        body::before {
            content: "";
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: none;
            opacity: 0.2;
            z-index: -1;
        }

        video#bg-video {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            object-fit: cover;
            z-index: -2;
            opacity: 0.4;
        }

        header {
            background-image: linear-gradient(to right, lightseagreen, palevioletred);
            color: white;
            padding: 10px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            position: fixed;
            width: 100%;
            top: 0;
            z-index: 1000;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
        }

        .logo {
            display: flex;
            align-items: center;
            cursor: pointer;
        }

        .logo img {
            height: 40px;
            vertical-align: middle;
        }

        .logo span {
            margin-left: 10px;
            font-size: 16px;
            font-weight: bold;
        }

        .header-right {
            display: flex;
            align-items: center;
        }

        .header-right span {
            margin-right: 20px;
            font-size: 14px;
        }

        .main-content {
            margin-left: 0;
            padding: 80px 20px 20px;
            min-height: 100vh;
        }

        .main-content-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 15px;
            margin-bottom: 20px;
        }

        .notifications {
            background: #fff;
            border-radius: 10px;
            padding: 20px;
            margin-top: 20px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }

        .notification-list {
            max-height: 300px;
            overflow-y: auto;
        }

        .notification-item {
            padding: 10px;
            border-bottom: 1px solid #ddd;
            font-family: Arial, sans-serif;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .notification-item span {
            font-size: 14px;
        }

        .parking-lot {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 10px;
            padding: 10px;
        }

        .slot {
            border: 1px solid #ccc;
            padding: 10px;
            text-align: center;
            background-color: #e9ecef;
            font-size: 12px;
            border-radius: 5px;
            position: relative;
            height: 60px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: background-color 0.3s;
        }

        .slot.occupied {
            background-color: #ffd700;
        }

        .slot.occupied .car {
            display: block;
            animation: carEnter 0.5s ease-in-out;
        }

        .slot:not(.occupied) .car {
            display: none;
        }

        .car {
            width: 40px;
            height: 30px;
            background-color: #333;
            border-radius: 5px;
            position: absolute;
            left: 50%;
            top: 50%;
            transform: translate(-50%, -50%);
            transition: opacity 0.5s ease-in-out;
        }

        @keyframes carEnter {
            from {
                transform: translate(-50%, -50%) scale(0);
                opacity: 0;
            }
            to {
                transform: translate(-50%, -50%) scale(1);
                opacity: 1;
            }
        }

        @keyframes carExit {
            from {
                transform: translate(-50%, -50%) scale(1);
                opacity: 1;
            }
            to {
                transform: translate(-50%, -50%) scale(0);
                opacity: 0;
            }
        }

        .slot.occupied.exiting .car {
            animation: carExit 0.5s ease-in-out forwards;
        }
    </style>
</head>
<body>
    <header>
        <div class="logo">
            <img src="logo.png" alt="Logo">
            <span>Dashboard Parkir</span>
        </div>
        <div class="header-right">
            <span>Status Pengguna</span>
        </div>
    </header>

    <main class="main-content">
        <section class="main-content-grid">
            <div class="notifications">
                <h2>Notifikasi Slot Parkir</h2>
                <div class="notification-list" id="notificationList"></div>
            </div>
        </section>

        <section class="parking-lot" id="parkingLot">
            <!-- Misal buat 20 slot -->
            <div class="slot" data-slot="1"><div class="car"></div>Slot 1</div>
            <div class="slot" data-slot="2"><div class="car"></div>Slot 2</div>
            <!-- Tambahkan sampai slot 20 -->
        </section>
    </main>

    <script src="https://www.gstatic.com/firebasejs/8.10.1/firebase-app.js"></script>
    <script src="https://www.gstatic.com/firebasejs/8.10.1/firebase-database.js"></script>
    <script>
        const firebaseConfig = {
            apiKey: "AIzaSyAef3SJwvVVTunr6CWki79aenfpXlgYc0s",
            authDomain: "digitaltwinparkingbrin.firebaseapp.com",
            databaseURL: "https://digitaltwinparkingbrin-default-rtdb.asia-southeast1.firebasedatabase.app",
            projectId: "digitaltwinparkingbrin",
            storageBucket: "digitaltwinparkingbrin.firebasestorage.app",
            messagingSenderId: "608462498913",
            appId: "1:608462498913:web:73695d8c91f923e2db8e20",
            measurementId: "G-F1TRY65RTG"
        };

        firebase.initializeApp(firebaseConfig);
        const database = firebase.database();

        const slotsRef = database.ref('slots');
        const slots = document.querySelectorAll('.slot');
        const notificationList = document.getElementById('notificationList');
        const slotStates = {};

        slotsRef.on('value', (snapshot) => {
            const data = snapshot.val();
            if (!data) return;

            let occupiedCount = 0;
            const totalSlots = 20;

            slots.forEach(slot => {
                const slotId = slot.dataset.slot;
                const isOccupied = data[`slot${slotId}`] && data[`slot${slotId}`].occupied;
                const wasOccupied = slotStates[slotId] || false;

                if (isOccupied && !wasOccupied) {
                    slot.classList.remove('exiting');
                    slot.classList.add('occupied');
                    const car = slot.querySelector('.car');
                    if (car) {
                        car.style.animation = 'carEnter 0.5s ease-in-out';
                        setTimeout(() => { car.style.animation = ''; }, 500);
                    }

                    const notif = document.createElement('div');
                    notif.className = 'notification-item';
                    notif.innerHTML = `<span>Slot ${slotId} sekarang TERISI</span><span>${new Date().toLocaleString()}</span>`;
                    notificationList.prepend(notif);
                } else if (!isOccupied && wasOccupied) {
                    slot.classList.add('exiting');
                    const car = slot.querySelector('.car');
                    if (car) {
                        car.style.animation = 'carExit 0.5s ease-in-out';
                        setTimeout(() => {
                            slot.classList.remove('occupied', 'exiting');
                            car.style.animation = '';
                        }, 500);
                    }

                    const notif = document.createElement('div');
                    notif.className = 'notification-item';
                    notif.innerHTML = `<span>Slot ${slotId} sekarang KOSONG</span><span>${new Date().toLocaleString()}</span>`;
                    notificationList.prepend(notif);
                }

                slotStates[slotId] = isOccupied;
                if (isOccupied) occupiedCount++;
            });
        });

        slots.forEach(slot => {
            slot.addEventListener('click', () => {
                const slotId = slot.dataset.slot;
                const isOccupied = slot.classList.contains('occupied');
                const car = slot.querySelector('.car');

                if (isOccupied) {
                    slot.classList.add('exiting');
                    if (car) car.style.animation = 'carExit 0.5s ease-in-out';
                    setTimeout(() => {
                        slot.classList.remove('occupied', 'exiting');
                        if (car) car.style.animation = '';
                        slotsRef.child(`slot${slotId}`).update({ occupied: false, licensePlate: "" });
                    }, 500);
                } else {
                    slot.classList.add('occupied');
                    if (car) car.style.animation = 'carEnter 0.5s ease-in-out';
                    slotsRef.child(`slot${slotId}`).update({ occupied: true, licensePlate: "" });
                    setTimeout(() => { if (car) car.style.animation = ''; }, 500);
                }
            });
        });
    </script>
</body>
</html>
