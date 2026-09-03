from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from hashlib import sha256
from urllib.parse import urlparse
import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="PMSI Analytics API", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000", "https://*.vercel.app"], allow_methods=["GET", "POST"], allow_headers=["*"])

NOW = datetime.now(timezone.utc).isoformat()
IMPORT = {"id": "imp_2026_01", "source": "Fixture synthétique", "referential": "ATIH MCO 2026", "status": "success", "rows": 18420, "sha256": "fixture-local-demo-256", "created_at": NOW, "duration": "00:01:42"}
QUALITY = [{"code":"SCH-001","severity":"success","label":"Schéma reconnu","detail":"12 colonnes attendues, types conformes","count":0},{"code":"DAT-014","severity":"warning","label":"Dates de sortie manquantes","detail":"Séjours sans date de sortie exploitable","count":24},{"code":"DUP-003","severity":"error","label":"Doublons de séjours","detail":"Identifiants présents plusieurs fois","count":7},{"code":"VAL-021","severity":"success","label":"Durées cohérentes","detail":"Bornes et ordre admission/sortie validés","count":0}]
DATASETS = [{"name":"sejours_normalises","label":"Séjours normalisés","rows":"18 420","updated":"Aujourd’hui, 09:42","status":"Prêt","description":"Table analytique issue de l’import PMSI synthétique."},{"name":"rsa_dimensions","label":"Dimensions RSA","rows":"18 420","updated":"Aujourd’hui, 09:42","status":"Prêt","description":"Dimensions codage, séjour et groupage."},{"name":"referentiel_atih","label":"Référentiel ATIH","rows":"3 281","updated":"Aujourd’hui, 09:40","status":"Versionné","description":"Formats MCO 2026 avec empreinte et provenance."}]

@app.get("/health")
def health(): return {"status":"ok","service":"pmsi-analytics","mode":"local-first"}
@app.get("/overview")
def overview(): return {"import":IMPORT,"quality":QUALITY,"kpis":[{"label":"Séjours analysés","value":"18 420","trend":"+4,8 %","tone":"positive"},{"label":"Durée moyenne","value":"4,6 j","trend":"−0,3 j","tone":"positive"},{"label":"Taux de groupage","value":"97,2 %","trend":"+1,1 pt","tone":"positive"},{"label":"Alertes ouvertes","value":"31","trend":"7 critiques","tone":"negative"}],"monthly":[{"month":"Avr","value":62},{"month":"Mai","value":68},{"month":"Juin","value":65},{"month":"Juil","value":74},{"month":"Août","value":78},{"month":"Sept","value":86}]}
@app.get("/datasets")
def datasets(): return {"items":DATASETS,"total":len(DATASETS)}
@app.get("/quality")
def quality(): return {"items":QUALITY,"summary":{"score":92,"critical":7,"warnings":24}}
@app.get("/provenance")
def provenance(): return {"items":[{"step":"Source déposée","value":"pmsi_fixture_2026.csv","meta":"Fixture synthétique · locale","state":"done"},{"step":"Import et validation","value":"imp_2026_01","meta":"18 420 lignes · 00:01:42","state":"done"},{"step":"Normalisation","value":"sejours_normalises","meta":"DuckDB + Parquet","state":"done"},{"step":"Indicateur","value":"Tableau de bord DIM","meta":"Calculé à la demande","state":"current"}]}
class ImportRequest(BaseModel):
    url: HttpUrl | None = None
    filename: str = "formats_mco_2026.xlsx"

@app.post("/imports")
def create_import(request: ImportRequest):
    if request.url:
        parsed = urlparse(str(request.url))
        if parsed.scheme != "https": raise HTTPException(400, "La source ATIH doit utiliser HTTPS")
        try:
            response = httpx.get(str(request.url), timeout=20, follow_redirects=True)
            response.raise_for_status()
            digest = sha256(response.content).hexdigest()
            return {"message":"Référentiel téléchargé et versionné", "source":str(request.url), "filename":request.filename, "bytes":len(response.content), "sha256":digest, "status":"validated"}
        except httpx.HTTPError as exc: raise HTTPException(502, f"Téléchargement ATIH impossible: {exc}")
    return {"message":"Import local démarré", "import":IMPORT, "provenance":"fixture-synthetic"}

@app.get("/")
def root(): return {"service":"PMSI Analytics API","docs":"/docs"}
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
