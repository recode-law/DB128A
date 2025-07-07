from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
import base64

from .models import Court, CourtType, Feedback, RejectionReason, DetailedFeedback, CameraPerspective, \
    ConferencingSoftware

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

    def test_list_courts_unauthenticated(self):
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


class CourtDetailsTests(CourtDatabaseTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse('court-database-restapi-court-detail')
        for i in range(100):
            Court.objects.create(
                name=f"Test Court {i}",
                type=CourtType.objects.first()
            )
        court = Court.objects.first()
        rejection_reason = RejectionReason.objects.create(name="Test Rejection Reason")
        Feedback.objects.create(
            court=court,
            provides_online_service=False,
            rejection_reason=rejection_reason
        )
        Feedback.objects.create(
            court=court,
            provides_online_service=True,
            online_service_quality=3
        )
        detailed_feedback = DetailedFeedback.objects.create(
            court=court,
            user=self.user,
            online_service_possible=True,
            feedback="This is a test feedback."
        )
        camera_perspective = CameraPerspective.objects.create(name="Test Camera Perspective")
        conferencing_software = ConferencingSoftware.objects.create(name="Test Conferencing Software")
        detailed_feedback.camera_perspectives.set([camera_perspective])
        detailed_feedback.conferencing_software.set([conferencing_software])

    def test_court_details_unauthenticated(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.content.decode('utf-8'), "Unauthorized")

    def test_court_details(self):
        response = self.client.get(self.url, {'ids': '1'}, HTTP_AUTHORIZATION=self.auth_header)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue('courts' in data)
        self.assertEqual(len(data['courts']), 1)
        court = data['courts'][0]
        self.assertEqual(court['id'], 1)
        self.assertEqual(court['name'], "Test Court 0")
        self.assertEqual(court['type'], CourtType.objects.first().name)
        self.assertEqual(court['parent'], None)
        self.assertEqual(court['parent'], None)
        feedbacks = court['feedbacks']
        self.assertEqual(len(feedbacks), 2)
        self.assertFalse(feedbacks[0]['provides_online_service'])
        self.assertEqual(feedbacks[0]['rejection_reason'], RejectionReason.objects.first().id)
        self.assertTrue(feedbacks[1]['provides_online_service'])
        self.assertEqual(feedbacks[1]['online_service_quality'], 3)
        detailed_feedbacks = court['detailed_feedbacks']
        self.assertEqual(len(detailed_feedbacks), 1)
        self.assertTrue(detailed_feedbacks[0]['online_service_possible'])
        self.assertEqual(detailed_feedbacks[0]['camera_perspectives'][0], CameraPerspective.objects.first().id)
        self.assertEqual(detailed_feedbacks[0]['conferencing_software'][0], ConferencingSoftware.objects.first().id)

    def test_court_details_multiple_ids(self):
        response = self.client.get(self.url, {'ids': '1,2,3'}, HTTP_AUTHORIZATION=self.auth_header)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue('courts' in data)
        self.assertEqual(len(data['courts']), 3)
        court_ids = [court['id'] for court in data['courts']]
        self.assertIn(1, court_ids)
        self.assertIn(2, court_ids)
        self.assertIn(3, court_ids)

    def test_court_details_unused_id(self):
        response = self.client.get(self.url, {'ids': '999'}, HTTP_AUTHORIZATION=self.auth_header)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['courts']), 0)

    def test_court_details_invalid_id(self):
        response = self.client.get(self.url, {'ids': 'invalid'}, HTTP_AUTHORIZATION=self.auth_header)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content.decode('utf-8'), "IDs must be integers")

    def test_court_details_empty_ids(self):
        response = self.client.get(self.url, HTTP_AUTHORIZATION=self.auth_header)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content.decode('utf-8'), "Missing parameter: 'ids'")

    def test_court_details_to_many_ids(self):
        response = self.client.get(self.url, {'ids': ','.join([str(i) for i in range(30)])}, HTTP_AUTHORIZATION=self.auth_header)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content.decode('utf-8'), "Too many court IDs provided. Maximum is 20.")
