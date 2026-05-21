import pytest
from django.contrib.auth.models import User

from moderator.moderate.auth import ModeratorAuthBackend


@pytest.mark.django_db
def test_create_user_uses_email_derived_username():
    backend = ModeratorAuthBackend()
    user = backend.create_user({"email": "newperson@mozilla.com"})
    assert user.username == "newperson"
    assert user.email == "newperson@mozilla.com"


@pytest.mark.django_db
def test_update_user_backfills_legacy_username():
    user = User.objects.create_user(
        username="ad|Mozilla-LDAP|jane", email="jane@mozilla.com"
    )
    backend = ModeratorAuthBackend()
    backend.update_user(user, {"email": "jane@mozilla.com"})
    user.refresh_from_db()
    assert user.username == "jane"


@pytest.mark.django_db
def test_update_user_leaves_clean_username_alone():
    user = User.objects.create_user(username="jane", email="jane@mozilla.com")
    backend = ModeratorAuthBackend()
    backend.update_user(user, {"email": "jane@mozilla.com"})
    user.refresh_from_db()
    assert user.username == "jane"


@pytest.mark.django_db
def test_update_user_backfill_resolves_collision():
    # Another user already owns the obvious derivation.
    User.objects.create_user(username="jane", email="other@mozilla.com")
    user = User.objects.create_user(
        username="ad|Mozilla-LDAP|jane2", email="jane@mozilla.com"
    )
    backend = ModeratorAuthBackend()
    backend.update_user(user, {"email": "jane@mozilla.com"})
    user.refresh_from_db()
    assert user.username == "jane1"


@pytest.mark.django_db
def test_update_user_updates_email_before_deriving_username():
    # User's email in claims differs from stored email; the derivation
    # should use the new email, not the stale one.
    user = User.objects.create_user(
        username="ad|Mozilla-LDAP|x", email="old@mozilla.com"
    )
    backend = ModeratorAuthBackend()
    backend.update_user(user, {"email": "newname@mozilla.com"})
    user.refresh_from_db()
    assert user.email == "newname@mozilla.com"
    assert user.username == "newname"
