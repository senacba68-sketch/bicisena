from fastapi import APIRouter, Form, UploadFile, File, HTTPException
from database import conectar
import base64
import io
import qrcode

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])

def blob_to_b64(blob):
    """Convierte BLOB a base64 string (con prefijo data URI si es imagen)"""
    if not blob:
        return None
    b64 = base64.b64encode(blob).decode('utf-8')
    return f"data:image/png;base64,{b64}"


@router.post("/registro")
async def registrar_usuario(
    nombre: str = Form(...),
    cedula: str = Form(...),
    telefono: str = Form(...),
    correo: str = Form(...),
    contrasena: str = Form(...),
    codigo: str = Form(...),
    foto_bici: UploadFile = File(None),
    foto_usuario: UploadFile = File(None)
):
    conn = None
    cursor = None
    try:
        conn = conectar()
        cursor = conn.cursor()

        # Leer imágenes
        bici_bytes = await foto_bici.read() if foto_bici else None
        usuario_bytes = await foto_usuario.read() if foto_usuario else None

        # Generar QR
        datos_qr = f"""
BICISENA - CODIGO UNICO
Codigo: {codigo}
Nombre: {nombre}
Cédula: {cedula}
Teléfono: {telefono}
Correo: {correo}
        """.strip()

        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
        qr.add_data(datos_qr)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        qr_bytes = buf.getvalue()
        buf.close()

        print(f"[DEBUG] Datos QR: {datos_qr}")
        print(f"[DEBUG] Tamaño QR bytes: {len(qr_bytes)}")

        # INSERT
        cursor.execute("""
            INSERT INTO usuarios 
            (nombre, cedula, telefono, correo, contrasena, codigo, qr_blob, foto_bici_blob, foto_usuario_blob)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (nombre, cedula, telefono, correo, contrasena, codigo, qr_bytes, bici_bytes, usuario_bytes))
        conn.commit()

        cursor.execute("SELECT LAST_INSERT_ID()")
        user_id = cursor.fetchone()[0]

        return {
            "ok": True,
            "mensaje": "Usuario registrado con éxito",
            "usuario": {
                "id": user_id,
                "nombre": nombre,
                "cedula": cedula,
                "telefono": telefono,
                "correo": correo,
                "codigo": codigo,
                "qr_blob": blob_to_b64(qr_bytes),
                "foto_bici_blob": blob_to_b64(bici_bytes),
                "foto_usuario_blob": blob_to_b64(usuario_bytes)
            }
        }

    except pymysql.Error as db_err:
        if conn:
            conn.rollback()
        print(f"[ERROR BD] {db_err}")
        raise HTTPException(status_code=500, detail=f"Error en base de datos: {str(db_err)}")
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"[ERROR GENERAL] {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
    finally:
        if cursor: cursor.close()
        if conn: conn.close()


@router.post("/login")
def login(cedula: str = Form(...), contrasena: str = Form(...)):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE cedula=%s AND contrasena=%s", (cedula, contrasena))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if not user:
        return {"ok": False, "mensaje": "Credenciales inválidas"}

    # Convertir blobs a base64 con prefijo
    user_dict = dict(user)
    user_dict["qr_blob"] = blob_to_b64(user.get("qr_blob"))
    user_dict["foto_bici_blob"] = blob_to_b64(user.get("foto_bici_blob"))
    user_dict["foto_usuario_blob"] = blob_to_b64(user.get("foto_usuario_blob"))

    return {"ok": True, "usuario": user_dict}

