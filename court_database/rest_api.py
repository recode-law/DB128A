from functools import cache
import json

from django.core.paginator import Paginator
from django.conf import settings
from django.urls import reverse
from django.contrib.auth import get_user_model

from court_database.models import Court, CourtType, Address, States, InvalidStateError, Feedback, DetailedFeedback, \
    RejectionReason, CameraPerspective, ConferencingSoftware

UserModel = get_user_model()


def dump_and_clear_quotations(data: dict | list) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False).replace('"\\"', "").replace('\\""', "")


def get_non_empty(data: dict, key: str) -> str:
    value = data[key]
    if value is None or not value.strip():
        raise ValueError(f'{key} cannot be empty')
    return value


@cache
def get_rest_api_info(base_url: str) -> list:
    return [
        {
            "id": "get-court-ids",
            "title": "Gericht IDs abfragen",
            "method": "GET",
            "url": f"{base_url}{reverse('court-database-restapi-court')}?per_page=<Anzahl IDs pro Seite>&page=<Seitenzahl>",
            "description": "Gibt eine paginierte Liste von Gericht-IDs und Namen zurück.",
            "request_schema": None,
            "response_schema": dump_and_clear_quotations({
                "pagination": {
                    "page_count": '"<Anzahl der Seiten>"',
                    "next": '"<Nächste Seite (falls vorhanden)>"',
                    "previous": '"<Vorherige Seite (falls vorhanden)>"'
                },
                "courts": [
                    {
                        "id": '"<ID des Gerichts>"',
                        "name": "<Name des Gerichts>"
                    }
                ]
            }),
        },
        {
            "id": "get-court-info",
            "title": "Gerichtsinformationen abfragen",
            "method": "GET",
            "url": f"{base_url}{reverse('court-database-restapi-court-detail')}?ids=<Kommagetrennte Liste von Gericht-IDs>",
            "description": f"Gibt detaillierte Informationen zu den spezifizierten Gerichten zurück. Maximal {settings.COURT_LIST_LIMIT} Gerichte können abgefragt werden.",
            "request_schema": None,
            "response_schema": dump_and_clear_quotations({
                "courts": [
                    {
                        "id": '"<ID des Gerichts>"',
                        "name": "<Name des Gerichts>",
                        "type": '"<ID der Gerichtart>"',
                        "parent": '"<ID des übergeordneten Gerichts>"',
                        "address": {
                            "state": "<ID des Bundeslandes>",
                            "city": "<Stadt>",
                            "postal_code": "<Postleitzahl>",
                            "street": "<Straße und Hausnummer>"
                        },
                        "provides_online_service": "<Ob Videoverhandlungen angeboten werden>",
                        "online_service_possible": "<Ob Videoverhandlungen möglich sind>",
                        "feedbacks": [
                            {
                                "provides_online_service": "<Ob Videoverhandlungen angeboten werden>",
                                "online_service_quality": '"<Qualität der Videoverhandlungen [1-5], null wenn nicht angegeben>"',
                                "rejection_reason": '"<ID des Ablehnungsgrundes, -1 wenn ein anderer Grund angegeben wurde>"',
                                "created_at": "<Datum der Erstellung>"
                            }
                        ],
                        "detailed_feedbacks": [
                            {
                                "online_service_possible": "<Ob Videoverhandlungen möglich sind>",
                                "camera_perspectives": '"<Kommagetrennte Liste der Kamera-Perspektiven IDs>"',
                                "conferencing_software": '"<Kommagetrennte Liste der Konferenzsoftware IDs>"',
                                "feedback": "<Freitext-Feedback>",
                                "created_at": "<Datum der Erstellung>"
                            }
                        ]
                    }
                ]
            }),
        },
        {
            "id": "create-court",
            "title": "Gericht erstellen",
            "method": "POST",
            "url": f"{base_url}{reverse('court-database-restapi-court')}",
            "description": "Erstellt ein neues Gericht.",
            "request_schema": dump_and_clear_quotations({
                "name": "<Name des Gerichts>",
                "type": '"<ID der Gerichtsart>"',
                "parent": '"<ID des übergeordneten Gerichts, optional>"',
                "address": {
                    "state": "<Bundesland>",
                    "city": "<Stadt>",
                    "postal_code": "<Postleitzahl>",
                    "street": "<Straße und Hausnummer>"
                }
            }),
            "response_schema": dump_and_clear_quotations({
                "id": '"<ID des neuen Gerichts>"',
            }),
        },
        {
            "id": "get-court-types",
            "title": "Gerichtsarten abfragen",
            "method": "GET",
            "url": f"{base_url}{reverse('court-database-restapi-court-type')}",
            "description": "Gibt eine Liste aller Gerichtsarten zurück.",
            "request_schema": None,
            "response_schema": dump_and_clear_quotations([
                {
                    "id": '"<ID der Gerichtsart>"',
                    "name": "<Name der Gerichtsart>"
                }
            ]),
        },
        {
            "id": "create-court-type",
            "title": "Gerichtsart erstellen",
            "method": "POST",
            "url": f"{base_url}{reverse('court-database-restapi-court-type')}",
            "description": "Erstellt eine neue Gerichtsart.",
            "request_schema": dump_and_clear_quotations({
                "name": "<Name der Gerichtsart>"
            }),
            "response_schema": dump_and_clear_quotations({
                "id": '"<ID der neuen Gerichtsart>"'
            }),
        },
        {
            "id": "get-states",
            "title": "Bundesländer abfragen",
            "method": "GET",
            "url": f"{base_url}{reverse('court-database-restapi-state')}",
            "description": "Gibt eine Liste aller Bundesländer zurück.",
            "request_schema": None,
            "response_schema": dump_and_clear_quotations([
                {
                    "id": "<ID des Bundeslandes>",
                    "name": "<Name des Bundeslandes>"
                }
            ]),
        },
        {
            "id": "create-feedback",
            "title": "Feedback erstellen",
            "method": "POST",
            "url": f"{base_url}{reverse('court-database-restapi-feedback')}",
            "description": "Erstellt ein Feedback zu einem Gericht.",
            "request_schema": dump_and_clear_quotations({
                "court_id": '"<ID des Gerichts>"',
                "provides_online_service": '"<Ob Videoverhandlungen angeboten werden>"',
                "online_service_quality": '"<1-5 oder null, nur wenn provides_online_service true ist>"',
                "rejection_reason": '"<ID des Ablehnungsgrundes, nur wenn provides_online_service false ist und kein other_rejection_reason angegeben ist>"',
                "other_rejection_reason": "<Freitext, nur wenn provides_online_service false ist und kein rejection_reason angegeben ist>'"
            }),
            "response_schema": None,
        },
        {
            "id": "create-detailed-feedback",
            "title": "Detailliertes Feedback erstellen",
            "method": "POST",
            "url": f"{base_url}{reverse('court-database-restapi-detailed-feedback')}",
            "description": "Erstellt ein detailliertes Feedback zu einem Gericht.",
            "request_schema": dump_and_clear_quotations({
                "court_id": '"<ID des Gerichts>"',
                "online_service_possible": '"<Ob Videoverhandlungen möglich sind>"',
                "camera_perspectives": '"<Kommagetrennte Liste der Kamera-Perspektiven IDs, nur wenn online_service_possible true ist, optional>"',
                "conferencing_software": '"<Kommagetrennte Liste der Konferenzsoftware IDs, nur wenn online_service_possible true ist, optional>"',
                "feedback": "<Freitext, optional>"
            }),
            "response_schema": None,
        },
        {
            "id": "get-rejection-reasons",
            "title": "Ablehnungsgründe abfragen",
            "method": "GET",
            "url": f"{base_url}{reverse('court-database-restapi-rejection-reason')}",
            "description": "Gibt eine Liste aller Ablehnungsgründe zurück.",
            "request_schema": None,
            "response_schema": dump_and_clear_quotations([
                {
                    "id": '"<ID des Ablehnungsgrundes>"',
                    "name": "<Name des Ablehnungsgrundes>"
                }
            ]),
        },
        {
            "id": "get-camera-perspectives",
            "title": "Kamera-Perspektiven abfragen",
            "method": "GET",
            "url": f"{base_url}{reverse('court-database-restapi-camera-perspective')}",
            "description": "Gibt eine Liste aller Kamera-Perspektiven zurück.",
            "request_schema": None,
            "response_schema": dump_and_clear_quotations([
                {
                    "id": '"<ID der Kamera-Perspektive>"',
                    "name": "<Name der Kamera-Perspektive>"
                }
            ]),
        },
        {
            "id": "create-camera-perspective",
            "title": "Kamera-Perspektive erstellen",
            "method": "POST",
            "url": f"{base_url}{reverse('court-database-restapi-camera-perspective')}",
            "description": "Erstellt eine neue Kamera-Perspektive.",
            "request_schema": dump_and_clear_quotations({
                "name": "<Name der Kamera-Perspektive>"
            }),
            "response_schema": dump_and_clear_quotations({
                "id": '"<ID der neuen Kamera-Perspektive>"'
            }),
        },
        {
            "id": "get-conferencing-software",
            "title": "Konferenzsoftware abfragen",
            "method": "GET",
            "url": f"{base_url}{reverse('court-database-restapi-conferencing-software')}",
            "description": "Gibt eine Liste aller Konferenzsoftware zurück.",
            "request_schema": None,
            "response_schema": dump_and_clear_quotations([
                {
                    "id": '"<ID der Konferenzsoftware>"',
                    "name": "<Name der Konferenzsoftware>"
                }
            ]),
        },
        {
            "id": "create-conferencing-software",
            "title": "Konferenzsoftware erstellen",
            "method": "POST",
            "url": f"{base_url}{reverse('court-database-restapi-conferencing-software')}",
            "description": "Erstellt eine neue Konferenzsoftware.",
            "request_schema": dump_and_clear_quotations({
                "name": "<Name der Konferenzsoftware>"
            }),
            "response_schema": dump_and_clear_quotations({
                "id": '"<ID der neuen Konferenzsoftware>"'
            }),
        }
    ]


def create_court(data: dict, api_user: UserModel):
    court = Court()
    court.api_user = api_user
    court.name = get_non_empty(data, "name")
    court.type = CourtType.objects.get(id=data["type"])

    if parent := data.get("parent"):
        court.parent = Court.objects.get(id=parent)

    if address := data.get("address"):
        state = address["state"]
        city = get_non_empty(address, "city")
        postal_code = get_non_empty(address, "postal_code")
        street = get_non_empty(address, "street")

        if not state in States.names:
            raise InvalidStateError(state)

        court.address = Address.objects.create(
            state=state,
            city=city,
            postal_code=postal_code,
            street=street,
            api_user=api_user
        )

    try:
        court.save()
        return {
            "id": court.id
        }
    except Exception:
        if court.address:
            court.address.delete()
        raise


def get_court_ids(data: dict):
    per_page = int(data.get('per_page', 10))
    page = int(data.get('page', 1))

    courts = Court.objects.order_by("id")
    paginator = Paginator(courts, per_page)
    paginated_courts = paginator.page(page)

    response_data = {
        "pagination": {
            "page_count": paginator.num_pages,
        },
        "courts": [{"id": court.id, "name": court.name} for court in paginated_courts]
    }
    if paginated_courts.has_next():
        response_data["pagination"]["next"] = paginated_courts.next_page_number()
    if paginated_courts.has_previous():
        response_data["pagination"]["previous"] = paginated_courts.previous_page_number()

    return response_data


class CourtListLimitExceededError(ValueError):
    pass


def get_court_detail(data: dict):
    court_ids = data['ids'].split(",")
    if len(court_ids) > settings.COURT_LIST_LIMIT:
        raise CourtListLimitExceededError(f"Too many court IDs provided. Maximum is {settings.COURT_LIST_LIMIT}.")

    courts = Court.objects.filter(id__in=court_ids)

    return {
        "courts": [
            {
                "id": court.id,
                "name": court.name,
                "type": court.type.name,
                "parent": court.parent.id if court.parent else None,
                "address": {
                    "state": court.address.state,
                    "city": court.address.city,
                    "postal_code": court.address.postal_code,
                    "street": court.address.street
                } if court.address else None,
                "provides_online_service": court.provides_online_service_attr,
                "online_service_possible": court.online_service_possible_attr,
                "feedbacks": [feedback.to_dict() for feedback in court.feedback_set.all()],
                "detailed_feedbacks": [feedback.to_dict() for feedback in court.detailedfeedback_set.all()]
            } for court in courts
        ]
    }


def create_court_type(data: dict, api_user: UserModel):
    name = get_non_empty(data, "name")
    court_type = CourtType(name=name, api_user=api_user)
    court_type.save()
    return {
        "id": court_type.id,
    }


def get_court_types():
    court_types = CourtType.objects.all()
    return [{"id": court_type.id, "name": court_type.name} for court_type in court_types]


def get_states():
    return [{"id": state[0], "name": str(state[1])} for state in States.choices]


def create_court_feedback(data: dict, api_user: UserModel):
    court = Court.objects.get(id=data["court_id"])
    provides_online_service = data["provides_online_service"]
    if not isinstance(provides_online_service, bool):
        raise ValueError("provides_online_service must be a boolean value.")
    feedback = Feedback(
        court=court,
        provides_online_service=provides_online_service,
        api_user=api_user
    )

    if provides_online_service:
        quality = data.get("online_service_quality", None)
        if quality not in [None, 1, 2, 3, 4, 5]:
            raise ValueError("Invalid online_service_quality. Must be 1-5 or null.")
        feedback.online_service_quality = quality
    else:
        rejection_reason = data.get("rejection_reason", None)
        other_rejection_reason = data.get("other_rejection_reason", None)
        if rejection_reason is not None:
            if other_rejection_reason is not None:
                raise ValueError("Either rejection_reason or other_rejection_reason must be provided, but not both.")
            feedback.rejection_reason = RejectionReason.objects.get(id=rejection_reason)
        elif other_rejection_reason is not None:
            feedback.other_rejection_reason = other_rejection_reason
        else:
            raise ValueError("Either rejection_reason or other_rejection_reason must be provided, but not both.")

    feedback.save()
    court.update_feedback_buffers()


def create_court_detailed_feedback(data: dict, api_user: UserModel):
    court = Court.objects.get(id=data["court_id"])
    online_service_possible = data["online_service_possible"]
    if not isinstance(online_service_possible, bool):
        raise ValueError("online_service_possible must be a boolean value.")
    feedback = DetailedFeedback(
        user=api_user,
        court=court,
        online_service_possible=online_service_possible,
        feedback=data.get("feedback", "").strip(),
        from_api=True
    )
    feedback.save()
    court.update_detailed_feedback_buffers()
    if online_service_possible:
        try:
            camera_ids = set(data.get("camera_perspectives", []))
            found_cameras = CameraPerspective.objects.filter(id__in=camera_ids)
            found_camera_ids = set(found_cameras.values_list("id", flat=True))
            missing_ids = camera_ids - found_camera_ids
            if missing_ids:
                raise ValueError(f"Invalid CameraPerspective IDs: {missing_ids}")
            feedback.camera_perspectives.set(found_cameras)

            software_ids = set(data.get("conferencing_software", []))
            found_software = ConferencingSoftware.objects.filter(id__in=software_ids)
            found_software_ids = set(found_software.values_list("id", flat=True))
            missing_software_ids = software_ids - found_software_ids
            if missing_software_ids:
                raise ValueError(f"Invalid ConferencingSoftware IDs: {missing_software_ids}")
            feedback.conferencing_software.set(found_software)

            feedback.save()
        except Exception:
            feedback.delete()
            court.update_detailed_feedback_buffers()
            raise


def create_camera_perspective(data: dict, api_user: UserModel):
    name = get_non_empty(data, "name")
    camera = CameraPerspective(name=name, api_user=api_user)
    camera.save()
    return {
        "id": camera.id
    }


def create_conferencing_software(data: dict, api_user: UserModel):
    name = get_non_empty(data, "name")
    software = ConferencingSoftware(name=name, api_user=api_user)
    software.save()
    return {
        "id": software.id
    }


def get_camera_perspectives():
    return [{"id": camera.id, "name": camera.name} for camera in CameraPerspective.objects.all()]


def get_conferencing_software():
    return [{"id": software.id, "name": software.name} for software in ConferencingSoftware.objects.all()]


def get_rejection_reasons():
    return [{"id": reason.id, "name": reason.name} for reason in RejectionReason.objects.all()]
