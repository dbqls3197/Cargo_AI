// shipper_request.js (수정 제안)

document.addEventListener("DOMContentLoaded", () => {
    // 폼 단계 요소
    const requestStep1 = document.getElementById('request-step-1');
    const requestStep2 = document.getElementById('request-step-2');
    const requestStep3 = document.getElementById('request-step-3');

    // "다음" 버튼 요소
    const nextToStep2Btn = document.getElementById('next-to-step-2');
    const nextToStep3Btn = document.getElementById('next-to-step-3');

    // "뒤로가기" 버튼 요소
    const backToStep1Btn = document.getElementById('back-to-step-1');
    const backToStep2Btn = document.getElementById('back-to-step-2');

    // 프로그레스 바 및 단계 이름 요소
    const progressBar = document.getElementById('progress-bar');
    const stepName1 = document.getElementById('step-name-1');
    const stepName2 = document.getElementById('step-name-2');
    const stepName3 = document.getElementById('step-name-3');

    // 1단계 입력 필드
    const originInput = document.getElementById('origin');
    const destinationInput = document.getElementById('destination');
    const cargoInfoRadios = document.querySelectorAll('input[name="cargo_info"]');
    const weightInput = document.getElementById('weight');

    // 2단계 입력 필드
    const cargoTypeSelect = document.getElementById('cargo_type');
    const pickupDateInput = document.getElementById('pickupDate');
    const pickupTimeInput = document.getElementById('pickupTime');
    const fastRequestCheckbox = document.getElementById('fast_request');
    const specialRequestTextarea = document.getElementById('special_request');
    const priceInput = document.getElementById('price');

    // 확인 단계의 span 요소
    const confirmOriginSpan = document.getElementById('confirm-origin');
    const confirmDestinationSpan = document.getElementById('confirm-destination');
    const confirmCargoInfoSpan = document.getElementById('confirm-cargo_info');
    const confirmWeightSpan = document.getElementById('confirm-weight');
    const confirmCargoTypeSpan = document.getElementById('confirm-cargo_type');
    const confirmPickupDateSpan = document.getElementById('confirm-pickupDate');
    const confirmPickupTimeSpan = document.getElementById('confirm-pickupTime');
    const confirmFastRequestSpan = document.getElementById('confirm-fast_request');
    const confirmSpecialRequestSpan = document.getElementById('confirm-special_request');
    const confirmPriceSpan = document.getElementById('confirm-price');

    // 대시보드 이동 화살표
    const arrowToDashboard = document.getElementById('arrow-to-dashboard');

    /**
     * @function updateProgressBarAndStepNames
     * @description 현재 단계에 따라 프로그레스 바와 단계 이름 텍스트의 스타일을 업데이트합니다.
     * @param {number} currentStep - 현재 단계 (1, 2, 3)
     */
    function updateProgressBarAndStepNames(currentStep) {
        if (progressBar) {
            let width = 0;
            [stepName1, stepName2, stepName3].forEach(span => {
                if (span) {
                    span.classList.remove('text-indigo-600', 'font-bold');
                    span.classList.add('text-gray-500');
                }
            });

            if (currentStep === 1) {
                width = 33;
                if (stepName1) {
                    stepName1.classList.add('text-indigo-600', 'font-bold');
                    stepName1.classList.remove('text-gray-500');
                }
            } else if (currentStep === 2) {
                width = 66;
                if (stepName2) {
                    stepName2.classList.add('text-indigo-600', 'font-bold');
                    stepName2.classList.remove('text-gray-500');
                }
            } else if (currentStep === 3) {
                width = 100;
                if (stepName3) {
                    stepName3.classList.add('text-indigo-600', 'font-bold');
                    stepName3.classList.remove('text-gray-500');
                }
            }
            progressBar.style.width = `${width}%`;
        }
    }

    /**
     * @function populateConfirmation
     * @description 3단계 (확인) 페이지에 입력된 정보를 채워 넣습니다.
     */
    function populateConfirmation() {
        confirmOriginSpan.textContent = originInput.value;
        confirmDestinationSpan.textContent = destinationInput.value;
        
        let selectedCargoInfo = '';
        cargoInfoRadios.forEach(radio => {
            if (radio.checked) {
                selectedCargoInfo = radio.value;
            }
        });
        confirmCargoInfoSpan.textContent = selectedCargoInfo;

        confirmWeightSpan.textContent = weightInput.value + ' kg';
        confirmCargoTypeSpan.textContent = cargoTypeSelect.value;
        confirmPickupDateSpan.textContent = pickupDateInput.value;
        confirmPickupTimeSpan.textContent = pickupTimeInput.value;
        confirmPriceSpan.textContent = priceInput.value + ' 원';

        confirmFastRequestSpan.textContent = fastRequestCheckbox.checked ? '긴급 운송' : '일반 운송';
        confirmSpecialRequestSpan.textContent = specialRequestTextarea.value.trim() !== '' ? specialRequestTextarea.value : '없음';
    }

    // 초기 로드 시 프로그레스 바 업데이트
    updateProgressBarAndStepNames(1);

    /**
     * @function validateCurrentStep
     * @description 현재 활성화된 (보이는) 스텝의 필드만 유효성을 검사합니다.
     * @param {HTMLElement} stepElement - 현재 스텝의 DOM 요소 (예: requestStep1, requestStep2)
     * @returns {boolean} - 유효하면 true, 아니면 false
     */
    function validateCurrentStep(stepElement) {
        const requiredInputs = stepElement.querySelectorAll('[required]');
        let allValid = true;

        requiredInputs.forEach(input => {
            if (!input.checkValidity()) {
                allValid = false;
                // 유효하지 않은 첫 번째 필드로 스크롤 및 브라우저 경고 표시
                // hidden 상태가 아니므로 focusable 에러 발생하지 않음
                input.reportValidity(); 
                return; // forEach 루프 중단
            }
        });

        // 라디오 버튼 그룹 (cargo_info) 별도 검사 - required 속성이 한 곳에만 있기 때문
        if (stepElement === requestStep1) {
            const cargoInfoChecked = document.querySelector('input[name="cargo_info"]:checked');
            if (!cargoInfoChecked) {
                allValid = false;
                // 사용자에게 직접적인 피드백 제공
                alert("물품 종류를 선택해 주세요."); 
            }
        }
        
        return allValid;
    }


    // "다음" 버튼 (1단계 → 2단계) 클릭 이벤트
    if (nextToStep2Btn) {
        nextToStep2Btn.addEventListener("click", () => {
            // 현재 1단계의 필드만 유효성 검사
            if (!validateCurrentStep(requestStep1)) {
                return; // 유효하지 않으면 다음 단계로 넘어가지 않음
            }

            requestStep1.classList.add("hidden");
            requestStep2.classList.remove("hidden");
            updateProgressBarAndStepNames(2);
        });
    }

    // "뒤로가기" 버튼 (2단계 → 1단계) 클릭 이벤트
    if (backToStep1Btn) {
        backToStep1Btn.addEventListener("click", () => {
            requestStep2.classList.add("hidden");
            requestStep1.classList.remove("hidden");
            updateProgressBarAndStepNames(1);
        });
    }

    // "다음" 버튼 (2단계 → 3단계) 클릭 이벤트
    if (nextToStep3Btn) {
        nextToStep3Btn.addEventListener("click", () => {
            // 현재 2단계의 필드만 유효성 검사
            if (!validateCurrentStep(requestStep2)) {
                return; // 유효하지 않으면 다음 단계로 넘어가지 않음
            }
            
            populateConfirmation(); // 확인 단계에 정보 채우기
            requestStep2.classList.add("hidden");
            requestStep3.classList.remove("hidden");
            updateProgressBarAndStepNames(3);
        });
    }

    // "뒤로가기" 버튼 (3단계 → 2단계) 클릭 이벤트
    if (backToStep2Btn) {
        backToStep2Btn.addEventListener("click", () => {
            requestStep3.classList.add("hidden");
            requestStep2.classList.remove("hidden");
            updateProgressBarAndStepNames(2);
        });
    }

    // 대시보드로 이동
    if (arrowToDashboard) {
        arrowToDashboard.addEventListener("click", () => {
            window.location.href = "/shipper/dashboard";
        });
    }

    // 최종 제출
    const requestForm = document.getElementById("shipper-request-form");
    if (requestForm) {
        requestForm.addEventListener("submit", function (e) {
            e.preventDefault(); // 기본 폼 제출 방지

            // 최종 제출 시에는 전체 폼의 유효성 검사가 필요하지만, 이미 각 스텝에서 검사했으므로
            // 여기서는 서버 전송 전 최종 확인만 진행
            // 만약 서버 전송 전에 전체 폼의 유효성 검사를 다시 하고 싶다면
            // if (!requestForm.checkValidity()) { requestForm.reportValidity(); return; }
            // 를 추가할 수 있으나, 이 경우 모든 필드가 보여야 문제가 없음.

            if (!confirm("운송을 요청하시겠습니까?")) return;

            // 라디오 버튼 그룹에서 선택된 값 가져오기
            const selectedCargoInfoRadio = document.querySelector('input[name="cargo_info"]:checked');
            const cargoInfoValue = selectedCargoInfoRadio ? selectedCargoInfoRadio.value : '';

            const data = {
                origin: originInput.value,
                destination: destinationInput.value,
                cargo_info: cargoInfoValue,
                weight: weightInput.value,
                cargo_type: cargoTypeSelect.value,
                pickup_date: pickupDateInput.value,
                pickup_time: pickupTimeInput.value,
                fast_request: fastRequestCheckbox.checked ? 1 : 0,
                special_request: specialRequestTextarea.value,
                price: priceInput.value
            };

            fetch("/shipper/request/submit", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(data)
            })
            .then(res => res.json())
            .then(result => {
                if (result.success) {
                    alert("운송 요청이 성공적으로 접수되었습니다.");
                    window.location.href = "/shipper/dashboard";
                } else {
                    alert("제출 실패: " + result.message);
                }
            })
            .catch(err => {
                console.error("Fetch Error:", err);
                alert("요청 중 오류 발생: " + err.message);
            });
        });
    }
});

// 주소 검색 함수 (window 객체에 할당하여 HTML에서 직접 호출 가능하도록)
window.searchAddress = function (targetInputId) {
    new daum.Postcode({
        oncomplete: function (data) {
            const address = data.roadAddress || data.jibunAddress;
            const targetInput = document.getElementById(targetInputId);
            if (targetInput) {
                targetInput.value = address;
                // Daum Postcode로 주소 입력 후, 해당 input 필드에 'input' 이벤트 강제 발생
                // 이렇게 하면 HTML5의 required 속성에 대한 유효성 검사가 즉시 트리거될 수 있음
                const event = new Event('input', { bubbles: true });
                targetInput.dispatchEvent(event);
            }
        }
    }).open();
};