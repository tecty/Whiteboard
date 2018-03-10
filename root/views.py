from django.shortcuts import render
from django.contrib.auth.decorators import login_required

# Create your views here.

def index(request):
    # index of the whole site
    return render(request, 'root/index.html')

# profile should be logined
@login_required
def profile(request):
    # profile for the login account
    return render(request, 'root/profile.html')
