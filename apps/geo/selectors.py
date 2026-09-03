from .models import Parish


def parishes_for_district(district_id):
    return Parish.objects.filter(subcounty__district_id=district_id)
