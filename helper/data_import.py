from court_database.models import Court, Address, States, CourtType
from video_conference.models import CameraPerspective, ConferencingSoftware, RejectionReason
import csv


def load_courts_from_csv(location: str):
    first_line_read = False
    with open(location) as csvfile:
        court_reader = csv.reader(csvfile, delimiter=';')
        for row in court_reader:
            if first_line_read:
                court_type = row[0]
                name = row[2]
                state = row[1]
                court = Court()
                court.name = name
                court.type = CourtType.objects.get(name=court_type)
                court.address = get_address(state)
                court.save()
            else:
                first_line_read = True


def get_address(state: str) -> Address:
    address = Address()
    address.state = States.values[States.labels.index(state)]
    address.city = "-"
    address.postal_code = "-"
    address.street = "-"
    address.save()
    return address


def create_base_data():

    if CameraPerspective.objects.count() == 0:
        for name in ["Sonstiges (Im Freitext erwähnen)",
                     "Eine Saalkamera",
                     "Kameras für Personengruppen",
                     "Eine Kamera pro Person"]:
            CameraPerspective(name=name).save()

    if ConferencingSoftware.objects.count() == 0:
        for name in ["Sonstiges (Im Freitext erwähnen)",
                     "Webex",
                     "Jitsi",
                     "Skype",
                     "Teams"]:
            ConferencingSoftware(name=name).save()

    if RejectionReason.objects.count() == 0:
        for name in ["Keine Begründung im Beschluss",
                     "Pauschale Begründung (ohne Einzelfallbezug)",
                     "Rechtlich unzulässig (z.B. Geheimhaltung)",
                     "Ungeeignet (z.B. Beweisaufnahme)",
                     "Antrag zu kurzfristig",
                     "Technische Schwierigkeiten",
                     "Keine Infrastruktur"]:
            RejectionReason(name=name).save()
