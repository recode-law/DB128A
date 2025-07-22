from random import randint
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
import base64

from court_database.models import Court, CourtType, States
from video_conference.models import Feedback, RejectionReason, DetailedFeedback, CameraPerspective, ConferencingSoftware

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
        self.url = reverse('video-conference-restapi-court')
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
        self.url = reverse('video-conference-restapi-court-detail')
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


class CourtSearchGetTests(CourtDatabaseTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse('video-conference-restapi-court-search')
        for i in range(20):
            Court.objects.create(name=f'Test Court A {i}', type=CourtType.objects.first())
            Court.objects.create(name=f'Test Court B {i+20}', type=CourtType.objects.first())

    def test_get_court_search_unauthenticated(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.content.decode('utf-8'), "Unauthorized")

    def test_get_court_search(self):
        response = self.get_auth(self.url, {'query': 'Test Court'})
        self.assertEqual(response.status_code, 200)
        courts = response.json()['courts']
        self.assertEqual(len(courts), 40)
        for i in range(20):
            a_found = False
            b_found = False
            for court in courts:
                if court['name'] == f'Test Court A {i}':
                    a_found = True
                if court['name'] == f'Test Court B {i+20}':
                    b_found = True
            self.assertTrue(a_found)
            self.assertTrue(b_found)

    def test_get_court_search_A(self):
        response = self.get_auth(self.url, {'query': 'A'})
        self.assertEqual(response.status_code, 200)
        courts = response.json()['courts']
        self.assertEqual(len(courts), 20)
        for i in range(20):
            a_found = False
            for court in courts:
                if court['name'] == f'Test Court A {i}':
                    a_found = True
            self.assertTrue(a_found)

    def test_get_court_search_0(self):
        response = self.get_auth(self.url, {'query': '0'})
        self.assertEqual(response.status_code, 200)
        courts = response.json()['courts']
        self.assertEqual(len(courts), 4)
        for i in range(2):
            a_found = False
            b_found = False
            for court in courts:
                if court['name'] == f'Test Court A {i*10}':
                    a_found = True
                if court['name'] == f'Test Court B {(i+2)*10}':
                    b_found = True
            self.assertTrue(a_found)
            self.assertTrue(b_found)

    def test_get_court_search_query_missing(self):
        response = self.get_auth(self.url)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content.decode('utf-8'), "Missing parameter: 'query'")

    def test_get_court_search_empty_query(self):
        response = self.get_auth(self.url, {'query': ''})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content.decode('utf-8'), "Invalid value provided: query cannot be empty")


class CourtPercentageGetTests(CourtDatabaseTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse('video-conference-restapi-court-percentage')
        self.court = Court.objects.create(name='Test Court', type=CourtType.objects.first())

    def test_get_court_percentage_unauthenticated(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.content.decode('utf-8'), "Unauthorized")

    def test_get_court_percentage(self):
        positive_feedback = randint(1, 20)
        for i in range(positive_feedback):
            Feedback.objects.create(court=self.court, provides_online_service=True)
        negative_feedback = randint(1, 20)
        for i in range(negative_feedback):
            Feedback.objects.create(court=self.court, provides_online_service=False)

        positive_detailed_feedback = randint(1, 20)
        for i in range(positive_detailed_feedback):
            DetailedFeedback.objects.create(court=self.court, user=self.user, online_service_possible=True)
        negative_detailed_feedback = randint(1, 20)
        for i in range(negative_detailed_feedback):
            DetailedFeedback.objects.create(court=self.court, user=self.user, online_service_possible=False)

        self.court.update_feedback_buffers()
        self.court.update_detailed_feedback_buffers()

        response = self.get_auth(self.url, {'court_id': self.court.id})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['court_id'], self.court.id)
        self.assertEqual(data['provides_online_service_percentage'], positive_feedback / (positive_feedback + negative_feedback))
        self.assertEqual(data['online_service_possible_percentage'], positive_detailed_feedback / (positive_detailed_feedback + negative_detailed_feedback))

    def test_get_court_percentage_no_feedbacks(self):
        response = self.get_auth(self.url, {'court_id': self.court.id})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['court_id'], self.court.id)
        self.assertEqual(data['provides_online_service_percentage'], -1)
        self.assertEqual(data['online_service_possible_percentage'], -1)

    def test_get_court_percentage_court_id_missing(self):
        response = self.get_auth(self.url)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content.decode('utf-8'), "Missing parameter: 'court_id'")

    def test_get_court_percentage_court_id_invalid(self):
        response = self.get_auth(self.url, {'court_id': 'no'})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content.decode('utf-8'), "Invalid value provided: Field 'id' expected a number but got 'no'.")

    def test_get_court_percentage_court_id_unused(self):
        response = self.get_auth(self.url, {'court_id': -1})
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.content.decode('utf-8'), "Selected Court does not exist")


class CourtCreateTests(CourtDatabaseTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse('video-conference-restapi-court')

    def test_create_court_unauthenticated(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.content.decode('utf-8'), "Unauthorized")

    def test_create_court(self):
        parent = Court.objects.create(name="Parent Court", type=CourtType.objects.first())
        request_data = {
            'name': 'New Test Court',
            'type': CourtType.objects.first().id,
            'parent': parent.id,
            'address': {
                'state': 'BY'
            }
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
            'type': CourtType.objects.first().id,
            'address': {
                'state': 'BY'
            }
        }
        response = self.post_auth(self.url, request_data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content.decode('utf-8'), "Missing required field: 'name'")

    def test_create_court_empty_name(self):
        request_data = {
            'name': '',
            'type': CourtType.objects.first().id,
            'address': {
                'state': 'BY'
            }
        }
        response = self.post_auth(self.url, request_data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content.decode('utf-8'), "Invalid value provided: name cannot be empty")

    def test_create_court_missing_type(self):
        request_data = {
            'name': 'New Test Court',
            'address': {
                'state': 'BY'
            }
        }
        response = self.post_auth(self.url, request_data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content.decode('utf-8'), "Missing required field: 'type'")

    def test_create_court_existing_name(self):
        Court.objects.create(name="Existing Court", type=CourtType.objects.first())
        request_data = {
            'name': 'Existing Court',
            'type': CourtType.objects.first().id,
            'address': {
                'state': 'BY'
            }
        }
        response = self.post_auth(self.url, request_data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content.decode('utf-8'), "Error creating court: UNIQUE constraint failed: court_database_court.name")

    def test_create_court_invalid_parent(self):
        request_data = {
            'name': 'New Test Court',
            'type': CourtType.objects.first().id,
            'parent': -1,
            'address': {
                'state': 'BY'
            }
        }
        response = self.post_auth(self.url, request_data)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.content.decode('utf-8'), "Parent court does not exist")

    def test_create_court_invalid_type(self):
        request_data = {
            'name': 'Existing Court',
            'type': -1,
            'address': {
                'state': 'BY'
            }
        }
        response = self.post_auth(self.url, request_data)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.content.decode('utf-8'), "Selected court type does not exist")

    def test_create_court_with_full_address(self):
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
        self.assertEqual(response.content.decode('utf-8'), "Invalid value provided: If 'city', 'postal_code' or 'street' are provided, all three must be provided.")

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

    def test_create_court_empty_city(self):
        request_data = {
            'name': 'New Test Court',
            'type': CourtType.objects.first().id,
            'address': {
                'state': 'BY',
                'city': '',
                'postal_code': '12345',
                'street': 'Street'
            }
        }
        response = self.post_auth(self.url, request_data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content.decode('utf-8'), "Invalid value provided: If 'city', 'postal_code' or 'street' are provided, all three must be provided.")

    def test_create_court_empty_postal_code(self):
        request_data = {
            'name': 'New Test Court',
            'type': CourtType.objects.first().id,
            'address': {
                'state': 'BY',
                'city': 'City',
                'postal_code': '',
                'street': 'Street'
            }
        }
        response = self.post_auth(self.url, request_data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content.decode('utf-8'), "Invalid value provided: If 'city', 'postal_code' or 'street' are provided, all three must be provided.")

    def test_create_court_empty_street(self):
        request_data = {
            'name': 'New Test Court',
            'type': CourtType.objects.first().id,
            'address': {
                'state': 'BY',
                'city': 'City',
                'postal_code': '12345',
                'street': ''
            }
        }
        response = self.post_auth(self.url, request_data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content.decode('utf-8'), "Invalid value provided: If 'city', 'postal_code' or 'street' are provided, all three must be provided.")


class CourtTypeGetTests(CourtDatabaseTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse('video-conference-restapi-court-type')

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
        self.url = reverse('video-conference-restapi-court-type')

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
        response = self.post_auth(self.url)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content.decode('utf-8'), "Missing required field: 'name'")

    def test_create_court_type_empty_name(self):
        request_data = {
            'name': ''
        }
        response = self.post_auth(self.url, request_data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content.decode('utf-8'), "Invalid value provided: name cannot be empty")

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
        self.url = reverse('video-conference-restapi-state')

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


class FeedbackCreateTests(CourtDatabaseTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse('video-conference-restapi-feedback')
        self.court = Court.objects.create(name='Feedback Court', type=CourtType.objects.first())

    def test_create_feedback_unauthenticated(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.content.decode('utf-8'), "Unauthorized")

    def test_create_positive_feedback(self):
        request_data = {
            'court_id': self.court.id,
            'provides_online_service': True,
            'online_service_quality': 5
        }
        response = self.post_auth(self.url, request_data)
        self.assertEqual(response.status_code, 201)
        feedback = self.court.feedback_set.first()
        self.assertEqual(feedback.court, self.court)
        self.assertTrue(feedback.provides_online_service)
        self.assertEqual(feedback.online_service_quality, 5)
        self.assertIsNone(feedback.rejection_reason)
        self.assertIsNone(feedback.other_rejection_reason)
        self.assertEqual(feedback.api_user, self.user)

    def test_create_positive_feedback_no_quality(self):
        request_data = {
            'court_id': self.court.id,
            'provides_online_service': True
        }
        response = self.post_auth(self.url, request_data)
        self.assertEqual(response.status_code, 201)
        feedback = self.court.feedback_set.first()
        self.assertEqual(feedback.court, self.court)
        self.assertTrue(feedback.provides_online_service)
        self.assertIsNone(feedback.online_service_quality)
        self.assertIsNone(feedback.rejection_reason)
        self.assertEqual(feedback.api_user, self.user)

    def test_create_positive_feedback_invalid_quality(self):
        request_data = {
            'court_id': self.court.id,
            'provides_online_service': True,
            'online_service_quality': 6
        }
        response = self.post_auth(self.url, request_data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content.decode('utf-8'), "Invalid value provided: Invalid online_service_quality. Must be 1-5 or null.")

    def test_create_negative_feedback(self):
        rejection_reason = RejectionReason.objects.create(name="Test Rejection Reason")
        request_data = {
            'court_id': self.court.id,
            'provides_online_service': False,
            'rejection_reason': rejection_reason.id
        }
        response = self.post_auth(self.url, request_data)
        self.assertEqual(response.status_code, 201)
        feedback = self.court.feedback_set.first()
        self.assertEqual(feedback.court, self.court)
        self.assertFalse(feedback.provides_online_service)
        self.assertIsNone(feedback.online_service_quality)
        self.assertEqual(feedback.rejection_reason, rejection_reason)
        self.assertIsNone(feedback.other_rejection_reason)
        self.assertEqual(feedback.api_user, self.user)

    def test_create_negative_feedback_other_reason(self):
        request_data = {
            'court_id': self.court.id,
            'provides_online_service': False,
            'other_rejection_reason': 'This is a test reason'
        }
        response = self.post_auth(self.url, request_data)
        self.assertEqual(response.status_code, 201)
        feedback = self.court.feedback_set.first()
        self.assertEqual(feedback.court, self.court)
        self.assertFalse(feedback.provides_online_service)
        self.assertIsNone(feedback.online_service_quality)
        self.assertIsNone(feedback.rejection_reason)
        self.assertEqual(feedback.other_rejection_reason, 'This is a test reason')
        self.assertEqual(feedback.api_user, self.user)

    def test_create_negative_feedback_missing_reason(self):
        request_data = {
            'court_id': self.court.id,
            'provides_online_service': False
        }
        response = self.post_auth(self.url, request_data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content.decode('utf-8'), "Invalid value provided: Either rejection_reason or other_rejection_reason must be provided, but not both.")

    def test_create_negative_feedback_both_reasons(self):
        rejection_reason = RejectionReason.objects.create(name="Test Rejection Reason")
        request_data = {
            'court_id': self.court.id,
            'provides_online_service': False,
            'rejection_reason': rejection_reason.id,
            'other_rejection_reason': 'This is a test reason'
        }
        response = self.post_auth(self.url, request_data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content.decode('utf-8'),"Invalid value provided: Either rejection_reason or other_rejection_reason must be provided, but not both.")

    def test_create_feedback_missing_court(self):
        request_data = {
            'provides_online_service': True,
            'online_service_quality': 5
        }
        response = self.post_auth(self.url, request_data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content.decode('utf-8'), "Missing required field: 'court_id'")

    def test_create_feedback_invalid_court(self):
        request_data = {
            'court_id': -1,
            'provides_online_service': True,
            'online_service_quality': 5
        }
        response = self.post_auth(self.url, request_data)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.content.decode('utf-8'), "Selected Court does not exist")

    def test_create_feedback_missing_provides_online_service(self):
        request_data = {
            'court_id': self.court.id
        }
        response = self.post_auth(self.url, request_data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content.decode('utf-8'), "Missing required field: 'provides_online_service'")

    def test_create_feedback_update_buffers(self):
        for quality in [1,1,2,3,5,5,None,None]:
            request_data = {
                'court_id': self.court.id,
                'provides_online_service': True,
                'online_service_quality': quality
            }
            response = self.post_auth(self.url, request_data)
            self.assertEqual(response.status_code, 201)

        rejection_reason = RejectionReason.objects.create(name="Test Rejection Reason")
        for _ in range(4):
            request_data = {
                'court_id': self.court.id,
                'provides_online_service': False,
                'rejection_reason': rejection_reason.id
            }
            response = self.post_auth(self.url, request_data)
            self.assertEqual(response.status_code, 201)

        test_court = Court.objects.get(id=self.court.id)
        self.assertEqual(test_court.provides_online_service_yes_count, 8)
        self.assertEqual(test_court.provides_online_service_no_count, 4)
        self.assertTrue(test_court.provides_online_service_attr)
        self.assertEqual(test_court.online_service_quality, sum([1,1,2,3,5,5])/6)


class DetailedFeedbackCreateTests(CourtDatabaseTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse('video-conference-restapi-detailed-feedback')
        self.court = Court.objects.create(name='Feedback Court', type=CourtType.objects.first())
        self.cam1 = CameraPerspective.objects.create(name='Test Camera Perspective 1')
        self.cam2 = CameraPerspective.objects.create(name='Test Camera Perspective 2')
        self.conf1 = ConferencingSoftware.objects.create(name='Test Conferencing Software 1')
        self.conf2 = ConferencingSoftware.objects.create(name='Test Conferencing Software 2')

    def test_create_detailed_feedback_unauthenticated(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.content.decode('utf-8'), "Unauthorized")

    def test_create_detailed_feedback(self):
        request_data = {
            'court_id': self.court.id,
            'online_service_possible': True,
            'feedback': 'This is a test feedback.',
            'camera_perspectives': [self.cam1.id, self.cam2.id],
            'conferencing_software': [self.conf1.id, self.conf2.id],
        }
        response = self.post_auth(self.url, request_data)
        self.assertEqual(response.status_code, 201)
        detailed_feedback = self.court.detailedfeedback_set.first()
        self.assertEqual(detailed_feedback.court, self.court)
        self.assertTrue(detailed_feedback.online_service_possible)
        self.assertEqual(detailed_feedback.feedback, 'This is a test feedback.')
        perspectives = detailed_feedback.camera_perspectives.all()
        self.assertEqual(len(perspectives), 2)
        self.assertEqual(perspectives[0].name, 'Test Camera Perspective 1')
        self.assertEqual(perspectives[1].name, 'Test Camera Perspective 2')
        software = detailed_feedback.conferencing_software.all()
        self.assertEqual(len(software), 2)
        self.assertEqual(software[0].name, 'Test Conferencing Software 1')
        self.assertEqual(software[1].name, 'Test Conferencing Software 2')
        self.assertTrue(detailed_feedback.from_api)
        self.assertEqual(detailed_feedback.user, self.user)

    def test_create_detailed_feedback_missing_court_id(self):
        request_data = {
            'online_service_possible': True,
            'feedback': 'This is a test feedback.',
            'camera_perspectives': [self.cam1.id, self.cam2.id],
            'conferencing_software': [self.conf1.id, self.conf2.id],
        }
        response = self.post_auth(self.url, request_data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content.decode('utf-8'), "Missing required field: 'court_id'")

    def test_create_detailed_feedback_missing_online_service_possible(self):
        request_data = {
            'court_id': self.court.id,
            'feedback': 'This is a test feedback.',
            'camera_perspectives': [self.cam1.id, self.cam2.id],
            'conferencing_software': [self.conf1.id, self.conf2.id],
        }
        response = self.post_auth(self.url, request_data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content.decode('utf-8'), "Missing required field: 'online_service_possible'")

    def test_create_detailed_feedback_missing_feedback(self):
        request_data = {
            'court_id': self.court.id,
            'online_service_possible': True,
            'camera_perspectives': [self.cam1.id, self.cam2.id],
            'conferencing_software': [self.conf1.id, self.conf2.id],
        }
        response = self.post_auth(self.url, request_data)
        self.assertEqual(response.status_code, 201)
        detailed_feedback = self.court.detailedfeedback_set.first()
        self.assertEqual(detailed_feedback.feedback, "")

    def test_create_detailed_feedback_missing_camera_perspectives(self):
        request_data = {
            'court_id': self.court.id,
            'online_service_possible': True,
            'feedback': 'This is a test feedback.',
            'conferencing_software': [self.conf1.id, self.conf2.id],
        }
        response = self.post_auth(self.url, request_data)
        self.assertEqual(response.status_code, 201)

    def test_create_detailed_feedback_missing_conferencing_software(self):
        request_data = {
            'court_id': self.court.id,
            'online_service_possible': True,
            'feedback': 'This is a test feedback.',
            'camera_perspectives': [self.cam1.id, self.cam2.id],
        }
        response = self.post_auth(self.url, request_data)
        self.assertEqual(response.status_code, 201)

    def test_create_detailed_feedback_invalid_court(self):
        request_data = {
            'court_id': -1,
            'online_service_possible': True,
            'feedback': 'This is a test feedback.',
            'camera_perspectives': [self.cam1.id, self.cam2.id],
            'conferencing_software': [self.conf1.id, self.conf2.id],
        }
        response = self.post_auth(self.url, request_data)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.content.decode('utf-8'), "Selected Court does not exist")

    def test_create_detailed_feedback_invalid_camera_perspective(self):
        request_data = {
            'court_id': self.court.id,
            'online_service_possible': True,
            'feedback': 'This is a test feedback.',
            'camera_perspectives': [-1],
            'conferencing_software': [self.conf1.id, self.conf2.id],
        }
        response = self.post_auth(self.url, request_data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content.decode('utf-8'), "Invalid value provided: Invalid CameraPerspective IDs: {-1}")

    def test_create_detailed_feedback_invalid_conferencing_software(self):
        request_data = {
            'court_id': self.court.id,
            'online_service_possible': True,
            'feedback': 'This is a test feedback.',
            'camera_perspectives': [self.cam1.id, self.cam2.id],
            'conferencing_software': [self.conf1.id, -1, -2],
        }
        response = self.post_auth(self.url, request_data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content.decode('utf-8'), "Invalid value provided: Invalid ConferencingSoftware IDs: {-1, -2}")

    def test_create_detailed_feedback_update_buffers(self):
        for _ in range(5):
            request_data = {
                'court_id': self.court.id,
                'online_service_possible': True
            }
            response = self.post_auth(self.url, request_data)
            self.assertEqual(response.status_code, 201)

        for _ in range(6):
            request_data = {
                'court_id': self.court.id,
                'online_service_possible': False
            }
            response = self.post_auth(self.url, request_data)
            self.assertEqual(response.status_code, 201)

        test_court = Court.objects.get(id=self.court.id)
        self.assertEqual(test_court.online_service_possible_yes_count, 5)
        self.assertEqual(test_court.online_service_possible_no_count, 6)
        self.assertFalse(test_court.online_service_possible_attr)


class RejectionReasonGetTests(CourtDatabaseTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse('video-conference-restapi-rejection-reason')
        self.num_of_objects = randint(3, 10)
        for i in range(self.num_of_objects):
            RejectionReason.objects.create(name=f'Test Rejection Reason {i}')

    def test_get_rejection_reason_unauthenticated(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.content.decode('utf-8'), "Unauthorized")

    def test_get_rejection_reason(self):
        response = self.get_auth(self.url)
        self.assertEqual(response.status_code, 200)
        rejection_reasons = response.json()
        self.assertEqual(len(rejection_reasons), self.num_of_objects)
        for i in range(self.num_of_objects):
            self.assertEqual(rejection_reasons[i]['name'], f'Test Rejection Reason {i}')


class CameraPerspectiveGetTests(CourtDatabaseTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse('video-conference-restapi-camera-perspective')
        self.num_of_objects = randint(3, 10)
        for i in range(self.num_of_objects):
            CameraPerspective.objects.create(name=f'Test Camera Perspective {i}')

    def test_get_camera_perspective_unauthenticated(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.content.decode('utf-8'), "Unauthorized")

    def test_get_camera_perspective(self):
        response = self.get_auth(self.url)
        self.assertEqual(response.status_code, 200)
        camera_perspectives = response.json()
        self.assertEqual(len(camera_perspectives), self.num_of_objects)
        for i in range(self.num_of_objects):
            self.assertEqual(camera_perspectives[i]['name'], f'Test Camera Perspective {i}')


class CameraPerspectiveCreateTests(CourtDatabaseTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse('video-conference-restapi-camera-perspective')

    def test_create_camera_perspective_unauthenticated(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.content.decode('utf-8'), "Unauthorized")

    def test_create_camera_perspective(self):
        request_data = {
            'name': 'New Camera Perspective'
        }
        response = self.post_auth(self.url, request_data)
        self.assertEqual(response.status_code, 201)
        data = response.json()
        camera_perspective = CameraPerspective.objects.get(id=data['id'])
        self.assertEqual(camera_perspective.name, 'New Camera Perspective')

    def test_create_camera_perspective_missing_name(self):
        response = self.post_auth(self.url)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content.decode('utf-8'), "Missing required field: 'name'")

    def test_create_camera_perspective_empty_name(self):
        request_data = {
            'name': ''
        }
        response = self.post_auth(self.url, request_data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content.decode('utf-8'), "Invalid value provided: name cannot be empty")

    def test_create_camera_perspective_existing_name(self):
        CameraPerspective.objects.create(name='Existing Camera Perspective')
        request_data = {
            'name': 'Existing Camera Perspective'
        }
        response = self.post_auth(self.url, request_data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content.decode('utf-8'), "Error creating camera perspective: UNIQUE constraint failed: video_conference_cameraperspective.name")


class ConferencingSoftwareGetTests(CourtDatabaseTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse('video-conference-restapi-conferencing-software')
        self.num_of_objects = randint(3, 10)
        for i in range(self.num_of_objects):
            ConferencingSoftware.objects.create(name=f'Test Conferencing Software {i}')

    def test_get_conferencing_software_unauthenticated(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.content.decode('utf-8'), "Unauthorized")

    def test_get_conferencing_software(self):
        response = self.get_auth(self.url)
        self.assertEqual(response.status_code, 200)
        conferencing_software = response.json()
        self.assertEqual(len(conferencing_software), self.num_of_objects)
        for i in range(self.num_of_objects):
            self.assertEqual(conferencing_software[i]['name'], f'Test Conferencing Software {i}')


class ConferencingSoftwareCreateTests(CourtDatabaseTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse('video-conference-restapi-conferencing-software')

    def test_create_conferencing_software_unauthenticated(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.content.decode('utf-8'), "Unauthorized")

    def test_create_conferencing_software(self):
        request_data = {
            'name': 'New Conferencing Software'
        }
        response = self.post_auth(self.url, request_data)
        self.assertEqual(response.status_code, 201)
        data = response.json()
        conferencing_software = ConferencingSoftware.objects.get(id=data['id'])
        self.assertEqual(conferencing_software.name, 'New Conferencing Software')

    def test_create_conferencing_software_missing_name(self):
        response = self.post_auth(self.url)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content.decode('utf-8'), "Missing required field: 'name'")

    def test_create_conferencing_software_empty_name(self):
        request_data = {
            'name': ''
        }
        response = self.post_auth(self.url, request_data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content.decode('utf-8'), "Invalid value provided: name cannot be empty")

    def test_create_conferencing_software_existing_name(self):
        ConferencingSoftware.objects.create(name='Existing Conferencing Software')
        request_data = {
            'name': 'Existing Conferencing Software'
        }
        response = self.post_auth(self.url, request_data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content.decode('utf-8'), "Error creating conferencing software: UNIQUE constraint failed: video_conference_conferencingsoftware.name")
