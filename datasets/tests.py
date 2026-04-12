from django.test import TestCase, Client
from django.contrib.auth.models import User
from datasets.models import Dataset, Record, Customer, Product


class AuthTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='TestPass@123'
        )

    def test_login_page_loads(self):
        response = self.client.get('/login/')
        self.assertEqual(response.status_code, 200)

    def test_signup_page_loads(self):
        response = self.client.get('/signup/')
        self.assertEqual(response.status_code, 200)

    def test_login_valid_user(self):
        response = self.client.post('/login/', {
            'username': 'testuser',
            'password': 'TestPass@123'
        })
        self.assertEqual(response.status_code, 302)

    def test_login_invalid_user(self):
        response = self.client.post('/login/', {
            'username': 'wrong',
            'password': 'wrong'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid')

    def test_signup_weak_password(self):
        response = self.client.post('/signup/', {
            'username': 'newuser',
            'password': 'weak'
        })
        self.assertEqual(response.status_code, 200)


class AnalyticsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='TestPass@123'
        )
        self.client.login(username='testuser', password='TestPass@123')
        dataset  = Dataset.objects.create(name='test.csv', uploaded_by=self.user)
        customer = Customer.objects.create(name='John Doe')
        product  = Product.objects.create(name='Laptop')
        Record.objects.create(
            dataset=dataset, customer=customer, product=product,
            customer_name='John Doe', product_name='Laptop', amount=1200.00
        )

    def test_analytics_page_loads(self):
        response = self.client.get('/analytics/')
        self.assertEqual(response.status_code, 200)

    def test_product_sales_api(self):
        response = self.client.get('/api/product-sales/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('products', data)
        self.assertIn('sales', data)

    def test_sales_trend_api(self):
        response = self.client.get('/api/sales-trend/')
        self.assertEqual(response.status_code, 200)

    def test_export_csv(self):
        response = self.client.get('/export/csv/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')

    def test_unauthenticated_redirect(self):
        self.client.logout()
        response = self.client.get('/analytics/')
        self.assertEqual(response.status_code, 302)


class APITests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='TestPass@123'
        )

    def test_api_requires_auth(self):
        response = self.client.get('/api/analytics/')
        self.assertEqual(response.status_code, 401)

    def test_api_chat_requires_post(self):
        self.client.login(username='testuser', password='TestPass@123')
        response = self.client.get('/api/ai-chat/')
        self.assertEqual(response.status_code, 405)
