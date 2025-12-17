# ============================================================
# WYSZUKIWARKA ZABIEGÓW MEDYCYNY ESTETYCZNEJ - 3 POZIOMY
# 🆕 WERSJA POPRAWIONA - bez marek urządzeń!
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
import hdbscan

from openai import OpenAI
from google.colab import userdata

# ============================================================
# KONFIGURACJA
# ============================================================

# @title 🔧 Konfiguracja projektu
PROJECT_NAME = "baza_zabiegow_3level"  # @param {type:"string"}
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
SEMANTIC_SIM_THRESHOLD = 0.30  # @param {type:"slider", min:0.15, max:0.55, step:0.01}

# @title 🔧 Jina rerank (opcjonalnie)
USE_JINA = True  # @param {type:"boolean"}
JINA_RERANK_THRESHOLD = 0.25  # @param {type:"slider", min:0.15, max:0.75, step:0.01}

# ============================================================
# SŁOWNIK MAREK (do czyszczenia)
# ============================================================

BRAND_REPLACEMENTS = {
    # Urządzenia do mezoterapii/mikronakłuwania
    "dermapen": "mezoterapia mikroigłowa",
    "dermaroller": "mezoterapia mikroigłowa rollerem",
    "aquagold": "mezoterapia mikrokanałowa",
    
    # Lasery
    "picosure": "laser pikosekundowy",
    "picoway": "laser pikosekundowy",
    "fraxel": "laser frakcyjny",
    "co2re": "laser CO2",
    "smartxide": "laser CO2",
    "nd:yag": "laser neodymowy",
    
    # Wypełniacze
    "juvederm": "wypełnienie kwasem hialuronowym",
    "restylane": "wypełnienie kwasem hialuronowym",
    "stylage": "wypełnienie kwasem hialuronowym",
    "belotero": "wypełnienie kwasem hialuronowym",
    "teosyal": "wypełnienie kwasem hialuronowym",
    "radiesse": "wypełnienie hydroksyapatytem wapnia",
    "ellanse": "wypełnienie stymulujące kolagen",
    "sculptra": "stymulacja kolagenem",
    
    # Toksyna botulinowa
    "botox": "toksyna botulinowa",
    "bocouture": "toksyna botulinowa",
    "azzalure": "toksyna botulinowa",
    "dysport": "toksyna botulinowa",
    "xeomin": "toksyna botulinowa",
    
    # Peelingi
    "prx-t33": "peeling biorewitalizujący",
    "prx t33": "peeling biorewitalizujący",
    "pca skin": "peeling chemiczny",
    "obagi": "peeling chemiczny",
    "mesoestetic": "peeling chemiczny",
    
    # Zabiegi naczyniowe
    "veneseal": "endowaskularne zamykanie żył klejem",
    "vnus": "ablacja żył radiofrekwencją",
    "venaseal": "endowaskularne zamykanie żył klejem",
    
    # Zabiegi pielęgnacyjne
    "geneo": "oksybrazja skóry",
    "hydrafacial": "zabieg oczyszczająco-nawilżający",
    "aquapure": "oczyszczanie wodorowe",
    "dermalogica": "zabieg pielęgnacyjny",
    "icoone": "masaż próżniowy",
    
    # Urządzenia do ciała
    "coolsculpting": "kriolipoliza",
    "clatuu": "kriolipoliza",
    "cristal": "kriolipoliza",
    "vanquish": "redukcja tkanki tłuszczowej falami RF",
    "emsculpt": "stymulacja elektromagnetyczna mięśni",
    "emsella": "stymulacja mięśni dna miednicy",
    
    # HIFU
    "ultherapy": "lifting ultradźwiękowy HIFU",
    "ultraformer": "lifting HIFU",
    "doublo": "lifting HIFU",
    
    # RF
    "thermage": "lifting radiofrekwencyjny",
    "profound": "lifting radiofrekwencyjny mikroigłowy",
    "infini": "radiofrekwencja mikroigłowa",
    "endymed": "radiofrekwencja",
    "venus freeze": "radiofrekwencja z pulsami magnetycznymi",
    
    # Nici
    "silhouette soft": "nici liftingujące", 
    "aptos": "nici liftingujące",
    "happy lift": "nici liftingujące",
    
    # Mezoterapia/biorewitalizacja
    "nucleofill": "biorewitalizacja polinukleotydami",
    "profhilo": "biorewitalizacja kwasem hialuronowym",
    "jalupro": "biorewitalizacja peptydami",
    "redensity": "biorewitalizacja",
    "dives med": "mesoterapia ampułkowa",
    
    # Inne
    "platelet-rich plasma": "osocze bogatopłytkowe",
    "prp": "osocze bogatopłytkowe",
}

# ============================================================
# KLUCZE API
# ============================================================

OPENROUTER_API_KEY = userdata.get("openrouter_api")
SERPDATA_KEY = userdata.get("serpdata_key")
JINA_API_KEY = userdata.get("jina_api")

if not OPENROUTER_API_KEY:
    raise ValueError("❌ Brak secreta: openrouter_api")
if not SERPDATA_KEY:
    raise ValueError("❌ Brak secreta: serpdata_key")
if USE_JINA and not JINA_API_KEY:
    print("⚠️ Brak jina_api → wyłączam Jina.")
    USE_JINA = False

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

def remove_brands(text: str) -> str:
    """Usuwa nazwy marek i zamienia na ogólne nazwy zabiegów."""
    if not isinstance(text, str):
        return text
    
    text_lower = text.lower()
    result = text
    
    for brand, replacement in BRAND_REPLACEMENTS.items():
        # Sprawdź czy marka występuje w tekście
        if brand in text_lower:
            # Zamień zachowując wielkość liter pierwszego słowa
            pattern = re.compile(re.escape(brand), re.IGNORECASE)
            # Sprawdź czy to początek zdania (wielka litera)
            if text[0].isupper():
                replacement = replacement[0].upper() + replacement[1:]
            result = pattern.sub(replacement, result)
            text_lower = result.lower()
    
    # Usuń znaki ™, ®, ©
    result = re.sub(r'[™®©]', '', result)
    
    return result.strip()

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

def or_chat_json(system_prompt: str, user_prompt: str, model: Optional[str]=None, max_tokens: int=2200) -> dict:
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

def jina_rerank(query: str, documents: List[str]) -> List[Tuple[int, float]]:
    url = "https://api.jina.ai/v1/rerank"
    headers = {"Content-Type":"application/json", "Authorization": f"Bearer {JINA_API_KEY}"}
    payload = {
        "model": "jina-reranker-v2-base-multilingual",
        "query": query,
        "documents": documents,
        "top_n": len(documents),
    }
    r = requests.post(url, headers=headers, json=payload, timeout=60)
    r.raise_for_status()
    results = r.json().get("results", [])
    return [(x["index"], x["relevance_score"]) for x in results]

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
- bez marek urządzeń (Dermapen, Geneo, VeneSeal itp.)
- realne zapytania usługowe
- pokryj różne dziedziny: dermatologia estetyczna, chirurgia plastyczna, kosmetologia, trychologia, ginekologia estetyczna, stomatologia estetyczna

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

from urllib.parse import urlparse

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
save_df(domains_df, f"{BASE_DIR}/domains.csv")
print()

# ============================================================
# FAZA 3: SCRAPOWANIE
# ============================================================

print("="*70)
print("🕷️ FAZA 3: SCRAPOWANIE DOMEN")
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

save_df(df_scraped, f"{BASE_DIR}/phase3_scraped_content.csv")
print()

# ============================================================
# FAZA 4: EKSTRAKCJA (ULEPSZONA - bez marek!)
# ============================================================

print("="*70)
print("🔍 FAZA 4: EKSTRAKCJA ZABIEGÓW (bez marek urządzeń)")
print("="*70)

def extract_treatments_from_text(domain: str, text: str) -> List[str]:
    text_chunk = text[:8000]
    
    system = "Jesteś ekspertem medycyny estetycznej. Wyciągasz OGÓLNE nazwy zabiegów, bez marek urządzeń."
    user = f"""
Tekst ze strony: {domain}

{text_chunk}

Wypisz WSZYSTKIE nazwy zabiegów medycyny estetycznej.

⚠️ WAŻNE - ZAMIEŃ MARKI NA OGÓLNE NAZWY:
❌ Dermapen → ✅ mezoterapia mikroigłowa
❌ Geneo → ✅ oksybrazja skóry
❌ VeneSeal → ✅ zamykanie żył klejem
❌ Juvederm → ✅ wypełnienie kwasem hialuronowym
❌ Botox → ✅ toksyna botulinowa
❌ PCA Skin → ✅ peeling chemiczny
❌ Profhilo → ✅ biorewitalizacja kwasem hialuronowym
❌ Coolsculpting → ✅ kriolipoliza
❌ Ultherapy → ✅ lifting ultradźwiękowy HIFU

DOBRE przykłady (ogólne nazwy):
✅ mezoterapia peptydowa twarzy
✅ toksyna botulinowa na bruksizm
✅ wypełnienie kwasem hialuronowym ust
✅ laser CO2 frakcyjny
✅ liposukcja brzucha
✅ biorewitalizacja polinukleotydami

ZŁE (zbyt ogólne - POMIŃ):
❌ zabiegi na twarz
❌ medycyna estetyczna
❌ usługi kosmetyczne

Jedna nazwa w linii, bez numeracji, BEZ MAREK!
"""
    
    try:
        response = or_chat([{"role":"system","content":system},{"role":"user","content":user}], temperature=0.1, max_tokens=1500)
        treatments = [clean_text(line) for line in response.split("\n") if clean_text(line)]
        
        # Dodatkowe czyszczenie marek
        treatments = [remove_brands(t) for t in treatments]
        
        return treatments
    except Exception as e:
        print(f"⚠️ Błąd: {e}")
        return []

all_treatments = []

for idx, row in tqdm(df_scraped.iterrows(), total=len(df_scraped), desc="Ekstrakcja"):
    treatments = extract_treatments_from_text(row["domain"], row["text"])
    for t in treatments:
        all_treatments.append({"domain": row["domain"], "treatment": t})
    time.sleep(0.3)

df_raw = pd.DataFrame(all_treatments)
print(f"\n📌 Wyciągnięto {len(df_raw)} surowych zabiegów")

df_raw["treatment_norm"] = df_raw["treatment"].apply(norm_key)
df_raw = df_raw[df_raw["treatment_norm"].str.len() >= MIN_TEXT_LEN]
df_raw = df_raw[df_raw["treatment_norm"].str.len() <= MAX_TEXT_LEN]
df_raw = df_raw.drop_duplicates(subset=["treatment_norm"]).reset_index(drop=True)

print(f"📌 Po deduplikacji: {len(df_raw)} unikalnych")

save_df(df_raw, f"{BASE_DIR}/phase4_raw_treatments.csv")
print()

# ============================================================
# FAZA 5: NORMALIZACJA (z czyszczeniem marek)
# ============================================================

print("="*70)
print("🧹 FAZA 5: NORMALIZACJA (z czyszczeniem marek)")
print("="*70)

print("\n🔹 Usuwanie duplikatów semantycznych...")
treatments_list = df_raw["treatment"].tolist()
embeddings = embed_texts(treatments_list)

sim_matrix = cosine_similarity(embeddings)
to_remove = set()

for i in range(len(sim_matrix)):
    if i in to_remove:
        continue
    for j in range(i+1, len(sim_matrix)):
        if j in to_remove:
            continue
        if sim_matrix[i][j] > (1.0 - SEMANTIC_SIM_THRESHOLD):
            if len(treatments_list[i]) <= len(treatments_list[j]):
                to_remove.add(j)
            else:
                to_remove.add(i)

df_filtered = df_raw.drop(index=list(to_remove)).reset_index(drop=True)
print(f"📌 Po deduplikacji semantycznej: {len(df_filtered)}")

print("\n🔹 Normalizacja nazw...")

def normalize_batch(treatments: List[str]) -> Dict[str, str]:
    treatments_str = "\n".join([f"{i+1}. {t}" for i, t in enumerate(treatments)])
    
    system = "Jesteś ekspertem medycyny estetycznej. Normalizujesz nazwy zabiegów BEZ MAREK urządzeń."
    user = f"""
Znormalizuj te zabiegi do poprawnej formy:

{treatments_str}

Zasady:
- Wielkie litery na początku
- Poprawna gramatyka polska
- BEZ MAREK urządzeń (zamień na ogólne nazwy!)
- Jeśli OK → bez zmian

JSON:
{{
  "normalized": ["Nazwa 1", "Nazwa 2", ...]
}}
"""
    
    result = or_chat_json(system, user, max_tokens=3000)
    normalized = result.get("normalized", [])
    
    mapping = {}
    for i, orig in enumerate(treatments):
        if i < len(normalized):
            # Dodatkowe czyszczenie marek po normalizacji
            norm_text = remove_brands(normalized[i])
            mapping[orig] = norm_text
        else:
            mapping[orig] = remove_brands(orig)
    return mapping

BATCH_SIZE = 30
all_mappings = {}

treatments_to_norm = df_filtered["treatment"].tolist()
for i in tqdm(range(0, len(treatments_to_norm), BATCH_SIZE), desc="Normalizacja"):
    batch = treatments_to_norm[i:i+BATCH_SIZE]
    try:
        mapping = normalize_batch(batch)
        all_mappings.update(mapping)
    except Exception as e:
        print(f"⚠️ Błąd: {e}")
        for t in batch:
            all_mappings[t] = remove_brands(t)
    time.sleep(0.5)

df_filtered["treatment_normalized"] = df_filtered["treatment"].map(all_mappings)
df_filtered["norm_key"] = df_filtered["treatment_normalized"].apply(norm_key)
df_normalized = df_filtered.drop_duplicates(subset=["norm_key"]).reset_index(drop=True)

print(f"📌 Po normalizacji: {len(df_normalized)}")

save_df(df_normalized, f"{BASE_DIR}/phase5_normalized.csv")
print()

# ============================================================
# FAZA 6: CLUSTERING
# ============================================================

print("="*70)
print("🔗 FAZA 6: CLUSTERING")
print("="*70)

treatments_list = df_normalized["treatment_normalized"].tolist()
embeddings = embed_texts(treatments_list)
embeddings_norm = normalize(embeddings, norm='l2')

clusterer = hdbscan.HDBSCAN(min_cluster_size=2, min_samples=1, metric="euclidean")
cluster_labels = clusterer.fit_predict(embeddings_norm)

df_normalized["cluster"] = cluster_labels
print(f"📌 Klastrów: {len(set(cluster_labels)) - (1 if -1 in cluster_labels else 0)}")

def select_representative(treatments: List[str]) -> str:
    if len(treatments) == 1:
        return treatments[0]
    
    if USE_JINA and len(treatments) > 2:
        try:
            query = " ".join(treatments)
            ranked = jina_rerank(query, treatments)
            top = sorted(ranked, key=lambda x: x[1], reverse=True)[:3]
            treatments = [treatments[idx] for idx, _ in top]
        except:
            pass
    
    t_str = "\n".join([f"{i+1}. {t}" for i, t in enumerate(treatments)])
    system = "Jesteś ekspertem medycyny estetycznej."
    user = f"""
Grupa podobnych zabiegów:
{t_str}

Wybierz JEDNĄ najbardziej ogólną nazwę (bez numeru, bez marek).
"""
    
    try:
        response = or_chat([{"role":"system","content":system},{"role":"user","content":user}], temperature=0, max_tokens=100)
        rep = clean_text(response)
        rep = remove_brands(rep)
        if rep not in treatments:
            rep = treatments[0]
        return rep
    except:
        return treatments[0]

mapping = {}
unique_clusters = [c for c in set(cluster_labels) if c != -1]

for cid in tqdm(unique_clusters, desc="Reprezentanci"):
    mask = df_normalized["cluster"] == cid
    treats = df_normalized[mask]["treatment_normalized"].tolist()
    rep = select_representative(treats)
    for t in treats:
        mapping[t] = rep
    time.sleep(0.2)

outliers = df_normalized[df_normalized["cluster"] == -1]["treatment_normalized"].tolist()
for t in outliers:
    mapping[t] = t

df_normalized["representative"] = df_normalized["treatment_normalized"].map(mapping)
df_unique = df_normalized[["representative"]].drop_duplicates().rename(columns={"representative": "treatment"}).reset_index(drop=True)

print(f"📌 Po clusteringu: {len(df_unique)} unikalnych zabiegów")

save_df(df_normalized, f"{BASE_DIR}/phase6_clustered.csv")
save_df(df_unique, f"{BASE_DIR}/phase6_unique.csv")
print()

# ============================================================
# FAZA 7: TAKSONOMIA 3-POZIOMOWA
# ============================================================

print("="*70)
print("🌳 FAZA 7: BUDOWA TAKSONOMII 3-POZIOMOWEJ")
print("="*70)

treatments_list = df_unique["treatment"].tolist()
print(f"🔹 Budowanie drzewa dla {len(treatments_list)} zabiegów...")

BATCH_SIZE = 80
all_tree_nodes = []

for batch_idx in tqdm(range(0, len(treatments_list), BATCH_SIZE), desc="Budowa drzewa"):
    batch = treatments_list[batch_idx:batch_idx+BATCH_SIZE]
    treats_str = "\n".join([f"- {t}" for t in batch])
    
    system = """
Jesteś ekspertem medycyny estetycznej w Polsce. Tworzysz 3-poziomową taksonomię zabiegów.

STRUKTURA:
Level 1: GŁÓWNA KATEGORIA
   └─ Level 2: PODKATEGORIA
      └─ Level 3: KONKRETNY ZABIEG

WAŻNE KATEGORIE Level 1:
- Dermatologia
- Chirurgia plastyczna
- Kosmetologia
- Trychologia (zabiegi na włosy)
- Ginekologia estetyczna (zabiegi intymne)
- Stomatologia estetyczna (zęby)
- Medycyna estetyczna (ogólne)

ZASADY:
1. Ginekologia (labioplastyka, plastyka pochwy) → "Ginekologia estetyczna" (NIE Dermatologia!)
2. Chirurgia (rinoplastyka, lifting operacyjny) → "Chirurgia plastyczna" (NIE Dermatologia!)
3. Włosy (przeszczep, mezoterapia włosów) → "Trychologia"
4. Level 3 to KONKRETNY zabieg (np. "Mezoterapia peptydowa twarzy")
5. BEZ MAREK urządzeń w nazwach!
"""
    
    user = f"""
Zabiegi:
{treats_str}

Przypisz każdy do Level 1 → Level 2 → Level 3.

JSON:
{{
  "tree": [
    {{
      "level1": "Dermatologia",
      "level2": "Dermatologia estetyczna",
      "level3": "Mezoterapia peptydowa twarzy"
    }},
    {{
      "level1": "Ginekologia estetyczna",
      "level2": "Chirurgia intymna",
      "level3": "Labioplastyka"
    }},
    ...
  ]
}}

KAŻDY zabieg z listy MUSI być w odpowiedzi!
"""
    
    try:
        result = or_chat_json(system, user, max_tokens=6000)
        nodes = result.get("tree", [])
        all_tree_nodes.extend(nodes)
    except Exception as e:
        print(f"⚠️ Błąd batch {batch_idx}: {e}")
        for t in batch:
            all_tree_nodes.append({
                "level1": "Dermatologia",
                "level2": "Dermatologia estetyczna",
                "level3": t
            })
    
    time.sleep(1)

df_tree = pd.DataFrame(all_tree_nodes)

if "level1" in df_tree.columns:
    df_tree = df_tree.drop_duplicates(subset=["level1", "level2", "level3"]).reset_index(drop=True)
    print(f"\n📌 Drzewo zawiera {len(df_tree)} węzłów")
    print(f"📌 Level 1: {df_tree['level1'].nunique()} kategorii")
    print(f"📌 Level 2: {df_tree['level2'].nunique()} podkategorii")
    print(f"📌 Level 3: {df_tree['level3'].nunique()} konkretnych zabiegów")
    
    save_df(df_tree, f"{BASE_DIR}/phase7_taxonomy.csv")
else:
    print("⚠️ Błąd: brak danych w drzewie")
    df_tree = pd.DataFrame()

print()

# ============================================================
# FAZA 8: MAPOWANIE
# ============================================================

print("="*70)
print("🗺️ FAZA 8: MAPOWANIE ZABIEGÓW")
print("="*70)

if len(df_tree) > 0:
    tree_items = df_tree["level3"].unique().tolist()
    print(f"Drzewo: {len(tree_items)} unikalnych Level 3")
    
    tree_embeddings = embed_texts(tree_items)
    
    all_treatments = df_normalized["representative"].unique().tolist()
    treatment_embeddings = embed_texts(all_treatments)
    
    similarity = cosine_similarity(treatment_embeddings, tree_embeddings)
    best_matches = np.argmax(similarity, axis=1)
    
    mapping = {}
    for i, treatment in enumerate(all_treatments):
        matched_l3 = tree_items[best_matches[i]]
        row = df_tree[df_tree["level3"] == matched_l3].iloc[0]
        mapping[treatment] = {
            "level1": row["level1"],
            "level2": row["level2"],
            "level3": matched_l3
        }
    
    df_normalized["level1"] = df_normalized["representative"].map(lambda x: mapping.get(x, {}).get("level1"))
    df_normalized["level2"] = df_normalized["representative"].map(lambda x: mapping.get(x, {}).get("level2"))
    df_normalized["level3"] = df_normalized["representative"].map(lambda x: mapping.get(x, {}).get("level3"))
    
    df_mapped = df_normalized
    
    print(f"\n📌 Zmapowano {len(df_mapped)} zabiegów")
    print(f"📌 Bez przypisania: {df_mapped['level1'].isna().sum()}")
    
    save_df(df_mapped, f"{BASE_DIR}/phase8_mapped.csv")
else:
    df_mapped = df_normalized

print()

# ============================================================
# FAZA 9: OPISY
# ============================================================

print("="*70)
print("📝 FAZA 9: GENEROWANIE OPISÓW")
print("="*70)

if len(df_tree) > 0:
    def generate_desc(l1: str, l2: str, l3: str) -> str:
        system = "Jesteś ekspertem medycyny estetycznej. Piszesz opisy dla pacjentów."
        user = f"""
Zabieg: {l3}
Kategoria: {l1} → {l2}

Napisz krótki opis (2-3 zdania):
- Co to za zabieg
- Jakie problemy rozwiązuje
- Jak działa

Tylko opis, bez nagłówków, BEZ MAREK urządzeń!
"""
        
        try:
            desc = clean_text(or_chat([{"role":"system","content":system},{"role":"user","content":user}], temperature=0.3, max_tokens=200))
            return remove_brands(desc)
        except:
            return ""
    
    df_unique_paths = df_tree.drop_duplicates(subset=["level1", "level2", "level3"]).reset_index(drop=True)
    
    descriptions = []
    for idx, row in tqdm(df_unique_paths.iterrows(), total=len(df_unique_paths), desc="Opisy"):
        desc = generate_desc(row["level1"], row["level2"], row["level3"])
        descriptions.append(desc)
        time.sleep(0.3)
    
    df_unique_paths["description"] = descriptions
    
    df_tree_desc = df_tree.merge(
        df_unique_paths[["level1", "level2", "level3", "description"]],
        on=["level1", "level2", "level3"],
        how="left"
    )
    
    print(f"\n📌 Wygenerowano {len(df_unique_paths)} opisów")
    
    save_df(df_tree_desc, f"{BASE_DIR}/phase9_with_descriptions.csv")
else:
    df_tree_desc = df_tree

print()

# ============================================================
# FAZA 10: EKSPORT FINALNY
# ============================================================

print("="*70)
print("📦 FAZA 10: EKSPORT FINALNY")
print("="*70)

if len(df_tree_desc) > 0:
    # final_tree.csv
    df_final_tree = df_tree_desc.drop_duplicates(subset=["level1", "level2", "level3"]).reset_index(drop=True)
    df_final_tree = df_final_tree[["level1", "level2", "level3", "description"]]
    save_df(df_final_tree, f"{BASE_DIR}/final_tree.csv")
    print(f"✅ final_tree.csv ({len(df_final_tree)} węzłów)")
    
    # final_treatments.csv
    df_final_treats = df_mapped[["domain", "treatment", "representative", "level1", "level2", "level3"]]
    save_df(df_final_treats, f"{BASE_DIR}/final_treatments.csv")
    print(f"✅ final_treatments.csv ({len(df_final_treats)} zabiegów)")
    
    # final_domains.csv
    domain_stats = df_final_treats.groupby("domain").agg({
        "treatment": "count",
        "representative": "nunique"
    }).reset_index()
    domain_stats.columns = ["domain", "total_treatments", "unique_treatments"]
    
    df_final_domains = df_scraped[["domain", "num_pages"]].merge(domain_stats, on="domain", how="left")
    df_final_domains["total_treatments"] = df_final_domains["total_treatments"].fillna(0).astype(int)
    df_final_domains["unique_treatments"] = df_final_domains["unique_treatments"].fillna(0).astype(int)
    
    save_df(df_final_domains, f"{BASE_DIR}/final_domains.csv")
    print(f"✅ final_domains.csv ({len(df_final_domains)} domen)")
    
    # final_tree.json
    tree_json = {}
    for _, row in df_final_tree.iterrows():
        l1, l2, l3 = row["level1"], row["level2"], row["level3"]
        desc = row.get("description", "")
        
        if l1 not in tree_json:
            tree_json[l1] = {}
        if l2 not in tree_json[l1]:
            tree_json[l1][l2] = []
        
        tree_json[l1][l2].append({"name": l3, "description": desc})
    
    with open(f"{BASE_DIR}/final_tree.json", "w", encoding="utf-8") as f:
        json.dump(tree_json, f, ensure_ascii=False, indent=2)
    print(f"✅ final_tree.json")
    
    # Podsumowanie
    print("\n" + "="*70)
    print("🎉 GOTOWE! PODSUMOWANIE:")
    print("="*70)
    print(f"📊 Kategorie Level 1: {df_final_tree['level1'].nunique()}")
    print(f"📊 Podkategorie Level 2: {df_final_tree['level2'].nunique()}")
    print(f"📊 Konkretne zabiegi Level 3: {df_final_tree['level3'].nunique()}")
    print(f"📊 Wszystkich zabiegów: {len(df_final_treats)}")
    print(f"📊 Unikalnych zabiegów: {df_final_treats['representative'].nunique()}")
    print(f"📊 Domen: {len(df_final_domains)}")
    print(f"\n💾 Pliki finalne:")
    print(f"   - {BASE_DIR}/final_tree.csv")
    print(f"   - {BASE_DIR}/final_treatments.csv")
    print(f"   - {BASE_DIR}/final_domains.csv")
    print(f"   - {BASE_DIR}/final_tree.json")
    
    print("\n📋 Przykładowe drzewo (top 20):")
    print(df_final_tree[["level1", "level2", "level3"]].head(20).to_string(index=False))
    
    print("\n📊 Statystyki per kategoria:")
    stats = df_final_tree.groupby("level1").size().reset_index(name="Liczba zabiegów")
    print(stats.to_string(index=False))
else:
    print("⚠️ Brak danych do eksportu")

print("\n" + "="*70)
print("✅ PIPELINE 3-POZIOMOWY ZAKOŃCZONY!")
print("✅ BEZ MAREK URZĄDZEŃ W WYNIKACH!")
print("="*70)
