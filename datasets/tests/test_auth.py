import pytest
from django.test import TestCase, Client
from django.contrib.auth.models import User
from datasets.tests.factories import UserFactory


class SignupViewTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_signup_page_loads(self):
        response = self.client.get('/signup/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Create Account')

    def test_signup_valid_user(self):
        response = self.client.post('/signup/', {
            'username': 'newuser',
            'password': 'StrongPass@123'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_signup_redirects_to_login(self):
        response = self.client.post('/signup/', {
            'username': 'newuser2',
            'password': 'StrongPass@123'
        })
        self.assertRedirects(response, '/login/?registered=1')

    def test_signup_duplicate_username(self):
        UserFactory(username='existing')
        response = self.client.post('/signup/', {
            'username': 'existing',
            'password': 'StrongPass@123'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'already taken')

    def test_signup_password_too_short(self):
        response = self.client.post('/signup/', {
            'username': 'newuser',
            'password': 'short'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'at least 8')

    def test_signup_password_no_uppercase(self):
        response = self.client.post('/signup/', {
            'username': 'newuser',
            'password': 'nouppercase@123'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'uppercase')

    def test_signup_password_no_number(self):
        response = self.client.post('/signup/', {
            'username': 'newuser',
            'password': 'NoNumber@!'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'number')

    def test_signup_password_no_special(self):
        response = self.client.post('/signup/', {
            'username': 'newuser',
            'password': 'NoSpecial123'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'special')


class LoginViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user   = UserFactory(username='testuser')

    def test_login_page_loads(self):
        response = self.client.get('/login/')
        self.assertEqual(response.status_code, 200)

    def test_login_valid_credentials(self):
        response = self.client.post('/login/', {
            'username': 'testuser',
            'password': 'TestPass@123'
        })
        self.assertEqual(response.status_code, 302)

    def test_login_invalid_password(self):
        response = self.client.post('/login/', {
            'username': 'testuser',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid')

    def test_login_invalid_username(self):
        response = self.client.post('/login/', {
            'username': 'nonexistent',
            'password': 'TestPass@123'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid')

    def test_logout(self):
        self.client.login(username='testuser', password='TestPass@123')
        response = self.client.get('/logout/')
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/login/')


class AuthRedirectTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_upload_requires_login(self):
        response = self.client.get('/upload/')
        self.assertRedirects(response, '/login/')

    def test_analytics_requires_login(self):
        response = self.client.get('/analytics/')
        self.assertRedirects(response, '/login/')

    def test_datasets_requires_login(self):
        response = self.client.get('/datasets/')
        self.assertRedirects(response, '/login/')
