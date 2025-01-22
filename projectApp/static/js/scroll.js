const translations = {
    "預約系統": { en: "Reserve", zh: "預約系統" },
    "注意事項": { en: "Note", zh: "注意事項" },
    "常見問題": { en: "F&Q", zh: "常見問題" },
    "歡迎": { en: "Welcome,", zh: "歡迎，" },
    "歡迎來到琴房預約系統": { en: "Welcome to the Piano Room Reservation System", zh: "歡迎來到琴房預約系統" },
    "若您是第一次使用，請閱讀以下注意事項": { en: "If this is your first time, please read the following precautions", zh: "若您是第一次使用，請閱讀以下注意事項" },
    "中央鋼琴社預約系統": { en: "National Central University Piano Society Reservation System", zh: "中央鋼琴社預約系統" },
    "每人每周不得預約超過七小時，違規者系統自動取消。": { en: "1.Each person is not allowed to book more than seven hours per week. Violators will have their reservations automatically canceled.", zh: "1.每人每周不得預約超過七小時，違規者系統自動取消。" },
    "為達使用琴房效率最大化，預約後若無法到場請記得取消預約": { en: "2.To maximize the efficiency of using the piano room, please remember to cancel your reservation if you cannot attend.", zh: "2.為達使用琴房效率最大化，預約後若無法到場請記得取消預約" },
    "開完琴房後鑰匙請記得掛回社窩，並鎖上門。": { en: "3.After using the piano room, please remember to hang the key back in the club room and lock the door.", zh: "3.開完琴房後鑰匙請記得掛回社窩，並鎖上門。" },
    "離開琴房時請記得關燈、鎖門。": { en: "4.When leaving the piano room, please remember to turn off the lights and lock the door.", zh: "4.離開琴房時請記得關燈、鎖門。" },
    "有任何問題請聯絡網管。": { en: "5.If you have any questions, please contact the network administrator.Email:yanchaun0970@gmail.com", zh: "5.有任何問題請聯絡網管。Email:yanchaun0970@gmail.com" }
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

function openDialog(event) {
  const button = event.currentTarget; // 取得被點擊的按鈕
  const date = button.getAttribute('data-date'); // 獲取按鈕上的本地日期資訊
  const roomType = button.closest('.button-container').previousElementSibling.textContent; // 獲取琴房類型

  // 更新彈窗內容
  const dialog = document.getElementById("myDialog");
  dialog.innerHTML = `
    <p>預約日期：${date}</p>
    <p>琴房類型：${roomType}</p>
    <button onclick="closeDialog()">關閉</button>
  `;
  dialog.showModal();
}
function closeDialog() {
  const dialog = document.getElementById("myDialog");
  dialog.close();
}

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
    weekDates.push(
      new Date(date.getFullYear(), date.getMonth(), date.getDate()) // 確保是本地時間
    );
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

function updateReservationButtons() {
  const weekDates = calculateWeekDates(); // 獲取當週日期
  const today = new Date(); // 獲取今天日期
  today.setHours(0, 0, 0, 0); // 將今天的時間設為 0 點，便於比較

  // 找到每個琴房區塊中的按鈕
  const roomContainers = document.querySelectorAll('.button-container');
  roomContainers.forEach((container) => {
    const buttons = container.querySelectorAll('.reservation-btn');
    buttons.forEach((button, index) => {
      if (index < weekDates.length) {
        const buttonDate = weekDates[index];
        button.innerText = formatDate(buttonDate); // 更新按鈕文字

        // 使用本地日期作為 data-date
        const localDate = `${buttonDate.getFullYear()}-${(buttonDate.getMonth() + 1)
          .toString()
          .padStart(2, '0')}-${buttonDate.getDate().toString().padStart(2, '0')}`;
        button.setAttribute('data-date', localDate); // 設定 data-date 屬性

        // 禁用過去的日期按鈕
        if (buttonDate < today) {
          button.style.backgroundColor = 'gray'; // 設定灰色背景
          button.style.cursor = 'not-allowed'; // 改變游標為不可用樣式
          button.onclick = null; // 禁止點擊事件
        } else {
          button.style.backgroundColor = ''; // 還原按鈕背景
          button.style.cursor = 'pointer'; // 還原游標樣式
          button.onclick = (event) => openDialog(event); // 綁定點擊事件
        }
      }
    });
  });
}



// 初始化
document.addEventListener('DOMContentLoaded', () => {
  updateReservationButtons(); // 在頁面加載時更新按鈕文字
});

