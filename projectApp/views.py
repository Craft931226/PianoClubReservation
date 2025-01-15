from django.http import HttpResponse
from django.shortcuts import render, redirect
from .models import User

# Create your views here.
def second_page(request):
    error_message = None

    if request.method == 'POST':
        name = request.POST.get('name')
        student_id = request.POST.get('student_id')

        try:
            user = User.objects.get(name=name, student_id=student_id)
            # 將使用者名稱存入 session
            request.session['username'] = user.name
            request.session.modified = True  # 確保 session 被標記為已修改
            return redirect('home')  # 跳轉到首頁
        except User.DoesNotExist:
            error_message = "帳號或密碼錯誤，請重新輸入。"

    return render(request, 'Login.html', {'error_message': error_message})

def home_view(request):
    # 確認 session 中是否有使用者名稱
    username = request.session.get('username')
    if not username:  # 若未登入，跳轉回登入頁面
        return redirect('login')

    return render(request, "homePage.html", {'username': username})
