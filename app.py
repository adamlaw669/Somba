from fastapi import FastAPI, Request

app = FastAPI()

@app.post("/webhooks/nomba")
async def nomba_webhook(request: Request):
    event = await request.json()
    print("Nomba event received:", event)
    return {"status": "received"}

@app.get("/")
async def health():
    return {"status": "Somba webhook is aliveee"}