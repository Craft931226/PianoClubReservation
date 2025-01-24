from django.http import HttpResponse
from django.shortcuts import render, redirect
from .google_sheets import read_data, update_data
from django.core.signing import Signer, BadSignature

signer = Signer()  # 簽名工具
# 試算表的範圍，包含用戶數據
GOOGLE_SHEET_RANGE = '社員資料!A2:C'  # 假設試算表有 Name 和 Student ID 列

def second_page(request):
    error_message = None

    if request.method == 'POST':
        name = request.POST.get('name')
        student_id = request.POST.get('student_id')

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

from django.http import JsonResponse
from .google_calendar import get_events_for_date

def get_calendar_events_view(request):
    if request.method == 'GET':
        date = request.GET.get('date')  # ISO 格式的日期
        print(date)
        if not date:
            return JsonResponse({'error': 'Missing date parameter'}, status=400)
        
        calendar_ids = [
            'ncupianolarge@gmail.com',
            'ncupianosmall@gmail.com',
            'ncupianomedium@gmail.com',
            'ncupiano31@gmail.com'
        ]
        
        events = get_events_for_date(calendar_ids, date)
        print(events)
        return JsonResponse({'events': events}, status=200)
    else:
        return JsonResponse({'error': 'Method not allowed'}, status=405)