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
    

class RecommendationInteraction(models.Model):
    ACTION_TYPES = [
        ('clicked',   'Clicked'),
        ('applied',   'Applied'),
        ('dismissed', 'Dismissed'),
    ]
    user        = models.ForeignKey(User, on_delete=models.CASCADE)
    product     = models.ForeignKey(Product, on_delete=models.CASCADE)
    action_type = models.CharField(max_length=50)   # increase_price, promote, etc.
    interaction = models.CharField(max_length=20, choices=ACTION_TYPES, default='clicked')
    impact      = models.CharField(max_length=20)   # high, medium, low
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user} → {self.product} → {self.action_type} ({self.interaction})"
    
class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('admin',   'Admin'),
        ('analyst', 'Analyst'),
        ('viewer',  'Viewer'),
    ]
    user       = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role       = models.CharField(max_length=20, choices=ROLE_CHOICES, default='analyst')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} — {self.role}"

    @property
    def is_admin(self):
        return self.role == 'admin'

    @property
    def is_analyst(self):
        return self.role == 'analyst'

    @property
    def is_viewer(self):
        return self.role == 'viewer'