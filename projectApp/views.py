from datetime import date, datetime, timedelta, timezone
import json
from zoneinfo import ZoneInfo
from django.http import HttpResponse
from django.shortcuts import render, redirect

from projectApp.Facebook_posts import get_facebook_posts

# from projectApp.google_gmail import send_cancel_email, send_email
from .google_sheets import cancel_reservation_log, create_reservation_log, get_user_email, read_data, reset_reservation_limits, update_data
from django.core.signing import Signer, BadSignature
from django.http import JsonResponse
from .google_calendar import create_event, get_events_for_date, create_event, service

number_sequence = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟', 
 '1️⃣ 1️⃣', '1️⃣ 2️⃣', '1️⃣ 3️⃣', '1️⃣ 4️⃣', '1️⃣ 5️⃣', '1️⃣ 6️⃣', '1️⃣ 7️⃣', '1️⃣ 8️⃣', '1️⃣ 9️⃣', 
 '2️⃣ 0️⃣', '2️⃣ 1️⃣', '2️⃣ 2️⃣', '2️⃣ 3️⃣', '2️⃣ 4️⃣', '2️⃣ 5️⃣', '2️⃣ 6️⃣', '2️⃣ 7️⃣', '2️⃣ 8️⃣', '2️⃣ 9️⃣', '3️⃣ 0️⃣']

signer = Signer()  # 簽名工具
# 試算表的範圍，包含用戶數據
GOOGLE_SHEET_RANGE = '社員資料!A2:C'  # 假設試算表有 Name 和 Student ID 列
RESERVATION_LIMIT_RANGE = '預約上限!A1:P'  # 假設試算表有 Name 和 Limit 列

def login_view(request):
    error_message = None

    if request.method == 'POST':
        name = request.POST.get('name')
        student_id = request.POST.get('student_id')
        print("--------------------這裡可以看到誰登入了系統：")
        # time = datetime.now()
        print(f'❓ {name} {student_id}嘗試登入了系統')
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
                        print(f'💁 {name} {student_id}登入成功')
                        print()
                        return redirect(f'/home/?username={signed_username}')
                
                if not user_found:
                    print(f'❌ {name} 登入失敗')
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
        signed_username = signer.sign(username)  # 重新產生簽名，確保安全

        # 每次訪問時檢查是否需要重置
        reset_limits_if_needed()

        return render(request, "homePage.html", {
            'username': username,
            'signed_username': signed_username  # 傳遞簽名名稱
        })    
    except BadSignature:
        return redirect('login')  # 簽名無效時重定向到登入頁面

def Profile_view(request):
    """
    進入個人資料頁面時，根據 username 從 Google Sheets 讀取密碼，並傳遞給前端
    """
    signed_username = request.GET.get('username')

    if not signed_username:
        return redirect('home')  # 如果沒有提供 username，返回首頁
    try:
        username = signer.unsign(signed_username)  # 驗證簽名
        signed_username = signer.sign(username)
        print("--------------------這裡可以看到誰點擊了個人：")
        print("📑 函式名稱：Profile_view")
        print(f"👤 使用者: {username}")
        # 社員資料表的範圍，包含用戶數據
        users = read_data(GOOGLE_SHEET_RANGE)  # 從 Google Sheets 讀取用戶數據
        if not users:
            return JsonResponse({'error': '無法讀取用戶數據'}, status=500)

        password = None
        for user in users:
            if len(user) >= 3 and user[0] == username:
                password = user[2]  # 獲取密碼
                break

        if password is None:
            return JsonResponse({'error': '未找到該用戶'}, status=404)
        
        # 讀取使用者的預約上限
        reserveLimit = None
        reservation_data = read_data(RESERVATION_LIMIT_RANGE)
        reservations = []

        for row in reservation_data:
            if len(row) >= 2 and row[0] == username:
                # print(row)
                reserveLimit = row[1]  # 獲取預約次數
                reservations = row[2:16]  # 讀取該使用者的預約記錄（最多 14 次）
                break

        if reserveLimit is None:
            return JsonResponse({'error': '未找到該用戶的預約上限'}, status=404)

        # 過濾空白預約紀錄，轉換成結構化數據
        filtered_reservations = []
        for res in reservations:
            if res.strip() and res.strip() != "-":
                date_time, room = res.split(" - ")
                date_part, time_part = date_time.split()
                filtered_reservations.append({
                    "date": date_part,
                    "time": time_part,
                    "room": room
                })

        # 按日期 + 時間排序
        sorted_reservations = sorted(filtered_reservations, key=lambda x: (x["date"], x["time"]))
        # print(len(reservations), reservations)
        # print(len(filtered_reservations), filtered_reservations)
        # print(len(sorted_reservations),sorted_reservations)
        num =1
        # for res in sorted_reservations:
        #     print(f"{num}. 📅 日期: {res['date']} 🕑 時間: {res['time']} 🎹 琴房: {res['room']}")
        #     num += 1
        # print()
        return render(request, 'Profile.html', {
            'signed_username' : signed_username,
            'username': username,
            'password': password,
            'reserveLimit': reserveLimit,
            'reservations': json.dumps(sorted_reservations)  # 傳遞 JSON 給前端
        })

    except Exception as e:
        return JsonResponse({'error': f'系統錯誤：{e}'}, status=500)




def change_password_view(request):
    error_message = None
    success_message = None
    print("--------------------這裡可以看到有人點擊了修改密碼：")
    print("📑 函式change_password_view")
    
    if request.method == 'POST':
        name = request.POST.get('name')
        current_password = request.POST.get('currentPassword')
        new_password = request.POST.get('newPassword')
        confirm_password = request.POST.get('confirmPassword')
        print(f'👤 {name} 想要從舊密碼"{current_password}"換成 ⏩ "{new_password}"，認證密碼"{confirm_password}"')
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
    print()
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
        print("📑 函式名稱：get_calendar_events_view")
        print(f"📅 日期: {date}, 🎹 琴房類型: {room_type}, 👤 使用者: {name}")

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
        print("🔽 當天預約情況：")
        if not events:
            print("✖️ 無預約事件 ✖️")
        # events_num = 1
        # for event in events:
        #     name = event['summary'].split()[0]
        #     time = event['start'].split("T")[1].split("+")[0].split(":")[0] + ":" + event['start'].split("T")[1].split("+")[0].split(":")[1]
        #     print(f"{number_sequence[events_num-1]} 📌 名字：{name} 🕑 開始時間：{time}")
        #     events_num += 1
        # print()

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
            data = json.loads(request.body)  # 解 析 JSON 數據
            # print("接收到的數據:", data)

            date = data.get('date')
            start_time = data.get('start_time')
            user_name = data.get('user_name')
            room_type = data.get('room_type')
            duration = int(data.get('duration', 30))
            event_details = f"{date} {start_time} - {room_type}"
            print()
            print("--------------------這裡可以看到使用者要預約的琴房：")
            print("📑 函式名稱：create_calendar_event_view")
            print(f"準備創建日曆事件: 📅 日期={date}, 🕑 時間={start_time}, 👤 使用者={user_name}, 🎹 琴房={room_type}")
            # 檢查使用者是否超過預約次數上限
            reservation_data = read_data(RESERVATION_LIMIT_RANGE)
            user_found = False
            # print(reservation_data)
            for index, row in enumerate(reservation_data):
                # print(index)
                if len(row) >= 2 and row[0] == user_name:  # 比對使用者名稱
                    user_found = True
                    current_count = int(row[1]) if row[1].isdigit() else 0
                    if current_count >= 14:
                        print(f"❎ {user_name} 已達到每周預約上限（14次）")
                        return JsonResponse({'success': False, 'error': '您已達到每周預約上限（14次）。'})
                    for i in range(2, 16):
                        if event_details == row[i]:
                            print(f"❌ 使用者點擊過快")
                            return JsonResponse({'success': False, 'error': '您已預約過該時段。'})
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
            # ✅ 記錄事件到 "預約上限" 試算表的第三欄開始
            create_reservation_log(user_name, event_details)
            # print("創建成功:", created_event) # 這邊可以看到創建成功的事件所有屬性
            print("📌", created_event['summary'])
            date, utctime = created_event['start']['dateTime'].split("T")
            time, utc = utctime.split("+")
            print("🕑", {date},{time})

            # # 發送郵件通知
            # recipient_email = get_user_email(user_name)
            # full_time = f"{date} {start_time}"
            # send_result = send_email(user_name, full_time, room_type, recipient_email)
            print()

            # if "error" in send_result:
            #     print("郵件發送錯誤：", send_result["error"])

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
            print(f"目標timeMin: {time_min}, 目標timeMax: {time_max}, 👤 使用者: {user_name}")

            # 獲取當日所有事件
            events_result = service.events().list(
                calendarId=calendar_id,
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy='startTime'
            ).execute()

            # 取消事件
            cancel_reservation_log(user_name, f"{date} {start_time} - {room_type}")

            # print("獲取的事件:", events_result) # 這邊可以看到獲取的事件所有屬性
            print(f"獲取的事件：\n - 標題：{events_result['summary']}\n - 開始時間：{events_result['items'][0]['start']['dateTime']}")

            # 查找對應的事件
            events = events_result.get('items', [])
            target_event = None
            for event in events:
                # print(f"檢查事件：\n - 標題：{events_result['summary']}\n - 開始時間：{events_result['items'][0]['start']['dateTime']}")
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
            # #郵件通知
            # recipient_email = get_user_email(user_name)
            # full_time = f"{date} {start_time}"
            # send_result = send_cancel_email(user_name, full_time, room_type, recipient_email)
            # if "error" in send_result:
            #     print("郵件發送錯誤：", send_result["error"])
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

def get_last_monday(input_date):
    """
    計算指定日期所在周的星期一日期
    :param input_date: 指定日期
    :return: 該日期所在周的星期一
    """
    return input_date - timedelta(days=input_date.weekday())

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
        tz = ZoneInfo("Asia/Taipei")  # 使用 zoneinfo 設定時區
        today = datetime.now(tz).date()
        last_sunday = get_last_sunday(today)  # 獲取當前日期所在周的星期天
        print(f"當前日期: {today}, 上次重置日期: {last_reset_date}, 上周星期天: {last_sunday}")
        # 如果 last_reset_date 為空，或者不屬於當週，執行重置
        if not last_reset_date or date.fromisoformat(last_reset_date) < last_sunday:
            reset_reservation_limits()  # 重置 B 欄
            print(f"執行重置操作，將預約次數重置為 0 (日期: {today})")
        else:
            print(f"不需要重置，最後重置日期為: {last_reset_date}")
    except Exception as e:
        print(f"重置檢查過程中出錯: {e}")
    print()

def get_latest_post_view(request):
    post = get_facebook_posts()
    # print(post)
    if post:
        return JsonResponse({'post': post}, status=200)
    else:
        return JsonResponse({'error': '無法獲取最新貼文'}, status=500)
