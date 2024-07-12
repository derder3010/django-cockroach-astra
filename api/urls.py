from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from .views.User import RegisterView, CustomTokenObtainPairView, LogoutView, UserDetailView, MeDetailView
from .views.Book import BookCreateView, BookDetailView, BookListView, search_books
from .views.Book import VolumeCreateView, VolumeDetailView
from .views.Book import ChapterCreateView, ChapterDetailView, GenreListView
from .views.Book import ChapterUpdateView, ChapterDeleteView, VolumeListView, VolumeListAllView

urlpatterns = [
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # User api
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', CustomTokenObtainPairView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('user/<int:pk>/', UserDetailView.as_view(), name='user-detail'),
    path('user/me/', MeDetailView.as_view(), name='me-detail'),


    # Book api
    path('books/', BookCreateView.as_view(), name='book-create'),
    path('books/<uuid:id>/', BookDetailView.as_view(), name='book-view'),
    path('books/list/', BookListView.as_view(), name='book-list'),
    path('books/permalink/<str:permalink>/',
         BookDetailView.as_view(), name='book-view-permalink'),
    path('books/search/', search_books, name='search-books'),


    path('genres/list/', GenreListView.as_view(), name='genre-list'),

    # Volume api
    path('volumes/', VolumeCreateView.as_view(), name='volume-create'),
    path('volumes/<uuid:id>/', VolumeDetailView.as_view(), name='volume-view'),
    path('books/<str:permalink>/volumes/', VolumeListView.as_view(), name='volume-list'),
    path('books/<uuid:id>/chapters/', VolumeListAllView.as_view(), name='volume-list-all'),

    # Chapter api
    path('chapters/', ChapterCreateView.as_view(), name='chapter-create'),
    path('chapters/<uuid:pk>/', ChapterUpdateView.as_view(), name='chapter-update'),
    path('chapters/<uuid:pk>/delete/', ChapterDeleteView.as_view(), name='chapter-delete'),
    path('chapters/<uuid:id>/',
         ChapterDetailView.as_view(), name='chapter-view'),
    path('chapters/permalink/<str:permalink>/',
         ChapterDetailView.as_view(), name='chapter-view-permalink'),
]
