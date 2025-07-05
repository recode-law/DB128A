from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
import base64

from .models import Court, CourtType

User = get_user_model()


class CourtDatabaseTestCase(TestCase):
    def setUp(self):
        username = 'test'
        password = 'test'
        self.user = User.objects.create_user(username=username, password=password)
        group = Group.objects.get(name='Verifiziert')
        group.user_set.add(self.user)

        credentials = f'{username}:{password}'
        encoded_credentials = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
        self.auth_header = f'Basic {encoded_credentials}'


class CourtListTests(CourtDatabaseTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse('court-database-restapi-court')
        for i in range(100):
            Court.objects.create(
                name=f"Test Court {i}",
                type=CourtType.objects.first()
            )

    def test_unauthenticated(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.content.decode('utf-8'), "Unauthorized")

    def test_list_courts(self):
        response = self.client.get(self.url, HTTP_AUTHORIZATION=self.auth_header)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue('pagination' in data)
        self.assertTrue('courts' in data)
        self.assertTrue(len(data['courts']) == 10)
        self.assertContains(response, "Test Court 0")
        self.assertNotContains(response, "Test Court 10")
        self.assertEqual(data['pagination']['page_count'], 10)
        self.assertEqual(data['pagination']['next'], 2)
        self.assertFalse('previous' in data['pagination'])

    def test_list_court_custom_page(self):
        response = self.client.get(self.url, {'page': 3}, HTTP_AUTHORIZATION=self.auth_header)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertNotContains(response, "Test Court 19")
        self.assertContains(response, "Test Court 20")
        self.assertNotContains(response, "Test Court 30")
        self.assertEqual(data['pagination']['previous'], 2)
        self.assertEqual(data['pagination']['next'], 4)

    def test_list_court_custom_page_invalid(self):
        response = self.client.get(self.url, {'page': 1000}, HTTP_AUTHORIZATION=self.auth_header)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.content.decode('utf-8'), "The requested page is empty")

    def test_list_court_custom_page_wrong_type(self):
        response = self.client.get(self.url, {'page': 'invalid'}, HTTP_AUTHORIZATION=self.auth_header)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content.decode('utf-8'), "Invalid page or per_page parameter")

    def test_list_court_custom_per_page(self):
        response = self.client.get(self.url, {'per_page': 5}, HTTP_AUTHORIZATION=self.auth_header)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['courts']), 5)
        self.assertContains(response, "Test Court 0")
        self.assertNotContains(response, "Test Court 5")
        self.assertEqual(data['pagination']['page_count'], 20)

    def test_list_court_custom_per_page_wrong_type(self):
        response = self.client.get(self.url, {'per_page': 'invalid'}, HTTP_AUTHORIZATION=self.auth_header)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content.decode('utf-8'), "Invalid page or per_page parameter")
