"""Legacy entrypoint placeholder. Somba implementation is not included yet."""

import os

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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
