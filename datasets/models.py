from django.db import models
from django.contrib.auth.models import User

class Dataset(models.Model):
    name        = models.CharField(max_length=200)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    file        = models.FileField(upload_to="datasets/", null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Record(models.Model):
    dataset       = models.ForeignKey(Dataset, on_delete=models.CASCADE)
    customer_name = models.CharField(max_length=200)
    product       = models.CharField(max_length=200)
    amount        = models.FloatField()
    created_at    = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.customer_name