from fastapi import APIRouter
import base64
from database import conectar




router = APIRouter(prefix="/qr", tags=["QR"])

@router.get("/{codigo}")
def obtener_qr(codigo: str):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT qr_blob FROM usuarios WHERE codigo=%s", (codigo,))
    row = cursor.fetchone()
    conn.close()
    if not row or not row["qr_blob"]:
        return {"qr": None}
    return {"qr": base64.b64encode(row["qr_blob"]).decode()}
