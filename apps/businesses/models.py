from django.db import models
from apps.core.models import TimeStampedModel

class Business(models.Model):
    name = models.CharField(max_length=150)

    def __str__(self):
        return self.name