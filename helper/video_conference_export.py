from court_database.models import Court

import csv

def export_court_data(location: str):
    with open(location, mode='w', newline='') as csvfile:
        data_writer = csv.writer(csvfile, delimiter=';')
        data_writer.writerow(['Court ID', 'Court Name', 'State', 'Court Type', 'Provides Online Service Yes Count',
                              'Provides Online Service No Count', 'Online Service Quality',
                              'Online Service Possible Yes Count', 'Online Service Possible No Count'])

        for court in Court.objects.order_by('id'):
            data_writer.writerow([
                court.id,
                court.name,
                court.address.get_state_display() if court.address else '',
                court.type.name if court.type else '',
                court.provides_online_service_yes_count,
                court.provides_online_service_no_count,
                court.online_service_quality,
                court.online_service_possible_yes_count,
                court.online_service_possible_no_count
            ])

def export_feedback_data(location: str):
    from video_conference.models import Feedback, DetailedFeedback

    with open(location, mode='w', newline='') as csvfile:
        data_writer = csv.writer(csvfile, delimiter=';')
        data_writer.writerow(['Court ID', 'Court Name', 'Feedback Type', 'Provides Online Service', 'Online Service Quality',
                              'Rejection Reason', 'Online Service Possible', 'Camera Perspectives',
                              'Conferencing Software', 'Textual Information'])

        for feedback in Feedback.objects.filter(disabled=False).order_by('court__id'):
            data_writer.writerow([
                feedback.court.id,
                feedback.court.name,
                'Public Feedback',
                feedback.provides_online_service,
                feedback.online_service_quality,
                feedback.rejection_reason if not feedback.provides_online_service and feedback.rejection_reason else feedback.other_rejection_reason,
                '',
                '',
                '',
                ''
            ])

        for detailed_feedback in DetailedFeedback.objects.filter(disabled=False).order_by('court__id'):
            data_writer.writerow([
                detailed_feedback.court.id,
                detailed_feedback.court.name,
                'Verified Persons Feedback',
                '',
                '',
                '',
                detailed_feedback.online_service_possible,
                detailed_feedback.camera_perspectives_text(),
                detailed_feedback.conferencing_software_text(),
                detailed_feedback.feedback
            ])