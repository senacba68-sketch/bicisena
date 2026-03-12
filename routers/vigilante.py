from fastapi import APIRouter, Form, Query
from fastapi.responses import JSONResponse
from database import conectar
from datetime import datetime
from typing import Optional
import base64
import pymysql

router = APIRouter(prefix="/vigilante", tags=["Vigilante"])

# Función auxiliar para convertir BLOB a base64 con prefijo data URI
def blob_to_b64(blob):
    try:
        if not blob:
            return None
        return f"data:image/png;base64,{base64.b64encode(blob).decode()}"
    except Exception:
        return None

# Entrada y Salida automática con la lectura del QR
@router.post("/movimiento")
def registrar_movimiento(codigo: str = Form(...)):
    conn = None
    cursor = None
    try:
        codigo = codigo.strip()
        conn = conectar()
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        # Buscar usuario
        cursor.execute("SELECT * FROM usuarios WHERE TRIM(codigo) = %s", (codigo,))
        usuario = cursor.fetchone()

        if not usuario:
            return JSONResponse(
                status_code=404,
                content={"ok": False, "mensaje": f"Usuario no encontrado para código: {codigo}"}
            )

        usuario_id = usuario["id"]

        # Verificar el último movimiento (si el último es 'Entrada', registrar 'Salida')
        cursor.execute(
            """
            SELECT accion FROM registros 
            WHERE usuario_id = %s 
            ORDER BY fecha DESC LIMIT 1
            """,
            (usuario_id,)
        )
        ultimo = cursor.fetchone()

        if ultimo and ultimo["accion"] == 'Entrada':
            accion_nueva = 'Salida'
            mensaje = "Salida registrada correctamente"
        else:
            accion_nueva = 'Entrada'
            mensaje = "Entrada registrada correctamente"

        # Registrar el nuevo movimiento
        cursor.execute(
            """
            INSERT INTO registros 
            (usuario_id, accion, fecha) 
            VALUES (%s, %s, NOW())
            """,
            (usuario_id, accion_nueva)
        )

        conn.commit()

        # Preparar datos del usuario para la respuesta
        usuario_data = {
            "nombre": usuario["nombre"],
            "cedula": usuario["cedula"],
            "telefono": usuario["telefono"],
            "codigo": usuario["codigo"],
            "qr_blob": blob_to_b64(usuario.get("qr_blob")),
            "foto_bici_blob": blob_to_b64(usuario.get("foto_bici_blob")),
            "foto_usuario_blob": blob_to_b64(usuario.get("foto_usuario_blob")),
        }

        return {
            "ok": True,
            "mensaje": mensaje,
            "usuario": usuario_data
        }

    except Exception as e:
        import traceback
        print("❌ ERROR en registrar_movimiento:", str(e))
        traceback.print_exc()
        if conn:
            conn.rollback()
        return JSONResponse(status_code=500, content={"ok": False, "error": str(e)})

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# Listar registros con filtros (estado basado en el último movimiento)
@router.get("/registros")
def listar_registros(
    busqueda: Optional[str] = Query(None),
    filtro: Optional[str] = Query("Todos")
):
    conn = None
    cursor = None
    try:
        conn = conectar()
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        query = """
            SELECT 
                u.codigo,
                u.nombre,
                u.cedula,
                u.telefono,
                MAX(r.fecha) AS ultima_fecha,
                MAX(r.accion) AS ultima_accion,
                CASE 
                    WHEN MAX(r.accion) = 'Entrada' THEN 'En parqueadero'
                    ELSE 'Retirada'
                END AS estado
            FROM usuarios u
            LEFT JOIN registros r ON u.id = r.usuario_id
            GROUP BY u.id, u.codigo, u.nombre, u.cedula, u.telefono
        """
        condiciones = []
        params = []

        if busqueda:
            condiciones.append("(u.codigo LIKE %s OR u.nombre LIKE %s OR u.cedula LIKE %s)")
            like = f"%{busqueda}%"
            params.extend([like, like, like])

        if filtro == "En parqueadero":
            condiciones.append("MAX(r.accion) = 'Entrada'")
        elif filtro == "Retiradas":
            condiciones.append("MAX(r.accion) = 'Salida' OR MAX(r.accion) IS NULL")

        if condiciones:
            query += " HAVING " + " AND ".join(condiciones)

        query += " ORDER BY ultima_fecha DESC"

        cursor.execute(query, params)
        registros = cursor.fetchall()

        return registros

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# Registrar salida manual
@router.post("/salida")
def registrar_salida(codigo: str = Form(...)):
    conn = None
    cursor = None
    try:
        codigo = codigo.strip()
        conn = conectar()
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        cursor.execute("SELECT id FROM usuarios WHERE codigo = %s", (codigo,))
        usuario = cursor.fetchone()
        if not usuario:
            return {"error": "Código no encontrado"}

        usuario_id = usuario["id"]

        # Verificar si hay una entrada sin salida (último movimiento es 'Entrada')
        cursor.execute(
            """
            SELECT id FROM registros 
            WHERE usuario_id = %s 
            ORDER BY fecha DESC LIMIT 1
            """,
            (usuario_id,)
        )
        ultimo = cursor.fetchone()

        if not ultimo or ultimo["accion"] == 'Salida':
            return {"mensaje": "No hay entrada abierta para registrar salida"}

        # Registrar salida
        cursor.execute(
            "INSERT INTO registros (usuario_id, accion, fecha) VALUES (%s, 'Salida', NOW())",
            (usuario_id,)
        )
        conn.commit()

        return {"mensaje": "Salida registrada manualmente"}

    except Exception as e:
        if conn:
            conn.rollback()
        return JSONResponse(status_code=500, content={"error": str(e)})

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# Borrar registros del día
@router.delete("/registros/dia")
def borrar_registros_dia():
    conn = None
    cursor = None
    try:
        conn = conectar()
        cursor = conn.cursor()

        cursor.execute(
            "DELETE FROM registros WHERE DATE(fecha) = CURDATE()"
        )
        eliminados = cursor.rowcount
        conn.commit()

        return {"eliminados": eliminados, "mensaje": f"Eliminados {eliminados} registros de hoy"}

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
