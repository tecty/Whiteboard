"""whiteboard URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include,path
from django.conf.urls import url

# the stuff remain by all component
from root import views as rviews

urlpatterns = [
    path('admin/', admin.site.urls),

    # bill app
    path('bills/', include('bills.urls')),
    path('settle/', include('settle.urls')),

    # import all auth
    url(r'^accounts/', include('allauth.urls')),

    # account profile pag
    path('accounts/profile/',  rviews.profile,name = "accounts/profile" ),

    # the whole site index
    path('',rviews.index,name = 'index'),
]
