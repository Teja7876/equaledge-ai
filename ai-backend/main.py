from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
from litellm import completion

app = FastAPI()

# 🔐 API Key (change later)
API_KEY = "test123"

def verify_key(x_api_key: str = Header(None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")


class Req(BaseModel):
    text: str


@app.post("/ai")
def ai(req: Req, x_api_key: str = Header(None)):
    # 🔒 Verify API key
    verify_key(x_api_key)

    res = completion(
        model="gemini-1.5-flash",
        messages=[{"role": "user", "content": req.text}]
    )

    return {
        "result": res['choices'][0]['message']['content']
    }
