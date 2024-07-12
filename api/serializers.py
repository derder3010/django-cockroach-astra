# api/serializers.py
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Book, Genre, Volume, Chapter, Status
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .custom_fields import UUIDField, TextField, DateTimeField, IntegerField, BooleanField
import uuid
from django.core.files.base import ContentFile
import requests
from django.core.cache import cache
from rest_framework.pagination import PageNumberPagination
from cassandra.cqlengine import connection


class UserSerializer(serializers.ModelSerializer):
    id = TextField()

    class Meta:
        model = User
        fields = "__all__"


class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'password', 'email']
        extra_kwargs = {'password': {'write_only': True}}

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "A user with this email already exists.")
        return value

    def validate_username(self, value):
        if len(value) < 6:
            raise serializers.ValidationError(
                "Username must be at least 6 characters long.")
        return value

    def validate_password(self, value):
        if len(value) < 6:
            raise serializers.ValidationError(
                "Password must be at least 6 characters long.")
        return value

    def create(self, validated_data):
        user = User.objects.create_user(
            validated_data['username'], validated_data['email'], validated_data['password'])
        return user


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = "__all__"


class StatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Status
        fields = '__all__'


class ChapterSerializer(serializers.ModelSerializer):
    book_id = serializers.SerializerMethodField()
    number = IntegerField(required=False)
    id = UUIDField(required=False)
    volume_id = UUIDField()
    name = TextField()
    content = TextField()
    permalink = TextField(required=False)
    date_created = DateTimeField(required=False)
    date_updated = DateTimeField(required=False)
    book_title = serializers.SerializerMethodField()
    

    class Meta:
        model = Chapter
        fields = "__all__"
        
    def get_book_id(self, obj):
        book = Volume.objects.get(id=obj.volume_id).book
        return str(book.id)
    
    def get_book_title(self, obj):
        book = Volume.objects.get(id=obj.volume_id).book
        return book.title


        
class ChapterForCreateSerializer(serializers.ModelSerializer):
    book_id = UUIDField()
    number = IntegerField(required=False)
    id = UUIDField(required=False)
    volume_id = UUIDField()
    name = TextField()
    content = TextField()
    permalink = TextField(required=False)
    date_created = DateTimeField(required=False)
    date_updated = DateTimeField(required=False)
    
    

    class Meta:
        model = Chapter
        fields = "__all__"
        
    
    def create(self, validated_data):
        try:
            chapter = Chapter(**validated_data)
            chapter.save()
            return chapter
        except Exception as e:
            return None




class ChapterSummarySerializer(serializers.ModelSerializer):
    id = UUIDField()
    name = TextField()
    permalink = TextField()
    date_updated = DateTimeField()

    class Meta:
        model = Chapter
        fields = fields = ['id', 'name', 'date_updated', 'permalink']


class ChapterPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100
    
class VolumeForCreateSerializer(serializers.ModelSerializer):
    id = UUIDField(required=False)

    class Meta:
        model = Volume
        fields = "__all__"

    def create(self, validated_data):
        volume = Volume.objects.create(**validated_data)
        volume.save()
        return volume
    
    
class VolumeSerializer(serializers.ModelSerializer):
    id = UUIDField(required=False)
    chapters = serializers.SerializerMethodField()

    class Meta:
        model = Volume
        fields = "__all__"

    def create(self, validated_data):
        volume = Volume.objects.create(**validated_data)
        volume.save()
        return volume


    def get_chapters(self, obj):
        request = self.context.get('request')
        if not request:
            return []

        paginator = ChapterPagination()
        page = request.query_params.get(paginator.page_query_param, 1)
        page_size = request.query_params.get(paginator.page_size_query_param, paginator.page_size)
        cache_key = f"chapters_{obj.id}_{page}_{page_size}"
        cached_chapters = cache.get(cache_key)
        if cached_chapters is not None:
            return cached_chapters

        
        query = f"""
        SELECT id, permalink, name, date_updated FROM doctruyen.chapter 
        WHERE volume_id = {obj.id}
        ALLOW FILTERING
        """
        session = connection.get_session()
        rows = session.execute(query)
        chapters_queryset = list(rows)
        paginated_chapters = paginator.paginate_queryset(chapters_queryset, request)
        

        response_data = paginator.get_paginated_response(ChapterSummarySerializer(paginated_chapters, many=True).data).data

        # Cache the response data
        cache.set(cache_key, response_data, timeout=60*60)  # Cache for 15 minutes

        return response_data
    


class ImageURLField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('http'):
            response = requests.get(data)
            if response.status_code == 200:
                file_name = str(uuid.uuid4()) + '.jpg'
                return ContentFile(response.content, name=file_name)
            raise serializers.ValidationError("Failed to download image.")
        return super().to_internal_value(data)

class BookListViewSerializer(serializers.ModelSerializer):

    class Meta:
        model = Book
        fields = ['id', 'title', 'cover_image', 'author', 'description', 'status', 'permalink', 'genres']

class BookDetailViewSerializer(serializers.ModelSerializer):
    id = UUIDField(required=False)
    genres = GenreSerializer(many=True)
    status = StatusSerializer()
    posted_by = serializers.ReadOnlyField(source='posted_by.username')
    is_following = serializers.SerializerMethodField()
    cover_image = ImageURLField()

    class Meta:
        model = Book
        fields = "__all__"



class BookSerializer(serializers.ModelSerializer):
    id = UUIDField(required=False)
    posted_by = serializers.ReadOnlyField(source='posted_by.username')
    volumes = VolumeSerializer(many=True, read_only=True)
    cover_image = ImageURLField()

    class Meta:
        model = Book
        fields = "__all__"

    def create(self, validated_data):
        genres_data = validated_data.pop('genres', [])
        book = Book.objects.create(**validated_data)
        book.genres.set(genres_data)
        return book



class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['username'] = user.username
        return token

    def validate(self, attrs):
        credentials = {
            'username': attrs.get('username'),
            'password': attrs.get('password'),
        }
        user = User.objects.filter(email=credentials['username']).first(
        ) or User.objects.filter(username=credentials['username']).first()
        if user is not None:
            credentials['username'] = user.username
        return super().validate(credentials)
