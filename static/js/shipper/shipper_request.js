document.addEventListener("DOMContentLoaded", () => {
    // 단계별 폼
    const step1 = document.getElementById("request-step-1");
    const step2 = document.getElementById("request-step-2");
    const step3 = document.getElementById("request-step-3");

    // 단계 이동: 1 → 2
    document.getElementById("next-to-step-2").addEventListener("click", () => {
        if (!document.getElementById("origin").value.trim() || !document.getElementById("destination").value.trim() ||
            !document.getElementById("itemType").value || !document.getElementById("itemWeight").value.trim()) {
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
        if (!document.getElementById("vehicleType").value || !document.getElementById("pickupDate").value ||
            !document.getElementById("pickupTime").value || !document.getElementById("dropoffDate").value || !document.getElementById("dropoffTime").value) {
            alert("모든 항목을 입력해주세요.");
            return;
        }

        // 요약 텍스트 표시
        document.getElementById("confirm-origin").textContent = document.getElementById("origin").value;
        document.getElementById("confirm-destination").textContent = document.getElementById("destination").value;
        document.getElementById("confirm-itemType").textContent = document.getElementById("itemType").value;
        document.getElementById("confirm-itemWeight").textContent = document.getElementById("itemWeight").value;
        document.getElementById("confirm-vehicleType").textContent = document.getElementById("vehicleType").value;
        document.getElementById("confirm-pickupDate").textContent = document.getElementById("pickupDate").value;
        document.getElementById("confirm-pickupTime").textContent = document.getElementById("pickupTime").value;
        document.getElementById("confirm-dropoffDate").textContent = document.getElementById("dropoffDate").value;
        document.getElementById("confirm-dropoffTime").textContent = document.getElementById("dropoffTime").value;

        step2.classList.add("hidden");
        step3.classList.remove("hidden");
    });

    // 3 → 2
    document.getElementById("back-to-step-2").addEventListener("click", () => {
        step3.classList.add("hidden");
        step2.classList.remove("hidden");
    });

    // 뒤로 가기 (대시보드)
    document.getElementById("arrow-to-dashboard").addEventListener("click", () => {
        window.location.href = "/shipper/dashboard";
    });

    // 제출
    const requestForm = document.getElementById("shipper-request-form");
    requestForm.addEventListener("submit", function (e) {
        e.preventDefault();

        if (!confirm("운송을 요청하시겠습니까?")) return;

        const data = {
            origin: document.querySelector('#origin').value,
            destination: document.querySelector('#destination').value,
            item_type: document.querySelector('#itemType').value,
            item_weight: document.querySelector('#itemWeight').value,
            vehicle_type: document.querySelector('#vehicleType').value,
            pickup_date: document.querySelector('#pickupDate').value,
            pickup_time: document.querySelector('#pickupTime').value,
            dropoff_date: document.querySelector('#dropoffDate').value,
            dropoff_time: document.querySelector('#dropoffTime').value
        };

        fetch("/shipper/request/submit", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data)
        })
        .then(res => res.json())
        .then(result => {
            if (result.success) {
                window.location.href = "/shipper/my_requests";
            } else {
                alert("제출 실패: " + result.message);
            }
        })
        .catch(err => {
            alert("요청 중 오류 발생: " + err);
        });
    });
});

// 주소 검색
window.searchAddress = function (targetInputId) {
    new daum.Postcode({
        oncomplete: function (data) {
            const address = data.roadAddress || data.jibunAddress;
            document.getElementById(targetInputId).value = address;
        }
    }).open();
};
