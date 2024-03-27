from django.core.management.base import BaseCommand
from court_database.models import Court


class Command(BaseCommand):
    help = "Updates the feedback buffers of all Courts"

    def handle(self, *args, **options):
        for court in Court.objects.all():
            court.update_feedback_buffers()
            court.update_detailed_feedback_buffers()

        self.stdout.write(
            self.style.SUCCESS("Successfully updated feedback buffers")
        )
