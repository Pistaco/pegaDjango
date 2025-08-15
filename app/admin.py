from django.contrib import admin
from rest_framework.authtoken.admin import TokenAdmin

admin.site.unregister(TokenAdmin)


