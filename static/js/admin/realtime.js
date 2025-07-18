/**
 * realtime.html 파일의 상호작용을 처리하는 스크립트입니다.
 */
document.addEventListener('DOMContentLoaded', () => {

    // [추가] 현재 페이지(실시간 관제)에 해당하는 메뉴에 활성 스타일을 적용합니다.
    const realtimeLink = document.querySelector('a[href="/realtime"]');
    if (realtimeLink) {
        realtimeLink.classList.add('active-nav-link');
    }

    // --- Mock Data ---
    const sampleDrivers = [
        { id: 'DRV001', name: '김철수', vehicle: '5톤 냉장', status: '운송 중', details: { progress: [{ step: '서울 상차 완료', time: '09:30', completed: true }, { step: '대전 하차 완료', time: '12:00', completed: true }, { step: '부산 이동 중', time: '진행 중', completed: false }, { step: '부산 하차 예정', time: '17:30', completed: false }], route: { next: '부산 물류센터', eta: '17:30', remaining: '250km' }, info: { cargoId: '#20250709-001', origin: '서울 강남구', dest: '부산 해운대구' }, logs: [{ time: '12:00', log: '대전 하차 완료' }, { time: '09:35', log: '운행 시작' }] } },
        { id: 'DRV002', name: '이영희', vehicle: '11톤 일반', status: '대기 중', details: null },
        { id: 'DRV003', name: '박지성', vehicle: '2.5톤 냉동', status: '운송 중', details: { progress: [{ step: '인천 상차 완료', time: '11:00', completed: true }, { step: '광주 이동 중', time: '진행 중', completed: false }], route: { next: '광주 물류센터', eta: '16:00', remaining: '180km' }, info: { cargoId: '#20250710-005', origin: '인천 서구', dest: '광주 광산구' }, logs: [{ time: '11:05', log: '운행 시작' }] } },
        { id: 'DRV004', name: '최민수', vehicle: '1톤 카고', status: '휴식 중', details: null },
    ];
    let selectedDriverId = null;

    // --- DOM 요소 ---
    const searchInput = document.getElementById('driver-search');
    const statusFilter = document.getElementById('driver-status-filter');
    const sortBy = document.getElementById('driver-sort-by');
    const driverListContainer = document.getElementById('driver-list-container');
    const mapContainer = document.getElementById('driver-map-container');
    const progressList = document.getElementById('transport-progress-list');
    const routeList = document.getElementById('route-info-list');
    const infoList = document.getElementById('transport-info-list');
    const logsList = document.getElementById('recent-logs-list');

    // --- 함수 ---
    const updateDriverDetails = (driver) => {
        if (driver && driver.details) {
            mapContainer.textContent = `[${driver.name}(${driver.id}) 기사 실시간 지도]`;
            progressList.innerHTML = driver.details.progress.map(p => `<div class="flex items-center"><i class="fas ${p.completed ? 'fa-check-circle text-green-500' : 'fa-circle text-gray-400'} mr-3"></i><span>${p.step} (${p.time})</span></div>`).join('');
            routeList.innerHTML = `<p><strong>다음 경유지:</strong> ${driver.details.route.next}</p><p><strong>예상 도착 시간:</strong> ${driver.details.route.eta}</p><p><strong>남은 거리:</strong> ${driver.details.route.remaining}</p>`;
            infoList.innerHTML = `<p><strong>운송 ID:</strong> ${driver.details.info.cargoId}</p><p><strong>출발지:</strong> ${driver.details.info.origin}</p><p><strong>도착지:</strong> ${driver.details.info.dest}</p>`;
            logsList.innerHTML = driver.details.logs.map(l => `<li class="flex items-start"><span class="font-semibold text-gray-600 w-16">[${l.time}]</span><span class="text-gray-800">${l.log}</span></li>`).join('');
        } else {
            const placeholder = `<p class="text-gray-500">기사를 선택하여 정보를 확인하세요.</p>`;
            mapContainer.textContent = driver ? `[${driver.name}(${driver.id}) 기사님은 현재 운송 중이 아닙니다.]` : '[기사를 선택해주세요]';
            progressList.innerHTML = placeholder;
            routeList.innerHTML = placeholder;
            infoList.innerHTML = placeholder;
            logsList.innerHTML = `<li>${placeholder}</li>`;
        }
    };

    const selectDriver = (driverId) => {
        selectedDriverId = driverId;
        document.querySelectorAll('.driver-item').forEach(item => {
            item.classList.toggle('selected', item.dataset.driverId === driverId);
        });
        const driver = sampleDrivers.find(d => d.id === driverId);
        updateDriverDetails(driver);
    };

    const renderDriverList = (drivers) => {
        driverListContainer.innerHTML = '';
        if (drivers.length === 0) {
            driverListContainer.innerHTML = `<p class="col-span-full text-center text-gray-500 py-4">검색 결과가 없습니다.</p>`;
            updateDriverDetails(null);
            return;
        }
        drivers.forEach(driver => {
            const driverDiv = document.createElement('div');
            driverDiv.className = 'driver-item bg-gray-50 p-4 rounded-lg shadow-sm border border-gray-200';
            driverDiv.dataset.driverId = driver.id;
            driverDiv.innerHTML = `<p class="font-semibold text-lg text-gray-800">${driver.name} <span class="text-sm text-gray-500">(${driver.id})</span></p><p class="text-sm text-gray-600">${driver.vehicle}</p><p class="text-sm mt-1 font-medium ${driver.status === '운송 중' ? 'text-green-600' : (driver.status === '대기 중' ? 'text-blue-600' : 'text-orange-500')}">${driver.status}</p>`;
            driverListContainer.appendChild(driverDiv);
        });

        const currentSelectionVisible = drivers.some(d => d.id === selectedDriverId);
        if (!currentSelectionVisible) {
            selectedDriverId = null;
            updateDriverDetails(null);
        } else {
            selectDriver(selectedDriverId);
        }
    };

    const filterAndSortDrivers = () => {
        let filtered = sampleDrivers.filter(driver => {
            const searchTerm = searchInput.value.toLowerCase();
            const status = statusFilter.value;
            return (driver.name.toLowerCase().includes(searchTerm) || driver.id.toLowerCase().includes(searchTerm)) && (status === 'all' || driver.status === status);
        });
        const sort = sortBy.value;
        filtered.sort((a, b) => (sort === 'name') ? a.name.localeCompare(b.name) : a.status.localeCompare(b.status));
        renderDriverList(filtered);
    };

    // --- 이벤트 리스너 ---
    searchInput.addEventListener('input', filterAndSortDrivers);
    statusFilter.addEventListener('change', filterAndSortDrivers);
    sortBy.addEventListener('change', filterAndSortDrivers);

    driverListContainer.addEventListener('click', (e) => {
        const driverItem = e.target.closest('.driver-item');
        if (driverItem) {
            selectDriver(driverItem.dataset.driverId);
        }
    });

    // --- 초기화 ---
    filterAndSortDrivers();
});
