from django.db import models


class Comment(models.Model):
    author = models.CharField(max_length=80, default='Аноним')
    text = models.TextField(max_length=500)
    currency = models.CharField(max_length=10, blank=True)
    rating = models.PositiveSmallIntegerField(default=5)
    pinned = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.author}: {self.text[:40]}'