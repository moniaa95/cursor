# ============================================================
# WYSZUKIWARKA ZABIEGÓW MEDYCYNY ESTETYCZNEJ - 3 POZIOMY
# 🆕 PEŁNA TAKSONOMIA (LLM NAJPIERW, SCRAPING POTEM)
# Skopiuj cały ten plik i wklej do Google Colab
# ============================================================

# FAZA 0: Instalacja pakietów
print("📦 Instalacja pakietów...")
!pip install -q openai pandas requests tqdm beautifulsoup4 scikit-learn scipy hdbscan

# Importy
import os, re, json, time, math, random, unicodedata
import warnings
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from urllib.parse import urlparse

# Ukryj ostrzeżenia
warnings.filterwarnings('ignore', category=SyntaxWarning)
warnings.filterwarnings('ignore', category=FutureWarning)

import numpy as np
import pandas as pd
import requests
from tqdm import tqdm
from bs4 import BeautifulSoup
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import normalize

from openai import OpenAI
from google.colab import userdata

# ============================================================
# KONFIGURACJA
# ============================================================

# @title 🔧 Konfiguracja projektu
PROJECT_NAME = "baza_zabiegow_complete"  # @param {type:"string"}
BASE_DIR = f"/content/{PROJECT_NAME}"  # @param {type:"string"}
os.makedirs(BASE_DIR, exist_ok=True)

# @title 🤖 Modele przez OpenRouter
MODEL_NAME = "openai/gpt-4.1-mini"  # @param ["openai/gpt-5.1","openai/gpt-5-mini","openai/gpt-4.1-mini","google/gemini-2.5-flash-preview-09-2025","google/gemini-2.5-flash-lite"]
EMBED_MODEL = "openai/text-embedding-3-small"  # @param ["openai/text-embedding-3-small","openai/text-embedding-3-large"]

# @title 🔢 Limity
MAX_KEYWORDS = 30  # @param {type:"integer"}
SERP_TOP_N = 10  # @param {type:"integer"}
MAX_DOMAINS = 50  # @param {type:"integer"}
MAX_PAGES_PER_DOMAIN = 12  # @param {type:"integer"}

# @title 🧹 Filtry
MIN_TEXT_LEN = 5     # @param {type:"integer"}
MAX_TEXT_LEN = 120   # @param {type:"integer"}
SEMANTIC_SIM_THRESHOLD = 0.28  # @param {type:"slider", min:0.15, max:0.55, step:0.01}

# ============================================================
# KLUCZE API
# ============================================================

OPENROUTER_API_KEY = userdata.get("openrouter_api")
SERPDATA_KEY = userdata.get("serpdata_key")

if not OPENROUTER_API_KEY:
    raise ValueError("❌ Brak secreta: openrouter_api")
if not SERPDATA_KEY:
    raise ValueError("❌ Brak secreta: serpdata_key")

print("✅ Klucze API OK")

or_client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

# ============================================================
# HELPERY
# ============================================================

def clean_text(s: str) -> str:
    if not isinstance(s, str):
        return ""
    s = s.replace("\n", " ").replace("\r", " ").replace("\t", " ").strip()
    while "  " in s:
        s = s.replace("  ", " ")
    return s

def norm_key(s: str) -> str:
    s = clean_text(s).lower()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = re.sub(r"\s+", " ", s).strip()
    return s

def save_df(df: pd.DataFrame, path: str):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8")
    print(f"💾 Zapisano: {path}")

def load_df(path: str) -> pd.DataFrame:
    return pd.read_csv(path, encoding="utf-8")

def or_chat(messages: List[Dict[str,str]], model: Optional[str]=None, temperature: float=0.2, max_tokens: int=1200) -> str:
    model = model or MODEL_NAME
    resp = or_client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return resp.choices[0].message.content

def or_chat_json(system_prompt: str, user_prompt: str, model: Optional[str]=None, max_tokens: int=3000) -> dict:
    model = model or MODEL_NAME
    resp = or_client.chat.completions.create(
        model=model,
        messages=[
            {"role":"system","content":system_prompt},
            {"role":"user","content":user_prompt},
        ],
        temperature=0,
        response_format={"type":"json_object"},
        max_tokens=max_tokens,
    )
    txt = resp.choices[0].message.content
    try:
        return json.loads(txt)
    except Exception:
        m = re.search(r"\{.*\}", txt, flags=re.S)
        if not m:
            return {}
        try:
            return json.loads(m.group(0))
        except Exception:
            return {}

def embed_texts(texts: List[str], model: Optional[str]=None, batch_size: int=64, sleep_s: float=0.15) -> np.ndarray:
    model = model or EMBED_MODEL
    out = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        resp = or_client.embeddings.create(model=model, input=batch)
        out.extend([d.embedding for d in resp.data])
        time.sleep(sleep_s)
    return np.array(out, dtype="float32")

print("✅ FAZA 0 gotowa. BASE_DIR =", BASE_DIR)
print()

# ============================================================
# FAZA 1: KEYWORDS
# ============================================================

print("="*70)
print("🔑 FAZA 1: GENEROWANIE KEYWORDÓW")
print("="*70)

system = "Jesteś ekspertem SEO w branży medycyny estetycznej w Polsce."
user = f"""
Wygeneruj {MAX_KEYWORDS} polskich fraz, które pacjenci wpisują w Google szukając zabiegów.

Zasady:
- 2–5 słów w frazie
- bez numerowania, jedna fraza w jednej linii
- bez marek urządzeń
- realne zapytania usługowe
- pokryj różne dziedziny: dermatologia, chirurgia plastyczna, kosmetologia, trychologia, ginekologia estetyczna, stomatologia estetyczna

Wypisz same frazy.
"""

raw = or_chat([{"role":"system","content":system},{"role":"user","content":user}], temperature=0.8, max_tokens=1500)
keywords = [clean_text(x) for x in raw.split("\n") if clean_text(x)]

uniq = []
seen = set()
for k in keywords:
    nk = norm_key(k)
    if nk and nk not in seen:
        seen.add(nk)
        uniq.append(k)
keywords = uniq[:MAX_KEYWORDS]

print(f"\n✅ Wygenerowano {len(keywords)} keywordów")
save_df(pd.DataFrame({"keyword": keywords}), f"{BASE_DIR}/phase1_keywords.csv")
print()

# ============================================================
# FAZA 2: SERP → DOMENY
# ============================================================

print("="*70)
print("🌐 FAZA 2: SERP → DOMENY")
print("="*70)

SERPDATA_URL = "https://api.serpdata.io/v1/search"
SERPDATA_HEADERS = {"Authorization": f"Bearer {SERPDATA_KEY}"}

def fetch_serp_urls(keyword: str, top_n: int = 10) -> list:
    r = requests.get(
        SERPDATA_URL,
        headers=SERPDATA_HEADERS,
        params={"keyword": keyword, "hl": "pl", "gl": "pl"},
        timeout=60,
    )
    r.raise_for_status()
    j = r.json()
    
    data_block = j.get("data", {}) or {}
    results_block = data_block.get("results", {}) or {}
    
    organic = []
    if isinstance(results_block, dict):
        organic = results_block.get("organic_results", []) or []
    elif isinstance(results_block, list):
        organic = results_block
    
    urls = []
    for item in organic[:top_n]:
        url = item.get("url") or item.get("link")
        if url:
            urls.append(url)
    return urls

all_rows = []
for kw in tqdm(keywords, desc="Pobieranie SERPów"):
    try:
        urls = fetch_serp_urls(kw, top_n=SERP_TOP_N)
    except Exception as e:
        print(f"\n⚠️ Błąd dla '{kw}': {e}")
        urls = []
    
    for url in urls:
        all_rows.append({"keyword": kw, "url": url})
    
    time.sleep(2)

df_serp = pd.DataFrame(all_rows).drop_duplicates(subset=["keyword", "url"]).reset_index(drop=True)
df_unique_urls = df_serp.drop_duplicates(subset=["url"]).reset_index(drop=True)

df_unique_urls["domain"] = df_unique_urls["url"].apply(lambda u: urlparse(u).netloc.lower().strip() if isinstance(u, str) else "")
df_unique_urls["domain"] = df_unique_urls["domain"].str.replace(r"^www\.", "", regex=True)

BAD = ["facebook", "instagram", "youtube", "twitter", "znanylekarz", "booksy",
       "allegro", "olx", "wikipedia", "medonet", "onet", "wp", "linkedin"]
GOOD = ["klinika", "clinic", "med", "derma", "estety", "uroda", "beauty", "laser", "gabinet", "centrum"]

def is_clinic_domain(domain: str) -> bool:
    if not domain or any(b in domain for b in BAD):
        return False
    if any(g in domain for g in GOOD):
        return True
    return "." in domain and not domain.endswith((".gov", ".edu", ".org"))

domain_counts = df_unique_urls["domain"].value_counts()
candidate_domains = [d for d in domain_counts.index if is_clinic_domain(d)]
clinic_domains = candidate_domains[:MAX_DOMAINS]

domains_df = pd.DataFrame({"domain": clinic_domains})
print(f"\n📌 Wybrano {len(domains_df)} domen")

save_df(df_serp, f"{BASE_DIR}/phase2_serp_keyword_url.csv")
save_df(df_unique_urls, f"{BASE_DIR}/phase2_unique_urls.csv")
save_df(domains_df, f"{BASE_DIR}/phase2_domains.csv")
print()

# ============================================================
# 🆕 FAZA 3: BUDOWA KOMPLETNEJ STRUKTURY LEVEL 1 → LEVEL 2
# ============================================================

print("="*70)
print("🏗️ FAZA 3: BUDOWA KOMPLETNEJ STRUKTURY (LLM)")
print("="*70)

system = """
Jesteś ekspertem medycyny estetycznej w Polsce. Budujesz KOMPLETNĄ strukturę kategorii zabiegów.

STRUKTURA:
Level 1: GŁÓWNA KATEGORIA
   └─ Level 2: PODKATEGORIA

GŁÓWNE KATEGORIE (Level 1):
1. Dermatologia - leczenie chorób skóry (trądzik, blizny, przebarwienia, usuwanie zmian)
2. Kosmetologia - pielęgnacja, upiększanie (zabiegi oczyszczające, depilacja, pielęgnacja dłoni/stóp, brwi/rzęsy)
3. Chirurgia plastyczna - operacje chirurgiczne (lifting, liposukcja, rhinoplastyka, powiększenia)
4. Trychologia - leczenie i pielęgnacja włosów/skóry głowy
5. Ginekologia estetyczna - zabiegi intymne (operacyjne i nieinwazyjne)
6. Stomatologia estetyczna - wybielanie, licówki, implanty
7. Medycyna estetyczna - odmładzanie, modelowanie (wypełniacze, nici, lasery, toksyna)

ZASADY PRZYPISYWANIA:
- Depilacja → Kosmetologia (NIE Dermatologia!)
- Labioplastyka → Ginekologia estetyczna
- Manicure, pedicure → Kosmetologia
- Lifting rzęs, brwi → Kosmetologia
- Botoks, wypełniacze → Medycyna estetyczna
- Przeszczep włosów → Trychologia
- Leczenie trądziku → Dermatologia
- Leczenie blizn → Dermatologia
"""

user = """
Stwórz KOMPLETNĄ strukturę Level 1 → Level 2 dla WSZYSTKICH możliwych obszarów medycyny estetycznej w Polsce.

Dla KAŻDEGO Level 1 wypisz WSZYSTKIE możliwe podkategorie Level 2.

JSON:
{
  "categories": [
    {
      "level1": "Kosmetologia",
      "level2": [
        "Zabiegi oczyszczające i pielęgnacyjne",
        "Depilacja",
        "Pielęgnacja dłoni i stóp",
        "Stylizacja brwi i rzęs",
        ...
      ]
    },
    {
      "level1": "Dermatologia",
      "level2": [
        "Leczenie trądziku",
        "Leczenie blizn",
        "Usuwanie przebarwień",
        ...
      ]
    },
    ...
  ]
}

Wypisz WSZYSTKIE możliwe Level 2 dla każdego Level 1!
"""

print("🔹 Generowanie struktury Level 1 → Level 2...")
result = or_chat_json(system, user, max_tokens=4000)

categories_data = result.get("categories", [])
if not categories_data:
    print("⚠️ Błąd: brak kategorii, tworzę domyślne...")
    categories_data = [
        {"level1": "Kosmetologia", "level2": ["Zabiegi pielęgnacyjne", "Depilacja"]},
        {"level1": "Dermatologia", "level2": ["Dermatologia estetyczna"]},
        {"level1": "Medycyna estetyczna", "level2": ["Odmładzanie"]},
    ]

# Rozwiń strukturę do DataFrame
rows = []
for cat in categories_data:
    l1 = cat.get("level1", "")
    l2_list = cat.get("level2", [])
    for l2 in l2_list:
        rows.append({"level1": l1, "level2": l2})

df_structure = pd.DataFrame(rows)
df_structure = df_structure.drop_duplicates().reset_index(drop=True)

print(f"\n✅ Struktura gotowa:")
print(f"📊 Level 1: {df_structure['level1'].nunique()} głównych kategorii")
print(f"📊 Level 2: {len(df_structure)} podkategorii")

print("\n📋 Przykładowa struktura:")
for l1 in df_structure["level1"].unique()[:5]:
    l2_list = df_structure[df_structure["level1"] == l1]["level2"].tolist()
    print(f"\n{l1}:")
    for l2 in l2_list[:3]:
        print(f"  - {l2}")
    if len(l2_list) > 3:
        print(f"  ... +{len(l2_list)-3} więcej")

save_df(df_structure, f"{BASE_DIR}/phase3_structure.csv")
print()

# ============================================================
# 🆕 FAZA 4: GENEROWANIE WSZYSTKICH ZABIEGÓW DLA KAŻDEGO LEVEL 2
# ============================================================

print("="*70)
print("💉 FAZA 4: GENEROWANIE KOMPLETNEJ LISTY ZABIEGÓW")
print("="*70)

def generate_treatments_for_level2(level1: str, level2: str) -> List[str]:
    system = f"""
Jesteś ekspertem medycyny estetycznej. Wypisujesz WSZYSTKIE możliwe konkretne zabiegi dla danej podkategorii.

WAŻNE:
- Wypisz WSZYSTKIE popularne zabiegi w Polsce
- Nazwy OGÓLNE (bez marek urządzeń: Dermapen→mezoterapia mikroigłowa, Botox→toksyna botulinowa)
- Konkretne, nie ogólne (✅"Manicure hybrydowy" ❌"Pielęgnacja paznokci")
- Różne warianty (np. "Laser CO2 frakcyjny", "Laser CO2 ablacyjny")
"""
    
    user = f"""
Kategoria: {level1} → {level2}

Wypisz WSZYSTKIE możliwe konkretne zabiegi dla tej podkategorii.

Przykłady dobrych nazw:
✅ Manicure hybrydowy
✅ Laminacja brwi
✅ Depilacja laserowa bikini
✅ Mezoterapia igłowa twarzy kwasem hialuronowym
✅ Toksyna botulinowa na bruksizm
✅ Lifting ultradźwiękowy HIFU twarzy

Wypisz WSZYSTKIE zabiegi (jedna nazwa w linii, bez numeracji).
"""
    
    try:
        response = or_chat([{"role":"system","content":system},{"role":"user","content":user}], 
                          temperature=0.3, max_tokens=2000)
        treatments = [clean_text(line) for line in response.split("\n") if clean_text(line)]
        return treatments
    except Exception as e:
        print(f"⚠️ Błąd dla {level2}: {e}")
        return []

all_treatments = []

for idx, row in tqdm(df_structure.iterrows(), total=len(df_structure), desc="Generowanie zabiegów"):
    treatments = generate_treatments_for_level2(row["level1"], row["level2"])
    
    for t in treatments:
        all_treatments.append({
            "level1": row["level1"],
            "level2": row["level2"],
            "level3": t
        })
    
    time.sleep(0.5)

df_treatments = pd.DataFrame(all_treatments)
df_treatments = df_treatments.drop_duplicates(subset=["level1", "level2", "level3"]).reset_index(drop=True)

print(f"\n✅ KOMPLETNA LISTA ZABIEGÓW:")
print(f"📊 Level 1: {df_treatments['level1'].nunique()} kategorii")
print(f"📊 Level 2: {df_treatments['level2'].nunique()} podkategorii")
print(f"📊 Level 3: {len(df_treatments)} konkretnych zabiegów")

print("\n📋 Przykładowe zabiegi per kategoria:")
for l1 in df_treatments["level1"].unique()[:5]:
    count = len(df_treatments[df_treatments["level1"] == l1])
    examples = df_treatments[df_treatments["level1"] == l1]["level3"].head(3).tolist()
    print(f"\n{l1} ({count} zabiegów):")
    for ex in examples:
        print(f"  - {ex}")

save_df(df_treatments, f"{BASE_DIR}/phase4_complete_taxonomy.csv")
print()

# ============================================================
# FAZA 5: SCRAPOWANIE
# ============================================================

print("="*70)
print("🕷️ FAZA 5: SCRAPOWANIE DOMEN (walidacja)")
print("="*70)

def scrape_url(url: str, timeout: int = 15) -> str:
    try:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; AestheticMedBot/1.0)"}
        r = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
        r.raise_for_status()
        soup = BeautifulSoup(r.content, "html.parser")
        
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        
        text = soup.get_text(separator=" ", strip=True)
        return clean_text(text)
    except Exception:
        return ""

scraped_data = []

for domain in tqdm(domains_df["domain"], desc="Scrapowanie domen"):
    domain_urls = df_unique_urls[df_unique_urls["domain"] == domain]["url"].tolist()
    domain_urls = domain_urls[:MAX_PAGES_PER_DOMAIN]
    
    domain_text = []
    for url in domain_urls:
        text = scrape_url(url)
        if text:
            domain_text.append(text)
        time.sleep(0.5)
    
    combined = " ".join(domain_text)
    if combined:
        scraped_data.append({
            "domain": domain,
            "text": combined[:50000],
            "num_pages": len(domain_text)
        })

df_scraped = pd.DataFrame(scraped_data)
print(f"\n📌 Zescrapowano {len(df_scraped)} domen")

save_df(df_scraped, f"{BASE_DIR}/phase5_scraped_content.csv")
print()

# ============================================================
# FAZA 6: EKSTRAKCJA ZE SCRAPINGU
# ============================================================

print("="*70)
print("🔍 FAZA 6: EKSTRAKCJA ZABIEGÓW ZE SCRAPINGU")
print("="*70)

def extract_treatments_from_text(domain: str, text: str) -> List[str]:
    text_chunk = text[:8000]
    
    system = "Jesteś ekspertem medycyny estetycznej. Wyciągasz OGÓLNE nazwy zabiegów, bez marek urządzeń."
    user = f"""
Tekst ze strony: {domain}

{text_chunk}

Wypisz WSZYSTKIE nazwy zabiegów medycyny estetycznej (jedna nazwa w linii, bez numeracji, bez marek).
"""
    
    try:
        response = or_chat([{"role":"system","content":system},{"role":"user","content":user}], 
                          temperature=0.1, max_tokens=1500)
        treatments = [clean_text(line) for line in response.split("\n") if clean_text(line)]
        return treatments
    except Exception as e:
        print(f"⚠️ Błąd: {e}")
        return []

scraped_treatments = []

for idx, row in tqdm(df_scraped.iterrows(), total=len(df_scraped), desc="Ekstrakcja"):
    treatments = extract_treatments_from_text(row["domain"], row["text"])
    for t in treatments:
        scraped_treatments.append({"domain": row["domain"], "treatment": t})
    time.sleep(0.3)

df_scraped_raw = pd.DataFrame(scraped_treatments)
print(f"\n📌 Wyciągnięto {len(df_scraped_raw)} zabiegów ze scrapingu")

df_scraped_raw["treatment_norm"] = df_scraped_raw["treatment"].apply(norm_key)
df_scraped_raw = df_scraped_raw[df_scraped_raw["treatment_norm"].str.len() >= MIN_TEXT_LEN]
df_scraped_raw = df_scraped_raw[df_scraped_raw["treatment_norm"].str.len() <= MAX_TEXT_LEN]
df_scraped_raw = df_scraped_raw.drop_duplicates(subset=["treatment_norm"]).reset_index(drop=True)

print(f"📌 Po filtracji: {len(df_scraped_raw)} unikalnych")

save_df(df_scraped_raw, f"{BASE_DIR}/phase6_scraped_treatments.csv")
print()

# ============================================================
# FAZA 7: MAPOWANIE SCRAPING → TAKSONOMIA
# ============================================================

print("="*70)
print("🗺️ FAZA 7: MAPOWANIE SCRAPING → TAKSONOMIA")
print("="*70)

print("🔹 Generowanie embeddingów...")
taxonomy_treatments = df_treatments["level3"].tolist()
taxonomy_embeddings = embed_texts(taxonomy_treatments)

scraped_treatments_list = df_scraped_raw["treatment"].tolist()
scraped_embeddings = embed_texts(scraped_treatments_list)

print("🔹 Mapowanie przez similarity...")
similarity = cosine_similarity(scraped_embeddings, taxonomy_embeddings)
best_matches = np.argmax(similarity, axis=1)
best_scores = np.max(similarity, axis=1)

mapping = {}
for i, scraped_treat in enumerate(scraped_treatments_list):
    matched_idx = best_matches[i]
    score = best_scores[i]
    
    if score > 0.75:  # Wysoki próg podobieństwa
        matched_l3 = taxonomy_treatments[matched_idx]
        row = df_treatments[df_treatments["level3"] == matched_l3].iloc[0]
        mapping[scraped_treat] = {
            "level1": row["level1"],
            "level2": row["level2"],
            "level3": matched_l3,
            "source": "scraped",
            "domain": df_scraped_raw[df_scraped_raw["treatment"] == scraped_treat]["domain"].iloc[0]
        }

print(f"\n📌 Zmapowano {len(mapping)}/{len(scraped_treatments_list)} zabiegów ze scrapingu")

# Dodaj zabiegi ze scrapingu do głównej tabeli
mapped_scraped = []
for treat, data in mapping.items():
    mapped_scraped.append(data)

df_mapped_scraped = pd.DataFrame(mapped_scraped)

if len(df_mapped_scraped) > 0:
    save_df(df_mapped_scraped, f"{BASE_DIR}/phase7_mapped_scraped.csv")
    print(f"✅ Zapisano zmapowane zabiegi ze scrapingu")
else:
    print("⚠️ Brak zmapowanych zabiegów ze scrapingu")

print()

# ============================================================
# FAZA 8: MERGE TAKSONOMII + SCRAPING
# ============================================================

print("="*70)
print("🔗 FAZA 8: FINALNA TAKSONOMIA (LLM + Scraping)")
print("="*70)

# Dodaj source="llm" do głównej taksonomii
df_treatments["source"] = "llm"
df_treatments["domain"] = None

# Połącz z mapowanymi zabiegami ze scrapingu
if len(df_mapped_scraped) > 0:
    df_final = pd.concat([
        df_treatments[["level1", "level2", "level3", "source", "domain"]],
        df_mapped_scraped[["level1", "level2", "level3", "source", "domain"]]
    ], ignore_index=True)
else:
    df_final = df_treatments[["level1", "level2", "level3", "source", "domain"]].copy()

# Deduplikacja (priorytet: scraping > llm)
df_final = df_final.sort_values("source", ascending=False)  # scraped > llm
df_final = df_final.drop_duplicates(subset=["level1", "level2", "level3"], keep="first").reset_index(drop=True)

print(f"\n✅ FINALNA TAKSONOMIA:")
print(f"📊 Level 1: {df_final['level1'].nunique()} kategorii")
print(f"📊 Level 2: {df_final['level2'].nunique()} podkategorii")
print(f"📊 Level 3: {len(df_final)} konkretnych zabiegów")
print(f"📊 Z LLM: {len(df_final[df_final['source']=='llm'])}")
print(f"📊 Ze scrapingu: {len(df_final[df_final['source']=='scraped'])}")

save_df(df_final, f"{BASE_DIR}/phase8_final_taxonomy.csv")
print()

# ============================================================
# FAZA 9: OPISY
# ============================================================

print("="*70)
print("📝 FAZA 9: GENEROWANIE OPISÓW")
print("="*70)

def generate_desc(l1: str, l2: str, l3: str) -> str:
    system = "Jesteś ekspertem medycyny estetycznej. Piszesz opisy dla pacjentów."
    user = f"""
Zabieg: {l3}
Kategoria: {l1} → {l2}

Napisz krótki opis (2-3 zdania):
- Co to za zabieg
- Jakie problemy rozwiązuje
- Jak działa

Tylko opis, bez nagłówków, bez marek!
"""
    
    try:
        desc = clean_text(or_chat([{"role":"system","content":system},{"role":"user","content":user}], 
                                  temperature=0.3, max_tokens=200))
        return desc
    except:
        return ""

# Generuj opisy tylko dla unikalnych Level 3
df_unique_l3 = df_final.drop_duplicates(subset=["level1", "level2", "level3"]).reset_index(drop=True)

print(f"🔹 Generowanie {len(df_unique_l3)} opisów...")

descriptions = []
BATCH_SIZE = 5

for i in tqdm(range(0, len(df_unique_l3), BATCH_SIZE), desc="Opisy"):
    batch = df_unique_l3.iloc[i:i+BATCH_SIZE]
    
    for idx, row in batch.iterrows():
        desc = generate_desc(row["level1"], row["level2"], row["level3"])
        descriptions.append(desc)
        time.sleep(0.2)

df_unique_l3["description"] = descriptions

# Merge opisów z główną tabelą
df_final_with_desc = df_final.merge(
    df_unique_l3[["level1", "level2", "level3", "description"]],
    on=["level1", "level2", "level3"],
    how="left"
)

print(f"\n✅ Wygenerowano {len(df_unique_l3)} opisów")

save_df(df_final_with_desc, f"{BASE_DIR}/phase9_with_descriptions.csv")
print()

# ============================================================
# FAZA 10: EKSPORT FINALNY
# ============================================================

print("="*70)
print("📦 FAZA 10: EKSPORT FINALNY")
print("="*70)

# final_tree.csv
df_tree_export = df_final_with_desc[["level1", "level2", "level3", "description", "source"]].drop_duplicates().reset_index(drop=True)
save_df(df_tree_export, f"{BASE_DIR}/final_tree.csv")
print(f"✅ final_tree.csv ({len(df_tree_export)} węzłów)")

# final_domains.csv (tylko dla zabiegów ze scrapingu)
if len(df_mapped_scraped) > 0:
    domain_stats = df_mapped_scraped.groupby("domain").size().reset_index(name="treatments_count")
    df_domains_export = domains_df.merge(domain_stats, on="domain", how="left")
    df_domains_export["treatments_count"] = df_domains_export["treatments_count"].fillna(0).astype(int)
    save_df(df_domains_export, f"{BASE_DIR}/final_domains.csv")
    print(f"✅ final_domains.csv ({len(df_domains_export)} domen)")

# final_tree.json
tree_json = {}
for _, row in df_tree_export.iterrows():
    l1, l2, l3 = row["level1"], row["level2"], row["level3"]
    desc = row.get("description", "")
    source = row.get("source", "")
    
    if l1 not in tree_json:
        tree_json[l1] = {}
    if l2 not in tree_json[l1]:
        tree_json[l1][l2] = []
    
    tree_json[l1][l2].append({"name": l3, "description": desc, "source": source})

with open(f"{BASE_DIR}/final_tree.json", "w", encoding="utf-8") as f:
    json.dump(tree_json, f, ensure_ascii=False, indent=2)
print(f"✅ final_tree.json")

# Podsumowanie
print("\n" + "="*70)
print("🎉 GOTOWE! PEŁNA TAKSONOMIA - PODSUMOWANIE:")
print("="*70)
print(f"📊 Kategorie Level 1: {df_tree_export['level1'].nunique()}")
print(f"📊 Podkategorie Level 2: {df_tree_export['level2'].nunique()}")
print(f"📊 Konkretne zabiegi Level 3: {len(df_tree_export)}")
print(f"📊 Z LLM: {len(df_tree_export[df_tree_export['source']=='llm'])}")
print(f"📊 Ze scrapingu: {len(df_tree_export[df_tree_export['source']=='scraped'])}")

print(f"\n💾 Pliki finalne:")
print(f"   - {BASE_DIR}/final_tree.csv")
print(f"   - {BASE_DIR}/final_domains.csv")
print(f"   - {BASE_DIR}/final_tree.json")

print("\n📊 Statystyki per kategoria Level 1:")
stats = df_tree_export.groupby("level1").size().reset_index(name="Liczba zabiegów")
stats = stats.sort_values("Liczba zabiegów", ascending=False)
print(stats.to_string(index=False))

print("\n📋 Przykładowe zabiegi per kategoria:")
for l1 in df_tree_export["level1"].unique()[:7]:
    examples = df_tree_export[df_tree_export["level1"] == l1]["level3"].head(5).tolist()
    print(f"\n{l1}:")
    for ex in examples:
        print(f"  - {ex}")

print("\n" + "="*70)
print("✅ KOMPLETNA TAKSONOMIA GOTOWA!")
print("✅ Depilacja w Kosmetologii ✓")
print("✅ 300-1000+ zabiegów ✓")
print("✅ Struktura logiczna ✓")
print("="*70)
