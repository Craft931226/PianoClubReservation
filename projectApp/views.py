from datetime import date, datetime, timedelta, timezone
import json
from zoneinfo import ZoneInfo
from django.http import HttpResponse
from django.shortcuts import render, redirect

from projectApp.google_gmail import send_cancel_email, send_email
from .google_sheets import get_user_email, read_data, reset_reservation_limits, update_data
from django.core.signing import Signer, BadSignature
from django.http import JsonResponse
from .google_calendar import create_event, get_events_for_date, create_event, service

signer = Signer()  # 簽名工具
# 試算表的範圍，包含用戶數據
GOOGLE_SHEET_RANGE = '社員資料!A2:C'  # 假設試算表有 Name 和 Student ID 列
RESERVATION_LIMIT_RANGE = '預約上限!A1:B'  # 假設試算表有 Name 和 Limit 列

def login_view(request):
    error_message = None

    if request.method == 'POST':
        name = request.POST.get('name')
        student_id = request.POST.get('student_id')
        print("--------------------這裡可以看到誰登入了系統：")
        time = datetime.now()
        print(f'{time} {name} 登入了系統')
        print()
        try:
            users = read_data(GOOGLE_SHEET_RANGE)  # 獲取用戶數據
            if not users:
                error_message = "無法讀取用戶數據，請稍後再試。"
            else:
                user_found = False
                for user in users:
                    if len(user) >= 2 and user[0] == name and user[2] == student_id:
                        user_found = True
                        signed_username = signer.sign(name)  # 生成簽名的用戶名
                        return redirect(f'/home/?username={signed_username}')
                
                if not user_found:
                    error_message = "帳號或密碼錯誤，請重新輸入。"
        except Exception as e:
            error_message = f"系統錯誤：{e}"

    return render(request, 'Login.html', {'error_message': error_message})

def home_view(request):
    signed_username = request.GET.get('username')
    if not signed_username:
        return redirect('login')  # 如果沒有簽名的用戶名，重定向到登入頁面

    try:
        username = signer.unsign(signed_username)  # 驗證簽名

        # 每次訪問時檢查是否需要重置
        reset_limits_if_needed()

        return render(request, "homePage.html", {'username': username})
    except BadSignature:
        return redirect('login')  # 簽名無效時重定向到登入頁面





def change_password_view(request):
    error_message = None
    success_message = None

    if request.method == 'POST':
        name = request.POST.get('name')
        current_password = request.POST.get('currentPassword')
        new_password = request.POST.get('newPassword')
        confirm_password = request.POST.get('confirmPassword')

        if new_password != confirm_password:
            error_message = "新密碼與確認密碼不符，請重新輸入。"
        else:
            try:
                # 從 Google Sheets 獲取數據
                users = read_data(GOOGLE_SHEET_RANGE)
                if not users:
                    error_message = "請檢查名子是否正確？。"
                else:
                    # 找到用戶
                    user_found = False
                    for index, user in enumerate(users):
                        if len(user) >= 3 and user[0] == name and user[2] == current_password:
                            user_found = True
                            # 更新密碼
                            range_to_update = f'社員資料!C{index + 2}'
                            update_data(range_to_update, [[new_password]])
                            success_message = "密碼修改成功！"
                            return redirect('login')  # 修改成功後重定向到登錄頁面
                            
                    
                    if not user_found:
                        error_message = "用戶名或當前密碼錯誤，請重新輸入。"
            except Exception as e:
                error_message = f"系統錯誤：{e}"

    return render(request, "ChangePassword.html", {
        'error_message': error_message,
        'success_message': success_message
    })


def get_calendar_events_view(request):
    if request.method == 'GET':
        date = request.GET.get('date')  # ISO 格式的日期
        room_type = request.GET.get('roomType')  # 獲取琴房類型
        name = request.GET.get('user_name')  # 獲取用戶名
        print()
        print("--------------------這裡可以看到使用者點擊哪天哪個琴房：")
        print("函式名稱：get_calendar_events_view")
        print(f"日期: {date}, 琴房類型: {room_type}, 使用者: {name}")

        if not date or not room_type:
            return JsonResponse({'error': 'Missing parameters'}, status=400)

        # 將琴房類型映射到日曆 ID
        calendar_mapping = {
            '大琴房': 'ncupianolarge@gmail.com',
            '中琴房': 'ncupianomedium@gmail.com',
            '小琴房': 'ncupianosmall@gmail.com',
            '社窩': 'ncupiano31@gmail.com'
        }

        calendar_id = calendar_mapping.get(room_type)
        if not calendar_id:
            return JsonResponse({'error': 'Invalid room type'}, status=400)

        # 獲取指定日曆的事件
        events = get_events_for_date([calendar_id], date)
        print("當天預約情況：")
        if not events:
            print("無預約事件")
        events_num = 1
        for event in events:
            print(f"{events_num} 標題：{event['summary']} 開始時間：{event['start']}")
            events_num += 1
        return JsonResponse({'events': events}, status=200)
    else:
        return JsonResponse({'error': 'Method not allowed'}, status=405)

def calculate_time_range(date, start_time):
    tz = ZoneInfo("Asia/Taipei")  # 使用 zoneinfo 設定時區
    
    # 將日期和時間結合，並附加時區
    start_datetime = datetime.fromisoformat(f"{date}T{start_time}:00").replace(tzinfo=tz)
    
    # 計算 timeMin 和 timeMax
    time_min = start_datetime.isoformat()
    time_max = (start_datetime + timedelta(minutes=30)).isoformat()
    
    return time_min, time_max

def create_calendar_event_view(request):
    """
    創建日曆事件的視圖。
    """
    # 接受 POST 請求
    if request.method == 'POST':
        try:
            data = json.loads(request.body)  # 解析 JSON 數據
            # print("接收到的數據:", data)

            date = data.get('date')
            start_time = data.get('start_time')
            user_name = data.get('user_name')
            room_type = data.get('room_type')
            duration = int(data.get('duration', 30))
            print()
            print("--------------------這裡可以看到使用者要預約的琴房：")
            print("函式名稱：create_calendar_event_view")
            print(f"準備創建日曆事件: 日期={date}, 時間={start_time}, 使用者={user_name}, 琴房={room_type}, 時長={duration}分鐘")
            # 檢查使用者是否超過預約次數上限
            reservation_data = read_data(RESERVATION_LIMIT_RANGE)
            user_found = False
            # print(reservation_data)
            for index, row in enumerate(reservation_data):
                if len(row) >= 2 and row[0] == user_name:  # 比對使用者名稱
                    user_found = True
                    current_count = int(row[1]) if row[1].isdigit() else 0
                    if current_count >= 14:
                        print(f"{user_name} 已達到每周預約上限（14次）")
                        return JsonResponse({'success': False, 'error': '您已達到每周預約上限（14次）。'})

                    # 更新次數 +1
                    reservation_data[index][1] = current_count + 1
                    range_to_update = f'預約上限!B{index + 1}'  # 假設第二列為預約次數
                    update_data(range_to_update, [[current_count + 1]])
                    break

            if not user_found:
                return JsonResponse({'success': False, 'error': '使用者未找到，請聯繫管理員。'})

            # 創建事件
            created_event = create_event(
                date=date,
                start_time=start_time,
                user_name=user_name,
                room_type=room_type,
                duration=duration
            )
            # print("創建成功:", created_event) # 這邊可以看到創建成功的事件所有屬性
            print("創建成功", created_event['summary'], "開始時間:", created_event['start']['dateTime'])

            # 發送郵件通知
            recipient_email = get_user_email(user_name)
            full_time = f"{date} {start_time}"
            send_result = send_email(user_name, full_time, room_type, recipient_email)
            print()
            print()

            if "error" in send_result:
                print("郵件發送錯誤：", send_result["error"])

            return JsonResponse({'success': True, 'event': created_event})
        except Exception as e:
            print("創建事件失敗:", str(e))  # 打印錯誤訊息
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)

def cancel_calendar_event_by_time(request):
    if request.method == 'GET':  # 接受 GET 請求
        try:
            date = request.GET.get('date')
            start_time = request.GET.get('start_time')
            room_type = request.GET.get('roomType')
            user_name = request.GET.get('user_name')

            if not date or not start_time or not room_type or not user_name:
                return JsonResponse({'success': False, 'error': 'Missing required parameters'}, status=400)

            # 將琴房類型映射到日曆 ID
            calendar_mapping = {
                '大琴房': 'ncupianolarge@gmail.com',
                '中琴房': 'ncupianomedium@gmail.com',
                '小琴房': 'ncupianosmall@gmail.com',
                '社窩': 'ncupiano31@gmail.com'
            }
            calendar_id = calendar_mapping.get(room_type)
            if not calendar_id:
                return JsonResponse({'success': False, 'error': '無效的琴房類型'}, status=400)

            # 計算完整的開始時間
            time_min, time_max = calculate_time_range(date, start_time)
            print()
            print("--------------------這裡可以看到使用者取消哪個琴房：")
            print(f"使用的日曆 ID: {calendar_id}, 目標timeMin: {time_min}, 目標timeMax: {time_max}")

            # 獲取當日所有事件
            events_result = service.events().list(
                calendarId=calendar_id,
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            # print("獲取的事件:", events_result) # 這邊可以看到獲取的事件所有屬性
            print(f"獲取的事件：\n - 標題：{events_result['summary']}\n - 開始時間：{events_result['items'][0]['start']['dateTime']}")

            # 查找對應的事件
            events = events_result.get('items', [])
            target_event = None
            for event in events:
                print(f"檢查事件：\n - 標題：{events_result['summary']}\n - 開始時間：{events_result['items'][0]['start']['dateTime']}")
                if user_name in event.get('summary', ''):  # 確認事件是否屬於該用戶
                    target_event = event
                    break
                
            if not target_event:
                return JsonResponse({'success': False, 'error': '未找到符合條件的事件'}, status=404)

            # 刪除事件
            service.events().delete(calendarId=calendar_id, eventId=target_event['id']).execute()

            # 減少預約次數
            reservation_data = read_data(RESERVATION_LIMIT_RANGE)
            user_found = False

            for index, row in enumerate(reservation_data):
                if len(row) >= 2 and row[0] == user_name:  # 比對使用者名稱
                    user_found = True
                    current_count = int(row[1]) if row[1].isdigit() else 0
                    if current_count > 0:
                        reservation_data[index][1] = current_count - 1
                        range_to_update = f'預約上限!B{index + 1}'  # 假設第二列為預約次數
                        update_data(range_to_update, [[current_count - 1]])
                    break
            recipient_email = get_user_email(user_name)
            full_time = f"{date} {start_time}"
            send_result = send_cancel_email(user_name, full_time, room_type, recipient_email)
            if "error" in send_result:
                print("郵件發送錯誤：", send_result["error"])
            print()
            print()
            if not user_found:
                return JsonResponse({'success': False, 'error': '使用者未找到，請聯繫管理員。'})
            return JsonResponse({'success': True, 'message': '預約已取消'})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)

def get_last_sunday(input_date):
    """
    計算指定日期所在周的星期天日期
    :param input_date: 指定日期
    :return: 該日期所在周的星期天
    """
    return input_date - timedelta(days=input_date.weekday() + 1) if input_date.weekday() != 6 else input_date

def reset_limits_if_needed():
    """
    如果預約次數尚未重置，檢查是否需要執行重置操作。
    """
    print("--------------------檢查是否需要重置預約次數")
    try:
        # 檢查試算表中的上次重置日期
        status_range = '系統狀態!A1:B1'
        status_data = read_data(status_range)
        last_reset_date = status_data[0][1] if len(status_data) > 0 and len(status_data[0]) > 1 else None

        # 當前日期
        today = date.today()
        last_sunday = get_last_sunday(today)  # 獲取當前日期所在周的星期天

        # 如果 last_reset_date 為空，或者不屬於當週，執行重置
        if not last_reset_date or date.fromisoformat(last_reset_date) < last_sunday:
            reset_reservation_limits()  # 重置 B 欄
            print(f"執行重置操作，將預約次數重置為 0 (日期: {today})")
        else:
            print(f"不需要重置，最後重置日期為: {last_reset_date}")
    except Exception as e:
        print(f"重置檢查過程中出錯: {e}")
    print()

