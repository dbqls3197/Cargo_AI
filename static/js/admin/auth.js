// 화면 전환 함수
function showScreen(screenId) {
    const screens = document.querySelectorAll('.auth-card');
    screens.forEach(screen => screen.classList.add('hidden'));  // 모든 화면 숨기기
    const activeScreen = document.getElementById(screenId);
    if (activeScreen) {
        activeScreen.classList.remove('hidden');  // 활성화할 화면 표시
    }
}

// 회원가입 함수
function register() {
    const username = document.getElementById('reg-username-input').value;
    const password = document.getElementById('reg-password-input').value;
    const confirmPassword = document.getElementById('reg-confirm-password-input').value;

    if (username && password && confirmPassword) {
        if (password !== confirmPassword) {
            alert('비밀번호가 일치하지 않습니다.');
        } else {
            alert('회원가입 완료!');
            // 회원가입 처리 로직 추가 (예: 서버로 데이터 전송)
        }
    } else {
        alert('모든 항목을 입력해주세요.');
    }
}

// 로그인 함수
function login() {
    const username = document.getElementById('username-input').value;
    const password = document.getElementById('password-input').value;

    if (username && password) {
        // 로그인 처리 로직 추가 (예: 서버로 로그인 요청)
        alert('로그인 성공');
        localStorage.setItem('isLoggedIn', 'true');
        window.location.href = "/dashboard"; // 로그인 후 대시보드로 이동
    } else {
        alert('사용자 이름과 비밀번호를 입력하세요.');
    }
}

// 페이지 로드 시 로그인 화면 표시
document.addEventListener('DOMContentLoaded', () => {
    showScreen('login-screen');
});
