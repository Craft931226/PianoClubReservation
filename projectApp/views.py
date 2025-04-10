from datetime import date, datetime, timedelta, timezone
import json
from venv import logger
from zoneinfo import ZoneInfo
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from .tasks import reset_reservation_weekly, update_FB
from django.shortcuts import render, redirect

from projectApp.Facebook_posts import get_facebook_posts

# from projectApp.google_gmail import send_cancel_email, send_email
from .google_sheets import GetRoomEmail, cancel_reservation_log, create_reservation_log, get_user_email, read_data, update_data
from django.core.signing import Signer, BadSignature
from django.http import JsonResponse
from .google_calendar import create_event, get_events_for_date, create_event, service
from urllib.parse import quote, unquote


signer = Signer()  # 簽名工具
# 試算表的範圍，包含用戶數據
GOOGLE_SHEET_RANGE = '社員資料!A2:C'  # 假設試算表有 Name 和 Student ID 列
RESERVATION_LIMIT_RANGE = '預約上限!A1:P'  # 假設試算表有 Name 和 Limit 列
STATUS_RANGE = '系統狀態'
RULES_RANGE = '規則'


def login_view(request):
    error_message = None

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        student_id = request.POST.get('student_id', '').strip()

        if not name or not student_id:
            error_message = "請輸入帳號與學號"
            return render(request, 'Login.html', {'error_message': error_message})

        try:
            users = read_data(GOOGLE_SHEET_RANGE)  # 獲取用戶數據
            if not users:
                error_message = "無法讀取用戶數據，請稍後再試。"
            else:
                for user in users:
                    if len(user) >= 2 and user[0] == name and user[2] == student_id:
                        logger.info(f'{name} 登入成功')

                        response = redirect('/home/')  # 重定向到首頁
                        encoded_name = quote(name)  # 簽名用戶名
                        response.set_cookie('username', encoded_name, 
                                            max_age=3600, 
                                            httponly=True,
                                            samesite="Strict",
                                            secure=True)  # 設定 Cookie
                        return response

                error_message = "帳號或密碼錯誤，請重新輸入。"
                logger.warning(f'{name} 登入失敗')
        except Exception as e:
            logger.error(f"系統錯誤: {e}")
            error_message = "系統發生錯誤，請聯繫管理員。"

    return render(request, 'Login.html', {'error_message': error_message})


def home_view(request):
    encoded_username = request.COOKIES.get('username')  # 從 Cookie 讀取 username
    username = unquote(encoded_username) if encoded_username else None  # 解碼 username

    if not username:
        return redirect('login')  # 如果 Cookie 不存在，跳轉到登入頁面

    return render(request, "homePage.html", {'username': username})


def Profile_view(request):
    encoded_username = request.COOKIES.get('username')  # 從 Cookie 讀取 username
    username = unquote(encoded_username) if encoded_username else None  # 解碼 username

    if not username:
        return redirect('home')  # 如果 Cookie 不存在，返回首頁

    try:
        print("--------------------這裡可以看到誰點擊了個人：")
        print("📑 函式名稱：Profile_view")
        print(f"👤 使用者: {username}")

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
        # num =1
        # for res in sorted_reservations:
        #     print(f"{num}. 📅 日期: {res['date']} 🕑 時間: {res['time']} 🎹 琴房: {res['room']}")
        #     num += 1
        # print()
        return render(request, 'Profile.html', {
            'username': username,
            'password': password,
            'reserveLimit': reserveLimit,
            'reservations': json.dumps(sorted_reservations)  # 傳遞 JSON 給前端
        })

    except Exception as e:
        return JsonResponse({'error': f'系統錯誤：{e}'}, status=500)

def logout_view(request):
    response = redirect('login')  # 登出後重定向到登入頁面
    response.delete_cookie('username')  # 刪除 Cookie
    return response



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
        calendar_mapping = GetRoomEmail()

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
            status_data = read_data(STATUS_RANGE)
            reserveLimit = 0
            for row in status_data:
                if len(row) > 0:
                    if row[0] == 'WeeklyReservationLimit':
                        reserveLimit = int(row[1])
            reservation_data = read_data(RESERVATION_LIMIT_RANGE)
            user_found = False
            # print(reservation_data)
            for index, row in enumerate(reservation_data):
                # print(index)
                if len(row) >= 2 and row[0] == user_name:  # 比對使用者名稱
                    user_found = True
                    current_count = int(row[1]) if row[1].isdigit() else 0
                    if current_count >= reserveLimit:
                        print(f"❎ {user_name} 已達到每周預約上限（14次）")
                        return JsonResponse({'success': False, 'error': '您已達到每周預約上限（14次）。'})
                    for i in range(2, reserveLimit+2):
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
            calendar_mapping = GetRoomEmail()
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


def get_latest_post_view(request):
    post = get_facebook_posts()
    # print(post)
    if post:
        return JsonResponse([post], safe = False)
    else:
        return JsonResponse({'error': '無法獲取最新貼文'}, status=500)
    
def get_show_reserve_name(request):
    data = read_data(STATUS_RANGE)
    for row in data:
        if len(row) > 0:
            if row[0] == 'ShowReserveName':
                return JsonResponse({'ShowReserveName': row[1]})

def get_room_type(request):
    # print("call 到")
    data = read_data(STATUS_RANGE)
    for row in data:
        if len(row) > 0:
            if row[0] == 'NumbersOfrooms':
                num =int(row[1])
                # print(num)
                break
    for row in data:
        if len(row) > 0:
            if row[0] == 'RoomName':
                room_name = row[1:1+num]
                # print(room_name)
                return JsonResponse({'RoomName': room_name})
            
def get_system_name(request):
    # print("call")
    data = read_data(STATUS_RANGE)
    for row in data:
        if len(row) > 0:
            if row[0] == 'SystemName':
                # print(row[1])
                return JsonResponse({'SystemName': row[1]})
            
def get_time_range(request):
    data = read_data(STATUS_RANGE)
    for row in data:
        if len(row) > 0:
            if row[0] == 'ReserveTimeRange':
                # print(row)
                return JsonResponse({'starttime': int(row[1]), 'endtime': int(row[2])}) 

def get_rules(request):
    data = read_data("規則")
    NumbersOfFAQs = 0
    NumbersOfAnnounce = 0
    for row in data:
        if len(row) > 0:
            if row[0] == '常見問題':
                if row[1] != '狀態':
                    if int(row[1][1]) > NumbersOfFAQs:
                        NumbersOfFAQs = int(row[1][1])
            if row[0] == '公告':
                if row[1] != '狀態':
                    if int(row[1][2]) > NumbersOfAnnounce:
                        NumbersOfAnnounce = int(row[1][2])

    # print(data)
    announcement_state = False
    notation_state = False
    QAstate = False
    announcement_title   = ["" for i in range(NumbersOfAnnounce)]
    announcement_content = ["" for i in range(NumbersOfAnnounce)]
    notation = {"system": [], "room": []}
    Q = ["" for i in range(NumbersOfFAQs)]
    A = ["" for i in range(NumbersOfFAQs)]
    for row in data:
        if len(row) > 0:
            if row[0] == '常見問題':
                if row[1] == '狀態':
                    if row[2] == "Y":
                        QAstate = True
                if row[1][0] == "Q" and QAstate:
                    Q[int(row[1][1])-1] = row[2]
                if row[1][0] == "A" and QAstate:
                    A[int(row[1][1])-1] = row[2]
            if row[0] == '注意事項':
                if row[1] == '狀態':
                    if row[2] == "Y":
                        notation_state = True
                if row[1] == '預約系統' and notation_state:
                    notation["system"].append(row[2])
                if row[1] == '琴房' and notation_state:
                    notation["room"].append(row[2])
            if row[0] == '公告':
                if row[1] == '狀態':
                    if row[2] == "Y":
                        announcement_state = True
                if row[1][:2] == '標題' and announcement_state:
                    announcement_title[int(row[1][2])-1] = row[2]
                if row[1][:2] == '內文' and announcement_state:
                    announcement_content[int(row[1][2])-1] = row[2]
    # print("公告標題", announcement_title)
    # print("公告內容", announcement_content)
    return JsonResponse({'Q': Q, 
                         'A': A,
                         'notation': notation, 
                         'announcement_title': announcement_title, 
                         'announcement_content': announcement_content})

@csrf_exempt
def reset_reservation_view(request):
    if request.method == 'POST':
        try:
            reset_reservation_weekly()  # 重置預約次數
            return JsonResponse({'success': True, 'message': '預約已重置'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)

@csrf_exempt
def refresh_fb_token(request):
    if request.method == 'POST':
        try:
            update_FB()  # 更新 Facebook token
            return JsonResponse({'success': True, 'message': 'Facebook token 已更新'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)
    
@csrf_exempt
def ping(request):
    return HttpResponse("pong")