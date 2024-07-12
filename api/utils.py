import unicodedata
import re
import random
import string
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from datetime import datetime


def normalize_text(text):
    # Normalize to NFKD and remove diacritics
    text = unicodedata.normalize('NFKD', text)
    text = ''.join(c for c in text if not unicodedata.combining(c))
    text = text.lower()
    return text


time = datetime.fromtimestamp(datetime.timestamp(
    datetime.now())).strftime("(%B %d, %Y, %H:%M:%S UTC)")


def generate_permalink(s):
    normalized_str = unicodedata.normalize('NFD', s)
    without_accents = ''.join(
        c for c in normalized_str if unicodedata.category(c) != 'Mn')
    cleaned_str = re.sub(r'[^\w\s-]', ' ', without_accents)
    single_spaced_str = re.sub(r'\s+', ' ', cleaned_str)
    hyphenated_str = single_spaced_str.replace(' ', '-')
    url_friendly_str = hyphenated_str.lower()
    url_friendly_str = url_friendly_str.strip('-')
    random_string = ''.join(random.choices(
        string.ascii_lowercase + string.digits, k=12))
    return f'{url_friendly_str}-{random_string}'