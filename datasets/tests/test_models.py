import pytest
from django.test import TestCase
from django.contrib.auth.models import User
from datasets.models import (
    Customer, Product, Dataset,
    Record, UserProfile, RecommendationInteraction
)
from datasets.tests.factories import (
    UserFactory, CustomerFactory, ProductFactory,
    DatasetFactory, RecordFactory,
    AdminUserFactory, ViewerUserFactory
)


class CustomerModelTest(TestCase):
    def test_customer_creation(self):
        customer = CustomerFactory(name="John Doe")
        self.assertEqual(customer.name, "John Doe")
        self.assertIsNotNone(customer.created_at)

    def test_customer_str(self):
        customer = CustomerFactory(name="Jane Smith")
        self.assertEqual(str(customer), "Jane Smith")

    def test_customer_get_or_create(self):
        Customer.objects.create(name="Alice")
        customer, created = Customer.objects.get_or_create(name="Alice")
        self.assertFalse(created)


class ProductModelTest(TestCase):
    def test_product_creation(self):
        product = ProductFactory(name="Laptop")
        self.assertEqual(product.name, "Laptop")
        self.assertIsNotNone(product.created_at)

    def test_product_str(self):
        product = ProductFactory(name="Phone")
        self.assertEqual(str(product), "Phone")


class DatasetModelTest(TestCase):
    def test_dataset_creation(self):
        user    = UserFactory()
        dataset = DatasetFactory(name="sales.csv", uploaded_by=user)
        self.assertEqual(dataset.name, "sales.csv")
        self.assertEqual(dataset.uploaded_by, user)
        self.assertIsNotNone(dataset.uploaded_at)

    def test_dataset_str(self):
        dataset = DatasetFactory(name="test.csv")
        self.assertEqual(str(dataset), "test.csv")


class RecordModelTest(TestCase):
    def setUp(self):
        self.user     = UserFactory()
        self.dataset  = DatasetFactory(uploaded_by=self.user)
        self.customer = CustomerFactory(name="John")
        self.product  = ProductFactory(name="Laptop")

    def test_record_creation(self):
        record = Record.objects.create(
            dataset=self.dataset,
            customer=self.customer,
            product=self.product,
            customer_name="John",
            product_name="Laptop",
            amount=1200.00
        )
        self.assertEqual(record.amount, 1200.00)
        self.assertEqual(record.customer_name, "John")
        self.assertEqual(record.product_name, "Laptop")

    def test_record_str(self):
        record = RecordFactory(
            dataset=self.dataset,
            customer=self.customer,
            product=self.product,
            customer_name="John",
            product_name="Laptop",
            amount=999.0
        )
        self.assertIn("John", str(record))

    def test_record_amount_positive(self):
        record = RecordFactory(
            dataset=self.dataset,
            customer=self.customer,
            product=self.product,
            customer_name="John",
            product_name="Laptop",
            amount=500.00
        )
        self.assertGreater(record.amount, 0)


class UserProfileModelTest(TestCase):
    def test_default_role_is_analyst(self):
        user    = UserFactory()
        profile = UserProfile.objects.create(user=user)
        self.assertEqual(profile.role, 'analyst')

    def test_admin_role(self):
        user    = AdminUserFactory()
        profile = user.profile
        self.assertEqual(profile.role, 'admin')
        self.assertTrue(profile.is_admin)
        self.assertFalse(profile.is_viewer)

    def test_viewer_role(self):
        user    = ViewerUserFactory()
        profile = user.profile
        self.assertEqual(profile.role, 'viewer')
        self.assertTrue(profile.is_viewer)
        self.assertFalse(profile.is_admin)

    def test_profile_str(self):
        user    = UserFactory(username='testuser')
        profile = UserProfile.objects.create(user=user, role='analyst')
        self.assertIn('testuser', str(profile))
        self.assertIn('analyst', str(profile))


class RecommendationInteractionTest(TestCase):
    def test_interaction_creation(self):
        user    = UserFactory()
        product = ProductFactory()
        interaction = RecommendationInteraction.objects.create(
            user=user,
            product=product,
            action_type='increase_price',
            interaction='clicked',
            impact='high'
        )
        self.assertEqual(interaction.action_type, 'increase_price')
        self.assertEqual(interaction.interaction, 'clicked')
        self.assertEqual(interaction.impact, 'high')
