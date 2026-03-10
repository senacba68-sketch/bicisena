from fastapi import FastAPI
from routers import usuarios, vigilante, qr   # ← vigilante debe estar aquí

app = FastAPI(title="Bicisena API")

@app.get("/")
def health():
    return {"status": "ok"}

app.include_router(usuarios.router)
app.include_router(vigilante.router)     # ← este include es clave
app.include_router(qr.router)
