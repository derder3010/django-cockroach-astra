# forms.py
from django import forms
from .models import Chapter, Book, Volume
import uuid


class ChapterAdminForm(forms.ModelForm):
    class Meta:
        model = Chapter
        fields = '__all__'

    content = forms.CharField(widget=forms.Textarea, required=False)
    book_id = forms.ModelChoiceField(queryset=Book.objects.all(), label='Book')
    volume_id = forms.ModelChoiceField(
        queryset=Volume.objects.none(), label='Volume')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'book_id' in self.data:
            try:
                book_id = uuid.UUID(self.data.get('book_id'))
                self.fields['volume_id'].queryset = Volume.objects.filter(
                    book_id=book_id).order_by('name')
            except (ValueError, TypeError):
                pass  # invalid input from the client; ignore and fallback to empty Volume queryset
        elif self.instance.pk:
            self.fields['volume_id'].queryset = Volume.objects.filter(
                book_id=self.instance.book_id).order_by('name')

        # Set read-only fields
        self.fields['date_created'].widget.attrs['readonly'] = True
        self.fields['date_updated'].widget.attrs['readonly'] = True
        self.fields['number'].widget.attrs['readonly'] = True
        
    def clean_book_id(self):
        book_id = uuid.UUID(self.data.get('book_id'))
        return book_id

    def clean_volume_id(self):
        volume_id = uuid.UUID(self.data.get('volume_id'))
        return volume_id

    def clean_date_created(self):
        return self.instance.date_created

    def clean_date_updated(self):
        return self.instance.date_updated
    
    def clean_number(self):
        return self.instance.number