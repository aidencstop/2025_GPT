# accounts/serializers.py
from rest_framework import serializers
from .models import Comment
from .models import GeneratedStory


class GeneratedStorySerializer(serializers.ModelSerializer):
    class Meta:
        model = GeneratedStory
        fields = ['id', 'topic', 'age', 'length', 'story', 'created_at']


class CommentSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'story', 'user', 'content', 'timestamp']