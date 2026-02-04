from fastapi import APIRouter, Form, Query
from fastapi.responses import JSONResponse
from database import conectar
from datetime import datetime
from typing import Optional
import base64
import pymysql

router = APIRouter(prefix="/vigilante", tags=["Vigilante"])


# Función auxiliar para convertir BLOB en base64
def blob_to_b64(blob):
    try:
        return base64.b64encode(blob).decode() if blob else None
    except Exception:
        return None


# Entrada y Salida automática con la lectura del QR
@router.post("/movimiento")
def registrar_movimiento(codigo: str = Form(...)):
    conn = None
    cursor = None
    try:
        conn = conectar()
        cursor = conn.cursor(pymysql.cursors.DictCursor)  # ✅ FIX

        # Buscar usuario con ese código
        cursor.execute("SELECT * FROM usuarios WHERE codigo=%s", (codigo,))
        usuario = cursor.fetchone()

        if not usuario:
            return JSONResponse(status_code=404, content={"ok": False, "mensaje": "Usuario no encontrado"})

        # Verificar si la bicicleta está dentro
        cursor.execute("SELECT * FROM bicicletas WHERE codigo=%s AND fecha_salida IS NULL", (codigo,))
        reg = cursor.fetchone()

        if reg:
            cursor.execute(
                "UPDATE bicicletas SET fecha_salida=%s, estado=%s WHERE id=%s",
                (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Retirada", reg["id"])
            )
            conn.commit()
            mensaje = "Salida registrada"
        else:
            cursor.execute(
                """INSERT INTO bicicletas 
                   (codigo, nombre, cedula, telefono, fecha_ingreso, estado) 
                   VALUES (%s,%s,%s,%s,%s,%s)""",
                (
                    usuario["codigo"],
                    usuario["nombre"],
                    usuario["cedula"],
                    usuario["telefono"],
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "En parqueadero"
                )
            )
            conn.commit()
            mensaje = "Entrada registrada"

        usuario_data = {
            "nombre": usuario["nombre"],
            "cedula": usuario["cedula"],
            "telefono": usuario["telefono"],
            "codigo": usuario["codigo"],
            "qr_blob": blob_to_b64(usuario.get("qr_blob")),
            "foto_bici_blob": blob_to_b64(usuario.get("foto_bici_blob")),
            "foto_usuario_blob": blob_to_b64(usuario.get("foto_usuario_blob")),
        }

        return {"ok": True, "mensaje": mensaje, "usuario": usuario_data}

    except Exception as e:
        import traceback
        print("❌ ERROR en registrar_movimiento:", str(e))
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"ok": False, "error": str(e)})
    finally:
        if cursor: cursor.close()
        if conn: conn.close()


# Listar registros con filtros
@router.get("/registros")
def listar_registros(
    busqueda: Optional[str] = Query(None),
    filtro: Optional[str] = Query("Todos")
):
    conn = None
    cursor = None
    try:
        conn = conectar()
        cursor = conn.cursor(pymysql.cursors.DictCursor)  # ✅ FIX

        query = "SELECT * FROM bicicletas"
        condiciones = []
        params = []

        if busqueda:
            condiciones.append("(codigo LIKE %s OR nombre LIKE %s OR cedula LIKE %s)")
            params.extend([f"%{busqueda}%"] * 3)

        if filtro == "En parqueadero":
            condiciones.append("estado = %s")
            params.append("En parqueadero")
        elif filtro == "Retiradas":
            condiciones.append("estado = %s")
            params.append("Retirada")

        if condiciones:
            query += " WHERE " + " AND ".join(condiciones)

        query += " ORDER BY fecha_ingreso DESC"

        cursor.execute(query, params)
        registros = cursor.fetchall()
        return registros

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    finally:
        if cursor: cursor.close()
        if conn: conn.close()


#  Registrar salida manual
@router.post("/salida")
def registrar_salida(codigo: str = Form(...)):
    conn = None
    cursor = None
    try:
        conn = conectar()
        cursor = conn.cursor(pymysql.cursors.DictCursor)  # ✅ FIX

        cursor.execute("SELECT estado FROM bicicletas WHERE codigo=%s", (codigo,))
        row = cursor.fetchone()
        if not row:
            return {"error": "Código no encontrado"}

        if row["estado"] == "Retirada":
            return {"mensaje": "La bicicleta ya fue retirada"}

        fecha_salida = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(
            "UPDATE bicicletas SET fecha_salida=%s, estado=%s WHERE codigo=%s",
            (fecha_salida, "Retirada", codigo)
        )
        conn.commit()
        return {"mensaje": "Salida registrada"}

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    finally:
        if cursor: cursor.close()
        if conn: conn.close()


# Borrar registros del día
@router.delete("/registros/dia")
def borrar_registros_dia():
    conn = None
    cursor = None
    try:
        conn = conectar()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM bicicletas WHERE DATE(fecha_ingreso) = CURDATE()")
        eliminados = cursor.rowcount
        conn.commit()
        return {"eliminados": eliminados}

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    finally:
        if cursor: cursor.close()
        if conn: conn.close()
