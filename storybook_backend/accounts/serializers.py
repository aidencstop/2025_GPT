# accounts/serializers.py
from rest_framework import serializers
from .models import Comment

class CommentSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'user', 'username', 'story_id', 'content', 'timestamp']
        read_only_fields = ['id', 'user', 'username', 'timestamp']
