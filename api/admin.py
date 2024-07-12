from django.contrib import admin
from .models import Book, Volume, Chapter, Genre, Status, Comment, Reply
from .models import Report
from .forms import ChapterAdminForm
from django.urls import path
from django.http import JsonResponse, HttpResponseRedirect
from django import forms
from django.conf import settings
import os
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.template.response import TemplateResponse

class VolumeInline(admin.TabularInline):
    model = Volume
    extra = 1


class BookAdmin(admin.ModelAdmin):
    inlines = [VolumeInline]
    list_display = ('title', 'posted_by', 'date_created', 'date_updated', 'id')
    search_fields = ['title']
    list_filter = ['status']


class ChapterAdmin(admin.ModelAdmin):
    form = ChapterAdminForm
    list_display = ('name', 'book_id', 'volume_id', 'date_created', 'date_updated')
    list_filter = ('book_id', 'volume_id')
    search_fields = ('name', 'content')

    actions = ['delete_selected']

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('', self.admin_site.admin_view(self.chapter_list_view), name='chapter_list'),
            path('add/', self.admin_site.admin_view(self.chapter_add_view), name='chapter_add'),
            path('change/<uuid:chapter_id>/', self.admin_site.admin_view(self.chapter_change_view), name='chapter_change'),
            path('delete/', self.admin_site.admin_view(self.chapter_delete_selected), name='chapter_delete_selected'),
            path('ajax/load-volumes/', self.admin_site.admin_view(self.load_volumes), name='ajax_load_volumes'),
        ]
        return custom_urls + urls

    def chapter_list_view(self, request):
        search_query = request.GET.get('q', '')
        chapters = Chapter.objects.all()
        if search_query:
            chapters = chapters.filter(name__icontains=search_query)
        context = {
            'chapters': chapters,
            'opts': self.model._meta,
            'app_label': self.model._meta.app_label,
            'search_query': search_query,
        }
        return render(request, 'admin/chapter_list.html', context)

    def chapter_add_view(self, request):
        if request.method == 'POST':
            form = ChapterAdminForm(request.POST)
            if form.is_valid():
                form.save()
                return redirect('admin:chapter_list')
        else:
            form = ChapterAdminForm()

        context = {
            'form': form,
            'opts': self.model._meta,
            'app_label': self.model._meta.app_label,
        }
        return render(request, 'admin/chapter_add.html', context)

    def chapter_change_view(self, request, chapter_id):
        chapter = get_object_or_404(Chapter, id=chapter_id)
        if request.method == 'POST':
            form = ChapterAdminForm(request.POST, instance=chapter)
            if form.is_valid():
                form.save()
                return redirect('admin:chapter_list')
        else:
            form = ChapterAdminForm(instance=chapter)

        context = {
            'form': form,
            'chapter': chapter,
            'opts': self.model._meta,
            'app_label': self.model._meta.app_label,
        }
        return render(request, 'admin/chapter_change.html', context)

    def chapter_delete_selected(self, request):
        if request.method == 'POST':
            selected_ids = request.POST.getlist('_selected_action')
            for chapter_id in selected_ids:
                chapter = get_object_or_404(Chapter, id=chapter_id)
                chapter.delete()
            messages.success(request, "Successfully deleted selected chapters.")
            return redirect('admin:chapter_list')
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    def load_volumes(self, request):
        book_id = request.GET.get('book_id')
        volumes = Volume.objects.filter(book_id=book_id).all()
        return JsonResponse(list(volumes.values('id', 'name')), safe=False)



class VolumeAdmin(admin.ModelAdmin):
    list_display = ('name', 'book', 'date_created', 'id')
    list_filter = ('book',)
    search_fields = ('title', 'description', 'author')


class GenreAdmin(admin.ModelAdmin):
    list_display = ('name', 'id')
    list_filter = ('name',)
    search_fields = ('name',)


class StatusAdmin(admin.ModelAdmin):
    list_display = ('name', 'id')
    list_filter = ('name',)
    search_fields = ('name',)


admin.site.register(Book, BookAdmin)
admin.site.register(Volume, VolumeAdmin)
admin.site.register(Chapter, ChapterAdmin)
admin.site.register(Genre, GenreAdmin)
admin.site.register(Status, StatusAdmin)
admin.site.register(Comment)
admin.site.register(Reply)
admin.site.register(Report)
