# accounts/urls.py
from django.urls import path
from .views import *

urlpatterns = [
    path('', LoginPageView.as_view()),         # Now root loads login page
    path('generate/', GeneratorPageView.as_view()),  # Story UI moved here
    path('register/', register_user),
    path('login/', login_user),
    path('api/generate/', generate_story),
    path('dashboard/', DashboardPageView.as_view()),
    path('api/comments/<str:story_id>/', get_comments),
    path('api/comments/', post_comment),
    path('api/comments/<int:comment_id>/edit/', edit_or_delete_comment),
    path('api/image/', generate_image),
    path('story/', StoryDetailView.as_view()),  # /story/?id=0 or 1 or 2...
]
