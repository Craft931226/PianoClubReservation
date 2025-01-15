const translations = {
    "預約系統": { en: "Reservation", zh: "預約系統" },
    "注意事項": { en: "Notations", zh: "注意事項" },
    "常見問題": { en: "F&Q", zh: "常見問題" },
    "歡迎來到琴房預約系統": { en: "Welcome to the Piano Room Reservation System", zh: "歡迎來到琴房預約系統" },
    "若您是第一次使用，請閱讀以下注意事項": { en: "If this is your first time, please read the following precautions", zh: "若您是第一次使用，請閱讀以下注意事項" },
    "中央鋼琴社預約系統": { en: "National Central University Piano Society Reservation System", zh: "中央鋼琴社預約系統" },
    "每人每周不得預約超過七小時，違規者系統自動取消。": { en: "1.Each person is not allowed to book more than seven hours per week. Violators will have their reservations automatically canceled.", zh: "1.每人每周不得預約超過七小時，違規者系統自動取消。" },
    "為達使用琴房效率最大化，預約後若無法到場請記得取消預約": { en: "2.To maximize the efficiency of using the piano room, please remember to cancel your reservation if you cannot attend.", zh: "2.為達使用琴房效率最大化，預約後若無法到場請記得取消預約" },
    "開完琴房後鑰匙請記得掛回社窩，並鎖上門。": { en: "3.After using the piano room, please remember to hang the key back in the club room and lock the door.", zh: "3.開完琴房後鑰匙請記得掛回社窩，並鎖上門。" },
    "離開琴房時請記得關燈、鎖門。": { en: "4.When leaving the piano room, please remember to turn off the lights and lock the door.", zh: "4.離開琴房時請記得關燈、鎖門。" },
    "有任何問題請聯絡網管。": { en: "5.If you have any questions, please contact the network administrator.", zh: "5.有任何問題請聯絡網管。" }
};

function initializeTranslations() {
    const selectedLanguage = document.getElementById('languages').value || 'zh'; // 預設為中文
    document.querySelectorAll('[data-translate]').forEach(element => {
        const key = element.getAttribute('data-translate');
        if (translations[key] && translations[key][selectedLanguage]) {
            element.textContent = translations[key][selectedLanguage];
        }
    });
}

// 在頁面載入時初始化
document.addEventListener('DOMContentLoaded', initializeTranslations);

// 切換語言功能
document.getElementById('languages').addEventListener('change', function () {
    const selectedLanguage = this.value;
    document.querySelectorAll('[data-translate]').forEach(element => {
        const key = element.getAttribute('data-translate');
        if (translations[key] && translations[key][selectedLanguage]) {
            element.textContent = translations[key][selectedLanguage];
        }
    });
});

document.addEventListener('DOMContentLoaded', function() {
    const sections = document.querySelectorAll('.full-screen-section');
    let currentSectionIndex = 0;

    function scrollToSection(index) {
        sections[index].scrollIntoView({ behavior: 'smooth' });
    }

    window.addEventListener('wheel', function(event) {
        if (event.deltaY > 0) {
            // Scroll down
            if (currentSectionIndex < sections.length - 2) {
                currentSectionIndex++;
                scrollToSection(currentSectionIndex);
            }
        } else {
            // Scroll up
            if (currentSectionIndex > 0) {
                currentSectionIndex--;
                scrollToSection(currentSectionIndex);
            }
        }
    });
});