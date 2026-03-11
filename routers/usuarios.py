from fastapi import APIRouter, Form, UploadFile, File, HTTPException
from database import conectar
import base64
import io
import qrcode
import json

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])

def blob_to_b64(blob):
    if not blob:
        return None
    b64 = base64.b64encode(blob).decode()
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
    try:
        conn = conectar()
        cursor = conn.cursor()

        bici_bytes = await foto_bici.read() if foto_bici else None
        usuario_bytes = await foto_usuario.read() if foto_usuario else None

        # Datos que irá en el QR (más información útil)
        datos_qr = json.dumps({
            "codigo": codigo,
            "nombre": nombre,
            "cedula": cedula,
            "telefono": telefono
        })

        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4
        )
        qr.add_data(datos_qr)
        qr.make(fit=True)

        qr_img = qr.make_image(fill_color="black", back_color="white")

        buf = io.BytesIO()
        qr_img.save(buf, format="PNG")
        qr_bytes = buf.getvalue()
        buf.close()

        cursor.execute("""
            INSERT INTO usuarios
            (nombre, cedula, telefono, correo, contrasena, codigo, qr_blob, foto_bici_blob, foto_usuario_blob)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (nombre, cedula, telefono, correo, contrasena, codigo, qr_bytes, bici_bytes, usuario_bytes))

        conn.commit()

        return {"ok": True, "mensaje": "Usuario registrado con éxito"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()


@router.post("/login")
def login(cedula: str = Form(...), contrasena: str = Form(...)):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM usuarios WHERE cedula=%s AND contrasena=%s",
        (cedula, contrasena)
    )
    user = cursor.fetchone()

    cursor.close()
    conn.close()

    if not user:
        return {"ok": False, "mensaje": "Credenciales inválidas"}

    user["qr_blob"] = blob_to_b64(user.get("qr_blob"))
    user["foto_bici_blob"] = blob_to_b64(user.get("foto_bici_blob"))
    user["foto_usuario_blob"] = blob_to_b64(user.get("foto_usuario_blob"))

    return {"ok": True, "usuario": user}
