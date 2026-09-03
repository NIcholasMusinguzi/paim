from .models import AdvisoryDelivery, AdvisoryRequest, AdvisoryResponse, Comment, Post


def record_delivery(*, farmer, channel, content=None, trend=None, fallback_language=False):
    return AdvisoryDelivery.objects.create(
        content=content, trend=trend, farmer=farmer, channel=channel, fallback_language=fallback_language)


class PostScopeError(Exception):
    pass


def _may_post_to(user, scope_level, scope_id) -> bool:
    from apps.accounts.models import Role, ScopeLevel

    if user.role == Role.NATIONAL_ADMIN:
        return True
    if scope_level == ScopeLevel.NATIONAL:
        return False
    if scope_level == user.scope_level and scope_id == user.scope_id:
        return True
    if scope_level == ScopeLevel.PARISH:
        from apps.accounts.scoping import parish_ids_for

        return parish_ids_for(user).filter(id=scope_id).exists()
    return False


def create_post(*, author, scope_level, scope_id, title, body) -> Post:
    """An officer can post at exactly their own scope (their parish, their
    subcounty, their district), or narrower — a district officer may target
    one parish within their district, but never outside their jurisdiction
    and never nationally unless they are the national admin."""
    if not _may_post_to(author, scope_level, scope_id):
        raise PostScopeError("You can only post within your own scope.")
    return Post.objects.create(author=author, scope_level=scope_level, scope_id=scope_id, title=title, body=body)


def add_comment(*, post, author, body) -> Comment:
    return Comment.objects.create(post=post, author=author, body=body)


class AdvisoryRequestError(Exception):
    pass


def submit_advisory_request(*, farmer, message) -> AdvisoryRequest:
    return AdvisoryRequest.objects.create(farmer=farmer, message=message)


def respond_to_request(*, advisory_request, responder, body) -> AdvisoryResponse:
    from apps.accounts.permissions import OFFICER_ROLES
    from apps.accounts.scoping import parish_ids_for

    has_authority = (
        responder.role in OFFICER_ROLES
        and parish_ids_for(responder).filter(id=advisory_request.farmer.village.parish_id).exists()
    )
    if not has_authority:
        raise AdvisoryRequestError("You do not have authority over this farmer's parish.")
    response = AdvisoryResponse.objects.create(request=advisory_request, responder=responder, body=body)
    advisory_request.status = "answered"
    advisory_request.save(update_fields=["status", "updated_at"])
    return response
