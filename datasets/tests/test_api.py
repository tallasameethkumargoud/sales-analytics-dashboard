import json
import pytest
from django.test import TestCase, Client
from django.contrib.auth.models import User
from datasets.models import Record
from datasets.tests.factories import (
    UserFactory, DatasetFactory, CustomerFactory,
    ProductFactory, RecordFactory
)


class ProductSalesAPITest(TestCase):
    def setUp(self):
        self.client  = Client()
        self.user    = UserFactory()
        self.client.login(username=self.user.username, password='TestPass@123')
        self.dataset  = DatasetFactory(uploaded_by=self.user)
        self.customer = CustomerFactory()
        self.product  = ProductFactory(name='Laptop')
        RecordFactory(
            dataset=self.dataset,
            customer=self.customer,
            product=self.product,
            customer_name=self.customer.name,
            product_name='Laptop',
            amount=1200.00
        )

    def test_returns_200(self):
        response = self.client.get('/api/product-sales/')
        self.assertEqual(response.status_code, 200)

    def test_returns_json(self):
        response = self.client.get('/api/product-sales/')
        data = response.json()
        self.assertIn('products', data)
        self.assertIn('sales', data)

    def test_products_list_not_empty(self):
        response = self.client.get('/api/product-sales/')
        data = response.json()
        self.assertGreater(len(data['products']), 0)

    def test_sales_match_products(self):
        response = self.client.get('/api/product-sales/')
        data = response.json()
        self.assertEqual(len(data['products']), len(data['sales']))

    def test_min_filter(self):
        response = self.client.get('/api/product-sales/?min=500')
        self.assertEqual(response.status_code, 200)

    def test_max_filter(self):
        response = self.client.get('/api/product-sales/?max=2000')
        self.assertEqual(response.status_code, 200)

    def test_requires_auth(self):
        self.client.logout()
        response = self.client.get('/api/product-sales/')
        self.assertEqual(response.status_code, 401)

    def test_user_isolation(self):
        other_user    = UserFactory()
        other_dataset = DatasetFactory(uploaded_by=other_user)
        other_product = ProductFactory(name='Other Product')
        RecordFactory(
            dataset=other_dataset,
            customer=CustomerFactory(),
            product=other_product,
            customer_name='Other',
            product_name='Other Product',
            amount=9999.00
        )
        response = self.client.get('/api/product-sales/')
        data     = response.json()
        self.assertNotIn('Other Product', data['products'])


class SalesTrendAPITest(TestCase):
    def setUp(self):
        self.client  = Client()
        self.user    = UserFactory()
        self.client.login(username=self.user.username, password='TestPass@123')
        self.dataset  = DatasetFactory(uploaded_by=self.user)
        self.customer = CustomerFactory()
        self.product  = ProductFactory()
        RecordFactory(
            dataset=self.dataset,
            customer=self.customer,
            product=self.product,
            customer_name=self.customer.name,
            product_name=self.product.name,
            amount=1000.00
        )

    def test_returns_200(self):
        response = self.client.get('/api/sales-trend/')
        self.assertEqual(response.status_code, 200)

    def test_returns_dates_and_sales(self):
        response = self.client.get('/api/sales-trend/')
        data     = response.json()
        self.assertIn('dates', data)
        self.assertIn('sales', data)

    def test_dates_match_sales(self):
        response = self.client.get('/api/sales-trend/')
        data     = response.json()
        self.assertEqual(len(data['dates']), len(data['sales']))

    def test_requires_auth(self):
        self.client.logout()
        response = self.client.get('/api/sales-trend/')
        self.assertEqual(response.status_code, 401)


class SalesForecastAPITest(TestCase):
    def setUp(self):
        self.client  = Client()
        self.user    = UserFactory()
        self.client.login(username=self.user.username, password='TestPass@123')

    def test_returns_200(self):
        response = self.client.get('/api/sales-forecast/')
        self.assertEqual(response.status_code, 200)

    def test_not_enough_data_message(self):
        response = self.client.get('/api/sales-forecast/')
        data     = response.json()
        self.assertIn('explanation', data)

    def test_requires_auth(self):
        self.client.logout()
        response = self.client.get('/api/sales-forecast/')
        self.assertEqual(response.status_code, 401)


class AIChatAPITest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user   = UserFactory()
        self.client.login(username=self.user.username, password='TestPass@123')

    def test_requires_post(self):
        response = self.client.get('/api/ai-chat/')
        self.assertEqual(response.status_code, 405)

    def test_requires_auth(self):
        self.client.logout()
        response = self.client.post('/api/ai-chat/',
            data=json.dumps({'question': 'test'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 401)

    def test_empty_question_returns_400(self):
        response = self.client.post('/api/ai-chat/',
            data=json.dumps({'question': ''}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)

    def test_returns_json(self):
        response = self.client.post('/api/ai-chat/',
            data=json.dumps({'question': 'test question'}),
            content_type='application/json'
        )
        self.assertIn(response.status_code, [200, 500])
        data = response.json()
        self.assertTrue('answer' in data or 'error' in data)


class ExportCSVTest(TestCase):
    def setUp(self):
        self.client  = Client()
        self.user    = UserFactory()
        self.client.login(username=self.user.username, password='TestPass@123')
        dataset  = DatasetFactory(uploaded_by=self.user)
        customer = CustomerFactory(name='John')
        product  = ProductFactory(name='Laptop')
        RecordFactory(
            dataset=dataset,
            customer=customer,
            product=product,
            customer_name='John',
            product_name='Laptop',
            amount=1200.00
        )

    def test_returns_csv(self):
        response = self.client.get('/export/csv/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')

    def test_csv_has_headers(self):
        response = self.client.get('/export/csv/')
        content  = response.content.decode('utf-8')
        self.assertIn('Customer Name', content)
        self.assertIn('Product', content)
        self.assertIn('Amount', content)

    def test_csv_has_data(self):
        response = self.client.get('/export/csv/')
        content  = response.content.decode('utf-8')
        self.assertIn('John', content)
        self.assertIn('1,200', content)  # check amount instead

    def test_requires_auth(self):
        self.client.logout()
        response = self.client.get('/export/csv/')
        self.assertEqual(response.status_code, 302)
