from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('court_database', '0013_alter_conferencingsoftware_name'),
        ('video_conference', '0002_migrate_feedback_data')
    ]

    operations = [
        migrations.DeleteModel('Feedback'),
        migrations.DeleteModel('DetailedFeedback'),
        migrations.DeleteModel('RejectionReason'),
        migrations.DeleteModel('CameraPerspective'),
        migrations.DeleteModel('ConferencingSoftware')
    ]