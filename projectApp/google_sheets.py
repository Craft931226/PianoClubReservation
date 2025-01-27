from datetime import date
from http import client
import json
import os
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# 配置 Google Sheets API 憑證
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
# 從環境變數中加載憑證
credentials_info = json.loads(os.getenv('GOOGLE_CREDENTIALS_JSON'))
credentials = Credentials.from_service_account_info(credentials_info, scopes=SCOPES)
SPREADSHEET_ID = os.getenv('GOOGLE_SHEET_ID')  # 修改為實際試算表的 ID
service = build('sheets', 'v4', credentials=credentials)


# # 配置 Google Sheets API 憑證
# SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
# SERVICE_ACCOUNT_FILE = r"C:\Users\User\Downloads\skilled-script-448314-j0-0c05f20ca146.json"
# credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
# service = build('sheets', 'v4', credentials=credentials)
# SPREADSHEET_ID = '1TWp1XNDx46NPLRZQA9AVA1yghVxhA_2TZwwb9c0fIMA'


# update_user_name 函數將用戶名更新到試算表中
# Define the sheet names and ranges
FORM_RESPONSES_SHEET = '社員資料'
RESERVATION_LIMIT_SHEET = '預約上限'
FORM_RESPONSES_RANGE = f'{FORM_RESPONSES_SHEET}!A1:B'  # 假設第一列為名稱，第二列為學號
RESERVATION_LIMIT_RANGE = f'{RESERVATION_LIMIT_SHEET}!A1:B'  # 假設第一列為名稱，第二列為學號

# 讀取數據
def read_data(range_name):
    """從 Google 試算表中讀取數據"""
    try:
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=range_name).execute()
        return result.get('values', [])
    except Exception as e:
        print(f"Error reading data: {e}")
        return []

def update_data(range_name, values):
    """更新 Google 試算表中的數據"""
    try:
        sheet = service.spreadsheets()
        body = {'values': values}
        result = sheet.values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=range_name,
            valueInputOption="RAW",
            body=body
        ).execute()
        print(f"{result.get('updatedCells')} cells updated.")
    except Exception as e:
        print(f"Error updating data: {e}")

def get_user_email(user_name):
    """
    根據使用者名稱從試算表中獲取信箱地址。
    :param user_name: 使用者名稱
    :return: 信箱地址 (如果找到)
    """
    try:
        # 讀取社員資料表的所有數據
        sheet_data = read_data(f'{FORM_RESPONSES_SHEET}!A1:D')  # 假設信箱在第四列
        for row in sheet_data:
            if len(row) >= 4 and row[0] == user_name:  # 確保行數據足夠長並匹配使用者名稱
                return row[3]  # 返回第四列（信箱）
        return None  # 如果未找到對應使用者
    except Exception as e:
        print(f"Error retrieving email for user {user_name}: {e}")
        return None

def reset_reservation_limits():
    """
    將預約上限試算表中的 B 欄（預約次數）全部重置為 0。
    僅當本週未執行過重置操作時執行。
    """
    try:
        # 檢查是否已經重置過
        status_range = '系統狀態!A1:B1'
        status_data = read_data(status_range)
        last_reset_date = status_data[0][1] if len(status_data) > 0 and len(status_data[0]) > 1 else None

        today = date.today()
        if last_reset_date == today.isoformat():
            print("今天已經執行過重置操作，跳過重置")
            return

        # 讀取當前試算表中的數據
        data = read_data(RESERVATION_LIMIT_RANGE)
        if not data:
            print("無法讀取預約上限數據")
            return

        # 構建新的數據，將 B 欄設置為 0
        reset_values = [[row[0], 0] for row in data if len(row) > 0]
        update_data(RESERVATION_LIMIT_RANGE, reset_values)
        print("預約次數已重置為 0")

        # 更新重置日期
        update_data(status_range, [["last_reset_date", today.isoformat()]])
        print("重置標記已更新")
    except Exception as e:
        print(f"重置預約次數失敗：{e}")

# 測試讀取數據
print(read_data(f'{FORM_RESPONSES_SHEET}!A1:B5'))  # 測試讀取表單回應的前 5 行