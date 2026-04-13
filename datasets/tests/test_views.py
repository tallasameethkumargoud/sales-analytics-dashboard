import pytest
from django.test import TestCase, Client
from datasets.models import Record, UserProfile
from datasets.tests.factories import (
    UserFactory, DatasetFactory, CustomerFactory,
    ProductFactory, RecordFactory,
    AdminUserFactory, ViewerUserFactory
)


class UploadViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user   = UserFactory()
        self.client.login(username=self.user.username, password='TestPass@123')

    def test_upload_page_loads(self):
        response = self.client.get('/upload/')
        self.assertEqual(response.status_code, 200)

    def test_upload_redirects_if_has_data(self):
        dataset  = DatasetFactory(uploaded_by=self.user)
        customer = CustomerFactory()
        product  = ProductFactory()
        RecordFactory(
            dataset=dataset,
            customer=customer,
            product=product,
            customer_name=customer.name,
            product_name=product.name,
            amount=100.00
        )
        response = self.client.get('/upload/')
        self.assertRedirects(response, '/analytics/')

    def test_upload_requires_auth(self):
        self.client.logout()
        response = self.client.get('/upload/')
        self.assertRedirects(response, '/login/')


class AnalyticsViewTest(TestCase):
    def setUp(self):
        self.client  = Client()
        self.user    = UserFactory()
        self.client.login(username=self.user.username, password='TestPass@123')
        dataset  = DatasetFactory(uploaded_by=self.user)
        customer = CustomerFactory()
        product  = ProductFactory()
        RecordFactory(
            dataset=dataset,
            customer=customer,
            product=product,
            customer_name=customer.name,
            product_name=product.name,
            amount=1200.00
        )

    def test_analytics_loads(self):
        response = self.client.get('/analytics/')
        self.assertEqual(response.status_code, 200)

    def test_analytics_has_kpis(self):
        response = self.client.get('/analytics/')
        self.assertContains(response, 'Total Revenue')
        self.assertContains(response, 'Top Product')

    def test_analytics_redirects_if_no_data(self):
        new_user = UserFactory()
        self.client.login(username=new_user.username, password='TestPass@123')
        response = self.client.get('/analytics/')
        self.assertRedirects(response, '/upload/')

    def test_analytics_requires_auth(self):
        self.client.logout()
        response = self.client.get('/analytics/')
        self.assertRedirects(response, '/login/')


class DatasetHistoryViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user   = UserFactory()
        self.client.login(username=self.user.username, password='TestPass@123')

    def test_history_page_loads(self):
        response = self.client.get('/datasets/')
        self.assertEqual(response.status_code, 200)

    def test_history_requires_auth(self):
        self.client.logout()
        response = self.client.get('/datasets/')
        self.assertRedirects(response, '/login/')


class RoleBasedAccessTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_admin_can_access_admin_panel(self):
        admin = AdminUserFactory()
        self.client.login(username=admin.username, password='TestPass@123')
        response = self.client.get('/admin-panel/')
        self.assertEqual(response.status_code, 200)

    def test_analyst_cannot_access_admin_panel(self):
        analyst = UserFactory()
        UserProfile.objects.create(user=analyst, role='analyst')
        self.client.login(username=analyst.username, password='TestPass@123')
        response = self.client.get('/admin-panel/')
        self.assertEqual(response.status_code, 302)

    def test_viewer_cannot_access_admin_panel(self):
        viewer = ViewerUserFactory()
        self.client.login(username=viewer.username, password='TestPass@123')
        response = self.client.get('/admin-panel/')
        self.assertEqual(response.status_code, 302)
