from django.db import models

class Article(models.Model):
    title = models.CharField(max_length=512)
    url = models.URLField(blank=True)
    summary = models.TextField(blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title[:80]
