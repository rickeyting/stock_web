"""
URL configuration for stock_web project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
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
from django.urls import path
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('<int:diseases_info_id>', views.home, name='home'),
    path('classification/', views.classification, name='classification'),
    path('strategy/', views.strategy, name='strategy'),
    path('refresh/', views.refresh, name='refresh'),
    path('update-pred/', views.update_daily_data, name='update_daily_data'),
    path('update-types/', views.update_stock_types, name='update_stock_types'),
    path('clean-data/', views.clean_all_data, name='clean_all_data'),
    path('download-csv/', views.download_csv, name='download_csv'),
]
