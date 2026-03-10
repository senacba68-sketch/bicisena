from fastapi import FastAPI
from routers import usuarios, vigilante, qr  # ← vigilante aquí es clave

app = FastAPI(title="Bicisena API")

@app.get("/")
def health():
    return {"status": "ok"}

app.include_router(usuarios.router)
app.include_router(vigilante.router)    # ← Esto trae todos los endpoints de vigilante
app.include_router(qr.router)
