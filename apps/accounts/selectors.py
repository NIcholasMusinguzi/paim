from apps.accounts.scoping import parish_ids_for


def scoped_parish_ids(user):
    return parish_ids_for(user)
