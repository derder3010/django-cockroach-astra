import django_filters
from .models import Book, Genre, Status
from django_filters.filters import OrderingFilter
from django_filters import rest_framework as filters

class BookFilter(django_filters.FilterSet):
    genres = django_filters.ModelMultipleChoiceFilter(
        field_name='genres__filter_name',
        to_field_name='filter_name',
        queryset=Genre.objects.all(),)
    status = django_filters.ModelChoiceFilter(queryset=Status.objects.all())
    author = django_filters.CharFilter(
        field_name='author',
        lookup_expr='icontains'
    )
    date_updated = django_filters.DateFilter()
    title = django_filters.CharFilter(
        field_name='title', lookup_expr='icontains')
    theme = django_filters.CharFilter(method='filter_by_theme')
    
    order_by_field = 'ordering'
    ordering = OrderingFilter(
        fields=(
            ('date_updated', 'date_updated'),
            ('title', 'title'),
        )
    )
    
    limit = filters.NumberFilter(method='filter_limit')

    class Meta:
        model = Book
        fields = ['genres', 'status', 'author', 'date_updated', 'title']

    def filter_by_theme(self, queryset, name, value):
        return queryset.filter(search_vector__icontains=value)
    
    def filter_limit(self, queryset, name, value):
        return queryset[:int(value)]
