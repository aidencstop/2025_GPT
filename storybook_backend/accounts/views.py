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
from .models import GeneratedStory
from .serializers import CommentSerializer
from .serializers import GeneratedStorySerializer


import openai
from openai import OpenAI

import requests


from rest_framework.authtoken.models import Token

from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator




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


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])  # ✅ anyone can access this
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


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])  # ✅ anyone can access this
def login_user(request):
    data = request.data
    email = data.get('email')
    password = data.get('password')
    user = authenticate(username=data['email'], password=data['password'])
    if user is not None:
        token, created = Token.objects.get_or_create(user=user)
        return Response({'message': 'Login successful', 'token': token.key}, status=200)
    else:
        return Response({'message': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)



@method_decorator(csrf_exempt, name='dispatch')
class GenerateStoryView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        topic = request.data.get("topic")
        age = request.data.get("age")
        length = request.data.get("length")

        prompt = (
            f"Write a children's story about {topic} for ages {age}. "
            f"The story should be {length} in length and educational."
        )

        try:
            client = OpenAI(api_key=settings.OPENAI_API_KEY)

            # chat_response = client.chat.completions.create(
            #     model="gpt-3.5-turbo",  # use this instead of gpt-4
            #     messages=[
            #         {"role": "system", "content": "You are a children's storybook author."},
            #         {"role": "user", "content": prompt}
            #     ],
            #     temperature=0.7
            # )

            story_text = f"This is a mock story about {topic} for ages {age} with a {length} length. Replace this with real OpenAI output after billing is enabled."

            GeneratedStory.objects.create(
                user=request.user,
                topic=topic,
                age=age,
                length=length,
                story=story_text
            )

            return Response({"story": story_text}, status=200)

        except Exception as e:
            return Response({"error": str(e)}, status=500)

# @method_decorator(csrf_exempt, name='dispatch')  # disables CSRF check for class view
# class GenerateStoryView(APIView):
#     permission_classes = [IsAuthenticated]
#
#     def post(self, request):
#         data = request.data
#         topic = data.get('topic')
#         age = data.get('age')
#         length = data.get('length')
#
#         prompt = f"""
#         Once upon a time, there was a curious child who loved learning about {topic}.
#         At the age of {age}, they discovered that the world of {topic} was filled with adventure!
#         This {length} story is just the beginning of their journey.
#         """
#
#         openai.api_key = settings.OPENAI_API_KEY
#
#         try:
#             response = openai.ChatCompletion.create(
#                 model='gpt-4',
#                 messages=[
#                     {"role": "system", "content": "You are a children's storybook author."},
#                     {"role": "user", "content": prompt}
#                 ],
#                 temperature=0.7
#             )
#             story = response['choices'][0]['message']['content']
#
#             GeneratedStory.objects.create(
#                 user=request.user,
#                 topic=topic,
#                 age=age,
#                 length=length,
#                 story=story
#             )
#
#             return Response({'story': story}, status=status.HTTP_200_OK)
#
#         except Exception as e:
#             return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# @api_view(['POST'])
# def generate_image(request):
#     data = request.data
#     prompt = data.get('prompt')  # You might pass part of the story here
#
#     url = "https://api.replicate.com/v1/predictions"
#     headers = {
#         "Authorization": f"Token {settings.REPLICATE_API_TOKEN}",
#         "Content-Type": "application/json"
#     }
#     body = {
#         "version": "your-stable-diffusion-model-id",
#         "input": { "prompt": prompt }
#     }
#
#     try:
#         res = requests.post(url, json=body, headers=headers)
#         prediction = res.json()
#         image_url = prediction['urls']['get']  # or however the model returns it
#         return Response({'image_url': image_url})
#     except Exception as e:
#         return Response({'error': str(e)}, status=500)

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

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_stories(request):
    stories = GeneratedStory.objects.filter(user=request.user).order_by('-created_at')
    serializer = GeneratedStorySerializer(stories, many=True)
    return Response(serializer.data)

@csrf_exempt
@api_view(['POST'])
def test_view(request):
    return Response({'message': 'It works!'})