/**
 * 모든 페이지에 공통으로 적용되는 스크립트입니다.
 * 기능: 로그인 상태 확인, 현재 메뉴 활성화, 로그아웃
 */
document.addEventListener('DOMContentLoaded', () => {

    // 1. 로그인 페이지가 아닐 경우에만 로그인 상태를 확인합니다.
    const isLoginPage = window.location.pathname === '/' || window.location.pathname === '/auth';
    if (!isLoginPage && localStorage.getItem('isLoggedIn') !== 'true') {
        // 로그인 상태가 아니면, 즉시 로그인 페이지로 쫓아냅니다.
        window.location.href = window.location.origin + '/';
        return; // 페이지 이동 후에는 아래 코드를 실행하지 않습니다.
    }

    // 2. 현재 URL과 일치하는 메뉴에 활성 스타일을 적용합니다.
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-link-item');

    navLinks.forEach(link => {
        const linkPath = link.getAttribute('href');
        // 현재 경로가 링크의 경로와 일치하거나,
        // 현재 경로가 '/dashboard'일 때 기본 주소('/') 링크를 활성화합니다.
        if (linkPath === currentPath) {
            link.classList.add('active-nav-link');
        }
    });

    // 3. 로그아웃 버튼 기능
    const logoutButton = document.getElementById('logout-button');
    if (logoutButton) {
        logoutButton.addEventListener('click', () => {
            localStorage.removeItem('isLoggedIn');
            window.location.href = window.location.origin + '/';
        });
    }
});
