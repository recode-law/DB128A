from functools import cache
import json

from django.core.paginator import Paginator
from django.conf import settings
from django.urls import reverse

from court_database.models import Court, CourtType, Address, States, InvalidStateError


@cache
def get_rest_api_info(base_url: str):
    return [
        {
            "id": "create-court",
            "title": "Create Court",
            "method": "POST",
            "url": f"{base_url}{reverse('court-database-restapi-court')}",
            "description": "Erstellt ein neues Gericht in der Datenbank.",
            "request_schema": json.dumps({
                "name": "<Name des Gerichts>",
                "type": "<ID des Gerichttyps>",
                "parent": "<ID des übergeordneten Gerichts>",
                "address": {
                    "state": "<Bundesland>",
                    "city": "<Stadt>",
                    "postal_code": "<Postleitzahl>",
                    "street": "<Straße und Hausnummer>"
                }
            }, indent=2, ensure_ascii=False),
            "response_schema": json.dumps({
                "id": "<ID des neuen Gerichts>",
            }, indent=2, ensure_ascii=False),
        },
        {
            "id": "get-court-ids",
            "title": "Get Court IDs",
            "method": "GET",
            "url": f"{base_url}{reverse('court-database-restapi-court')}",
            "description": "Gibt eine paginierte Liste von Gerichts-IDs und Namen zurück.",
            "request_schema": None,
            "response_schema": json.dumps({
                "pagination": {
                    "page_count": "<Anzahl der Seiten>",
                    "next": "<Nächste Seite (falls vorhanden)>",
                    "previous": "<Vorherige Seite (falls vorhanden)>"
                },
                "courts": [
                    {
                        "id": "<ID des Gerichts>",
                        "name": "<Name des Gerichts>"
                    }
                ]
            }, indent=2, ensure_ascii=False),
        },
        {
            "id": "get-court-info",
            "title": "Get Court Info",
            "method": "GET",
            "url": f"{base_url}{reverse('court-database-restapi-court-detail')}?ids=<comma-separated-ids>",
            "description": f"Gibt detaillierte Informationen zu den spezifizierten Gerichten zurück. Maximal {settings.COURT_LIST_LIMIT} Gerichte können abgefragt werden.",
            "request_schema": None,
            "response_schema": json.dumps({
                "courts": [
                    {
                        "id": "<ID des Gerichts>",
                        "name": "<Name des Gerichts>",
                        "type": "<ID des Gerichttyps>",
                        "parent": "<ID des übergeordneten Gerichts>",
                        "address": {
                            "state": "<Bundesland>",
                            "city": "<Stadt>",
                            "postal_code": "<Postleitzahl>",
                            "street": "<Straße und Hausnummer>"
                        },
                        "online_service_possible": "<Ob Videoverhandlungen möglich sind>",
                        "provides_online_service": "<Ob Videoverhandlungen angeboten werden>",
                        "feedbacks": [
                            {
                                "provides_online_service": "<Ob Videoverhandlungen angeboten werden>",
                                "online_service_quality": "<Qualität der Videoverhandlungen [1-5]>",
                                "rejection_reason": "<Grund für Ablehnung der Videoverhandlung>",
                                "created_at": "<Datum der Erstellung>"
                            }
                        ],
                        "detailed_feedbacks": [
                            {
                                "online_service_possible": "<Ob Videoverhandlungen möglich sind>",
                                "camera_perspectives": "<Kommagetrennte Liste der Kamera-Perspektiven>",
                                "conferencing_software": "<Kommagetrennte Liste der Konferenzsoftware>",
                                "feedback": "<Freitext-Feedback>",
                                "created_at": "<Datum der Erstellung>"
                            }
                        ]
                    }
                ]
            }, indent=2, ensure_ascii=False),
        },
        {
            "id": "create-court-type",
            "title": "Create Court Type",
            "method": "POST",
            "url": f"{base_url}{reverse('court-database-restapi-court-type')}",
            "description": "Erstellt einen neuen Gerichtstyp in der Datenbank.",
            "request_schema": json.dumps({
                "name": "<Name des Gerichtstyps>"
            }, indent=2, ensure_ascii=False),
            "response_schema": json.dumps({
                "id": "<ID des neuen Gerichtstyps>"
            }, indent=2, ensure_ascii=False),
        },
        {
            "id": "get-court-types",
            "title": "Get Court Types",
            "method": "GET",
            "url": f"{base_url}{reverse('court-database-restapi-court-type')}",
            "description": "Gibt eine Liste aller Gerichtstypen zurück.",
            "request_schema": None,
            "response_schema": json.dumps([
                {
                    "id": "<ID des Gerichtstyps>",
                    "name": "<Name des Gerichtstyps>"
                }
            ], indent=2, ensure_ascii=False),
        },
        {
            "id": "get-states",
            "title": "Get States",
            "method": "GET",
            "url": f"{base_url}{reverse('court-database-restapi-state')}",
            "description": "Gibt eine Liste aller Bundesländer zurück.",
            "request_schema": None,
            "response_schema": json.dumps([
                {
                    "id": "<ID des Bundeslandes>",
                    "name": "<Name des Bundeslandes>"
                }
            ], indent=2, ensure_ascii=False),
        },
    ]


def create_court(data: dict):
    court = Court()
    court.name = data["name"]
    court.type = CourtType.objects.get(id=data["type"])

    if parent := data.get("parent"):
        court.parent = Court.objects.get(id=parent)

    if address := data.get("address"):
        state = address["state"]
        city = address["city"]
        postal_code = address["postal_code"]
        street = address["street"]

        if not state in States.names:
            raise InvalidStateError(state)

        court.address = Address.objects.create(
            state=state,
            city=city,
            postal_code=postal_code,
            street=street
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
                "online_service_possible": court.online_service_possible_attr,
                "provides_online_service": court.provides_online_service_attr,
                "feedbacks": [feedback.to_dict() for feedback in court.feedback_set.all()],
                "detailed_feedbacks": [feedback.to_dict() for feedback in court.detailedfeedback_set.all()]
            } for court in courts
        ]
    }


def create_court_type(data: dict):
    court_type = CourtType(name=data["name"])
    court_type.save()
    return {
        "id": court_type.id,
    }


def get_court_types():
    court_types = CourtType.objects.all()
    return [{"id": court_type.id, "name": court_type.name} for court_type in court_types]


def get_states():
    return [{"id": state[0], "name": str(state[1])} for state in States.choices]