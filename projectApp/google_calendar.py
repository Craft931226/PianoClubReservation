from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from datetime import datetime, timedelta

SCOPES = ['https://www.googleapis.com/auth/calendar']
SERVICE_ACCOUNT_FILE = r"C:\Users\User\Downloads\skilled-script-448314-j0-0c05f20ca146.json"

credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
service = build('calendar', 'v3', credentials=credentials)

# 獲取指定日期的事件
def get_events_for_date(calendar_ids, date):
    events = []
    time_min = datetime.fromisoformat(date).isoformat() + 'Z'
    time_max = (datetime.fromisoformat(date) + timedelta(days=1)).isoformat() + 'Z'

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
