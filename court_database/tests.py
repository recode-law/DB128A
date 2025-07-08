from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
import base64

from .models import Court, CourtType, Feedback, RejectionReason, DetailedFeedback, CameraPerspective, \
    ConferencingSoftware, States

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

    def get_auth(self, path, data=None):
        return self.client.get(path, data, HTTP_AUTHORIZATION=self.auth_header)

    def post_auth(self, path, data=None):
        return self.client.post(path, data, content_type="application/json", HTTP_AUTHORIZATION=self.auth_header)


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
        response = self.get_auth(self.url)
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
        response = self.get_auth(self.url, {'page': 3})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertNotContains(response, "Test Court 19")
        self.assertContains(response, "Test Court 20")
        self.assertNotContains(response, "Test Court 30")
        self.assertEqual(data['pagination']['previous'], 2)
        self.assertEqual(data['pagination']['next'], 4)

    def test_list_court_custom_page_invalid(self):
        response = self.get_auth(self.url, {'page': 1000})
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.content.decode('utf-8'), "The requested page is empty")

    def test_list_court_custom_page_wrong_type(self):
        response = self.get_auth(self.url, {'page': 'invalid'})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content.decode('utf-8'), "Invalid page or per_page parameter")

    def test_list_court_custom_per_page(self):
        response = self.get_auth(self.url, {'per_page': 5})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['courts']), 5)
        self.assertContains(response, "Test Court 0")
        self.assertNotContains(response, "Test Court 5")
        self.assertEqual(data['pagination']['page_count'], 20)

    def test_list_court_custom_per_page_wrong_type(self):
        response = self.get_auth(self.url, {'per_page': 'invalid'})
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
        response = self.get_auth(self.url, {'ids': '1'})
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
        response = self.get_auth(self.url, {'ids': '1,2,3'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue('courts' in data)
        self.assertEqual(len(data['courts']), 3)
        court_ids = [court['id'] for court in data['courts']]
        self.assertIn(1, court_ids)
        self.assertIn(2, court_ids)
        self.assertIn(3, court_ids)

    def test_court_details_unused_id(self):
        response = self.get_auth(self.url, {'ids': '999'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['courts']), 0)

    def test_court_details_invalid_id(self):
        response = self.get_auth(self.url, {'ids': 'invalid'})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content.decode('utf-8'), "IDs must be integers")

    def test_court_details_empty_ids(self):
        response = self.get_auth(self.url)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content.decode('utf-8'), "Missing parameter: 'ids'")

    def test_court_details_to_many_ids(self):
        response = self.get_auth(self.url, {'ids': ','.join([str(i) for i in range(30)])})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content.decode('utf-8'), "Too many court IDs provided. Maximum is 20.")


class CourtCreateTests(CourtDatabaseTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse('court-database-restapi-court')

    def test_create_court_unauthenticated(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.content.decode('utf-8'), "Unauthorized")

    def test_create_court(self):
        parent = Court.objects.create(name="Parent Court", type=CourtType.objects.first())
        request_data = {
            'name': 'New Test Court',
            'type': CourtType.objects.first().id,
            'parent': parent.id
        }
        response = self.post_auth(self.url, request_data)
        self.assertEqual(response.status_code, 201)
        data = response.json()
        court = Court.objects.get(id=data['id'])
        self.assertEqual(court.name, 'New Test Court')
        self.assertEqual(court.type, CourtType.objects.first())
        self.assertEqual(court.parent, parent)

    def test_create_court_missing_name(self):
        request_data = {
            'type': CourtType.objects.first().id
        }
        response = self.post_auth(self.url, request_data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content.decode('utf-8'), "Missing required field: 'name'")

    def test_create_court_missing_type(self):
        request_data = {
            'name': 'New Test Court'
        }
        response = self.post_auth(self.url, request_data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content.decode('utf-8'), "Missing required field: 'type'")

    def test_create_court_existing_name(self):
        Court.objects.create(name="Existing Court", type=CourtType.objects.first())
        request_data = {
            'name': 'Existing Court',
            'type': CourtType.objects.first().id
        }
        response = self.post_auth(self.url, request_data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content.decode('utf-8'), "Error creating court: UNIQUE constraint failed: court_database_court.name")

    def test_create_court_invalid_parent(self):
        request_data = {
            'name': 'New Test Court',
            'type': CourtType.objects.first().id,
            'parent': -1
        }
        response = self.post_auth(self.url, request_data)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.content.decode('utf-8'), "Parent court does not exist")

    def test_create_court_invalid_type(self):
        request_data = {
            'name': 'Existing Court',
            'type': -1
        }
        response = self.post_auth(self.url, request_data)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.content.decode('utf-8'), "Selected court type does not exist")

    def test_create_court_with_address(self):
        request_data = {
            'name': 'New Test Court',
            'type': CourtType.objects.first().id,
            'address': {
                'state': 'BY',
                'city': 'City',
                'postal_code': '12345',
                'street': 'Street'
            }
        }
        response = self.post_auth(self.url, request_data)
        self.assertEqual(response.status_code, 201)
        data = response.json()
        address = Court.objects.get(id=data['id']).address
        self.assertEqual(address.state, 'BY')
        self.assertEqual(address.city, 'City')
        self.assertEqual(address.postal_code, '12345')
        self.assertEqual(address.street, 'Street')

    def test_create_court_incomplete_address(self):
        request_data = {
            'name': 'New Test Court',
            'type': CourtType.objects.first().id,
            'address': {
                'state': 'BY',
                'city': 'City',
                'postal_code': '12345',
            }
        }
        response = self.post_auth(self.url, request_data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content.decode('utf-8'), "Missing required field: 'street'")

    def test_create_court_invalid_state(self):
        request_data = {
            'name': 'New Test Court',
            'type': CourtType.objects.first().id,
            'address': {
                'state': 'Bavaria',
                'city': 'City',
                'postal_code': '12345',
                'street': 'Street'
            }
        }
        response = self.post_auth(self.url, request_data)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.content.decode('utf-8'), "Invalid state provided: Bavaria")

class CourtTypeGetTests(CourtDatabaseTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse('court-database-restapi-court-type')

    def test_get_court_type_unauthenticated(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.content.decode('utf-8'), "Unauthorized")

    def test_get_court_type(self):
        CourtType.objects.create(name='New Test Court Type')
        response = self.get_auth(self.url)
        self.assertEqual(response.status_code, 200)
        court_types = response.json()
        # Four Court Types are created by default and should always be there
        self.assertEqual(len(court_types), 5)
        self.assertEqual(court_types[0]['name'], 'Bundesgericht')
        self.assertEqual(court_types[1]['name'], 'Oberlandesgericht')
        self.assertEqual(court_types[2]['name'], 'Landgericht')
        self.assertEqual(court_types[3]['name'], 'Amtsgericht')
        self.assertEqual(court_types[4]['name'], 'New Test Court Type')


class CourtTypeCreateTests(CourtDatabaseTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse('court-database-restapi-court-type')

    def test_create_court_type_unauthenticated(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.content.decode('utf-8'), "Unauthorized")

    def test_create_court_type(self):
        request_data = {
            'name': 'New Court Type'
        }
        response = self.post_auth(self.url, request_data)
        self.assertEqual(response.status_code, 201)
        data = response.json()
        court_type = CourtType.objects.get(id=data['id'])
        self.assertEqual(court_type.name, 'New Court Type')

    def test_create_court_type_missing_name(self):
        request_data = {}
        response = self.post_auth(self.url, request_data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content.decode('utf-8'), "Missing required field: 'name'")

    def test_create_court_type_existing_name(self):
        CourtType.objects.create(name='Existing Court Type')
        request_data = {
            'name': 'Existing Court Type'
        }
        response = self.post_auth(self.url, request_data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content.decode('utf-8'), "Error creating court type: UNIQUE constraint failed: court_database_courttype.name")


class StateGetTests(CourtDatabaseTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse('court-database-restapi-state')

    def test_get_state_unauthenticated(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.content.decode('utf-8'), "Unauthorized")

    def test_get_state(self):
        response = self.get_auth(self.url)
        self.assertEqual(response.status_code, 200)
        states = response.json()
        self.assertEqual(len(states), len(States))
        for state_id, state_name in States.choices:
            found = False
            for response_state in states:
                if response_state['id'] == state_id:
                    found = True
                    self.assertEqual(response_state['name'], state_name)
                    break
            if not found:
                self.fail(f"State with ID {state_id} not found in response")
