from fastapi import FastAPI

app = FastAPI(title="Smart Fridge API")

@app.get("/health")
def health():
    return {"status": "ok"}