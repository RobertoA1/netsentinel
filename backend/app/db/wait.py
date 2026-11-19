"""Espera a que la base de datos acepte conexiones (arranque en contenedor)."""
import sys
import time

from sqlalchemy import text

from app.db.session import get_engine


def main(timeout: int = 90) -> None:
    end = time.time() + timeout
    while True:
        try:
            with get_engine().connect() as c:
                c.execute(text("SELECT 1"))
            print("Base de datos disponible")
            return
        except Exception as e:  # noqa: BLE001
            if time.time() > end:
                print(f"No se pudo conectar a la base de datos: {e}", file=sys.stderr)
                sys.exit(1)
            time.sleep(2)


if __name__ == "__main__":
    main()
