"""

URL configuration for platform_backend project.
The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
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
from django.http import HttpResponse
from datasets.views import (
    signup_view,
    login_view,
    logout_view,
    upload_dataset,
    preview_dataset,
    view_records,
    analytics,
    dataset_history,
    analytics_api,
    product_sales_api,
    sales_trend_api,
    sales_forecast_api,
    ai_chat_api,
    ai_sentiment_api,
    export_csv,
    ai_recommendations_api,
    track_recommendation,
    admin_panel,
    update_user_role,
    delete_user_api,
)

urlpatterns = [
    path("admin/",             admin.site.urls),
    path("signup/",            signup_view,       name="signup"),
    path("login/",             login_view,        name="login"),
    path("logout/",            logout_view,       name="logout"),
    path("",                   upload_dataset,    name="upload"),
    path("upload/",            upload_dataset,    name="upload_page"),
    path("preview/",           preview_dataset,   name="preview"),
    path("records/",           view_records,      name="records"),
    path("analytics/",         analytics,         name="analytics"),
    path("datasets/",          dataset_history,   name="datasets"),
    path("api/analytics/",     analytics_api,     name="analytics_api"),
    path("api/product-sales/", product_sales_api, name="product_sales_api"),
    path("api/sales-trend/",   sales_trend_api,   name="sales_trend_api"),
    path("api/sales-forecast/", sales_forecast_api, name="sales_forecast_api"),
    path("api/ai-chat/", ai_chat_api, name="ai_chat_api"),
    path("api/ai-sentiment/", ai_sentiment_api, name="ai_sentiment_api"),
    path("export/csv/", export_csv, name="export_csv"),
    path("api/ai-recommendations/", ai_recommendations_api, name="ai_recommendations_api"),
    path("admin-panel/",          admin_panel,       name="admin_panel"),
    path("api/update-user-role/", update_user_role,  name="update_user_role"),
    path("api/delete-user/",      delete_user_api,   name="delete_user_api"),
    



]