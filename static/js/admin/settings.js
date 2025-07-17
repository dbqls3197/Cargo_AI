/**
 * auth.html 파일의 상호작용을 처리합니다.
 */
document.addEventListener('DOMContentLoaded', () => {
    const loginButton = document.getElementById('login-button');

    if(loginButton) {
        loginButton.addEventListener('click', () => {
            console.log('로그인 시도...');
            // 로그인 성공 시, 서버의 기본 주소(대시보드)로 이동합니다.
            window.location.href = '/';
        });
    }
});
