from .models import Parish, Subcounty


def create_parish(*, district, subcounty_name, parish_name, agro_zone=""):
    subcounty, _ = Subcounty.objects.get_or_create(
        district=district, name=subcounty_name)
    return Parish.objects.create(subcounty=subcounty, name=parish_name, agro_zone=agro_zone)
