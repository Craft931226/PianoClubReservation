const translations = {
    "預約系統": { en: "Reserve", zh: "預約系統" },
    "注意事項": { en: "Note", zh: "注意事項" },
    "常見問題": { en: "F&Q", zh: "常見問題" },
    "歡迎": { en: "Welcome，", zh: "歡迎，" },
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

function openDialog() {
    document.getElementById("myDialog").showModal();
}

function closeDialog() {
    document.getElementById("myDialog").close();
}

// 計算當週的日期
function calculateWeekDates() {
  const today = new Date(); // 當前日期
  const dayOfWeek = today.getDay(); // 今天是星期幾 (0: 星期日, 1: 星期一, ...)
  const startOfWeek = new Date(today); // 複製當前日期
  startOfWeek.setDate(today.getDate() - dayOfWeek); // 設定為當週星期日

  // 生成當週 7 天的日期
  const weekDates = [];
  for (let i = 0; i < 7; i++) {
    const date = new Date(startOfWeek);
    date.setDate(startOfWeek.getDate() + i); // 增加 i 天
    weekDates.push(date);
  }
  return weekDates;
}

// 格式化日期為 "月/日 星期X"
function formatDate(date) {
  const options = { month: 'numeric', day: 'numeric' }; // 格式：月/日
  const weekdayNames = ['日', '一', '二', '三', '四', '五', '六']; // 星期名稱
  const formattedDate = date.toLocaleDateString('zh-TW', options);
  const weekday = weekdayNames[date.getDay()];
  return `${formattedDate} 星期${weekday}`;
}

// 更新所有琴房的按鈕文字
function updateReservationButtons() {
  const weekDates = calculateWeekDates(); // 獲取當週日期
  const today = new Date(); // 獲取今天日期

  // 找到每個琴房區塊中的按鈕
  const roomContainers = document.querySelectorAll('.button-container');
  roomContainers.forEach((container) => {
    const buttons = container.querySelectorAll('.reservation-btn');
    buttons.forEach((button, index) => {
      if (index < weekDates.length) {
        const buttonDate = weekDates[index];
        button.innerText = formatDate(buttonDate); // 更新按鈕文字

        // 比較日期，小於今天則設為灰色並禁用
        if (buttonDate < today.setHours(0, 0, 0, 0)) {
          button.style.backgroundColor = 'gray'; // 設定灰色背景
          button.style.cursor = 'not-allowed'; // 改變游標為不可用樣式
          button.onclick = null; // 禁止點擊事件
        } else {
          button.style.backgroundColor = ''; // 還原按鈕背景
          button.style.cursor = 'pointer'; // 還原游標樣式
          button.onclick = openDialog; // 恢復點擊事件
        }
      }
    });
  });
}

// 初始化
document.addEventListener('DOMContentLoaded', () => {
  updateReservationButtons(); // 在頁面加載時更新按鈕文字
});

