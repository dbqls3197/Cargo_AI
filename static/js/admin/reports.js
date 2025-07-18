/**
 * reports.html 파일의 모든 상호작용을 처리하는 스크립트입니다. (사용자 코드 기반 수정)
 */
document.addEventListener('DOMContentLoaded', () => {

    // --- Mock Data ---
    const reportData = {
        monthly_performance: {
            title: '월간 운송 실적 보고서',
            kpis: [
                { label: '총 운송 건수', value: '2,580 건', color: 'indigo' },
                { label: '총 매출', value: '₩125,000,000', color: 'green' },
                { label: '평균 운송 거리', value: '152 km', color: 'sky' },
                { label: '클레임 발생률', value: '0.8 %', color: 'red' },
            ],
            chartImage: 'https://placehold.co/1200x240/E0E7FF/6366F1?text=월간+매출+및+운송+건수+추이',
            sections: [
                { heading: '주요 성과', items: ['매칭 성공률: 92%', '평균 배차 시간: 3.5분'] }
            ]
        },
        driver_performance: {
            'DRV001': {
                title: '김철수 기사 성과 분석',
                kpis: [
                    { label: '개인 평점', value: '4.9 / 5.0', color: 'yellow' },
                    { label: '수락률', value: '95 %', color: 'blue' },
                    { label: '완료 건수 (월)', value: '120 건', color: 'green' },
                    { label: '취소율', value: '2 %', color: 'red' },
                ],
                chartImage: 'https://placehold.co/1200x240/D1C4E9/512DA8?text=김철수+기사+월별+운행+실적',
                sections: [
                    { heading: '주요 운행 특성', items: ['주로 장거리 운행 선호 (평균 250km 이상)', '오전 시간대 활동 집중'] },
                    { heading: '개선 필요 사항', items: ['심야 운행 배차 수락률 낮음'] }
                ]
            },
            'DRV002': {
                title: '이영희 기사 성과 분석',
                kpis: [
                    { label: '개인 평점', value: '4.7 / 5.0', color: 'yellow' },
                    { label: '수락률', value: '98 %', color: 'blue' },
                    { label: '완료 건수 (월)', value: '150 건', color: 'green' },
                    { label: '취소율', value: '1 %', color: 'red' },
                ],
                chartImage: 'https://placehold.co/1200x240/D1C4E9/512DA8?text=이영희+기사+월별+운행+실적',
                sections: [
                    { heading: '주요 운행 특성', items: ['수도권 단거리 운행에 강점', '고객 만족도 매우 높음'] },
                    { heading: '개선 필요 사항', items: ['특수 화물 운송 경험 부족'] }
                ]
            }
        },
    };
    const sampleDrivers = [ { id: 'DRV001', name: '김철수' }, { id: 'DRV002', name: '이영희' } ];

    const typeSelector = document.getElementById('report-type-selector');
    const monthFilter = document.getElementById('report-month-filter-container');
    const driverFilter = document.getElementById('report-driver-filter-container');
    const driverSearchInput = document.getElementById('report-driver-search');
    const driverSearchResults = document.getElementById('report-driver-search-results');
    const contentDisplay = document.getElementById('report-content-display');

    const renderReport = (report) => {
        if (report) {
            const kpiHtml = report.kpis ? `
                <div class="flex flex-wrap gap-4 mb-6">
                    ${report.kpis.map(kpi => `
                        <div class="flex-1 bg-${kpi.color}-50 p-4 rounded-lg border border-${kpi.color}-200" style="min-width: 200px;">
                            <p class="text-sm text-${kpi.color}-700 font-medium">${kpi.label}</p>
                            <p class="text-2xl font-bold text-${kpi.color}-900 mt-1 whitespace-nowrap">${kpi.value}</p>
                        </div>
                    `).join('')}
                </div>` : '';

            // [삭제] 이 부분이 보라색 박스(차트)를 생성하는 코드입니다.
            // const chartHtml = report.chartImage ? ... ;

            const sectionsHtml = report.sections ? report.sections.map(section => `
                <div class="mb-6">
                    <h4 class="text-lg font-semibold text-gray-700 mb-2">${section.heading}</h4>
                    <ul class="list-disc list-inside text-gray-600 space-y-1">
                        ${section.items.map(item => `<li>${item}</li>`).join('')}
                    </ul>
                </div>
            `).join('') : '';

            contentDisplay.innerHTML = `
                <div class="bg-white p-6 rounded-xl shadow-lg">
                    <div class="flex justify-between items-start mb-4">
                        <h3 class="text-2xl font-bold text-gray-800">${report.title}</h3>
                        <div class="flex space-x-2">
                            <button class="p-2 bg-gray-200 text-gray-600 rounded-lg hover:bg-gray-300"><i class="fas fa-share-alt"></i></button>
                            <button class="p-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"><i class="fas fa-file-pdf"></i> PDF</button>
                        </div>
                    </div>
                    ${kpiHtml}
                    ${sectionsHtml}
                </div>`;
        } else {
            contentDisplay.innerHTML = `<div class="bg-white p-6 rounded-xl shadow-lg text-center text-gray-500">표시할 보고서가 없습니다. 필터를 확인해주세요.</div>`;
        }
    };

    const updateUI = () => {
        const reportType = typeSelector.value;
        driverFilter.classList.toggle('hidden', reportType !== 'driver_performance');
        monthFilter.classList.toggle('hidden', reportType === 'driver_performance');

        if (reportType !== 'driver_performance') {
            renderReport(reportData[reportType]);
        } else {
            renderReport(null);
            driverSearchInput.value = '';
        }
    };

        const filterDrivers = () => {
        const searchTerm = driverSearchInput.value.toLowerCase();
        driverSearchResults.innerHTML = '';
        if (!searchTerm) {
            driverSearchResults.style.display = 'none';
            return;
        }
        const matched = sampleDrivers.filter(d => d.name.toLowerCase().includes(searchTerm) || d.id.toLowerCase().includes(searchTerm));
        if (matched.length > 0) {
            // [수정] 검색 결과 목록을 담을 컨테이너 스타일링
            driverSearchResults.className = 'absolute w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg z-10';

            matched.forEach(driver => {
                const item = document.createElement('div');

                // [수정] 1. 커서 변경 및 2. 디자인 개선을 위한 클래스 추가
                item.className = 'p-3 hover:bg-indigo-50 rounded-md'; // 패딩과 호버 효과 추가
                item.style.cursor = 'pointer'; // 1. 마우스 오버 시 커서를 포인터(클릭 모양)로 변경

                // [수정] 2. 이름과 ID를 분리하여 보기 좋게 디자인
                item.innerHTML = `
                    <div class="flex justify-between items-center">
                        <span class="font-semibold text-gray-800">${driver.name}</span>
                        <span class="text-sm text-gray-500">${driver.id}</span>
                    </div>
                `;

                item.addEventListener('click', () => {
                    driverSearchInput.value = `${driver.name} (${driver.id})`;
                    driverSearchResults.style.display = 'none';
                    renderReport(reportData.driver_performance[driver.id]);
                });
                driverSearchResults.appendChild(item);
            });
            driverSearchResults.style.display = 'block';
        } else {
            driverSearchResults.style.display = 'none';
        }
    };

    typeSelector.addEventListener('change', updateUI);
    driverSearchInput.addEventListener('input', filterDrivers);
    driverSearchInput.addEventListener('focus', filterDrivers);
    document.addEventListener('click', (e) => {
        if (!driverFilter.contains(e.target)) {
            driverSearchResults.style.display = 'none';
        }
    });

    updateUI();
});
