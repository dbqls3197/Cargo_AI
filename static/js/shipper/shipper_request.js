document.addEventListener("DOMContentLoaded", () => {
    // 단계별 폼
    const step1 = document.getElementById("request-step-1");
    const step2 = document.getElementById("request-step-2");
    const step3 = document.getElementById("request-step-3");

    // 1 → 2
    document.getElementById("next-to-step-2").addEventListener("click", () => {
        if (!document.getElementById("origin").value.trim() ||
            !document.getElementById("destination").value.trim() ||
            !document.getElementById("cargo_info").value ||
            !document.getElementById("weight").value.trim()) {
            alert("모든 항목을 입력해주세요.");
            return;
        }
        step1.classList.add("hidden");
        step2.classList.remove("hidden");
    });

    // 2 → 1
    document.getElementById("back-to-step-1").addEventListener("click", () => {
        step2.classList.add("hidden");
        step1.classList.remove("hidden");
    });

    // 2 → 3
    document.getElementById("next-to-step-3").addEventListener("click", () => {
        if (!document.getElementById("cargo_type").value ||
            !document.getElementById("pickupDate").value ||
            !document.getElementById("pickupTime").value ||
            !document.getElementById("special_request").value.trim() ||
            !document.getElementById("price").value.trim()) {
            alert("모든 항목을 입력해주세요.");
            return;
        }

        // 요약 텍스트 표시
        document.getElementById("confirm-origin").textContent = document.getElementById("origin").value;
        document.getElementById("confirm-destination").textContent = document.getElementById("destination").value;
        document.getElementById("confirm-cargo_info").textContent = document.getElementById("cargo_info").value;
        document.getElementById("confirm-weight").textContent = document.getElementById("weight").value;
        document.getElementById("confirm-cargo_type").textContent = document.getElementById("cargo_type").value;
        document.getElementById("confirm-pickupDate").textContent = document.getElementById("pickupDate").value;
        document.getElementById("confirm-pickupTime").textContent = document.getElementById("pickupTime").value;
        document.getElementById("confirm-special_request").textContent = document.getElementById("special_request").value;

        const isFastChecked = document.getElementById("fast_request").checked;
        document.getElementById("confirm-fast_request").textContent = isFastChecked ? "긴급" : "일반";

        document.getElementById("confirm-price").textContent = document.getElementById("price").value;

        step2.classList.add("hidden");
        step3.classList.remove("hidden");
    });

    // 3 → 2
    document.getElementById("back-to-step-2").addEventListener("click", () => {
        step3.classList.add("hidden");
        step2.classList.remove("hidden");
    });

    // 대시보드로 이동
    document.getElementById("arrow-to-dashboard").addEventListener("click", () => {
        window.location.href = "/shipper/dashboard";
    });

    // ✅ MySQL datetime 형식으로 포맷하는 함수
    function formatToMySQLDatetime(date) {
        return date.getFullYear() + '-' +
            String(date.getMonth() + 1).padStart(2, '0') + '-' +
            String(date.getDate()).padStart(2, '0') + ' ' +
            String(date.getHours()).padStart(2, '0') + ':' +
            String(date.getMinutes()).padStart(2, '0') + ':' +
            String(date.getSeconds()).padStart(2, '0');
    }

    // 제출
    const requestForm = document.getElementById("shipper-request-form");
    requestForm.addEventListener("submit", function (e) {
        e.preventDefault();

        if (!confirm("운송을 요청하시겠습니까?")) return;

        const pickupDate = document.querySelector('#pickupDate').value;
        const pickupTime = document.querySelector('#pickupTime').value;
        const pickupDatetime = new Date(`${pickupDate}T${pickupTime}`);
        const pickupDeadlineFormatted = formatToMySQLDatetime(pickupDatetime); // ✅ 수정된 부분

        const data = {
            origin: document.querySelector('#origin').value,
            destination: document.querySelector('#destination').value,
            cargo_info: document.querySelector('#cargo_info').value,
            weight: document.querySelector('#weight').value,
            cargo_type: document.querySelector('#cargo_type').value,
            pickup_date: pickupDate,
            pickup_time: pickupTime,
            pickup_deadline: pickupDeadlineFormatted, // ✅ 수정된 부분
            fast_request: document.querySelector('#fast_request').checked ? 1 : 0,
            special_request: document.querySelector('#special_request').value,
            price: document.querySelector('#price').value
        };

        fetch("/shipper/request/submit", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data)
        })
        .then(res => res.json())
        .then(result => {
            if (result.success) {
                window.location.href = "/shipper/dashboard";
            } else {
                alert("제출 실패: " + result.message);
            }
        })
        .catch(err => {
            alert("요청 중 오류 발생: " + err);
        });
    });

    // 주소 검색 함수
    window.searchAddress = function (targetInputId) {
        new daum.Postcode({
            oncomplete: function (data) {
                const address = data.roadAddress || data.jibunAddress;
                document.getElementById(targetInputId).value = address;
            }
        }).open();
    };
});
