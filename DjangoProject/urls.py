"""
URL configuration for DjangoProject project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
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
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

from DjangoProject import settings
from app.admin import bodeguero_admin_site
from rest_framework import routers
from rest_framework.authtoken.views import obtain_auth_token

from app.views import CurrentUserGroupView, PDFUploadView, ExcelUploadView

urlpatterns = [
        path('admin/', admin.site.urls),
        path('api/', include('app.urls')),
        path('api/user-groups/', CurrentUserGroupView.as_view(), name='user-groups'),
        path('api-token-auth/', obtain_auth_token, name='api_token_auth'),
        path('api/upload-pdf/', PDFUploadView.as_view(), name='upload_pdf'),
        path("api/upload-excel/", ExcelUploadView.as_view(), name="upload_excel"),
]
