from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def populate_requesters(apps, schema_editor):
    AdvisoryRequest = apps.get_model("advisory", "AdvisoryRequest")
    AdvisoryRequest.objects.filter(requester__isnull=True, farmer__user__isnull=False).update(
        requester=models.Subquery(
            apps.get_model("farmers", "Farmer").objects.filter(
                advisory_requests__pk=models.OuterRef("pk")
            ).values("user_id")[:1]
        )
    )


class Migration(migrations.Migration):
    dependencies = [
        ("advisory", "0003_advisoryrequest_advisoryresponse_post_comment"),
    ]

    operations = [
        migrations.AlterField(
            model_name="advisoryrequest",
            name="farmer",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE,
                                    related_name="advisory_requests", to="farmers.farmer"),
        ),
        migrations.AddField(
            model_name="advisoryrequest",
            name="requester",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE,
                                    related_name="advisory_requests_submitted", to=settings.AUTH_USER_MODEL),
        ),
        migrations.RunPython(populate_requesters, migrations.RunPython.noop),
    ]
