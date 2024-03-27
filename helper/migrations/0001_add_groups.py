from django.db import migrations


def apply_migration(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Group.objects.bulk_create([
        Group(name=u'Verifizierer'),
        Group(name=u'Verifiziert')
    ])


def revert_migration(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Group.objects.filter(
        name__in=[
            u'Verifizierer',
            u'Verifiziert'
        ]
    ).delete()


class Migration(migrations.Migration):
    dependencies = []

    operations = [
        migrations.RunPython(apply_migration, revert_migration)
    ]
