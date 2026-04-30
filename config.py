import os
from pathlib import Path

import pika


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DATA_DIR = Path(os.getenv("DATA_DIR", BASE_DIR))


def get_data_file(env_var: str, filename: str) -> Path:
    configured_path = os.getenv(env_var)
    path = Path(configured_path) if configured_path else DEFAULT_DATA_DIR / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def get_service_url(
    url_env: str,
    host_env: str,
    port_env: str,
    default_url: str,
    scheme_env: str | None = None,
) -> str:
    explicit_url = os.getenv(url_env)
    if explicit_url:
        return explicit_url.rstrip("/")

    host = os.getenv(host_env)
    if not host:
        return default_url.rstrip("/")

    port = os.getenv(port_env)
    scheme = os.getenv(scheme_env, "http") if scheme_env else "http"

    if port:
        return f"{scheme}://{host}:{port}".rstrip("/")

    return f"{scheme}://{host}".rstrip("/")


def get_rabbitmq_connection_parameters() -> pika.ConnectionParameters | pika.URLParameters:
    rabbitmq_url = os.getenv("RABBITMQ_URL")
    if rabbitmq_url:
        return pika.URLParameters(rabbitmq_url)

    host = os.getenv("RABBITMQ_HOST", "localhost")
    port = int(os.getenv("RABBITMQ_PORT", "5672"))
    user = os.getenv("RABBITMQ_USER", "guest")
    password = os.getenv("RABBITMQ_PASS", "guest")

    credentials = pika.PlainCredentials(user, password)
    return pika.ConnectionParameters(
        host=host,
        port=port,
        credentials=credentials,
        heartbeat=30,
        blocked_connection_timeout=30,
    )
