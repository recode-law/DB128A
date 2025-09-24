import csv
from court_database.models import Court, CourtType, States


def get_state(state_name: str):
    for choice in States.choices:
        if choice[1] == state_name:
            return choice[0]
    return ""


def load_courts(path: str):
    with open(path) as csvfile:
        courts = []
        reader = csv.reader(csvfile, delimiter=';')

        for court_name, court_state, court_type in reader:
            court = Court()
            court.name = court_name
            court.type = CourtType.objects.get(name=court_type)
            court.state = get_state(court_state)
            courts.append(court)

        for court in courts:
            print(court.state)

        for court in courts:
            court.save()
