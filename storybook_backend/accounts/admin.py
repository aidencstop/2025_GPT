from django.contrib import admin
from .models import CustomUser
from .models import Comment

admin.site.register(Comment)
admin.site.register(CustomUser)
