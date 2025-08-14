import jwt
import pytest


pytestmark = [pytest.mark.django_db]


def decode_jwt_without_validation(token: str) -> dict:
    return jwt.decode(token, options={"verify_signature": False}, algorithms=["HS256"])


@pytest.fixture
def random_user(factory):
    return factory.user(is_admin=False)


def test_as_superuser(as_user, random_user):
    as_user.user.setattr_and_save("is_staff", True)
    as_user.user.setattr_and_save("is_superuser", True)

    got = as_user.get(f"/api/demo/auth/token/as/{random_user.pk}/")

    token = decode_jwt_without_validation(got["token"])
    assert token["user_id"] == str(random_user.id)


def test_as_staff(as_user, random_user):
    as_user.user.setattr_and_save("is_staff", True)

    got = as_user.get(f"/api/demo/auth/token/as/{random_user.pk}/")

    token = decode_jwt_without_validation(got["token"])
    assert token["user_id"] == str(random_user.id)


def test_no_anon(as_anon, random_user):
    as_anon.get(f"/api/demo/auth/token/as/{random_user.pk}/", expected_status=401)


def test_no_regular_users(as_user, random_user):
    as_user.get(f"/api/demo/auth/token/as/{random_user.pk}/", expected_status=403)
