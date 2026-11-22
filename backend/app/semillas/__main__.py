from app.db.session import SessionLocal
from app.semillas import cargar

with SessionLocal() as db:
    resultado = cargar(db)
print(f"Catálogo de ejemplo cargado: {resultado['palas']} palas en {resultado['tiendas']} tiendas.")
