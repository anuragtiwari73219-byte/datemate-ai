import os, json, itertools, re
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
import httpx

app = FastAPI(title="DateMate AI", description="Consent-based agent dating simulator")
app.mount("/static", StaticFiles(directory="static"), name="static")

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

DEMO_PEOPLE = [
("Aarav Mehta","designer","hiking, photography, indie music","honest communication, curiosity","weekend hikes and thoughtful conversations"),
("Diya Sharma","software engineer","reading, running, board games","kindness, humor, consistency","a quiet cafe and a long walk"),
("Kabir Singh","teacher","cooking, history podcasts, cycling","patience, openness, shared learning","cooking together and exploring museums"),
("Mira Kapoor","product manager","travel, films, volunteering","ambition, empathy, direct communication","trying a new restaurant and talking"),
("Rohan Verma","data analyst","football, sci-fi, coffee","humor, reliability, intellectual curiosity","a casual game and coffee"),
("Anaya Rao","illustrator","art galleries, plants, poetry","creativity, emotional maturity, kindness","an art walk and bookstore visit"),
("Ishaan Gupta","researcher","astronomy, documentaries, chess","curiosity, honesty, calm communication","stargazing and a relaxed conversation"),
("Sana Khan","founder","entrepreneurship, fitness, travel","drive, warmth, independence","a new activity and a good conversation"),
("Arjun Nair","chef","food markets, jazz, swimming","playfulness, respect, shared effort","cooking a new recipe together"),
("Tara Joshi","doctor","running, fiction, nature","compassion, reliability, balance","a park walk and a cozy cafe"),
("Neil Das","musician","guitar, live gigs, cycling","authenticity, patience, humor","a small live music show"),
("Ira Malhotra","lawyer","debates, theatre, travel","clear communication, fairness, curiosity","a play followed by a discussion"),
("Dev Patel","architect","urban design, sketching, trekking","creativity, dependability, openness","a city walk noticing architecture"),
("Meera Iyer","UX researcher","podcasts, pottery, badminton","empathy, curiosity, collaboration","a pottery class and tea"),
("Vivaan Shah","writer","short stories, films, cooking","thoughtfulness, humor, emotional openness","a bookstore and dinner"),
("Nisha Roy","environmental scientist","birdwatching, gardening, cycling","care, shared values, patience","a nature trail and picnic"),
("Aditya Bose","accountant","cricket, personal finance, films","stability, honesty, easygoing nature","a match and street food"),
("Zoya Ali","photographer","street photography, dance, travel","spontaneity, respect, warmth","a photo walk around the city"),
("Kunal Sethi","developer","open source, gaming, cycling","clear communication, kindness, curiosity","a board-game cafe"),
("Pooja Menon","nutritionist","yoga, cooking, beach walks","balance, compassion, consistency","making a healthy meal together"),
("Reyansh Kulkarni","musician","classical music, books, running","patience, sincerity, shared interests","a concert and a late coffee"),
("Aditi Sen","journalist","current affairs, theatre, hiking","honesty, curiosity, independence","a walk and a lively discussion"),
("Manav Bhatia","mechanical engineer","DIY projects, football, travel","teamwork, humor, dependability","trying an outdoor activity"),
("Kiara Fernandes","event planner","dance, design, food festivals","energy, kindness, flexibility","a local festival and dessert"),
("Samir Chawla","psychology student","volunteering, films, meditation","empathy, openness, respect","a quiet cafe and meaningful talk")
]

def slug(s): return re.sub(r'[^a-z0-9]+','-',s.lower()).strip('-')

people = []
for i, (name, role, interests, values, date_idea) in enumerate(DEMO_PEOPLE, 1):
    people.append({
        "id": f"demo-{i}", "name": name, "role": role,
        "linkedin": f"https://www.linkedin.com/in/demo-consented-{i}/",
        "instagram": f"https://www.instagram.com/demo-consented-{i}/",
        "interests": [x.strip() for x in interests.split(",")],
        "values": [x.strip() for x in values.split(",")],
        "date_idea": date_idea,
        "bio": f"Demo persona for testing only. {name} is a {role} who enjoys {interests}.",
        "source_mode": "demo persona (not a real person)",
        "analysis": f"{name} may connect well with someone who shares {interests} and values {values}.",
        "needs": values.split(","),
        "hobbies": interests.split(","),
    })

class ProfileIn(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    linkedin: str
    instagram: str
    role: str = ""
    interests: str = ""
    values: str = ""
    date_idea: str = ""
    bio: str = ""
    consent_confirmed: bool = False

class DateRequest(BaseModel):
    person_id: str
    candidate_id: str

async def llm(prompt: str) -> Optional[str]:
    if not GROQ_API_KEY:
        return None
    try:
        async with httpx.AsyncClient(timeout=25) as client:
            r = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type":"application/json"},
                json={"model": MODEL, "temperature": 0.7, "messages":[
                    {"role":"system","content":"You are an agent in a consent-based dating compatibility simulator. Use only the provided self-reported profile details. Do not infer sensitive traits. Be respectful, non-manipulative, and explain uncertainty."},
                    {"role":"user","content":prompt}
                ]}
            )
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]
    except Exception:
        return None

def overlap(a,b):
    A = set(x.strip().lower() for x in a if x.strip())
    B = set(x.strip().lower() for x in b if x.strip())
    return len(A & B), sorted(A & B)

def compatibility(a,b):
    shared, common = overlap(a.get("interests",[]), b.get("interests",[]))
    va, vc = overlap(a.get("values",[]), b.get("values",[]))
    # Transparent heuristic; score is a conversation-fit estimate, not a scientific prediction.
    score = min(98, 42 + shared*9 + va*11 + (8 if a.get("date_idea") and b.get("date_idea") else 0))
    reasons = []
    if common: reasons.append("Shared interests: " + ", ".join(common[:4]))
    if vc: reasons.append("Similar stated values: " + ", ".join(vc[:3]))
    if not reasons: reasons.append("Limited overlap in supplied details; a conversation could clarify fit.")
    return score, reasons

@app.get("/")
def home():
    return FileResponse("static/index.html")

@app.get("/api/people")
def get_people():
    return {"people": people, "demo_mode": True, "llm_enabled": bool(GROQ_API_KEY)}

@app.post("/api/people")
async def add_person(p: ProfileIn):
    if not p.consent_confirmed:
        raise HTTPException(400, "Please confirm the person has consented to be represented in this dating simulation.")
    if not p.linkedin.startswith("https://www.linkedin.com/") or not p.instagram.startswith("https://www.instagram.com/"):
        raise HTTPException(400, "Use official LinkedIn and Instagram profile URLs.")
    interests = [x.strip() for x in p.interests.split(",") if x.strip()]
    values = [x.strip() for x in p.values.split(",") if x.strip()]
    if not interests:
        raise HTTPException(400, "Add self-reported interests; this demo does not scrape social networks.")
    item = {
        "id": "user-" + str(len(people)+1), "name": p.name, "role": p.role,
        "linkedin": p.linkedin, "instagram": p.instagram,
        "interests": interests, "values": values,
        "date_idea": p.date_idea, "bio": p.bio,
        "source_mode": "consent-confirmed, user-provided details",
        "needs": values, "hobbies": interests,
        "analysis": f"{p.name}'s profile is based on the interests and values they supplied: {', '.join(interests)}. This is a tentative summary, not a claim about private traits."
    }
    prompt = f"Summarize this self-reported profile in 3 concise sentences. Include interests, stated values, and a respectful first-date idea. Return plain text.\nName: {p.name}\nRole: {p.role}\nInterests: {interests}\nValues: {values}\nDate idea: {p.date_idea}\nBio: {p.bio}"
    generated = await llm(prompt)
    if generated: item["analysis"] = generated
    people.append(item)
    return {"person": item, "llm_used": bool(generated)}

@app.post("/api/date")
async def date(req: DateRequest):
    a = next((x for x in people if x["id"] == req.person_id), None)
    b = next((x for x in people if x["id"] == req.candidate_id), None)
    if not a or not b: raise HTTPException(404, "Profile not found")
    if a["id"] == b["id"]: raise HTTPException(400, "An agent cannot date its own person.")
    score, reasons = compatibility(a,b)
    prompt = f"""Simulate a short first-date conversation between two fictionalized profile agents, speaking on behalf of consenting participants. 6-8 turns total, alternating Agent A and Agent B. They should ask respectful questions about shared interests and stated values, reveal possible differences, and end with a candid compatibility reflection. No claims of actual contact. Avoid private or sensitive inferences.
Agent A: {a['name']}; interests={a['interests']}; values={a['values']}; date idea={a['date_idea']}
Agent B: {b['name']}; interests={b['interests']}; values={b['values']}; date idea={b['date_idea']}
Return JSON with keys "conversation" (array of objects speaker,text) and "reflection" (string)."""
    result = await llm(prompt)
    if result:
        try:
            match = re.search(r'\{.*\}', result, re.S)
            parsed = json.loads(match.group(0) if match else result)
            conversation = parsed.get("conversation", [])
            reflection = parsed.get("reflection", "")
        except Exception:
            conversation = [{"speaker":"Agent A", "text":f"I noticed we both enjoy {', '.join(a['interests'][:2])}. What do you enjoy most about that?"},
                            {"speaker":"Agent B", "text":f"For me, {', '.join(b['interests'][:2])} are a great way to spend time. What would a good first date look like to you?"},
                            {"speaker":"Agent A", "text":a.get("date_idea") or "Something relaxed where we can talk."},
                            {"speaker":"Agent B", "text":b.get("date_idea") or "I would enjoy that. I'd also like to learn more about your interests."}]
            reflection = result
    else:
        shared, common = overlap(a["interests"], b["interests"])
        conversation = [
            {"speaker":f"{a['name']}'s agent","text":f"Hi! I represent {a['name']}. They enjoy {', '.join(a['interests'][:3])}. What interests would you most like to share with someone?"},
            {"speaker":f"{b['name']}'s agent","text":f"I represent {b['name']}. They are into {', '.join(b['interests'][:3])}. What does a comfortable first date look like for your person?"},
            {"speaker":f"{a['name']}'s agent","text":a.get("date_idea") or "They prefer a relaxed setting where conversation can flow."},
            {"speaker":f"{b['name']}'s agent","text":b.get("date_idea") or "They would like to choose something low-pressure and fun."},
            {"speaker":f"{a['name']}'s agent","text":("We share " + ", ".join(common[:3]) + ", which gives us a natural starting point.") if common else "Our listed interests differ, so we'd need to ask more questions rather than assume a fit."},
            {"speaker":f"{b['name']}'s agent","text":("Those shared interests sound promising. " if common else "Different interests can still work if our values align. ") + "What matters most to your person in communication?"},
            {"speaker":f"{a['name']}'s agent","text":("Their stated values include " + ", ".join(a["values"][:3]) + ".") if a["values"] else "We would need to ask them directly about their communication preferences."},
            {"speaker":"Joint reflection","text":"This is a tentative fit estimate based only on supplied profile details. The people should decide for themselves."}
        ]
        reflection = "The agents found " + (", ".join(common) if common else "no directly shared listed interests") + f". Heuristic compatibility estimate: {score}%. This score is not scientifically validated."
    return {"person":a["name"], "candidate":b["name"], "score":score, "reasons":reasons, "conversation":conversation, "reflection":reflection, "llm_used":bool(result)}

@app.get("/api/rankings/{person_id}")
def rankings(person_id: str):
    a = next((x for x in people if x["id"] == person_id), None)
    if not a: raise HTTPException(404, "Profile not found")
    rows = []
    for b in people:
        if b["id"] == a["id"]: continue
        score, reasons = compatibility(a,b)
        rows.append({"person":b, "score":score, "reasons":reasons})
    rows.sort(key=lambda x:x["score"], reverse=True)
    return {"person":a, "rankings":rows}

@app.get("/health")
def health():
    return {"status":"ok", "profiles":len(people), "llm_enabled":bool(GROQ_API_KEY)}
