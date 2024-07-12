from django.db import models, connection
from django.contrib.auth.models import User
from django.db.models import Manager
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError
import uuid
import re
from .utils import generate_permalink, normalize_text
from django.utils import timezone
from django_cassandra_engine.models import DjangoCassandraModel
from cassandra.cqlengine.columns import UUID as CassandraUUID, Text, DateTime, Integer

class SearchManager(Manager):
    def search_query(self, raw_query):
        sanitized_query = re.sub(r'[^a-zA-Z0-9\s]', '', raw_query)
        sanitized_query = normalize_text(sanitized_query)
        query = f"""
            SELECT id, similarity(search_vector, '{sanitized_query}')
            FROM api_book
            WHERE search_vector LIKE '%{sanitized_query}%' OR search_vector % '{sanitized_query}'
            ORDER BY similarity(search_vector, '{sanitized_query}') DESC, search_vector;
            """

        with connection.cursor() as cursor:
            cursor.execute(query)
            ids = [row[0] for row in cursor.fetchall()]

        return self.get_queryset().filter(id__in=ids)


class Genre(models.Model):
    name = models.CharField(max_length=100)
    filter_name = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.filter_name:
            self.filter_name = generate_permalink(self.name)
        super().save(*args, **kwargs)


class Status(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Book(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField(max_length=10000)
    cover_image = models.ImageField(upload_to='covers/')
    genres = models.ManyToManyField(Genre)
    posted_by = models.ForeignKey(User, on_delete=models.CASCADE)
    author = models.CharField(max_length=200, default='unknown')
    date_created = models.DateField(auto_now_add=True)
    date_updated = models.DateField(null=True, blank=True, auto_now=True)
    permalink = models.CharField(max_length=255, unique=True, blank=True)
    status = models.ForeignKey(Status, on_delete=models.SET_NULL, null=True)
    search_vector = models.TextField(null=True, blank=True)
    objects = SearchManager()

        
    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.permalink:
            self.permalink = generate_permalink(self.title)
        super().save(*args, **kwargs)
        self.update_search_vector()

    def update_search_vector(self):
        normalized_title = normalize_text(self.title)
        normalized_description = normalize_text(self.description)
        normalized_author = normalize_text(self.author)
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE api_book SET search_vector = (%s || ' ' || %s || ' ' || %s) WHERE id = %s;
            """, [normalized_title, normalized_description, normalized_author, str(self.id)])


class Volume(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    book = models.ForeignKey(
        Book, related_name='volumes', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    date_created = models.DateField(auto_now_add=True)
    date_updated = models.DateField(null=True, blank=True, auto_now=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.date_updated = timezone.now()
        super().save(*args, **kwargs)
        self.book.date_updated = timezone.now()
        self.book.save()


class Chapter(DjangoCassandraModel):
    book_id = CassandraUUID(primary_key=True)
    number = Integer(primary_key=True, clustering_order="ASC")
    id = CassandraUUID(primary_key=True, default=uuid.uuid4)
    volume_id = CassandraUUID()
    name = Text()
    date_created = DateTime()
    date_updated = DateTime()
    content = Text()
    permalink = Text()

    class Meta:
        get_pk_field = 'id'

    def clean(self):
        volume = Volume.objects.get(id=self.volume_id)
        if volume.book.id != self.book_id:
            raise ValidationError(
                "The book of the chapter must match the book of the volume.")

    def save(self, *args, **kwargs):
        self.date_updated = timezone.now()
        if not self.date_created:
            self.date_created = timezone.now()
        if not self.permalink:
            self.permalink = generate_permalink(self.name)
        if not self.number:
            self.number = self.get_next_chapter_number()
        super().save(*args, **kwargs)
        Book.objects.filter(id=self.book_id).update(
            date_updated=timezone.now())

    def __str__(self):
        return self.name
    
    def get_next_chapter_number(self):
        last_chapter = Chapter.objects.filter(book_id=self.book_id).order_by('-number').first()
        return last_chapter.number + 1 if last_chapter else 1



User.add_to_class('is_banned', models.BooleanField(default=False))
