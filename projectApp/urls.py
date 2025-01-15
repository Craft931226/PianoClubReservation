from django.urls import path
from . import views
from .views import home_view

urlpatterns = [
    path('', views.second_page, name='login'),  # 空路徑對應登入頁面
    path('login/', views.second_page, name='login'),  # 可選，提供 /login/ 進入
    path('home/', views.home_view, name='home'),
]