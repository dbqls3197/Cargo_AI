// static/js/driver/navigation.js
document.addEventListener('DOMContentLoaded', function() {
    console.log("DOM 콘텐츠 로드됨 - navigation.js 초기화 시작");

    // 1. loggedInDriverId 가져오기 및 유효성 검사 (기존 코드 유지)
    const loggedInDriverId = localStorage.getItem('loggedInDriverId');

    if (!loggedInDriverId) {
        console.error("Driver ID가 localStorage에 없습니다. 로그인이 필요합니다.");
        alert("로그인이 필요합니다. 다시 로그인해주세요.");
        window.location.href = '/login'; // 로그인 페이지 URL로 변경
        return;
    }
    console.log("Navigation.js에서 감지된 Driver ID:", loggedInDriverId);

    // 모든 UI 요소들을 가져옵니다. (기존 코드 유지)
    const driverStatusToggle = document.getElementById('driverStatusToggle');
    const driverStatusText = document.getElementById('driverStatusText');
    const startGuidanceButton = document.getElementById('start-guidance-button');
    const currentStartAddressElem = document.getElementById('current-start-address');
    const currentEndAddressElem = document.getElementById('current-end-address');
    const manualInputSection = document.getElementById('manual-input-section');
    const inputStartAddress = document.getElementById('inputStartAddress');
    const inputEndAddress = document.getElementById('inputEndAddress');
    const searchManualRouteButton = document.getElementById('searchManualRouteButton');
    const currentTripStatusSection = document.getElementById('current-trip-status-section');
    const realtimeNavigationSection = document.getElementById('realtime-navigation-section');
    const recentRoutesSection = document.getElementById('recent-routes-section'); // HTML에 없으면 사용 안 됨

    const mapLoadingOverlay = document.getElementById('map-loading-overlay');
    const routeInfoOverlay = document.getElementById('route-info-overlay');
    const navSummaryOverlay = document.getElementById('nav-summary-overlay');

    let guidanceActive = false;
    let simulationIntervalId = null;
    let currentSimulationIndex = 0;
    let currentRoutePolylinePath = [];
    let totalRouteDistance = 0;
    let currentSpeed = 60;

    let map = null; // 지도 객체 초기에는 null로 설정
    let currentPolyline = null;
    let startMarker = null;
    let endMarker = null;
    let currentLocationMarker = null;
    let waypointMarkers = []; // 경유지 마커를 저장할 배열 추가

    const mapContainer = document.getElementById('map');

    // 새로 추가할 주소 검색 버튼 요소 가져오기
    const searchStartAddressButton = document.getElementById('searchStartAddressButton');
    const searchEndAddressButton = document.getElementById('searchEndAddressButton');


    // UI 텍스트 및 스타일 업데이트 함수 (기존 코드 유지)
    function updateDriverStatusTextUI(isChecked) {
        if (isChecked) {
            driverStatusText.textContent = '운행 가능';
            driverStatusText.classList.remove('text-red-700');
            driverStatusText.classList.add('text-green-700');
            console.log('운행 가능으로 변경됨 (UI)');
        } else {
            driverStatusText.textContent = '운행 불가';
            driverStatusText.classList.remove('text-green-700');
            driverStatusText.classList.add('text-red-700');
            console.log('운행 불가로 변경됨 (UI)');
        }
    }

    // 운전자 상태를 서버로 전송하는 함수 (기존 코드 유지)
    async function sendDriverStatusToServer(status) {
        const driverId = localStorage.getItem('loggedInDriverId');
        if (!driverId) {
            console.error('sendDriverStatusToServer: Driver ID를 찾을 수 없습니다. 로그인 상태를 확인하세요.');
            alert('로그인이 필요합니다. 다시 로그인 해주세요.');
            if (driverStatusToggle) {
                driverStatusToggle.checked = !driverStatusToggle.checked;
                updateDriverStatusTextUI(driverStatusToggle.checked);
            }
            return;
        }

        try {
            const response = await fetch('/update_driver_status', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    driver_id: driverId,
                    status: status
                })
            });
            const data = await response.json();
            if (data.success) {
                console.log(`운전자 상태 DB 업데이트 성공: ${status}`);
            } else {
                console.error('운전자 상태 DB 업데이트 실패:', data.message);
                alert('운전자 상태 업데이트에 실패했습니다: ' + data.message);
                if (driverStatusToggle) {
                    driverStatusToggle.checked = !driverStatusToggle.checked;
                    updateDriverStatusTextUI(driverStatusToggle.checked);
                }
            }
        } catch (error) {
            console.error('운전자 상태 DB 업데이트 중 통신 오류 발생:', error);
            alert('운전자 상태 업데이트 중 통신 오류 발생.');
            if (driverStatusToggle) {
                driverStatusToggle.checked = !driverStatusToggle.checked;
                updateDriverStatusTextUI(driverStatusToggle.checked);
            }
        }
    }

    // 페이지 로드 시 운전자의 초기 상태를 DB에서 가져와 토글에 반영하는 함수 (기존 코드 유지)
    async function loadDriverStatus() {
        const driverId = localStorage.getItem('loggedInDriverId');
        if (!driverId) {
            console.warn('loadDriverStatus: Driver ID를 찾을 수 없습니다. 초기 상태 로드를 건너뜁니다.');
            if (driverStatusToggle) {
                driverStatusToggle.checked = false;
                updateDriverStatusTextUI(driverStatusToggle.checked);
            }
            return;
        }

        try {
            const response = await fetch(`/get_driver_status?driver_id=${driverId}`);
            const data = await response.json();
            if (data.success) {
                if (driverStatusToggle) {
                    driverStatusToggle.checked = (data.status === 0);
                    updateDriverStatusTextUI(driverStatusToggle.checked);
                }
                console.log(`운전자 초기 상태 로드 성공: ${data.status}`);
            } else {
                console.error('운전자 초기 상태 로드 실패:', data.message);
                if (driverStatusToggle) {
                    driverStatusToggle.checked = false;
                    updateDriverStatusTextUI(driverStatusToggle.checked);
                }
            }
        } catch (error) {
            console.error('운전자 초기 상태 로드 중 오류 발생:', error);
            if (driverStatusToggle) {
                driverStatusToggle.checked = false;
                updateDriverStatusTextUI(driverStatusToggle.checked);
            }
        }
    }

    // driverStatusToggle 및 driverStatusText 요소가 HTML에 존재하는지 확인 후 이벤트 리스너 설정 (기존 코드 유지)
    if (driverStatusToggle && driverStatusText) {
        driverStatusToggle.addEventListener('change', function() {
            const statusValue = this.checked ? 0 : 1;
            updateDriverStatusTextUI(this.checked);
            sendDriverStatusToServer(statusValue);
        });
        loadDriverStatus();
    } else {
        console.error("driverStatusToggle 또는 driverStatusText 요소를 찾을 수 없습니다. HTML 구조를 확인하세요.");
    }

    // 지도를 실제로 생성하는 함수. 이제 이 함수가 필요한 시점에만 호출됩니다. (기존 코드 유지)
    function initializeMap(latitude, longitude) {
        const mapOption = {
            center: new kakao.maps.LatLng(latitude, longitude),
            level: 3
        };
        map = new kakao.maps.Map(mapContainer, mapOption);
        console.log("카카오맵 초기화 완료.");
    }

    // 거리 계산 함수 (기존 코드 유지)
    function calculateDistance(lat1, lon1, lat2, lon2) {
        const R = 6371;
        const dLat = (lat2 - lat1) * Math.PI / 180;
        const dLon = (lon2 - lon1) * Math.PI / 180;
        const a =
            Math.sin(dLat/2) * Math.sin(dLat/2) +
            Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
            Math.sin(dLon/2) * Math.sin(dLon/2);
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
        return R * c;
    }

    // 잔여 거리 계산 함수 (기존 코드 유지)
    function calculateRemainingDistance(currentIndex) {
        if (currentIndex >= currentRoutePolylinePath.length - 1) {
            return 0;
        }
        let remainingDistance = 0;
        for (let i = currentIndex; i < currentRoutePolylinePath.length - 1; i++) {
            const point1 = currentRoutePolylinePath[i];
            const point2 = currentRoutePolylinePath[i + 1];
            remainingDistance += calculateDistance(
                point1.getLat(), point1.getLng(),
                point2.getLat(), point2.getLng()
            );
        }
        return remainingDistance;
    }

    // ETA 계산 함수 (기존 코드 유지)
    function calculateETA(remainingDistanceKm, speedKmH) {
        const remainingTimeHours = remainingDistanceKm / speedKmH;
        const remainingTimeMinutes = remainingTimeHours * 60;

        const now = new Date();
        now.setMinutes(now.getMinutes() + remainingTimeMinutes);

        return {
            estimatedTime: Math.ceil(remainingTimeMinutes),
            arrivalTime: now
        };
    }

    // 네비게이션 UI 업데이트 함수 (기존 코드 유지)
    function updateNavigationUI(remainingDistanceKm, estimatedMinutes, arrivalTime) {
        document.getElementById('current-remaining-distance').textContent = `잔여 거리: ${remainingDistanceKm.toFixed(1)}km`;
        document.getElementById('current-eta').textContent =
            `예상 도착 시간: ${arrivalTime.getHours() % 12 || 12}:${arrivalTime.getMinutes().toString().padStart(2, '0')} ${arrivalTime.getHours() >= 12 ? '오후' : '오전'}`;
        document.getElementById('display-estimated-time').textContent = `예상 ${estimatedMinutes}분`;
    }

    // 네비게이션 시뮬레이션 시작 함수 (기존 코드 유지)
    function startNavigationSimulation(speedKmH, startAddrDisplay, endAddrDisplay) { // display용 주소 추가
        if (currentRoutePolylinePath.length === 0) {
            alert("경로 데이터가 없어 시뮬레이션을 시작할 수 없습니다. 먼저 경로를 검색해주세요.");
            return;
        }

        console.log(`네비게이션 시뮬레이션 시작: ${speedKmH}km/h로 ${startAddrDisplay}에서 ${endAddrDisplay}까지`);
        guidanceActive = true;
        currentSpeed = speedKmH;
        updateGuidanceButtonState();
        alert(`안내를 시작합니다!\n출발지: ${startAddrDisplay}\n도착지: ${endAddrDisplay}\n초기 속도: ${speedKmH}km/h`);

        if (simulationIntervalId) {
            clearInterval(simulationIntervalId);
        }
        currentSimulationIndex = 0;

        // 현재 위치 마커 설정
        if (!currentLocationMarker) {
            const markerImageSrc = 'https://t1.daumcdn.net/localimg/localimages/07/mapapidoc/marker_red.png';
            const markerImageSize = new kakao.maps.Size(30, 30);
            const markerImageOption = { offset: new kakao.maps.Point(15, 15) };
            const markerImage = new kakao.maps.MarkerImage(markerImageSrc, markerImageSize, markerImageOption);

            currentLocationMarker = new kakao.maps.Marker({
                map: map,
                position: currentRoutePolylinePath[0],
                image: markerImage
            });
        } else {
            currentLocationMarker.setPosition(currentRoutePolylinePath[0]);
            currentLocationMarker.setMap(map);
        }
        map.setCenter(currentRoutePolylinePath[0]);

        map.setLevel(5); // 네비게이션 시작 시 지도를 더 확대합니다. (레벨 5)

        const speedMps = speedKmH * 1000 / 3600;

        simulationIntervalId = setInterval(() => {
            if (currentSimulationIndex >= currentRoutePolylinePath.length - 1) {
                console.log("시뮬레이션 종료: 목적지에 도달했습니다.");
                stopNavigation();
                alert("목적지에 도착했습니다! 안내를 종료합니다.");
                return;
            }

            currentSimulationIndex++;
            const nextPosition = currentRoutePolylinePath[currentSimulationIndex];

            if (currentLocationMarker) {
                currentLocationMarker.setPosition(nextPosition);
                map.setCenter(nextPosition);
            }

            const remainingDistance = calculateRemainingDistance(currentSimulationIndex);
            const etaData = calculateETA(remainingDistance, currentSpeed);

            updateNavigationUI(remainingDistance, etaData.estimatedTime, etaData.arrivalTime);

            sendLocationToServer({
                latitude: nextPosition.getLat(),
                longitude: nextPosition.getLng(),
                speed: currentSpeed,
                timestamp: new Date().toISOString(),
                status: 'navigation_active',
                remainingDistance: remainingDistance,
                estimatedArrivalTime: etaData.arrivalTime.toISOString()
            });

        }, 200);
    } // startNavigationSimulation 함수 닫는 괄호

    // 네비게이션 종료 함수 (기존 코드 유지)
    function stopNavigation() {
        console.log("네비게이션이 종료되었습니다.");
        guidanceActive = false;
        updateGuidanceButtonState();

        if (simulationIntervalId !== null) {
            clearInterval(simulationIntervalId);
            simulationIntervalId = null;
        }
        if (currentLocationMarker) {
            currentLocationMarker.setMap(null);
        }
        sendLocationToServer({ status: 'navigation_inactive' });
    }

    // 위치 데이터 전송 함수 (기존 코드 유지)
    function sendLocationToServer(locationData) {
        fetch('/send_location', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(locationData)
        })
        .then(response => response.json())
        .then(data => {
            // console.log('위치 데이터 전송 성공:', data);
        })
        .catch(error => {
            console.error('위치 데이터 전송 실패:', error);
        });
    }

    // 카카오 주소 검색 API 연동 (기존 코드 유지)
    inputStartAddress.addEventListener("click", function () {
        new daum.Postcode({
            oncomplete: function (data) {
                inputStartAddress.value = data.address;
            }
        }).open();
    });

    inputEndAddress.addEventListener("click", function () {
        new daum.Postcode({
            oncomplete: function (data) {
                inputEndAddress.value = data.address;
            }
        }).open();
    });

    // 안내 버튼 상태 업데이트 함수 (기존 코드 유지)
    function updateGuidanceButtonState() {
        if (startGuidanceButton) {
            if (guidanceActive) {
                startGuidanceButton.innerHTML = `
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9v-9"></path>
                    </svg>
                    <span class="text-sm">안내 종료</span>
                `;
                startGuidanceButton.classList.remove('bg-blue-600', 'hover:bg-blue-700');
                startGuidanceButton.classList.add('bg-green-600', 'hover:bg-green-700');
            } else {
                startGuidanceButton.innerHTML = `
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"></path>
                    </svg>
                    <span class="text-sm">안내 시작</span>
                `;
                startGuidanceButton.classList.remove('bg-green-600', 'hover:bg-green-700');
                startGuidanceButton.classList.add('bg-blue-600', 'hover:bg-blue-700');
            }
        }
    }

    if (startGuidanceButton) { // startGuidanceButton이 존재하는지 확인 (기존 코드 유지)
        startGuidanceButton.addEventListener('click', function() {
            if (guidanceActive) {
                stopNavigation();
            } else {
                // 시뮬레이션 시작 시에는 현재 UI에 표시된 주소를 사용
                const startAddrDisplay = currentStartAddressElem.textContent.replace('출발지: ', '');
                const endAddrDisplay = currentEndAddressElem.textContent.replace('도착지: ', '');

                if (!startAddrDisplay || !endAddrDisplay || startAddrDisplay.includes('미정') || endAddrDisplay.includes('미정')) {
                    alert("출발지 또는 도착지 주소가 설정되지 않았습니다. 경로를 먼저 검색해주세요.");
                    return;
                }
                const initialSpeed = 60;
                startNavigationSimulation(initialSpeed, startAddrDisplay, endAddrDisplay);
            }
        });
    }


    // ====== 카카오 주소 검색 API 연동 로직 (기존 코드 유지) ======

    // 주소 검색 팝업을 여는 함수
    function openPostcodeSearch(targetInputId) {
        new daum.Postcode({
            oncomplete: function(data) {
                let fullRoadAddr = data.roadAddress;
                let extraRoadAddr = '';

                if (data.bname !== '' && /[동|로|가]$/g.test(data.bname)){
                    extraRoadAddr += data.bname;
                }
                if (data.buildingName !== '' && data.apartment === 'Y'){
                    extraRoadAddr += (extraRoadAddr !== '' ? ', ' + data.buildingName : data.buildingName);
                }
                if (extraRoadAddr !== ''){
                    fullRoadAddr += ' (' + extraRoadAddr + ')';
                }

                document.getElementById(targetInputId).value = fullRoadAddr;
            }
        }).open();
    }

    // 주소 검색 버튼 이벤트 리스너
    if (searchStartAddressButton) {
        searchStartAddressButton.addEventListener('click', function() {
            openPostcodeSearch('inputStartAddress');
        });
    }

    if (searchEndAddressButton) {
        searchEndAddressButton.addEventListener('click', function() {
            openPostcodeSearch('inputEndAddress');
        });
    }

    // ====== 카카오 주소 검색 API 연동 로직 끝 ======

    // 현재 위치를 가져오는 Promise 기반 함수 추가
    function getCurrentLocation() {
        return new Promise((resolve, reject) => {
            if (navigator.geolocation) {
                navigator.geolocation.getCurrentPosition(
                    (position) => {
                        const lat = position.coords.latitude;
                        const lon = position.coords.longitude;
                        console.log(`현재 위치: 위도 ${lat}, 경도 ${lon}`);
                        resolve({ lat, lon });
                    },
                    (error) => {
                        console.error("현재 위치를 가져오는 데 실패했습니다:", error);
                        alert("현재 위치를 가져올 수 없습니다. 기본 위치로 지도를 표시합니다.");
                        reject(error);
                    },
                    {
                        enableHighAccuracy: true, // 높은 정확도 요구
                        timeout: 10000,           // 10초 타임아웃
                        maximumAge: 0             // 캐시된 위치 사용 안 함
                    }
                );
            } else {
                alert("이 브라우저에서는 Geolocation을 지원하지 않습니다.");
                reject(new Error("Geolocation not supported"));
            }
        });
    }

    kakao.maps.load(function() {
        const urlParams = new URLSearchParams(window.location.search);
        const initialStartAddrParam = urlParams.get('start'); // 요청 출발지 (경유지)
        const initialEndAddrParam = urlParams.get('end');     // 요청 도착지 (최종 도착지)
        const navigationMode = urlParams.get('mode') || 'manual';

        // 페이지 로드 시 모든 UI 요소의 초기 display 상태를 설정합니다. (기존 코드 유지)
        if (currentTripStatusSection) currentTripStatusSection.style.display = 'none';
        if (realtimeNavigationSection) realtimeNavigationSection.style.display = 'none';
        if (recentRoutesSection) recentRoutesSection.style.display = 'none';
        if (mapLoadingOverlay) mapLoadingOverlay.style.display = 'none';
        if (routeInfoOverlay) routeInfoOverlay.style.display = 'none';
        if (navSummaryOverlay) navSummaryOverlay.style.display = 'none';

        if (manualInputSection) manualInputSection.style.display = 'block'; // '주소 직접 입력' 섹션은 기본적으로 보이게 함.

        // 경로를 가져오고 지도에 그리는 핵심 함수 수정
        async function loadAndDrawRoute(currentLocationLatLon, firstWaypointAddress, finalDestinationAddress) {
            // 경로 검색 시작 시 로딩 오버레이 표시 및 지도 섹션 보이게 설정 (기존 코드 유지)
            if (mapLoadingOverlay) mapLoadingOverlay.style.display = 'flex';
            if (realtimeNavigationSection) realtimeNavigationSection.style.display = 'block';

            // 다른 UI 요소들도 함께 숨겨서 깔끔하게 로딩 화면만 보이도록 (기존 코드 유지)
            if (currentTripStatusSection) currentTripStatusSection.style.display = 'none';
            if (manualInputSection) manualInputSection.style.display = 'none';


            // 경로를 가져오기 전에 지도가 생성되지 않았다면, 여기서 생성합니다. (기존 코드 유지)
            if (!map) {
                console.log("지도 객체가 없어 새로 생성합니다.");
                // 현재 위치를 가져오기 전에 지도를 초기화해야 할 경우를 대비한 기본 중심
                initializeMap(37.566826, 126.9786567);
            } else {
                map.relayout();
            }

            if (!currentLocationLatLon || !finalDestinationAddress) {
                alert("경로를 검색하려면 현재 위치와 도착지 주소가 모두 필요합니다.");
                if (mapLoadingOverlay) mapLoadingOverlay.style.display = 'none';
                if (manualInputSection) manualInputSection.style.display = 'block';
                if (realtimeNavigationSection) realtimeNavigationSection.style.display = 'none';
                return;
            }

            // 기존 마커 및 폴리라인 제거
            if (currentPolyline) currentPolyline.setMap(null);
            if (startMarker) startMarker.setMap(null);
            if (endMarker) endMarker.setMap(null);
            if (currentLocationMarker) currentLocationMarker.setMap(null);
            // 모든 경유지 마커 제거
            waypointMarkers.forEach(marker => marker.setMap(null));
            waypointMarkers = [];


            const payload = {
                start_addr: `${currentLocationLatLon.lat},${currentLocationLatLon.lon}`, // 현재 위치 (위도,경도)
                end_addr: finalDestinationAddress, // 최종 도착지
                pass_addr_list: []
            };

            // '입력한 출발지'가 최종 도착지와 다르고, 유효한 경우 경유지로 추가
            if (firstWaypointAddress && firstWaypointAddress.trim() !== '' && firstWaypointAddress !== finalDestinationAddress) {
                payload.pass_addr_list.push(firstWaypointAddress);
            }
            console.log("경로 요청 페이로드:", payload);

            try {
                const response = await fetch('/route_process', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const data = await response.json();
                if (data.error) {
                    alert("경로를 가져오는 데 실패했습니다: " + data.error);
                    if (mapLoadingOverlay) mapLoadingOverlay.style.display = 'none';
                    if (manualInputSection) manualInputSection.style.display = 'block';
                    if (realtimeNavigationSection) realtimeNavigationSection.style.display = 'none';
                    return;
                }

                const routeCoordinates = data.coords;
                const totalDistance = data.totalDistance;
                const totalTime = data.totalTime;
                const passCoords = data.passCoords || []; // 경유지 좌표 배열
                totalRouteDistance = totalDistance;

                if (routeCoordinates.length === 0) {
                    alert("경로 데이터가 없습니다. 주소를 다시 확인해주세요.");
                    if (mapLoadingOverlay) mapLoadingOverlay.style.display = 'none';
                    if (manualInputSection) manualInputSection.style.display = 'block';
                    if (realtimeNavigationSection) realtimeNavigationSection.style.display = 'none';
                    return;
                }

                currentRoutePolylinePath = routeCoordinates.map(coord => new kakao.maps.LatLng(coord.lat, coord.lon));

                currentPolyline = new kakao.maps.Polyline({
                    path: currentRoutePolylinePath,
                    strokeWeight: 5,
                    strokeColor: '#FF3E00',
                    strokeOpacity: 0.7,
                    strokeStyle: 'solid'
                });
                currentPolyline.setMap(map);

                const startPoint = currentRoutePolylinePath[0]; // 실제 경로의 시작점 (현재 위치)
                const endPoint = currentRoutePolylinePath[currentRoutePolylinePath.length - 1]; // 실제 경로의 끝점 (최종 도착지)

                // 도착 마커 (최종 도착지)
                endMarker = new kakao.maps.Marker({
                    position: endPoint,
                    image: new kakao.maps.MarkerImage(
                        'https://t1.daumcdn.net/localimg/localimages/07/mapapidoc/blue_b.png', // 파란색 마커
                        new kakao.maps.Size(24, 35),
                        { offset: new kakao.maps.Point(12, 35) }
                    )
                });
                endMarker.setMap(map);

                // 출발지 마커 
                passCoords.forEach((passCoord, index) => {
                    const waypointMarker = new kakao.maps.Marker({
                        position: new kakao.maps.LatLng(passCoord.lat, passCoord.lon),
                        image: new kakao.maps.MarkerImage(
                            'https://t1.daumcdn.net/localimg/localimages/07/mapapidoc/red_b.png',
                            new kakao.maps.Size(24, 35),
                            { offset: new kakao.maps.Point(12, 35) }
                        )
                    });
                    waypointMarker.setMap(map);
                    waypointMarkers.push(waypointMarker); // 배열에 추가하여 나중에 제거할 수 있도록
                });


                const bounds = new kakao.maps.LatLngBounds();
                currentRoutePolylinePath.forEach(point => bounds.extend(point));
                map.setBounds(bounds);

                // UI 업데이트
                if (currentStartAddressElem) currentStartAddressElem.textContent = `출발: ${firstWaypointAddress}`;
                if (currentEndAddressElem) currentEndAddressElem.textContent = `도착지: ${finalDestinationAddress}`;
                if (document.getElementById('display-start-address')) document.getElementById('display-start-address').textContent = `출발: ${firstWaypointAddress}`;
                if (document.getElementById('display-end-address')) document.getElementById('display-end-address').textContent = `도착: ${finalDestinationAddress}`;
                if (document.getElementById('display-total-distance')) document.getElementById('display-total-distance').textContent = `${(totalDistance / 1000).toFixed(1)}km`;
                if (document.getElementById('current-remaining-distance')) document.getElementById('current-remaining-distance').textContent = `잔여 거리: ${(totalDistance / 1000).toFixed(1)}km`;

                const estimatedMinutes = Math.ceil(totalTime / 60);
                if (document.getElementById('display-estimated-time')) document.getElementById('display-estimated-time').textContent = `예상 ${estimatedMinutes}분`;
                const now = new Date();
                now.setMinutes(now.getMinutes() + estimatedMinutes);
                if (document.getElementById('current-eta')) document.getElementById('current-eta').textContent = `예상 도착 시간: ${now.getHours() % 12 || 12}:${now.getMinutes().toString().padStart(2, '0')} ${now.getHours() >= 12 ? '오후' : '오전'}`;

                // 경로 검색 완료 후 UI 섹션 표시 (기존 코드 유지)
                if (mapLoadingOverlay) mapLoadingOverlay.style.display = 'none';
                if (currentTripStatusSection) currentTripStatusSection.style.display = 'block';
                if (routeInfoOverlay) routeInfoOverlay.style.display = 'block';
                if (navSummaryOverlay) navSummaryOverlay.style.display = 'block';

            } catch (error) { // 에러 처리 (기존 코드 유지)
                console.error("경로 데이터를 가져오거나 지도에 그리는 중 오류 발생:", error);
                alert("경로를 표시하는 데 문제가 생겼습니다. 개발자 도구(F12)의 콘솔 탭을 확인해주세요.");
                if (mapLoadingOverlay) mapLoadingOverlay.style.display = 'none';
                if (manualInputSection) manualInputSection.style.display = 'block';
                if (realtimeNavigationSection) realtimeNavigationSection.style.display = 'none';
            }
        }

        // 초기 페이지 로드 시 모드에 따른 UI 상태 설정
        if (navigationMode === 'request' && initialStartAddrParam && initialEndAddrParam) {
            if (manualInputSection) manualInputSection.style.display = 'none';
            if (currentTripStatusSection) currentTripStatusSection.style.display = 'block';
            if (realtimeNavigationSection) realtimeNavigationSection.style.display = 'block';
            if (mapLoadingOverlay) mapLoadingOverlay.style.display = 'flex';
            if (routeInfoOverlay) routeInfoOverlay.style.display = 'none';
            if (navSummaryOverlay) navSummaryOverlay.style.display = 'none';

            if (!map) {
                console.log("요청 모드에서 지도 객체가 없어 새로 생성합니다.");
                initializeMap(37.566826, 126.9786567); // 기본 위치로 지도 초기화
            }
            if (map) {
                map.relayout();
            }

            // 요청 모드일 때 현재 위치를 가져와서 경로를 그립니다.
            getCurrentLocation().then(currentLoc => {
                // initialStartAddrParam은 이제 경유지, initialEndAddrParam은 최종 도착지
                loadAndDrawRoute(currentLoc, initialStartAddrParam, initialEndAddrParam);
            }).catch(error => {
                alert("현재 위치를 가져올 수 없어 요청된 경로를 표시할 수 없습니다.");
                // 에러 발생 시 수동 입력 섹션 표시
                if (mapLoadingOverlay) mapLoadingOverlay.style.display = 'none';
                if (manualInputSection) manualInputSection.style.display = 'block';
                if (realtimeNavigationSection) realtimeNavigationSection.style.display = 'none';
            });

        } else {
            // 주소 직접 입력 모드 또는 파라미터가 없는 경우 (기존 코드 유지)
            if (currentTripStatusSection) currentTripStatusSection.style.display = 'none';
            if (realtimeNavigationSection) realtimeNavigationSection.style.display = 'none';
            if (mapLoadingOverlay) mapLoadingOverlay.style.display = 'none';

            if (currentStartAddressElem) currentStartAddressElem.textContent = `출발지: 주소 미정`;
            if (currentEndAddressElem) currentEndAddressElem.textContent = `도착지: 주소 미정`;
            if (document.getElementById('display-start-address')) document.getElementById('display-start-address').textContent = `출발: 주소 미정`;
            if (document.getElementById('display-end-address')) document.getElementById('display-end-address').textContent = `도착: 주소 미정`;
            if (document.getElementById('display-total-distance')) document.getElementById('display-total-distance').textContent = `0.0km`;
            if (document.getElementById('current-remaining-distance')) document.getElementById('current-remaining-distance').textContent = `잔여 거리: 0.0km`;
            if (document.getElementById('display-estimated-time')) document.getElementById('display-estimated-time').textContent = `예상 0분`;
            if (document.getElementById('current-eta')) document.getElementById('current-eta').textContent = `예상 도착 시간: --:--`;
            if (routeInfoOverlay) routeInfoOverlay.style.display = 'none';
            if (navSummaryOverlay) navSummaryOverlay.style.display = 'none';
        }

        // "경로 재검색" 버튼 클릭 이벤트 (기존 코드 유지)
        const reRouteButton = document.getElementById('re-route-button');
        if (reRouteButton) {
            reRouteButton.addEventListener('click', function() {
                // 재검색 시에도 현재 위치를 출발지로 사용
                const firstWaypoint = inputStartAddress.value.trim(); // 입력한 출발지 (경유지)
                const finalDestination = inputEndAddress.value.trim(); // 입력한 도착지 (최종 도착지)

                if (!firstWaypoint || !finalDestination) {
                    alert("재검색할 주소가 없습니다. 주소를 먼저 입력하거나 선택해주세요.");
                    return;
                }
                alert("경로를 재검색합니다.");
                getCurrentLocation().then(currentLoc => {
                    loadAndDrawRoute(currentLoc, firstWaypoint, finalDestination);
                }).catch(error => {
                    alert("현재 위치를 가져올 수 없어 경로를 재검색할 수 없습니다.");
                });
            });
        }

        // "주소 직접 입력" 섹션의 "경로 검색" 버튼 클릭 이벤트 (수정됨)
        if (searchManualRouteButton) {
            searchManualRouteButton.addEventListener('click', function() {
                const firstWaypoint = inputStartAddress.value.trim(); // 입력한 출발지 (경유지)
                const finalDestination = inputEndAddress.value.trim(); // 입력한 도착지 (최종 도착지)

                if (!firstWaypoint || !finalDestination) {
                    alert("출발지와 도착지 주소를 모두 검색하여 입력해주세요.");
                    return;
                }

                alert("경로를 안내합니다.");
                getCurrentLocation().then(currentLoc => {
                    loadAndDrawRoute(currentLoc, firstWaypoint, finalDestination);
                }).catch(error => {
                    alert("현재 위치를 가져올 수 없어 경로를 검색할 수 없습니다.");
                });
            });
        }

        document.querySelectorAll('.recent-route-item button').forEach(button => {
            button.addEventListener('click', function() {
                const startAddr = this.dataset.startAddr; // 이전에 저장된 출발지 (경유지)
                const endAddr = this.dataset.endAddr;     // 이전에 저장된 도착지 (최종 도착지)
                alert("경로를 안내합니다.");
                getCurrentLocation().then(currentLoc => {
                    loadAndDrawRoute(currentLoc, startAddr, endAddr);
                }).catch(error => {
                    alert("현재 위치를 가져올 수 없어 경로를 안내할 수 없습니다.");
                });
            });
        });
    });
});