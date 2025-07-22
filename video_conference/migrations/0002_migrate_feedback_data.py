from django.db import migrations

def migrate_rejection_reason(apps, schema_editor):
    OldRejectionReason = apps.get_model('court_database', 'RejectionReason')
    NewRejectionReason = apps.get_model('video_conference', 'RejectionReason')
    for obj in OldRejectionReason.objects.all():
        NewRejectionReason.objects.create(
            id=obj.id,
            name=obj.name
        )

def migrate_camera_perspective(apps, schema_editor):
    OldCameraPerspective = apps.get_model('court_database', 'CameraPerspective')
    NewCameraPerspective = apps.get_model('video_conference', 'CameraPerspective')
    for obj in OldCameraPerspective.objects.all():
        NewCameraPerspective.objects.create(
            id=obj.id,
            name=obj.name,
            api_user=obj.api_user
        )

def migrate_conferencing_software(apps, schema_editor):
    OldConferencingSoftware = apps.get_model('court_database', 'ConferencingSoftware')
    NewConferencingSoftware = apps.get_model('video_conference', 'ConferencingSoftware')
    for obj in OldConferencingSoftware.objects.all():
        NewConferencingSoftware.objects.create(
            id=obj.id,
            name=obj.name,
            api_user=obj.api_user
        )

def migrate_feedback(apps, schema_editor):
    OldFeedback = apps.get_model('court_database', 'Feedback')
    NewFeedback = apps.get_model('video_conference', 'Feedback')
    NewRejectionReason = apps.get_model('video_conference', 'RejectionReason')
    for obj in OldFeedback.objects.all():
        rejection_reason = None
        if obj.rejection_reason:
            rejection_reason = NewRejectionReason.objects.get(id=obj.rejection_reason.id)
        NewFeedback.objects.create(
            id=obj.id,
            court=obj.court,
            provides_online_service=obj.provides_online_service,
            online_service_quality=obj.online_service_quality,
            rejection_reason=rejection_reason,
            other_rejection_reason=obj.other_rejection_reason,
            creator_ip=obj.creator_ip,
            created_at=obj.created_at,
            disabled=obj.disabled,
            api_user=obj.api_user,
        )

def migrate_detailed_feedback(apps, schema_editor):
    OldDetailedFeedback = apps.get_model('court_database', 'DetailedFeedback')
    NewDetailedFeedback = apps.get_model('video_conference', 'DetailedFeedback')
    for obj in OldDetailedFeedback.objects.all():
        new_obj = NewDetailedFeedback.objects.create(
            id=obj.id,
            user=obj.user,
            court=obj.court,
            online_service_possible=obj.online_service_possible,
            feedback=obj.feedback,
            created_at=obj.created_at,
            disabled=obj.disabled,
            from_api=obj.from_api,
        )
        NewCameraPerspective = apps.get_model('video_conference', 'CameraPerspective')
        camera_perspectives = [NewCameraPerspective.objects.get(id=cp.id) for cp in obj.camera_perspectives.all()]
        new_obj.camera_perspectives.set(camera_perspectives)


        NewConferencingSoftware = apps.get_model('video_conference', 'ConferencingSoftware')
        conferencing_software = [NewConferencingSoftware.objects.get(id=cs.id) for cs in obj.conferencing_software.all()]
        new_obj.conferencing_software.set(conferencing_software)

class Migration(migrations.Migration):

    dependencies = [
        ('video_conference', '0001_initial'),
        ('court_database', '0013_alter_conferencingsoftware_name'),
    ]

    operations = [
        migrations.RunPython(migrate_rejection_reason),
        migrations.RunPython(migrate_camera_perspective),
        migrations.RunPython(migrate_conferencing_software),
        migrations.RunPython(migrate_feedback),
        migrations.RunPython(migrate_detailed_feedback),
    ]