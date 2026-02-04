from fastapi import FastAPI
from routers import usuarios, vigilante, qr

app = FastAPI(title="Bicisena API")

@app.get("/", tags=["health"])
def health():
    return {"status": "ok", "service": "bicisena-api"}

# Routers
app.include_router(usuarios.router)
app.include_router(vigilante.router)
app.include_router(qr.router)  # si ya tienes endpoints QR
