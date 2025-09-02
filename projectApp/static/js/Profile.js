// const translation = {
//     "(返回上一頁以回到主頁)" : {en: "(Return to the main page by going back)", zh: "(返回上一頁以回到主頁)"},
//     "個人中心": {en: "Profile", zh: "個人中心"},
//     "姓名": {en: "Name:", zh: "姓名："},
//     "密碼": {en: "Password:", zh: "密碼："},
//     "本週預約次數": {en: "This Week's Reservation Times:", zh: "本週預約次數："},
//     "預約紀錄": {en: "Reservation History", zh: "預約紀錄"},
//     "大琴房": {en: "Large Piano Room", zh: "大琴房"},
//     "中琴房": {en: "Medium Piano Room", zh: "中琴房"},
//     "小琴房": {en: "Small Piano Room", zh: "小琴房"},
//     "社窩": {en: "Club Room", zh: "社窩"},
//     "修改密碼": {en: "Change Password", zh: "修改密碼"},
//     "日期": {en: "Date", zh: "日期"},
//     "時間": {en: "Time", zh: "時間"},
//     "地點": {en: "Location", zh: "地點"},
//     "顯示": {en: "Show", zh: "顯示"},
//     "隱藏": {en: "Hide", zh: "隱藏"},
//     "登出": {en: "Logout", zh: "登出"},
// };

// function translatePage() {
//     const selectedLanguage = document.getElementById('languages').value || 'zh';
//     document.querySelectorAll('[data-translate]').forEach(element => {
//         const key = element.getAttribute('data-translate');
//         if (translation[key] && translation[key][selectedLanguage]) {
//             element.textContent = translation[key][selectedLanguage];
//         }
//     });
// }

// // 頁面載入時初始化翻譯
// document.addEventListener('DOMContentLoaded', translatePage);

// // 切換語言時重新翻譯
// document.getElementById('languages').addEventListener('change', translatePage);

function togglePassword() {
    let passwordField = document.getElementById('user-password');
    let toggleButton = document.getElementById('toggle-password-btn');
    const selectedLanguage = document.getElementById('languages').value || 'zh';

    if (passwordField.style.display === 'none') {
        passwordField.style.display = 'inline';
        toggleButton.textContent = translation["隱藏"][selectedLanguage]; // 變成 "隱藏"
    } else {
        passwordField.style.display = 'none';
        toggleButton.textContent = translation["顯示"][selectedLanguage]; // 變成 "顯示"
    }
}

document.addEventListener('DOMContentLoaded', function () {
    const reservationList = document.getElementById('reservation-list');

    function renderReservations() {
        reservationList.innerHTML = ""; // 清空現有內容

        if (reservations.length === 0) {
            reservationList.innerHTML = `<tr><td colspan="3" style="text-align:center;">沒有預約紀錄</td></tr>`;
            return;
        }

        const now = new Date(); // 獲取當前時間

        reservations.forEach(res => {
            let row = document.createElement('tr');

            // 解析預約日期時間
            let reservationDateTime = new Date(`${res.date}T${res.time}`);

            // 設置背景顏色
            // console.log(reservationDateTime, now);
            if (reservationDateTime >  now) {
                row.style.backgroundColor="rgb(226, 255, 224)"; // 綠色（未來預約）
                // console.log("green");
            } else {
                row.style.backgroundColor = "rgb(248, 211, 211)"; // 紅色（已過期預約）
            }

            row.innerHTML = `
                <td>${res.date}</td>
                <td>${res.time}</td>
                <td data-translate="${res.room}">${res.room}</td>
            `;
            reservationList.appendChild(row);
        });

        // translatePage(); // 重新翻譯房間名稱
    }

    renderReservations();
});

