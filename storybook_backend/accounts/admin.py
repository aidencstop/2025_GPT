from django.contrib import admin
from .models import CustomUser
from .models import Comment
from .models import GeneratedStory

admin.site.register(Comment)
admin.site.register(CustomUser)
admin.site.register(GeneratedStory)