document.addEventListener("DOMContentLoaded", () => {
    const buttons = document.querySelectorAll(".select-driver-btn");
    buttons.forEach(btn => {
        btn.addEventListener("click", () => {
            const driverId = btn.dataset.driverId;

            fetch("/shipper/select_driver", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    driver_id: driverId,
                    shipment_id: localStorage.getItem("shipment_id") || null
                })
            }).then(res => res.json())
            .then(data => {
                if (data.success) {
                    alert("기사님이 선택되었습니다.");
                    window.location.href = "/shipper/matching_result";
                } else {
                    alert("선택 실패: " + data.message);
                }
            });
        });
    });
});
