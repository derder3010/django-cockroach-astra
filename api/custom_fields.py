from rest_framework import serializers
import uuid
from datetime import datetime


class UUIDField(serializers.Field):
    def to_internal_value(self, data):
        try:
            return uuid.UUID(data)
        except ValueError:
            raise serializers.ValidationError('Invalid UUID format.')

    def to_representation(self, value):
        return str(value)


class TextField(serializers.Field):
    def to_internal_value(self, data):
        if not isinstance(data, str):
            raise serializers.ValidationError('Invalid text format.')
        return data

    def to_representation(self, value):
        return str(value)


class DateTimeField(serializers.Field):
    def to_internal_value(self, data):
        try:
            return datetime.fromisoformat(data)
        except ValueError:
            raise serializers.ValidationError('Invalid datetime format.')

    def to_representation(self, value):
        return value.isoformat()


class IntegerField(serializers.Field):
    def to_internal_value(self, data):
        try:
            return int(data)
        except (ValueError, TypeError):
            raise serializers.ValidationError('Invalid integer format.')

    def to_representation(self, value):
        return int(value)


class BooleanField(serializers.Field):
    def to_internal_value(self, data):
        try:
            return bool(data)
        except (ValueError, TypeError):
            raise serializers.ValidationError('Invalid integer format.')

    def to_representation(self, value):
        return bool(value)
