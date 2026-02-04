import os
import pymysql
from pymysql.cursors import DictCursor
from urllib.parse import urlparse, unquote

def _config_from_database_url(url: str) -> dict:
    """Soporta mysql://user:pass@host:port/dbname"""
    p = urlparse(url)
    if p.scheme not in ("mysql", "mariadb"):
        raise ValueError("DATABASE_URL debe iniciar con mysql:// o mariadb://")
    return {
        "host": p.hostname or "127.0.0.1",
        "user": unquote(p.username or ""),
        "password": unquote(p.password or ""),
        "database": (p.path or "/").lstrip("/"),
        "port": int(p.port or 3306),
    }

def get_db_config() -> dict:
    # Opción 1 (recomendada en la nube): DATABASE_URL
    db_url = os.getenv("DATABASE_URL") or os.getenv("DB_URL")
    if db_url:
        cfg = _config_from_database_url(db_url)
    else:
        # Opción 2: variables separadas
        cfg = {
            "host": os.getenv("DB_HOST", "127.0.0.1"),
            "user": os.getenv("DB_USER", "root"),
            "password": os.getenv("DB_PASSWORD", ""),
            "database": os.getenv("DB_NAME", "railway"),
            "port": int(os.getenv("DB_PORT", "3306")),
        }

    # SSL opcional (algunos proveedores lo exigen).
    # Si tu proveedor te da un CA, pon su ruta en DB_SSL_CA (Render: env var + mount/secret).
    ssl_ca = os.getenv("DB_SSL_CA")
    if ssl_ca:
        cfg["ssl"] = {"ca": ssl_ca}

    return cfg

def conectar():
    cfg = get_db_config()
    return pymysql.connect(
        host=cfg["host"],
        user=cfg["user"],
        password=cfg["password"],
        database=cfg["database"],
        port=cfg.get("port", 3306),
        charset="utf8mb4",
        cursorclass=DictCursor,
        connect_timeout=int(os.getenv("DB_CONNECT_TIMEOUT", "10")),
        read_timeout=int(os.getenv("DB_READ_TIMEOUT", "30")),
        write_timeout=int(os.getenv("DB_WRITE_TIMEOUT", "30")),
        ssl=cfg.get("ssl"),
    )
