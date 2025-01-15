from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.home, name='home'),  # 將首頁指向 home 視圖
    path('second/', views.second_page, name='second_page'),  # 第二頁
]