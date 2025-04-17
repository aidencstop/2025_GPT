from django.shortcuts import render
import os
from django.http import HttpResponse
from django.views import View
from django.conf import settings

# accounts/views.py
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import Comment
from .serializers import CommentSerializer

import openai

import requests


BASE_FRONTEND_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'storybook_backend',
    'frontend'
)

class LoginPageView(View):
    def get(self, request):
        html_path = os.path.join(BASE_FRONTEND_PATH, 'index.html')
        with open(html_path, 'r', encoding='utf-8') as f:
            return HttpResponse(f.read())

class GeneratorPageView(View):
    def get(self, request):
        html_path = os.path.join(BASE_FRONTEND_PATH, 'generate.html')
        with open(html_path, 'r', encoding='utf-8') as f:
            return HttpResponse(f.read())

class StaticHTMLView(View):
    def get(self, request):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # points to storybook_backend/
        html_path = os.path.join(base_dir, 'storybook_backend', 'frontend', 'generate.html')
        try:
            with open(html_path, 'r', encoding='utf-8') as f:
                return HttpResponse(f.read())
        except FileNotFoundError:
            return HttpResponse('<h1>generate.html not found</h1>', status=404)

class DashboardPageView(View):
    def get(self, request):
        html_path = os.path.join(BASE_FRONTEND_PATH, 'dashboard.html')
        with open(html_path, 'r', encoding='utf-8') as f:
            return HttpResponse(f.read())

class StoryDetailView(View):
    def get(self, request):
        html_path = os.path.join(BASE_FRONTEND_PATH, 'story_detail.html')
        with open(html_path, 'r', encoding='utf-8') as f:
            return HttpResponse(f.read())

@api_view(['POST'])
def register_user(request):
    try:
        data = request.data
        if User.objects.filter(username=data['username']).exists():
            return Response({'message': 'Username already exists'}, status=status.HTTP_400_BAD_REQUEST)
        if User.objects.filter(email=data['email']).exists():
            return Response({'message': 'Email already registered'}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.create(
            username=data['username'],
            email=data['email'],
            password=make_password(data['password'])
        )
        return Response({'message': 'User registered successfully'})
    except Exception as e:
        return Response({'message': 'Registration failed', 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def login_user(request):
    data = request.data
    user = authenticate(username=data['email'], password=data['password'])
    if user is not None:
        return Response({'message': 'Login successful'})
    else:
        return Response({'message': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
def generate_story(request):
    data = request.data
    topic = data.get('topic')
    age = data.get('age')
    length = data.get('length')

    prompt = f"""
    Write a {length} children's story for ages {age} about the topic: {topic}.
    Make it fun, educational, and age-appropriate.
    """

    openai.api_key = settings.OPENAI_API_KEY

    try:
        response = openai.ChatCompletion.create(
            model='gpt-4',
            messages=[
                {"role": "system", "content": "You are a children's storybook author."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        story = response['choices'][0]['message']['content']
        return Response({'story': story})
    except Exception as e:
        return Response({'error': str(e)}, status=500)

@api_view(['POST'])
def generate_image(request):
    data = request.data
    prompt = data.get('prompt')  # You might pass part of the story here

    url = "https://api.replicate.com/v1/predictions"
    headers = {
        "Authorization": f"Token {settings.REPLICATE_API_TOKEN}",
        "Content-Type": "application/json"
    }
    body = {
        "version": "your-stable-diffusion-model-id",
        "input": { "prompt": prompt }
    }

    try:
        res = requests.post(url, json=body, headers=headers)
        prediction = res.json()
        image_url = prediction['urls']['get']  # or however the model returns it
        return Response({'image_url': image_url})
    except Exception as e:
        return Response({'error': str(e)}, status=500)


@api_view(['GET'])
def get_comments(request, story_id):
    comments = Comment.objects.filter(story_id=story_id).order_by('-timestamp')
    serializer = CommentSerializer(comments, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def post_comment(request):
    data = request.data
    serializer = CommentSerializer(data=data)
    if serializer.is_valid():
        serializer.save(user=request.user)
        return Response(serializer.data, status=201)
    return Response(serializer.errors, status=400)

@api_view(['PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def edit_or_delete_comment(request, comment_id):
    try:
        comment = Comment.objects.get(id=comment_id, user=request.user)
    except Comment.DoesNotExist:
        return Response({'error': 'Not found or unauthorized'}, status=404)

    if request.method == 'PUT':
        comment.content = request.data.get('content')
        comment.save()
        return Response({'message': 'Comment updated'})
    elif request.method == 'DELETE':
        comment.delete()
        return Response({'message': 'Comment deleted'})