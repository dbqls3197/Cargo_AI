document.addEventListener("DOMContentLoaded", () => {
  const payButtons = document.querySelectorAll(".pay-now-btn");

  payButtons.forEach((button) => {
    button.addEventListener("click", async () => {
      // 버튼에서 matchId 추출
      const matchId = button.dataset.matchId;  //data-match-id="{{ payment.match_id }}">

      // // 버튼에서 id 추출
      // const id = button.dataset.id;


      // if (!matchId  || !id) {
      if (!matchId ) {
        alert("❌ 매칭 ID가 없습니다. 결제를 진행할 수 없습니다.");
        console.error("❌ 버튼에 data-match-id가 없습니다.");
        return;
      }

      // 결제 금액 추출
      const feeElement = button.closest(".payment-item")?.querySelector(".text-indigo-600");
      if (!feeElement) {
        alert("❌ 결제 금액 정보를 찾을 수 없습니다.");
        console.error("❌ .text-indigo-600 요소를 찾을 수 없습니다.");
        return;
      }

      const feeText = feeElement.textContent;
      const amount = parseInt(feeText.replace(/[^0-9]/g, ""));

      if (isNaN(amount) || amount <= 0) {
        alert("❌ 잘못된 결제 금액입니다.");
        console.error("❌ 금액 파싱 실패:", feeText);
        return;
      }

      // 고유 주문번호 생성
      const orderId = `ORDER_${matchId}_${Date.now()}`;
      console.log("✅ 결제 요청 준비:", { matchId, amount, orderId });

      //---------------------------------------------------
      // 토스 결제 서버 연동 : CORS 설정
      // 토스 결제 페이지  : localhost:8000
      //---------------------------------------------------
      const url = `http://127.0.0.1:8000/?match_id=${matchId}&amount=${amount}&orderId=${orderId}`;
      window.open(url, "_blank");

      // try {
      //       const response = await fetch("http://localhost:5555/api/toss/payment", {
      //         method: "POST",
      //         headers: {
      //           "Content-Type": "application/json",
      //         },
      //         body: JSON.stringify({
      //           orderId: orderId,
      //           amount: amount,
      //           orderName: "운송료 결제",
      //         }),
      //       });

      //       const result = await response.json();
      //       console.log("✅ Toss 응답:", result);

      //       if (result.code && result.code.startsWith("INVALID")) {
      //         alert(`❌ 결제 요청 실패: ${result.message}`);
      //       } else if (result.checkout && result.checkout.url) {
      //         // ✅ 새 창으로 띄움
      //         window.open(result.checkout.url, "_blank");
      //       } else {
      //         alert("❌ 결제 응답 오류. 다시 시도해주세요.");
      //         console.error(result);
      //       }
      //     } catch (err) {
      //       alert("❌ 네트워크 오류. 다시 시도해주세요.");
      //       console.error("❌ 네트워크 오류:", err);
      //     }


      
      


    });
  });

  // 모달 확인 버튼 처리
  const confirmBtn = document.getElementById("confirm-payment-btn");
  if (confirmBtn) {
    confirmBtn.addEventListener("click", () => {
      document.getElementById("payment-complete-modal").classList.add("hidden");
      location.reload();
    });
  }
});
