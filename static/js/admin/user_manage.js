document.addEventListener('DOMContentLoaded', () => {
    const list = document.getElementById('user-manage-list');
    const users = [
        { id: 'USR001', name: '관리자A', role: '관리자' },
        { id: 'USR002', name: '담당자B', role: '운송 담당' },
    ];

    users.forEach(user => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td class="p-3">${user.id}</td>
            <td class="p-3">${user.name}</td>
            <td class="p-3">${user.role}</td>
            <td class="p-3"><button class="bg-red-600 text-white px-3 py-1 rounded hover:bg-red-700">삭제</button></td>
        `;
        list.appendChild(row);
    });
});
