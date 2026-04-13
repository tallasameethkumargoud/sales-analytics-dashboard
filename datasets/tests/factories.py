import factory
from django.contrib.auth.models import User
from datasets.models import Dataset, Customer, Product, Record, UserProfile


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username  = factory.Sequence(lambda n: f'user{n}')
    email     = factory.LazyAttribute(lambda o: f'{o.username}@test.com')
    password  = factory.PostGenerationMethodCall('set_password', 'TestPass@123')
    is_active = True


class AdminUserFactory(UserFactory):
    username = factory.Sequence(lambda n: f'admin{n}')

    @factory.post_generation
    def make_admin(self, create, extracted, **kwargs):
        if create:
            UserProfile.objects.create(user=self, role='admin')


class AnalystUserFactory(UserFactory):
    username = factory.Sequence(lambda n: f'analyst{n}')

    @factory.post_generation
    def make_analyst(self, create, extracted, **kwargs):
        if create:
            UserProfile.objects.create(user=self, role='analyst')


class ViewerUserFactory(UserFactory):
    username = factory.Sequence(lambda n: f'viewer{n}')

    @factory.post_generation
    def make_viewer(self, create, extracted, **kwargs):
        if create:
            UserProfile.objects.create(user=self, role='viewer')


class CustomerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Customer
    name = factory.Sequence(lambda n: f'Customer {n}')


class ProductFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Product
    name = factory.Sequence(lambda n: f'Product {n}')


class DatasetFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Dataset
    name        = factory.Sequence(lambda n: f'dataset_{n}.csv')
    uploaded_by = factory.SubFactory(UserFactory)


class RecordFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Record
    dataset       = factory.SubFactory(DatasetFactory)
    customer      = factory.SubFactory(CustomerFactory)
    product       = factory.SubFactory(ProductFactory)
    customer_name = factory.LazyAttribute(lambda o: o.customer.name)
    product_name  = factory.LazyAttribute(lambda o: o.product.name)
    amount        = factory.Sequence(lambda n: float(100 * (n + 1)))
