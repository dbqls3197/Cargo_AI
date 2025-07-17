/**
 * cargo_approval.html 파일의 상호작용을 처리하는 스크립트입니다.
 */
document.addEventListener('DOMContentLoaded', () => {

    // 가짜 데이터 (임시로 하드코딩된 화물 데이터)
    const cargos = [
        { id: 'CARGO001', origin: '서울', destination: '부산', status: '대기 중', approved: false },
        { id: 'CARGO002', origin: '대전', destination: '인천', status: '대기 중', approved: false },
        { id: 'CARGO003', origin: '광주', destination: '서울', status: '매칭 완료', approved: true },
        { id: 'CARGO004', origin: '대구', destination: '울산', status: '대기 중', approved: false }
    ];

    // 가짜 데이터 (임시로 하드코딩된 기사 데이터)
    const drivers = [
        { id: 'DRIVER001', name: '김철수', vehicle: '트럭 A', status: '운송 중', approved: false },
        { id: 'DRIVER002', name: '이영희', vehicle: '트럭 B', status: '대기 중', approved: false },
        { id: 'DRIVER003', name: '박정훈', vehicle: '트럭 C', status: '휴식 중', approved: true },
        { id: 'DRIVER004', name: '최수민', vehicle: '트럭 D', status: '운송 중', approved: true }
    ];

    // DOM 요소
    const cargoTable = document.getElementById('cargoTable');
    const modal = document.getElementById('modal');
    const driverSelect = document.getElementById('driverSelect');

    // 화물 데이터 렌더링
    function renderCargoTable() {
        cargoTable.innerHTML = '';  // 테이블 초기화
        cargos.forEach(cargo => {
            const row = cargoTable.insertRow();
            row.classList.add('text-sm', 'text-gray-600', 'border-b');

            const cargoIdCell = row.insertCell();
            cargoIdCell.classList.add('p-3', 'text-center');
            cargoIdCell.textContent = cargo.id;

            const statusCell = row.insertCell();
            statusCell.classList.add('p-3', 'text-center');
            statusCell.textContent = cargo.status;

            const actionCell = row.insertCell();
            actionCell.classList.add('p-3', 'text-center');
            const actionButton = document.createElement('button');
            actionButton.classList.add('text-white', 'py-2', 'px-4', 'rounded-lg', 'text-xs');

            if (cargo.status === '대기 중') {
                actionButton.textContent = '수동 매칭';
                actionButton.classList.add('bg-blue-500', 'hover:bg-blue-600');
                actionButton.onclick = () => openModal(cargo.id);
            } else {
                actionButton.textContent = cargo.status;
                actionButton.classList.add('bg-gray-400', 'cursor-not-allowed');
                actionButton.disabled = true;
            }

            actionCell.appendChild(actionButton);
        });
    }

    // 기사 선택 팝업 열기
    window.openModal = function(cargoId) {
        modal.style.display = 'flex';
        driverSelect.innerHTML = '';
        drivers.filter(driver => driver.status === '대기 중').forEach(driver => {
            const option = document.createElement('option');
            option.value = driver.id;
            option.textContent = `${driver.name} (${driver.vehicle}) - ${driver.status}`;
            driverSelect.appendChild(option);
        });
        window.selectedCargoId = cargoId;
    }

    // 기사 매칭 완료
    window.matchCargo = function() {
        const selectedDriverId = driverSelect.value;
        const selectedCargo = cargos.find(cargo => cargo.id === window.selectedCargoId);

        if (selectedCargo && selectedDriverId) {
            selectedCargo.status = '매칭 완료';
            alert(`기사 ${selectedDriverId}님과 매칭 완료되었습니다.`);
            renderCargoTable();
            closeModal();
        } else {
            alert('기사를 선택해주세요.');
        }
    }

    // 팝업 닫기
    window.closeModal = function() {
        modal.style.display = 'none';
    }

    // 초기 렌더링
    renderCargoTable();
});
