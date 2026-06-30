# Generated manually to fix telemetry date collisions with get_or_create

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ("dashboard", "0004_cgpapredictionhistory_semestersimulationhistory"),
    ]

    operations = [
        migrations.AlterField(
            model_name="completestudenttelemetry",
            name="date",
            field=models.DateField(default=django.utils.timezone.localdate),
        ),
    ]
