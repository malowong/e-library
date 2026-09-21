import pytest

from elibrary.domain.errors import EmailAlreadyRegistered, InvalidCredentials
from elibrary.domain.services import AuthService


@pytest.fixture
def auth(user_repository) -> AuthService:
    return AuthService(user_repository)


async def test_registration_stores_a_hash_not_the_password(auth):
    user = await auth.register("Reader@Example.com ", "correct-horse")

    assert user.email == "reader@example.com"
    assert user.password_hash != "correct-horse"


async def test_email_is_unique(auth):
    await auth.register("reader@example.com", "correct-horse")

    with pytest.raises(EmailAlreadyRegistered):
        await auth.register("READER@example.com", "another-password")


async def test_authentication_round_trip(auth):
    registered = await auth.register("reader@example.com", "correct-horse")

    assert (await auth.authenticate("reader@example.com", "correct-horse")).id == registered.id


@pytest.mark.parametrize(
    ("email", "password"),
    [("reader@example.com", "wrong-password"), ("nobody@example.com", "correct-horse")],
)
async def test_bad_credentials_are_indistinguishable(auth, email, password):
    await auth.register("reader@example.com", "correct-horse")

    with pytest.raises(InvalidCredentials):
        await auth.authenticate(email, password)
