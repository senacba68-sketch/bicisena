from fastapi import APIRouter, Form, UploadFile, File, HTTPException
from database import conectar
import base64, io, qrcode

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])

def blob_to_b64(blob):
    return base64.b64encode(blob).decode() if blob else None

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

        # Leer imágenes
        bici_bytes = await foto_bici.read() if foto_bici else None
        usuario_bytes = await foto_usuario.read() if foto_usuario else None

        # Generar QR en el servidor
        datos_qr = f"Codigo: {codigo}\nNombre: {nombre}\nCedula: {cedula}\nTelefono: {telefono}"
        qr_img = qrcode.make(datos_qr)
        buf = io.BytesIO()
        qr_img.save(buf)  # guardar imagen generada en PNG
        qr_bytes = buf.getvalue()
        buf.close()

        cursor.execute("""
            INSERT INTO usuarios 
            (nombre, cedula, telefono, correo, contrasena, codigo, qr_blob, foto_bici_blob, foto_usuario_blob)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
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
    cursor.execute("SELECT * FROM usuarios WHERE cedula=%s AND contrasena=%s", (cedula, contrasena))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if not user:
        return {"ok": False, "mensaje": "Credenciales inválidas"}

    # blobs → base64
    user["qr_blob"] = blob_to_b64(user.get("qr_blob"))
    user["foto_bici_blob"] = blob_to_b64(user.get("foto_bici_blob"))
    user["foto_usuario_blob"] = blob_to_b64(user.get("foto_usuario_blob"))

    return {"ok": True, "usuario": user}
