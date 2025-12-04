"""
Pytest konfiguráció és közös fixture-ök.

Ez a fájl tartalmazza a tesztekhez használt közös beállításokat,
fixture-öket és mock konfigurációkat.
"""

import os
import sys
from pathlib import Path
from typing import Generator
from unittest.mock import MagicMock, patch

import pytest

# Projekt gyökérkönyvtár hozzáadása a Python path-hoz
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# ============================================
# Környezeti változók fixture-ök
# ============================================


@pytest.fixture(autouse=True)
def setup_test_environment() -> Generator[None, None, None]:
    """
    Teszt környezet beállítása minden teszthez.

    Beállítja a szükséges környezeti változókat és
    a teszt végén visszaállítja az eredeti állapotot.
    """
    # Eredeti környezet mentése
    original_env = os.environ.copy()

    # Teszt környezeti változók beállítása
    os.environ.update(
        {
            "SNMP_COMMUNITY": "public",
            "SNMP_VERSION": "2c",
            "DEFAULT_TIMEOUT": "5.0",
            "LOG_LEVEL": "DEBUG",
        }
    )

    yield

    # Eredeti környezet visszaállítása
    os.environ.clear()
    os.environ.update(original_env)


# ============================================
# Hálózati mock fixture-ök
# ============================================


@pytest.fixture
def mock_ping() -> Generator[MagicMock, None, None]:
    """
    Mock a ping3.ping függvényhez.

    Szimulálja a sikeres ping választ hálózati hívás nélkül.
    """
    with patch("ping3.ping") as mock:
        # Alapértelmezett: sikeres ping 10ms latency-vel
        mock.return_value = 10.0
        yield mock


@pytest.fixture
def mock_socket() -> Generator[MagicMock, None, None]:
    """
    Mock a socket műveletekhez.

    Szimulálja a socket kapcsolatokat hálózati hívás nélkül.
    """
    with patch("socket.socket") as mock:
        mock_instance = MagicMock()
        mock.return_value.__enter__ = MagicMock(return_value=mock_instance)
        mock.return_value.__exit__ = MagicMock(return_value=False)
        yield mock_instance


@pytest.fixture
def mock_dns_resolver() -> Generator[MagicMock, None, None]:
    """
    Mock a DNS resolver-hez.

    Szimulálja a DNS lekérdezéseket hálózati hívás nélkül.
    """
    with patch("dns.resolver.resolve") as mock:
        # Alapértelmezett A rekord válasz
        mock_answer = MagicMock()
        mock_answer.to_text.return_value = "93.184.216.34"
        mock.return_value = [mock_answer]
        yield mock


# ============================================
# SNMP mock fixture-ök
# ============================================


@pytest.fixture
def mock_snmp_engine() -> Generator[MagicMock, None, None]:
    """
    Mock az SNMP engine-hez.

    Szimulálja az SNMP lekérdezéseket hálózati hívás nélkül.
    """
    with patch("pysnmp.hlapi.v3arch.asyncio.SnmpEngine") as mock:
        mock_instance = MagicMock()
        mock.return_value = mock_instance
        yield mock_instance


# ============================================
# Fájlrendszer fixture-ök
# ============================================


@pytest.fixture
def temp_directory(tmp_path: Path) -> Path:
    """
    Ideiglenes könyvtár létrehozása tesztekhez.

    Args:
        tmp_path: Pytest által biztosított ideiglenes útvonal

    Returns:
        Path objektum az ideiglenes könyvtárhoz
    """
    test_dir = tmp_path / "test_data"
    test_dir.mkdir(parents=True, exist_ok=True)
    return test_dir


@pytest.fixture
def sample_log_file(temp_directory: Path) -> Path:
    """
    Minta log fájl létrehozása tesztekhez.

    Args:
        temp_directory: Ideiglenes könyvtár

    Returns:
        Path a létrehozott log fájlhoz
    """
    log_file = temp_directory / "sample.log"
    log_content = """2024-01-15 10:00:00 INFO Application started
2024-01-15 10:00:01 DEBUG Loading configuration
2024-01-15 10:00:02 WARNING Disk usage above 80%
2024-01-15 10:00:03 ERROR Connection failed to database
2024-01-15 10:00:04 INFO Retrying connection
2024-01-15 10:00:05 INFO Connection established
"""
    log_file.write_text(log_content)
    return log_file


# ============================================
# Marker konfigurációk
# ============================================


def pytest_configure(config: pytest.Config) -> None:
    """
    Pytest konfiguráció egyedi markerekkel.

    Regisztrálja a projektben használt egyedi markereket.
    """
    config.addinivalue_line("markers", "slow: marks tests as slow running")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "network: marks tests that require network access")
