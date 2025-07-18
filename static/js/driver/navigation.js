document.addEventListener('DOMContentLoaded', function() {
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
    const recentRoutesSection = document.getElementById('recent-routes-section');

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

    const mapContainer = document.getElementById('map');


    // UI 텍스트 및 스타일 업데이트 함수 (이 함수는 그대로 둡니다)
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

    // 운전자 상태를 서버로 전송하는 함수
    async function sendDriverStatusToServer(status) {
        // test_driver_id 대신 localStorage에서 driverId를 가져옵니다.
        const driverId = localStorage.getItem('loggedInDriverId');

        if (!driverId) {
            console.error('Driver ID를 찾을 수 없습니다. 로그인 상태를 확인하세요.');
            alert('로그인이 필요합니다. 다시 로그인 해주세요.');
            // UI를 원래 상태로 되돌리기 (옵션)
            if (driverStatusToggle) { // 토글이 존재하는지 다시 한번 확인
                driverStatusToggle.checked = !driverStatusToggle.checked;
                updateDriverStatusTextUI(driverStatusToggle.checked);
            }
            return;
        }

        try {
            const response = await fetch('/update_driver_status', { // 이 URL은 백엔드에서 상태를 업데이트할 엔드포인트입니다.
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    driver_id: driverId, // localStorage에서 가져온 driverId 사용
                    status: status // 0: 운행 중(가능), 1: 운행 종료(불가)
                })
            });
            const data = await response.json();
            if (data.success) {
                console.log(`운전자 상태 DB 업데이트 성공: ${status}`);
            } else {
                console.error('운전자 상태 DB 업데이트 실패:', data.message);
                alert('운전자 상태 업데이트에 실패했습니다: ' + data.message);
                // 실패 시 UI를 원래 상태로 되돌리기
                if (driverStatusToggle) {
                    driverStatusToggle.checked = !driverStatusToggle.checked;
                    updateDriverStatusTextUI(driverStatusToggle.checked);
                }
            }
        } catch (error) {
            console.error('운전자 상태 DB 업데이트 중 통신 오류 발생:', error);
            alert('운전자 상태 업데이트 중 통신 오류 발생.');
            // 오류 발생 시 UI를 원래 상태로 되돌리기
            if (driverStatusToggle) {
                driverStatusToggle.checked = !driverStatusToggle.checked;
                updateDriverStatusTextUI(driverStatusToggle.checked);
            }
        }
    }

    // 페이지 로드 시 운전자의 초기 상태를 DB에서 가져와 토글에 반영하는 함수
    async function loadDriverStatus() {
        // test_driver_id 대신 localStorage에서 driverId를 가져옵니다.
        const driverId = localStorage.getItem('loggedInDriverId');

        if (!driverId) {
            console.warn('Driver ID를 찾을 수 없습니다. 초기 상태 로드를 건너뜁니다.');
            // driverStatusToggle이 있다면 기본값을 설정합니다.
            if (driverStatusToggle) {
                driverStatusToggle.checked = false; // 기본적으로 운행 불가
                updateDriverStatusTextUI(driverStatusToggle.checked);
            }
            return;
        }

        try {
            const response = await fetch(`/get_driver_status?driver_id=${driverId}`); // 백엔드 GET 엔드포인트
            const data = await response.json();
            if (data.success) {
                if (driverStatusToggle) { // 토글이 존재하는 경우에만 처리
                    driverStatusToggle.checked = (data.status === 0);
                    updateDriverStatusTextUI(driverStatusToggle.checked); // UI 텍스트 업데이트
                }
                console.log(`운전자 초기 상태 로드 성공: ${data.status}`);
            } else {
                console.error('운전자 초기 상태 로드 실패:', data.message);
                // 실패 시 기본값(운행 불가)으로 설정
                if (driverStatusToggle) {
                    driverStatusToggle.checked = false;
                    updateDriverStatusTextUI(driverStatusToggle.checked);
                }
            }
        } catch (error) {
            console.error('운전자 초기 상태 로드 중 오류 발생:', error);
            // 오류 발생 시 기본값(운행 불가)으로 설정
            if (driverStatusToggle) {
                driverStatusToggle.checked = false;
                updateDriverStatusTextUI(driverStatusToggle.checked);
            }
        }
    }

    // Initial state for driver status toggle
    if (driverStatusToggle && driverStatusText) {
        // 토글 변경 이벤트 리스너 (이 부분은 그대로 둡니다)
        driverStatusToggle.addEventListener('change', function() {
            const statusValue = this.checked ? 0 : 1; // 0: 운행 가능(운행 중), 1: 운행 불가(운행 종료)
            updateDriverStatusTextUI(this.checked); // UI 먼저 업데이트
            sendDriverStatusToServer(statusValue); // DB 업데이트 요청
        });
    } else {
        console.error("driverStatusToggle 또는 driverStatusText 요소를 찾을 수 없습니다.");
    }

    // 지도를 실제로 생성하는 함수. 이제 이 함수가 필요한 시점에만 호출됩니다.
    function initializeMap(latitude, longitude) {
        const mapOption = {
            center: new kakao.maps.LatLng(latitude, longitude),
            level: 3 // 초기 레벨을 3으로 유지하여 너무 과도한 확대 방지
        };
        map = new kakao.maps.Map(mapContainer, mapOption);
        console.log("카카오맵 초기화 완료.");
    }

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

    function updateNavigationUI(remainingDistanceKm, estimatedMinutes, arrivalTime) {
        document.getElementById('current-remaining-distance').textContent = `잔여 거리: ${remainingDistanceKm.toFixed(1)}km`;
        document.getElementById('current-eta').textContent =
            `예상 도착 시간: ${arrivalTime.getHours() % 12 || 12}:${arrivalTime.getMinutes().toString().padStart(2, '0')} ${arrivalTime.getHours() >= 12 ? '오후' : '오전'}`;
        document.getElementById('display-estimated-time').textContent = `예상 ${estimatedMinutes}분`;
    }

    function startNavigationSimulation(speedKmH, startAddr, endAddr) {
        if (currentRoutePolylinePath.length === 0) {
            alert("경로 데이터가 없어 시뮬레이션을 시작할 수 없습니다. 먼저 경로를 검색해주세요.");
            return;
        }

        console.log(`네비게이션 시뮬레이션 시작: ${speedKmH}km/h로 ${startAddr}에서 ${endAddr}까지`);
        guidanceActive = true;
        currentSpeed = speedKmH;
        updateGuidanceButtonState();
        alert(`안내를 시작합니다!\n출발지: ${startAddr}\n도착지: ${endAddr}\n초기 속도: ${speedKmH}km/h`);

        if (simulationIntervalId) {
            clearInterval(simulationIntervalId);
        }
        currentSimulationIndex = 0;

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

        // 네비게이션 시작 시 지도를 더 확대합니다. (레벨 5)
        map.setLevel(5);

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

    function updateGuidanceButtonState() {
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

    startGuidanceButton.addEventListener('click', function() {
        if (guidanceActive) {
            stopNavigation();
        } else {
            const currentStartAddress = currentStartAddressElem.textContent.replace('출발지: ', '');
            const currentEndAddress = currentEndAddressElem.textContent.replace('도착지: ', '');

            if (!currentStartAddress || !currentEndAddress || currentStartAddress.includes('미정') || currentEndAddress.includes('미정')) {
                alert("출발지 또는 도착지 주소가 설정되지 않았습니다. 경로를 먼저 검색해주세요.");
                return;
            }
            const initialSpeed = 60;
            startNavigationSimulation(initialSpeed, currentStartAddress, currentEndAddress);
        }
    });

    kakao.maps.load(function() {
        const urlParams = new URLSearchParams(window.location.search);
        const initialStartAddrParam = urlParams.get('start');
        const initialEndAddrParam = urlParams.get('end');
        const navigationMode = urlParams.get('mode') || 'manual';

        // 페이지 로드 시 모든 UI 요소의 초기 display 상태를 설정합니다.
        // HTML에서 style="display: none;"을 제거했으므로, 여기서 명시적으로 설정합니다.
        currentTripStatusSection.style.display = 'none';
        realtimeNavigationSection.style.display = 'none';
        recentRoutesSection.style.display = 'none';
        mapLoadingOverlay.style.display = 'none';
        routeInfoOverlay.style.display = 'none';
        navSummaryOverlay.style.display = 'none';

        // '주소 직접 입력' 섹션은 기본적으로 보이게 합니다.
        manualInputSection.style.display = 'block';

        // 페이지 로드 완료 후 초기 운전자 상태 로드
        // driverStatusToggle이 존재하는 경우에만 loadDriverStatus 호출
        if (driverStatusToggle) {
            loadDriverStatus();
        }

        async function loadAndDrawRoute(startAddress, endAddress) {
            // 경로 검색 시작 시 로딩 오버레이 표시 및 지도 섹션 보이게 설정
            mapLoadingOverlay.style.display = 'flex';
            realtimeNavigationSection.style.display = 'block';

            // 다른 UI 요소들도 함께 숨겨서 깔끔하게 로딩 화면만 보이도록
            currentTripStatusSection.style.display = 'none';
            manualInputSection.style.display = 'none';
            recentRoutesSection.style.display = 'none';

            // 경로를 가져오기 전에 지도가 생성되지 않았다면, 여기서 생성합니다.
            if (!map) {
                console.log("지도 객체가 없어 새로 생성합니다.");
                // 지도를 처음 생성할 때 기본 위치 (서울)로 설정합니다.
                initializeMap(37.566826, 126.9786567);
            } else {
                // 지도가 이미 생성되어 있다면, 컨테이너 크기 변경에 맞춰 relayout 호출
                map.relayout();
            }

            if (!startAddress || !endAddress) {
                alert("출발지 또는 도착지 주소가 유효하지 않습니다.");
                mapLoadingOverlay.style.display = 'none';
                manualInputSection.style.display = 'block';
                realtimeNavigationSection.style.display = 'none'; // 에러 시 지도 섹션 숨김
                return;
            }

            try {
                const response = await fetch('/route_process', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ start_addr: startAddress, end_addr: endAddress })
                });
                const data = await response.json();
                if (data.error) {
                    alert("경로를 가져오는 데 실패했습니다: " + data.error);
                    mapLoadingOverlay.style.display = 'none';
                    manualInputSection.style.display = 'block';
                    realtimeNavigationSection.style.display = 'none'; // 에러 시 지도 섹션 숨김
                    return;
                }

                const routeCoordinates = data.coords;
                const totalDistance = data.totalDistance;
                const totalTime = data.totalTime;
                totalRouteDistance = totalDistance;

                if (routeCoordinates.length === 0) {
                    alert("경로 데이터가 없습니다. 주소를 다시 확인해주세요.");
                    mapLoadingOverlay.style.display = 'none';
                    manualInputSection.style.display = 'block';
                    realtimeNavigationSection.style.display = 'none'; // 에러 시 지도 섹션 숨김
                    return;
                }

                // 기존 마커 및 폴리라인 제거
                if (currentPolyline) currentPolyline.setMap(null);
                if (startMarker) startMarker.setMap(null);
                if (endMarker) endMarker.setMap(null);
                if (currentLocationMarker) currentLocationMarker.setMap(null);

                currentRoutePolylinePath = routeCoordinates.map(coord => new kakao.maps.LatLng(coord.lat, coord.lon));

                currentPolyline = new kakao.maps.Polyline({
                    path: currentRoutePolylinePath,
                    strokeWeight: 5,
                    strokeColor: '#FF3E00',
                    strokeOpacity: 0.7,
                    strokeStyle: 'solid'
                });
                currentPolyline.setMap(map);

                const startPoint = currentRoutePolylinePath[0];
                const endPoint = currentRoutePolylinePath[currentRoutePolylinePath.length - 1];

                const startImageSrc = 'https://t1.daumcdn.net/localimg/localimages/07/mapapidoc/red_b.png';
                const endImageSrc = 'https://t1.daumcdn.net/localimg/localimages/07/mapapidoc/blue_b.png';

                startMarker = new kakao.maps.Marker({
                    position: startPoint,
                    image: new kakao.maps.MarkerImage(
                        startImageSrc,
                        new kakao.maps.Size(24, 35),
                        { offset: new kakao.maps.Point(12, 35) }
                    )
                });
                startMarker.setMap(map);

                endMarker = new kakao.maps.Marker({
                    position: endPoint,
                    image: new kakao.maps.MarkerImage(
                        endImageSrc,
                        new kakao.maps.Size(24, 35),
                        { offset: new kakao.maps.Point(12, 35) }
                    )
                });
                endMarker.setMap(map);

                const bounds = new kakao.maps.LatLngBounds();
                currentRoutePolylinePath.forEach(point => bounds.extend(point));
                map.setBounds(bounds); // 경로 전체가 보이도록 지도 범위 설정

                // UI 업데이트
                currentStartAddressElem.textContent = `출발지: ${startAddress}`;
                currentEndAddressElem.textContent = `도착지: ${endAddress}`;
                document.getElementById('display-start-address').textContent = `출발: ${startAddress}`;
                document.getElementById('display-end-address').textContent = `도착: ${endAddress}`;
                document.getElementById('display-total-distance').textContent = `${(totalDistance / 1000).toFixed(1)}km`;
                document.getElementById('current-remaining-distance').textContent = `잔여 거리: ${(totalDistance / 1000).toFixed(1)}km`;

                const estimatedMinutes = Math.ceil(totalTime / 60);
                document.getElementById('display-estimated-time').textContent = `예상 ${estimatedMinutes}분`;
                const now = new Date();
                now.setMinutes(now.getMinutes() + estimatedMinutes);
                document.getElementById('current-eta').textContent = `예상 도착 시간: ${now.getHours() % 12 || 12}:${now.getMinutes().toString().padStart(2, '0')} ${now.getHours() >= 12 ? '오후' : '오전'}`;

                // 경로 검색 완료 후 UI 섹션 표시
                mapLoadingOverlay.style.display = 'none';
                currentTripStatusSection.style.display = 'block';
                recentRoutesSection.style.display = 'block';
                routeInfoOverlay.style.display = 'block';
                navSummaryOverlay.style.display = 'block';

            } catch (error) {
                console.error("경로 데이터를 가져오거나 지도에 그리는 중 오류 발생:", error);
                alert("경로를 표시하는 데 문제가 생겼습니다. 개발자 도구(F12)의 콘솔 탭을 확인해주세요.");
                mapLoadingOverlay.style.display = 'none';
                manualInputSection.style.display = 'block';
                realtimeNavigationSection.style.display = 'none'; // 에러 시 지도 섹션 숨김
            }
        }

        // 초기 페이지 로드 시 모드에 따른 UI 상태 설정
        if (navigationMode === 'request' && initialStartAddrParam && initialEndAddrParam) {
            // 운송 요청에서 넘어온 경우
            manualInputSection.style.display = 'none';
            currentTripStatusSection.style.display = 'block';
            realtimeNavigationSection.style.display = 'block'; // 지도를 담는 div를 보이게 함
            recentRoutesSection.style.display = 'block';
            mapLoadingOverlay.style.display = 'flex';
            routeInfoOverlay.style.display = 'none';
            navSummaryOverlay.style.display = 'none';

            // 경로 요청이 있는 경우, 여기서 지도를 생성합니다.
            if (!map) {
                console.log("요청 모드에서 지도 객체가 없어 새로 생성합니다.");
                initializeMap(37.566826, 126.9786567); // 처음 지도를 생성할 때 기본 위치 (서울)로 설정
            }
            // 지도가 생성된 후에 relayout 호출
            if (map) {
                map.relayout();
            }

            loadAndDrawRoute(initialStartAddrParam, initialEndAddrParam);
        } else {
            // 주소 직접 입력 모드 또는 파라미터가 없는 경우
            // 이미 위에서 초기 display를 설정했으므로, 여기서는 특정 상태만 재설정합니다.
            // manualInputSection.style.display = 'block'; (이미 위에서 기본으로 설정)
            currentTripStatusSection.style.display = 'none';
            realtimeNavigationSection.style.display = 'none';
            recentRoutesSection.style.display = 'none';
            mapLoadingOverlay.style.display = 'none';

            // 초기 UI 상태 (주소 미정, 정보 오버레이 숨김)
            currentStartAddressElem.textContent = `출발지: 주소 미정`;
            currentEndAddressElem.textContent = `도착지: 주소 미정`;
            document.getElementById('display-start-address').textContent = `출발: 주소 미정`;
            document.getElementById('display-end-address').textContent = `도착: 주소 미정`;
            document.getElementById('display-total-distance').textContent = `0.0km`;
            document.getElementById('current-remaining-distance').textContent = `잔여 거리: 0.0km`;
            document.getElementById('display-estimated-time').textContent = `예상 0분`;
            document.getElementById('current-eta').textContent = `예상 도착 시간: --:--`;
            routeInfoOverlay.style.display = 'none';
            navSummaryOverlay.style.display = 'none';
        }

        // "경로 재검색" 버튼 클릭 이벤트
        document.getElementById('re-route-button').addEventListener('click', function() {
            const currentStartAddress = currentStartAddressElem.textContent.replace('출발지: ', '');
            const currentEndAddress = currentEndAddressElem.textContent.replace('도착지: ', '');
            if (currentStartAddress === '주소 미정' || currentEndAddress === '주소 미정') {
                alert("재검색할 주소가 없습니다. 주소를 먼저 입력하거나 선택해주세요.");
                return;
            }
            alert("경로를 재검색합니다."); // alert 추가
            loadAndDrawRoute(currentStartAddress, currentEndAddress);
        });

        // "주소 직접 입력" 섹션의 "경로 검색" 버튼 클릭 이벤트
        searchManualRouteButton.addEventListener('click', function() {
            const startAddr = inputStartAddress.value.trim();
            const endAddr = inputEndAddress.value.trim();

            if (!startAddr || !endAddr) {
                alert("출발지와 도착지 주소를 모두 입력해주세요.");
                return;
            }

            alert("경로를 안내합니다."); // alert 먼저 띄우기
            loadAndDrawRoute(startAddr, endAddr);
        });

        // "다시 안내받기" 버튼 클릭 이벤트
        document.querySelectorAll('.recent-route-item button').forEach(button => {
            button.addEventListener('click', function() {
                const startAddr = this.dataset.startAddr;
                const endAddr = this.dataset.endAddr;
                alert("경로를 안내합니다."); // alert 먼저 띄우기
                loadAndDrawRoute(startAddr, endAddr);
            });
        });
    });
});