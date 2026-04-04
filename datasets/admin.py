from django.contrib import admin
from .models import Dataset, Record, Customer, Product

admin.site.register(Dataset)
admin.site.register(Record)
admin.site.register(Customer)
admin.site.register(Product)