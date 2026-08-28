import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from aps_ssa.config import SsaConfig


@pytest.fixture
def config(tmp_path) -> SsaConfig:
    key_path = tmp_path / "ssa_private_key.pem"
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    key_path.write_bytes(
        private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
    return SsaConfig(
        client_id="client-abc",
        client_secret="secret-abc",
        service_account_id="sa-abc",
        key_id="key-abc",
        private_key_path=str(key_path),
        base_url="https://fake.local",
        scopes="data:read data:write account:write",
        request_timeout_seconds=5,
    )
