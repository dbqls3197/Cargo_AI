/**
 * inquiry.html 파일의 모든 상호작용을 처리하는 스크립트입니다. (답변 상태에 따른 UI 변경 기능 추가)
 */
document.addEventListener('DOMContentLoaded', () => {

    // --- Mock Data ---
    const inquiryHistory = [
        { id: 'INQ001', sender: '화주 (홍길동)', type: '시스템 오류', title: '지도 로딩 오류', content: '화물 위치가 지도에 표시되지 않습니다. 빠른 확인 부탁드립니다.', status: 'answered', date: '2025-07-01', response: '지도 API 키 문제였습니다. 수정 완료되었습니다.' },
        { id: 'INQ002', sender: '기사 (김철수)', type: '기능 개선 제안', title: '배차 알고리즘 개선 제안', content: '현재 배차 알고리즘이 특정 시간대에 공차 운행을 유발합니다. 개선 제안드립니다.', status: 'pending', date: '2025-07-05', response: '' },
        { id: 'INQ003', sender: '화주 (이순신)', type: '기타 문의', title: '보고서 데이터 문의', content: '월간 운송 실적 보고서의 특정 데이터가 이해가 가지 않습니다. 설명 부탁드립니다.', status: 'waiting', date: '2025-07-08', response: '' },
    ];

    // --- DOM 요소 ---
    const tableBody = document.getElementById('inquiry-table-body');
    const modalOverlay = document.getElementById('inquiry-modal-overlay');
    const modalContent = document.getElementById('inquiry-modal-content');

    // --- 함수 ---

    const renderInquiries = () => {
        tableBody.innerHTML = '';
        inquiryHistory.forEach(inquiry => {
            const row = document.createElement('tr');
            row.className = 'border-b border-gray-200';
            row.dataset.inquiryId = inquiry.id;
            let statusClass = inquiry.status;
            row.innerHTML = `<td class="p-3 text-sm text-gray-700">${inquiry.id}</td><td class="p-3 text-sm font-medium text-gray-900">${inquiry.sender}</td><td class="p-3 text-sm text-gray-600">${inquiry.type}</td><td class="p-3 text-sm text-gray-800">${inquiry.title}</td><td class="p-3 text-sm"><span class="status-badge ${statusClass}">${inquiry.status}</span></td><td class="p-3 text-sm text-gray-600">${inquiry.date}</td>`;
            tableBody.appendChild(row);
        });
    };

    const closeModal = () => {
        modalOverlay.classList.add('hidden');
        modalOverlay.classList.remove('flex');
    };

    const showInquiryDetail = (inquiryId, isEditing = false) => {
        const inquiry = inquiryHistory.find(i => i.id === inquiryId);
        if (!inquiry) return;

        let responseAreaHtml = '';
        // [수정] 문의 상태와 수정 모드에 따라 다른 UI를 보여줍니다.
        if (inquiry.status === 'answered' && !isEditing) {
            // 답변 완료 상태 (읽기 전용)
            responseAreaHtml = `
                <div>
                    <p class="font-semibold mb-2">저장된 답변:</p>
                    <div class="bg-gray-100 p-4 rounded-lg border text-gray-800">${inquiry.response}</div>
                </div>
                <div class="text-right">
                    <button id="edit-response-btn" data-inquiry-id="${inquiry.id}" class="bg-gray-600 text-white py-2 px-5 rounded-lg font-semibold hover:bg-gray-700">수정하기</button>
                </div>
            `;
        } else {
            // 미답변 또는 수정 중인 상태
            responseAreaHtml = `
                <div>
                    <label for="response-textarea" class="block font-semibold mb-2">답변 작성:</label>
                    <textarea id="response-textarea" rows="4" class="w-full p-3 border border-gray-300 rounded-lg" placeholder="답변을 입력하세요...">${inquiry.response}</textarea>
                </div>
                <div class="text-right">
                    <button id="submit-response-btn" data-inquiry-id="${inquiry.id}" class="bg-indigo-600 text-white py-2 px-5 rounded-lg font-semibold hover:bg-indigo-700">답변 저장</button>
                </div>
            `;
        }

        modalContent.innerHTML = `
            <div class="flex justify-between items-center mb-6">
                <h3 class="text-2xl font-bold text-gray-800">문의 상세 내용 (${inquiry.id})</h3>
                <button id="close-modal-btn" class="text-gray-400 hover:text-gray-600 text-3xl leading-none">&times;</button>
            </div>
            <div class="space-y-4">
                <div><strong class="w-24 inline-block">발신자:</strong> ${inquiry.sender}</div>
                <div><strong class="w-24 inline-block">유형:</strong> ${inquiry.type}</div>
                <div class="bg-gray-50 p-4 rounded-lg border"><p class="font-semibold mb-2">문의 내용:</p><p>${inquiry.content}</p></div>
                ${responseAreaHtml}
            </div>
        `;
        modalOverlay.classList.remove('hidden');
        modalOverlay.classList.add('flex');
    };

    // [수정] 이벤트 위임을 사용하여 모달 내의 모든 클릭 이벤트를 한 번에 처리합니다.
    modalOverlay.addEventListener('click', (e) => {
        const inquiryId = e.target.dataset.inquiryId;

        // 닫기 버튼 또는 모달 바깥 영역 클릭
        if (e.target.id === 'close-modal-btn' || e.target === modalOverlay) {
            closeModal();
        }
        // 답변 저장 버튼 클릭
        else if (e.target.id === 'submit-response-btn') {
            const inquiry = inquiryHistory.find(i => i.id === inquiryId);
            if (inquiry) {
                const responseText = document.getElementById('response-textarea').value;
                inquiry.response = responseText;
                inquiry.status = 'answered';
                closeModal();
                renderInquiries();
            }
        }
        // 수정하기 버튼 클릭
        else if (e.target.id === 'edit-response-btn') {
            showInquiryDetail(inquiryId, true); // 수정 모드로 다시 렌더링
        }
    });

    tableBody.addEventListener('click', (e) => {
        const row = e.target.closest('tr');
        if (row && row.dataset.inquiryId) {
            showInquiryDetail(row.dataset.inquiryId);
        }
    });

    renderInquiries();
});
