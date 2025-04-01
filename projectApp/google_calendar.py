import json
import os
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from datetime import datetime, timedelta, timezone

# 配置 Google Calendar API 憑證
SCOPES = ['https://www.googleapis.com/auth/calendar']
credentials_info = json.loads(os.getenv('GOOGLE_CREDENTIALS_JSON'))
credentials = Credentials.from_service_account_info(credentials_info, scopes=SCOPES)
service = build('calendar', 'v3', credentials=credentials)

# # 本地憑證文件的路徑
# SCOPES = ['https://www.googleapis.com/auth/calendar']
# SERVICE_ACCOUNT_FILE = r"C:\Users\User\Downloads\skilled-script-448314-j0-0c05f20ca146.json"
# credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
# service = build('calendar', 'v3', credentials=credentials)

# 獲取指定日期的事件
def get_events_for_date(calendar_ids, date):
    events = []
    
    # 設定台北時區
    taipei_tz = timezone(timedelta(hours=8))

    # 設定當天時間範圍
    date_obj = datetime.fromisoformat(date)
    time_min = datetime(date_obj.year, date_obj.month, date_obj.day, 0, 0, 0, tzinfo=taipei_tz).isoformat()
    time_max = datetime(date_obj.year, date_obj.month, date_obj.day, 23, 59, 59, tzinfo=taipei_tz).isoformat()

    for calendar_id in calendar_ids:
        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        events.extend(events_result.get('items', []))

    # 格式化事件
    formatted_events = []
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        end = event['end'].get('dateTime', event['end'].get('date'))
        formatted_events.append({
            'summary': event.get('summary', 'No Title'),
            'start': start,
            'end': end
        })
    
    return formatted_events

def create_event(date, start_time, user_name, room_type, duration):
    """
    創建 Google Calendar 事件
    :param date: 日期 (格式: YYYY-MM-DD)
    :param start_time: 開始時間 (格式: HH:MM)
    :param user_name: 使用者姓名
    :param room_type: 琴房類型 (如: '大琴房', '中琴房', '小琴房')
    :param duration: 使用時間 (單位: 分鐘，例如 30 或 60)
    :return: 創建的事件詳細信息
    """
    # 琴房類型對應的日曆 ID
    calendar_mapping = {
        '大琴房': 'ncupianolarge@gmail.com',
        '中琴房': 'ncupianomedium@gmail.com',
        '小琴房': 'ncupianosmall@gmail.com',
        '社窩': 'ncupiano31@gmail.com'
    }
    
    calendar_id = calendar_mapping.get(room_type)
    if not calendar_id:
        raise ValueError(f"無效的琴房類型: {room_type}")

    # 計算開始和結束時間
    start_datetime = datetime.fromisoformat(f"{date}T{start_time}:00")
    end_datetime = start_datetime + timedelta(minutes=duration)

    # 建立事件內容
    event = {
        'summary': f"{user_name} 預約 {room_type}",
        'description': f"使用者: {user_name}\n琴房類型: {room_type}\n預約時長: {duration} 分鐘",
        'start': {
            'dateTime': start_datetime.isoformat(),
            'timeZone': 'Asia/Taipei'
        },
        'end': {
            'dateTime': end_datetime.isoformat(),
            'timeZone': 'Asia/Taipei'
        }
    }

    # 創建事件
    created_event = service.events().insert(calendarId=calendar_id, body=event).execute()
    print(f"✅ 事件已創建，連結: {created_event.get('htmlLink')}")
    return created_event

# cancel 的功能在view.py中