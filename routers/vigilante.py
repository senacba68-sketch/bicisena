from fastapi import APIRouter, Form
import pymysql
import base64
from database import get_connection

router = APIRouter()


@router.post("/vigilante/movimiento")
def registrar_movimiento(codigo: str = Form(...)):

    try:

        conn = get_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        # -----------------------------
        # BUSCAR USUARIO POR CODIGO QR
        # -----------------------------

        cursor.execute(
            """
            SELECT id, nombre, qr_blob, foto_bici_blob, foto_usuario_blob
            FROM usuarios
            WHERE codigo = %s
            """,
            (codigo,)
        )

        usuario = cursor.fetchone()

        if not usuario:
            return {"mensaje": "Código QR no registrado"}

        usuario_id = usuario["id"]

        # -----------------------------
        # REGISTRAR MOVIMIENTO
        # -----------------------------

        cursor.execute(
            """
            INSERT INTO movimientos (usuario_id, tipo_movimiento)
            VALUES (%s, 'ENTRADA')
            """,
            (usuario_id,)
        )

        conn.commit()

        # -----------------------------
        # CONVERTIR IMAGENES A BASE64
        # -----------------------------

        qr_base64 = None
        bici_base64 = None
        usuario_base64 = None

        if usuario["qr_blob"]:
            qr_base64 = base64.b64encode(usuario["qr_blob"]).decode()

        if usuario["foto_bici_blob"]:
            bici_base64 = base64.b64encode(usuario["foto_bici_blob"]).decode()

        if usuario["foto_usuario_blob"]:
            usuario_base64 = base64.b64encode(usuario["foto_usuario_blob"]).decode()

        return {
            "mensaje": "Movimiento registrado",
            "usuario": {
                "nombre": usuario["nombre"],
                "qr_blob": qr_base64,
                "foto_bici_blob": bici_base64,
                "foto_usuario_blob": usuario_base64
            }
        }

    except Exception as e:
        print("❌ ERROR en registrar_movimiento:", e)
        return {"mensaje": "Error del servidor"}
