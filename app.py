import os, re
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from elasticsearch import Elasticsearch
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
app = FastAPI()

ES_CLOUD_ID = os.getenv("ES_CLOUD_ID")
ES_USER = os.getenv("ES_USER", "elastic")
ES_PASS = os.getenv("ES_PASS")
ES_INDEX = os.getenv("ES_INDEX", "jobs")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

es = Elasticsearch(cloud_id=ES_CLOUD_ID, basic_auth=(ES_USER, ES_PASS))
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

def parse_filters(q: str):
    ql = q.lower()
    remote = "remote" in ql
    m_state = re.search(r"\b(AL|AK|AZ|AR|CA|CO|CT|DE|FL|GA|HI|ID|IL|IN|IA|KS|KY|LA|ME|MD|MA|MI|MN|MS|MO|MT|NE|NV|NH|NJ|NM|NY|NC|ND|OH|OK|OR|PA|RI|SC|SD|TN|TX|UT|VT|VA|WA|WV|WI|WY)\b", q.upper())
    state = m_state.group(1) if m_state else None
    m_cap = re.search(r"under\s*\$?(\d{2,3}k|\d{5,6})", ql)
    salary_cap = int(m_cap.group(1).replace("k","000")) if m_cap else None
    return remote, state, salary_cap

@app.get("/", response_class=HTMLResponse)
def home():
    return """<!doctype html><meta charset="utf-8">
<title>AI Job Search Assistant</title>
<style>body{font:16px system-ui;margin:40px} #o{white-space:pre-wrap;border:1px solid #ddd;padding:12px;border-radius:10px;margin-top:12px}</style>
<h2>AI Job Search Assistant (Elastic + Gemini)</h2>
<p>Try: <code>Find me remote data analyst jobs in TX under $120k</code></p>
<input id=i style="width:80%" placeholder="Type your request..." />
<button onclick="send()">Send</button>
<div id=o></div>
<script>
async function send(){
  const v=document.getElementById('i').value;
  if(!v) return;
  document.getElementById('o').textContent="Thinking...";
  const r=await fetch('/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:v})});
  const j=await r.json();
  document.getElementById('o').textContent=j.answer || JSON.stringify(j);
}
</script>"""

@app.post("/chat")
async def chat(payload: dict):
    message = payload.get("message","")
    remote, state, salary_cap = parse_filters(message)
    must = [{"multi_match": {"query": message, "fields": ["title^3","description","location"]}}]
    filt = []
    if remote: filt.append({"term":{"remote": True}})
    if state:  filt.append({"term":{"state": state}})
    if salary_cap: filt.append({"range":{"salary_max":{"lte": salary_cap}}})
    query = {"bool":{"must": must, "filter": filt}}
    res = es.search(index=ES_INDEX, query=query, size=5)
    hits = [h["_source"] for h in res["hits"]["hits"]]

    ctx = "\n".join([
      f"- {x.get('title','')} at {x.get('company','')} "
      f"({('Remote' if x.get('remote') else (x.get('location') or x.get('state') or ''))}) "
      f"{'(up to $'+str(x.get('salary_max'))+')' if x.get('salary_max') else ''} — {x.get('url','')}"
      for x in hits
    ]) or "No matches."

    prompt = f"""User: {message}
Return a short list of up to 5 jobs (title, company, location/remote, salary if present, link). Use ONLY the items below. If no matches, say so and suggest a tweak.
Jobs:
{ctx}"""
    out = model.generate_content(prompt)
    return JSONResponse({"answer": out.text})
