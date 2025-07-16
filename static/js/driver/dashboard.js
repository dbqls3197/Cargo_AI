
document.addEventListener('DOMContentLoaded', function () {
        const toggle = document.getElementById('driverStatusToggle');
        const statusText = document.getElementById('driverStatusText');

        function updateStatusUI() {
            if (toggle.checked) {
                statusText.textContent = '운행 가능';
                statusText.classList.remove('text-red-700');
                statusText.classList.add('text-green-700');
            } else {
                statusText.textContent = '운행 불가(휴식중)';
                statusText.classList.remove('text-green-700');
                statusText.classList.add('text-red-700');
            }
        }

        toggle.addEventListener('change', updateStatusUI);
        updateStatusUI();  // 초기 상태 적용
    });

document.addEventListener('DOMContentLoaded', () => {
const statusToggle = document.getElementById('driverStatusToggle');
const statusText = document.getElementById('driverStatusText');

if (statusToggle && statusText) {
    statusToggle.addEventListener('change', () => {
        if (statusToggle.checked) {
            statusText.textContent = '운행 가능';
            statusText.classList.remove('text-red-700');
            statusText.classList.add('text-green-700');
        } else {
            statusText.textContent = '운행 중지';
            statusText.classList.remove('text-green-700');
            statusText.classList.add('text-red-700');
        }
    });
}

const notificationIcon = document.getElementById('driver-notification-icon');
if (notificationIcon) {
    notificationIcon.addEventListener('click', () => {
        alert('새로운 알림이 도착했습니다!');
    });
}
});
