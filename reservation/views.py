from django.shortcuts import render

# Create your views here.
def home(request):
    return render(request, 'home.html')
def second_page(request):
    return render(request, 'second.html')