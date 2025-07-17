/**
 * driver_approval.html 파일의 상호작용을 처리하는 스크립트입니다.
 */
document.addEventListener('DOMContentLoaded', () => {

    // 임시 데이터 (하드코딩된 기사 목록)
    const driverData = [
        { id: 'DRV001', name: '김철수', vehicle: '트럭 A', status: '운송 중', approved: false },
        { id: 'DRV002', name: '이영희', vehicle: '트럭 B', status: '대기 중', approved: false },
        { id: 'DRV003', name: '박정훈', vehicle: '트럭 C', status: '휴식 중', approved: true },
        { id: 'DRV004', name: '최수민', vehicle: '트럭 D', status: '운송 중', approved: true },
    ];

    // 기사 목록을 테이블에 삽입하는 함수
    function loadDriverData() {
        const tbody = document.getElementById('driverTable');
        if (!tbody) return;
        tbody.innerHTML = ''; // 테이블 초기화

        driverData.forEach(driver => {
            const row = document.createElement('tr');
            row.classList.add('text-sm', 'text-gray-600', 'border-b');

            row.innerHTML = `
                <td class="p-3">${driver.id}</td>
                <td class="p-3">${driver.name}</td>
                <td class="p-3">${driver.vehicle}</td>
                <td class="p-3">${driver.status}</td>
                <td class="p-3 text-center"></td>
            `;

            const approveButton = document.createElement('button');
            approveButton.classList.add('text-white', 'py-2', 'px-4', 'rounded-lg', 'text-xs');

            if (driver.approved) {
                approveButton.textContent = '승인됨';
                approveButton.classList.add('bg-gray-400', 'cursor-not-allowed');
                approveButton.disabled = true;
            } else {
                approveButton.textContent = '승인 대기';
                approveButton.classList.add('bg-blue-500', 'hover:bg-blue-600');
                approveButton.addEventListener('click', () => approveDriver(driver.id));
            }

            row.cells[4].appendChild(approveButton);
            tbody.appendChild(row);
        });
    }

    // 기사 승인 함수
    function approveDriver(driverId) {
        const driver = driverData.find(d => d.id === driverId);
        if (driver) {
            driver.approved = true;
            loadDriverData(); // 승인 상태 변경 후 데이터 다시 로드
        }
    }

    // 페이지 로드 시 기사 데이터 로드
    loadDriverData();
});
