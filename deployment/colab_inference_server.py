"""
Colab GPU Inference Server for MotherlyPulse (Chewie 1.2 + Baseline A/B)
Loads google/gemma-2-2b-it (4-bit NF4) + chewie_adapter/ from Google Drive,
serves GET /health, POST /generate, and POST /compare via FastAPI,
and exposes a temporary HTTPS URL via cloudflared.
"""

import os
import re
import subprocess
import threading
import time
from typing import Optional

import torch
import uvicorn
from fastapi import Depends, FastAPI, Header, HTTPException
from peft import PeftModel
from pydantic import BaseModel
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

MODEL_ID = "google/gemma-2-2b-it"
MODEL_REV = "299a8560bedf22ed1c72a8a11e7dce4a7f9f51f8"
ADAPTER_DIR = os.environ.get(
    "CHEWIE_ADAPTER_DIR",
    "/content/drive/MyDrive/MotherlyPulse_Chewie_1_2_Fresh/chewie_adapter",
)
API_KEY = os.environ.get("AI_MODEL_API_KEY", "").strip()
HF_TOKEN = os.environ.get("HF_TOKEN")

if not os.path.exists(ADAPTER_DIR):
    raise FileNotFoundError(
        f"Adapter directory not found at {ADAPTER_DIR}. Mount Google Drive first."
    )

tokenizer = AutoTokenizer.from_pretrained(ADAPTER_DIR)
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16,
    bnb_4bit_use_double_quant=True,
)
base_model = AutoModelForCausalLM.from_pretrained(
    MODEL_ID,
    revision=MODEL_REV,
    quantization_config=bnb_config,
    device_map="auto",
    token=HF_TOKEN,
)
model = PeftModel.from_pretrained(base_model, ADAPTER_DIR)
model.eval()
gen_lock = threading.Lock()


class QueryRequest(BaseModel):
    message: str
    urgency_category: str = "routine"
    language: str = "English"


def verify_auth(authorization: Optional[str] = Header(default=None)):
    if not API_KEY:
        return
    if authorization != f"Bearer {API_KEY}":
        raise HTTPException(status_code=401, detail="Unauthorized")


def build_prompt(message: str, language: str) -> str:
    user_text = (
        "You are MotherlyPulse, a maternal and child health assistant for Ondo State, Nigeria. "
        "Start your reply with EMERGENCY:, PRIORITY:, or ROUTINE:. "
        f"Reply in {language}.\n\nUser Question: {message.strip()}"
    )
    return tokenizer.apply_chat_template(
        [{"role": "user", "content": user_text}],
        tokenize=False,
        add_generation_prompt=True,
    )


def run_single(message: str, language: str, use_adapter: bool) -> dict:
    prompt_text = build_prompt(message, language)
    inputs = tokenizer(prompt_text, return_tensors="pt").to(model.device)
    t0 = time.time()
    with gen_lock:
        if use_adapter:
            with torch.no_grad():
                out = model.generate(**inputs, max_new_tokens=100, do_sample=False)
        else:
            with model.disable_adapter(), torch.no_grad():
                out = model.generate(**inputs, max_new_tokens=100, do_sample=False)
    latency_ms = round((time.time() - t0) * 1000, 2)
    gen_ids = out[0][inputs["input_ids"].shape[1]:]
    text = tokenizer.decode(gen_ids, skip_special_tokens=True).strip()
    return {"response": text, "latency_ms": latency_ms}


app = FastAPI(title="MotherlyPulse Chewie 1.2 Inference Server")


@app.get("/health")
def health():
    return {
        "status": "ok",
        "model_id": MODEL_ID,
        "model_revision": MODEL_REV,
        "adapter_dir": ADAPTER_DIR,
        "device": str(model.device),
    }


@app.post("/generate", dependencies=[Depends(verify_auth)])
def generate(req: QueryRequest):
    res = run_single(req.message, req.language, use_adapter=True)
    return {"response": res["response"], "latency_ms": res["latency_ms"], "model": "chewie-1.2-qlora"}


@app.post("/compare", dependencies=[Depends(verify_auth)])
def compare(req: QueryRequest):
    base_res = run_single(req.message, req.language, use_adapter=False)
    ft_res = run_single(req.message, req.language, use_adapter=True)
    return {"base": base_res, "finetuned": ft_res}


def start_server_and_tunnel(port: int = 8000):
    threading.Thread(
        target=lambda: uvicorn.run(app, host="0.0.0.0", port=port, log_level="warning"),
        daemon=True,
    ).start()
    time.sleep(2)
    proc = subprocess.Popen(
        ["cloudflared", "tunnel", "--url", f"http://localhost:{port}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    for line in proc.stdout:
        m = re.search(r"https://[a-z0-9-]+\.trycloudflare\.com", line)
        if m:
            print(f"PUBLIC AI_MODEL_ENDPOINT={m.group(0)}")
            break


if __name__ == "__main__":
    start_server_and_tunnel()
    while True:
        time.sleep(60)

