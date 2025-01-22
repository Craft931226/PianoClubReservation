from http import client
import json
import os
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# 配置 Google Sheets API 憑證
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
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
    


# 測試讀取數據
print(read_data(f'{FORM_RESPONSES_SHEET}!A1:B5'))  # 測試讀取表單回應的前 5 行