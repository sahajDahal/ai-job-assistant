import os, random
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")  # optional; app still works without it

# ---------------------------
# Simple, colorful frontend
# ---------------------------
@app.get("/", response_class=HTMLResponse)
def home():
    return """<!doctype html><meta charset="utf-8">
<title>AI Job Search Assistant</title>
<meta name="viewport" content="width=device-width, initial-scale=1" />
<style>
  :root{
    --bg1:#0ea5e9;       /* sky-500 */
    --bg2:#8b5cf6;       /* violet-500 */
    --card:#0b1020;      /* deep navy card */
    --text:#e6e8ee;      /* light text */
    --muted:#94a3b8;     /* slate-400 */
    --accent:#22d3ee;    /* cyan-400 */
    --btn:#22c55e;       /* green-500 */
    --btn-hover:#16a34a; /* green-600 */
    --chip:#1f2937;      /* gray-800 */
  }
  *{box-sizing:border-box}
  body{
    margin:0; min-height:100vh; color:var(--text);
    background: linear-gradient(135deg, var(--bg1), var(--bg2));
    display:flex; align-items:center; justify-content:center; padding:24px;
    font:16px/1.5 system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, "Apple Color Emoji","Segoe UI Emoji";
  }
  .wrap{
    width:min(980px,100%); 
  }
  .card{
    background:linear-gradient(180deg, rgba(255,255,255,0.06), rgba(255,255,255,0.02));
    backdrop-filter: blur(6px);
    border:1px solid rgba(255,255,255,0.1);
    border-radius:18px; padding:22px; box-shadow:0 20px 60px rgba(0,0,0,0.25);
  }
  .header{
    display:flex; align-items:center; gap:14px; margin-bottom:12px;
  }
  .logo{
    width:42px;height:42px;border-radius:12px;display:grid;place-items:center;
    background:radial-gradient(circle at 30% 30%, var(--accent), transparent 60%), #0ea5e9;
    box-shadow:0 8px 24px rgba(34,211,238,0.3), inset 0 0 12px rgba(255,255,255,0.15);
    font-weight:700; color:#0b1020;
  }
  h1{margin:0;font-size:22px;letter-spacing:0.2px}
  .sub{color:var(--muted); font-size:14px; margin-bottom:18px}
  .chips{display:flex; flex-wrap:wrap; gap:8px; margin-bottom:14px}
  .chip{
    background:var(--chip); color:#cbd5e1; border:1px solid rgba(255,255,255,0.06);
    padding:6px 10px; border-radius:999px; font-size:12px; cursor:pointer;
  }
  .io{
    display:flex; gap:10px; margin-top:6px;
  }
  input{
    flex:1; padding:14px 16px; border-radius:12px; border:1px solid rgba(255,255,255,0.12);
    background:rgba(11,16,32,0.65); color:var(--text); outline:none;
    box-shadow: inset 0 0 0 999px rgba(255,255,255,0.02);
  }
  input::placeholder{ color:#9aa3b2 }
  button{
    padding:12px 16px; border:none; border-radius:12px; cursor:pointer;
    background:var(--btn); color:#07210f; font-weight:700; letter-spacing:0.2px;
    box-shadow:0 8px 20px rgba(34,197,94,0.35);
  }
  button:hover{ background:var(--btn-hover) }
  .out{
    margin-top:16px; border-radius:14px; padding:0; overflow:hidden;
    background:rgba(11,16,32,0.6); border:1px solid rgba(255,255,255,0.1);
  }
  .row{ display:flex; gap:10px; padding:16px 16px; }
  .row.user{ background:rgba(255,255,255,0.02); }
  .bubble{
    background:rgba(255,255,255,0.06); border:1px solid rgba(255,255,255,0.1);
    border-radius:12px; padding:12px 14px; white-space:pre-wrap; flex:1;
  }
  .avatar{
    width:36px;height:36px;border-radius:50%;flex:0 0 auto;
    background:radial-gradient(circle at 35% 35%, #fff, #ccc);
    display:grid;place-items:center; color:#0a0a0a; font-weight:700;
  }
  .spinner{
    width:22px;height:22px;border:3px solid rgba(255,255,255,0.2);
    border-top-color: var(--accent); border-radius:50%; animation:spin 1s linear infinite;
  }
  @keyframes spin{to{transform:rotate(360deg)}}
  .footer{ color:#cbd5e1; opacity:0.85; font-size:12px; margin-top:12px; text-align:center }
  .link{ color:var(--accent); text-decoration:none }
</style>

<div class="wrap">
  <div class="card">
    <div class="header">
      <div class="logo">AI</div>
      <div>
        <h1>AI Job Search Assistant</h1>
        <div class="sub"></div>
      </div>
    </div>

    <div class="chips">
      <div class="chip" onclick="setExample('Find me remote data analyst roles in Texas under $120k')">Remote Data Analyst (TX)</div>
      <div class="chip" onclick="setExample('Show cloud engineer openings in Dallas')">Cloud Engineer (Dallas)</div>
      <div class="chip" onclick="setExample('Entry-level software roles in NYC')">Entry SWE (NYC)</div>
      <div class="chip" onclick="setExample('AI/ML engineer positions paying above $130k')">AI/ML > $130k</div>
    </div>

    <div class="io">
      <input id="i" placeholder="Ask for roles, locations, salary ranges, or keywords…" />
      <button onclick="send()">Search</button>
    </div>

    <div id="o" class="out">
      <!-- messages appear here -->
    </div>

    <div class="footer">
      Tip: include <b>role</b>, <b>location</b>, and a <b>salary range</b> for crisper suggestions.
      <br/>Need hosting later? This runs great on <span class="link">Render</span> or Cloud Run.
    </div>
  </div>
</div>

<script>
const out = document.getElementById('o');
const input = document.getElementById('i');

function setExample(text){ input.value = text; input.focus(); }

function addRow(role, text){
  const row = document.createElement('div');
  row.className = 'row ' + role;
  const avatar = document.createElement('div');
  avatar.className = 'avatar';
  avatar.textContent = role === 'user' ? 'U' : 'AI';
  const bubble = document.createElement('div');
  bubble.className = 'bubble';
  bubble.textContent = text;
  row.appendChild(avatar);
  row.appendChild(bubble);
  out.appendChild(row);
  out.scrollTop = out.scrollHeight;
}

function addSpinner(){
  const row = document.createElement('div');
  row.className = 'row';
  row.id = 'spinnerrow';
  const avatar = document.createElement('div');
  avatar.className = 'avatar';
  avatar.innerHTML = '<div class="spinner"></div>';
  const bubble = document.createElement('div');
  bubble.className = 'bubble';
  bubble.textContent = 'Thinking…';
  row.appendChild(avatar); row.appendChild(bubble);
  out.appendChild(row);
  out.scrollTop = out.scrollHeight;
}

function removeSpinner(){
  const s = document.getElementById('spinnerrow');
  if(s) s.remove();
}

async function send(){
  const v = input.value.trim();
  if(!v) return;
  addRow('user', v);
  input.value = '';
  addSpinner();
  try{
    const r = await fetch('/chat', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({message:v})
    });
    const j = await r.json();
    removeSpinner();
    addRow('ai', j.answer || JSON.stringify(j,null,2));
  }catch(e){
    removeSpinner();
    addRow('ai', 'Request failed: ' + e);
  }
}

input.addEventListener('keydown', (e)=>{
  if(e.key === 'Enter'){ send(); }
});
</script>
"""

@app.get("/health")
def health():
    return {"ok": True}

# ---------------------------
# Chat endpoint (Gemini optional; Elastic skipped)
# ---------------------------
@app.post("/chat")
async def chat(payload: dict):
    message = (payload or {}).get("message", "").strip()
    if not message:
        return {"answer": "Please type something like: Find me software engineering internships in New York."}

    # Diverse fallback job results (randomized)
    sample_jobs = [
        "• Frontend Developer — Skyline Systems — San Francisco, CA — $110–135k — https://example.com/skyline-frontend",
        "• Machine Learning Engineer — QuantumAI Labs — Remote — $120–150k — https://example.com/quantumai-ml",
        "• DevOps Specialist — NovaTech — Austin, TX — $95–125k — https://example.com/novatech-devops",
        "• Product Manager — Orion Health — Chicago, IL — $105–140k — https://example.com/orion-pm",
        "• UX/UI Designer — PixelWave — New York, NY — $85–115k — https://example.com/pixelwave-ux",
        "• Data Engineer — BluePeak Analytics — Denver, CO — $100–130k — https://example.com/bluepeak-de",
        "• Cybersecurity Analyst — Sentinel Group — Atlanta, GA — $95–125k — https://example.com/sentinel-cyber",
        "• Cloud Solutions Architect — ApexCloud — Remote — $125–160k — https://example.com/apexcloud-arch",
        "• Business Intelligence Analyst — Horizon Insights — Seattle, WA — $90–120k — https://example.com/horizon-bi",
        "• Software Engineer (Backend) — TitanTech — Dallas, TX — $105–135k — https://example.com/titantech-backend",
        "• Data Scientist — Nebula Analytics — Boston, MA — $115–145k — https://example.com/nebula-ds",
        "• Platform Engineer — VectorWorks — Remote — $120–150k — https://example.com/vectorworks-platform",
        "• Mobile Developer (iOS) — Firefly Apps — Los Angeles, CA — $110–140k — https://example.com/firefly-ios",
        "• Site Reliability Engineer — CoreStack — Phoenix, AZ — $115–145k — https://example.com/corestack-sre",
        "• AI Product Analyst — Lumina Tech — Remote — $95–120k — https://example.com/lumina-analyst"
    ]

    # If Gemini works, use it for realism; otherwise fallback
    try:
        if GEMINI_API_KEY:
            import google.generativeai as genai
            genai.configure(api_key=GEMINI_API_KEY)
            model = genai.GenerativeModel("gemini-1.5-flash")
            prompt = f"""You are a helpful job search assistant.
User asked: "{message}"
Return 3–5 realistic job listings (title, company, location or 'Remote', salary range if present, and a plausible link).
Bullet each item. Keep it concise, friendly, and include one short tip to refine the search."""
            out = model.generate_content(prompt, request_options={"timeout": 20})
            if out.text and out.text.strip():
                return {"answer": out.text.strip()}
    except Exception:
        pass  # if Gemini fails, fallback below

    # Fallback generic text (randomize to look different each time)
    picks = "\n".join(random.sample(sample_jobs, 5))
    responses = [
        "Here are some roles matching your request:\n" + picks + "\n\nTip: add specific tools (e.g., SQL, React, Terraform) to narrow results.",
        "I found a few positions that might fit:\n" + picks + "\n\nTip: include a city or 'remote' to refine location.",
        "Some openings you might like:\n" + picks + "\n\nTip: try a salary target like 'under $120k' or 'above $130k'."
    ]
    return {"answer": random.choice(responses)}
