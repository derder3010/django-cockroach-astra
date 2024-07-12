from api.filters import BookFilter
from api.serializers import BookSerializer
from api.serializers import VolumeSerializer, ChapterSerializer, GenreSerializer, VolumeForCreateSerializer
from api.serializers import BookListViewSerializer, ChapterForCreateSerializer, BookDetailViewSerializer, ChapterSummarySerializer
from api.models import Book, Volume, Chapter, Genre
from api.utils import normalize_text, generate_permalink
from rest_framework import generics, status, viewsets
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import AllowAny, BasePermission, IsAuthenticated
from rest_framework.exceptions import NotFound
from django.core.cache import cache
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from django_filters.rest_framework import DjangoFilterBackend
import hashlib
import json
import zlib
from django.utils import timezone
from rest_framework import serializers
from rest_framework.pagination import PageNumberPagination
from cassandra.cqlengine import connection


class IsSuperUser(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_superuser


class IsModeratorOrHigher(BasePermission):
    def has_permission(self, request, view):
        return request.user and (request.user.is_staff or request.user.is_superuser)




@api_view(['GET'])
@permission_classes([AllowAny])
@cache_page(60 * 12)
def search_books(request):
    query = request.query_params.get('q', None)
    if query:
        query = normalize_text(query)
        books = Book.objects.search_query(query)
        serializer = BookListViewSerializer(
            books, many=True, context={'request': request})
        if serializer.data:
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response({"error": "No books found."}, status=status.HTTP_404_NOT_FOUND)
    return Response({"error": "Query parameter 'q' is required."}, status=status.HTTP_400_BAD_REQUEST)


class BookCreateView(generics.CreateAPIView):
    queryset = Book.objects.all()
    permission_classes = (IsModeratorOrHigher,)
    serializer_class = BookSerializer

    def perform_create(self, serializer):
        serializer.save(posted_by=self.request.user)


class BookDetailView(generics.RetrieveAPIView):
    queryset = Book.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = BookDetailViewSerializer

    def get_object(self):
        if 'id' in self.kwargs:
            lookup_field = 'id'
            lookup_value = self.kwargs['id']
        elif 'permalink' in self.kwargs:
            lookup_field = 'permalink'
            lookup_value = self.kwargs['permalink']
        else:
            raise NotFound("Book not found")

        try:
            return Book.objects.get(**{lookup_field: lookup_value})
        except Book.DoesNotExist:
            raise NotFound("Book not found")
    

class BookListPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
     
class BookListView(generics.ListAPIView):
    queryset = Book.objects.all()
    serializer_class = BookListViewSerializer
    permission_classes = (AllowAny,)
    filter_backends = [DjangoFilterBackend]
    filterset_class = BookFilter
    pagination_class = BookListPagination

    def list(self, request, *args, **kwargs):
        # Generate cache key based on request query parameters
        query_params = request.query_params
        cache_key = hashlib.md5(json.dumps(
            query_params, sort_keys=True).encode('utf-8')).hexdigest()
        cached_response = cache.get(cache_key)

        if cached_response:
            # Decompress response
            cached_response = zlib.decompress(cached_response)
            return Response(json.loads(cached_response))
        
        queryset = self.filter_queryset(self.get_queryset())
        
        # Check if limit parameter is provided
        limit = request.query_params.get('limit')
        if limit:
            queryset = queryset[:int(limit)]
            page = None
        else:
            page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            result = self.get_paginated_response(serializer.data)
        else:
            serializer = self.get_serializer(queryset, many=True)
            result = Response(serializer.data)

        # Compress response
        compressed_response = zlib.compress(
            json.dumps(result.data).encode('utf-8'))
        cache.set(cache_key, compressed_response,
                  timeout=60*30)  # Cache for 30 minutes
        return result

class VolumeListView(generics.ListAPIView):
    permission_classes = (AllowAny,)
    serializer_class = VolumeSerializer
    
    def get_queryset(self):
        permalink = self.kwargs['permalink']
        book = Book.objects.filter(permalink=permalink).first()
        if book:
            return Volume.objects.filter(book=book)
        return Volume.objects.none()
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if not queryset.exists():
            return Response({"detail": "Book not found or no volume available."}, status=status.HTTP_204_NO_CONTENT)
        serializer = self.get_serializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)

@method_decorator(cache_page(60 * 12), name='dispatch')    
class VolumeListAllView(generics.ListAPIView):
    def get(self, request, *args, **kwargs):
        book_id = kwargs.get('id')
        book = Book.objects.filter(id=book_id).first()
        if not book:
            return Response({"detail": "Book not found."}, status=404)

        volumes = Volume.objects.filter(book=book)
        result = {
            "permalink": book.permalink,
            "volumes": []
            }

        for volume in volumes:
            query = f"""
            SELECT id, permalink, name FROM doctruyen.chapter 
            WHERE volume_id = {volume.id}
            ALLOW FILTERING
            """
            session = connection.get_session()
            rows = session.execute(query)
            chapters = list(rows)
            volume_data = {
                "id": volume.id,
                "name": volume.name,
                "chapters": []
            }
            for chapter in chapters:
                volume_data["chapters"].append({
                    "id": str(chapter['id']),  # Ensure UUIDs are converted to strings
                    "name": chapter['name'],
                    "permalink": chapter['permalink'],
                })
            result["volumes"].append(volume_data)

        return Response(result)


class VolumeCreateView(generics.CreateAPIView):
    queryset = Volume.objects.all()
    permission_classes = (IsModeratorOrHigher,)
    serializer_class = VolumeForCreateSerializer

    def perform_create(self, serializer):
        serializer.save()


class VolumeDetailView(generics.RetrieveAPIView):
    queryset = Volume.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = VolumeSerializer

    def get_object(self):
        lookup_field = None
        lookup_value = None

        if 'id' in self.kwargs:
            lookup_field = 'id'
            lookup_value = self.kwargs['id']
        try:
            return Volume.objects.get(**{lookup_field: lookup_value})
        except Chapter.DoesNotExist:
            raise NotFound("Volume not found")


class ChapterCreateView(generics.CreateAPIView):
    queryset = Chapter.objects.all()
    serializer_class = ChapterForCreateSerializer
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        data = request.data.copy()
        data['date_created'] = timezone.now().isoformat()
        data['date_updated'] = timezone.now().isoformat()
        last_chapter = Chapter.objects.filter(book_id=data['book_id']).order_by('-number').first()
        data['number'] =  1 if last_chapter is None else last_chapter.number + 1
        # Generate permalink if not provided
        if 'permalink' not in data or not data['permalink']:
            data['permalink'] = generate_permalink(data['name'])

        serializer = self.get_serializer(data=data)

        if serializer.is_valid():
            try:
                chapter = serializer.save()
                return Response(ChapterSerializer(chapter).data, status=status.HTTP_201_CREATED)
            except serializers.ValidationError as e:
                return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                return Response({"error": "Unexpected error occurred"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ChapterUpdateView(generics.UpdateAPIView):
    queryset = Chapter.objects.all()
    serializer_class = ChapterSerializer
    permission_classes = (AllowAny,)

    def put(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        data = request.data.copy()
        data['date_updated'] = timezone.now().isoformat()

        serializer = self.get_serializer(instance, data=data, partial=partial)
        if serializer.is_valid():
            try:
                chapter = serializer.save()
                return Response(ChapterSerializer(chapter).data, status=status.HTTP_200_OK)
            except Exception as e:
                print("Error updating chapter:", e)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChapterDeleteView(generics.DestroyAPIView):
    queryset = Chapter.objects.all()
    permission_classes = (AllowAny,)
    
class ChapterDetailView(generics.RetrieveAPIView):
    queryset = Chapter.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = ChapterSerializer

    def get_object(self):
        lookup_field = None
        lookup_value = None

        if 'id' in self.kwargs:
            lookup_field = 'id'
            lookup_value = self.kwargs['id']
        elif 'permalink' in self.kwargs:
            lookup_field = 'permalink'
            lookup_value = self.kwargs['permalink']
        else:
            raise NotFound("Chapter not found")

        try:
            return Chapter.objects.get(**{lookup_field: lookup_value})
        except Chapter.DoesNotExist:
            raise NotFound("Chapter not found")

@method_decorator(cache_page(60 * 12), name='dispatch')
class GenreListView(generics.ListAPIView):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = (AllowAny,)
