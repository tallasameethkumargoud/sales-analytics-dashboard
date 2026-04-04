from django.db import models
from django.contrib.auth.models import User


class Dataset(models.Model):
    name        = models.CharField(max_length=200)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    file        = models.FileField(upload_to="datasets/", null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Customer(models.Model):
    name       = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Product(models.Model):
    name       = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Record(models.Model):
    dataset    = models.ForeignKey(Dataset,  on_delete=models.CASCADE)
    customer   = models.ForeignKey(Customer, on_delete=models.CASCADE, null=True, blank=True)
    product    = models.ForeignKey(Product,  on_delete=models.CASCADE, null=True, blank=True)
    amount     = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    # Keep old fields for backward compatibility during migration
    customer_name = models.CharField(max_length=200, blank=True, default="")
    product_name  = models.CharField(max_length=200, blank=True, default="")

    def __str__(self):
        return f"{self.customer} - {self.product} - ${self.amount}"