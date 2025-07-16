document.addEventListener("DOMContentLoaded", () => {
  const payButtons = document.querySelectorAll(".pay-now-btn");
  const modal = document.getElementById("payment-complete-modal");
  const confirmBtn = document.getElementById("confirm-payment-btn");

  let selectedMatchId = null;

  payButtons.forEach(button => {
    button.addEventListener("click", async () => {
      selectedMatchId = button.dataset.matchId;

      try {
        const response = await fetch("/api/process_payment", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ match_id: selectedMatchId }),
        });

        const result = await response.json();

        if (result.success) {
          modal.classList.remove("hidden");
        } else {
          alert("결제에 실패했습니다. 다시 시도해주세요.");
        }
      } catch (error) {
        console.error("결제 처리 중 오류:", error);
        alert("결제 처리 중 오류가 발생했습니다.");
      }
    });
  });

  confirmBtn.addEventListener("click", () => {
    modal.classList.add("hidden");

    if (selectedMatchId) {
      window.location.href = `/shipper/review?match_id=${selectedMatchId}`;
    }
  });
});