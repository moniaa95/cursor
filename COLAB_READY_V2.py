# ============================================================
# WYSZUKIWARKA ZABIEGÓW MEDYCYNY ESTETYCZNEJ V2
# 🆕 Ulepszona wersja z elastycznym Level 4 i lepszymi promptami
# Skopiuj cały ten plik i wklej do Google Colab
# ============================================================

# FAZA 0: Instalacja pakietów
print("📦 Instalacja pakietów...")
!pip install -q openai pandas requests tqdm beautifulsoup4 scikit-learn scipy hdbscan

# Importy
import os, re, json, time, math, random, unicodedata
from pathlib import Path
from typing import List, Dict, Tuple, Optional

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
PROJECT_NAME = "baza_zabiegow_v2"  # @param {type:"string"}
BASE_DIR = f"/content/{PROJECT_NAME}"  # @param {type:"string"}
os.makedirs(BASE_DIR, exist_ok=True)

# @title 🤖 Modele przez OpenRouter
MODEL_NAME = "openai/gpt-4.1-mini"  # @param ["openai/gpt-5.1","openai/gpt-5-mini","openai/gpt-4.1-mini","google/gemini-2.5-flash-preview-09-2025","google/gemini-2.5-flash-lite"]
EMBED_MODEL = "openai/text-embedding-3-small"  # @param ["openai/text-embedding-3-small","openai/text-embedding-3-large"]

# @title 🔢 Limity
MAX_KEYWORDS = 20  # @param {type:"integer"}
SERP_TOP_N = 10  # @param {type:"integer"}
MAX_DOMAINS = 50  # @param {type:"integer"}
MAX_PAGES_PER_DOMAIN = 12  # @param {type:"integer"}

# @title 🧹 Filtry (ważne: to ogranicza LLM)
MIN_TEXT_LEN = 5     # @param {type:"integer"}
MAX_TEXT_LEN = 120   # @param {type:"integer"}
MIN_DOMAIN_COUNT = 2 # @param {type:"integer"}
SEMANTIC_SIM_THRESHOLD = 0.30  # @param {type:"slider", min:0.15, max:0.55, step:0.01}

# (opcjonalnie) Jina rerank – możesz wyłączyć ustawiając USE_JINA=False
USE_JINA = True  # @param {type:"boolean"}
JINA_RERANK_THRESHOLD = 0.25  # @param {type:"slider", min:0.15, max:0.75, step:0.01}

# ============================================================
# KLUCZE API (z Colab Secrets)
# ============================================================

OPENROUTER_API_KEY = userdata.get("openrouter_api")
SERPDATA_KEY = userdata.get("serpdata_key")
JINA_API_KEY = userdata.get("jina_api")

if not OPENROUTER_API_KEY:
    raise ValueError("❌ Brak secreta: openrouter_api (Colab → 🔑 Obiekty tajne)")
if not SERPDATA_KEY:
    raise ValueError("❌ Brak secreta: serpdata_key (Colab → 🔑 Obiekty tajne)")
if USE_JINA and not JINA_API_KEY:
    print("⚠️ USE_JINA=True, ale brak secreta jina_api → wyłączam Jina.")
    USE_JINA = False

print("✅ Klucze API załadowane")

# OpenRouter client
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
# FAZA 1-6: IDENTYCZNE JAK POPRZEDNIO
# (Keywords, SERP, Scraping, Extraction, Normalization, Clustering)
# ============================================================

# [... FAZY 1-6 bez zmian - kopiuję z poprzedniej wersji ...]

print("="*70)
print("🔑 FAZA 1: GENEROWANIE KEYWORDÓW")
print("="*70)

system = "Jesteś ekspertem SEO w branży medycyny estetycznej w Polsce."
user = f"""
Wygeneruj {MAX_KEYWORDS} polskich fraz, które pacjenci wpisują w Google szukając konkretnych zabiegów.

Zasady:
- 2–5 słów w frazie
- bez numerowania, jedna fraza w jednej linii
- bez marek (np. Dermapen, PRX-T33, Nucleofill itp.)
- mają to być realne zapytania usługowe (np. 'mezoterapia igłowa twarzy', 'botoks bruksizm')
- pokryj różne dziedziny: dermatologia estetyczna, chirurgia plastyczna, kosmetologia, trychologia, ginekologia estetyczna

Wypisz same frazy.
"""

raw = or_chat([{"role":"system","content":system},{"role":"user","content":user}], temperature=0.8, max_tokens=1200)
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

# FAZA 2: SERP → DOMENY
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

from urllib.parse import urlparse

df_serp = pd.DataFrame(all_rows).drop_duplicates(subset=["keyword", "url"]).reset_index(drop=True)
df_unique_urls = df_serp.drop_duplicates(subset=["url"]).reset_index(drop=True)

df_unique_urls["domain"] = df_unique_urls["url"].apply(lambda u: urlparse(u).netloc.lower().strip() if isinstance(u, str) else "")
df_unique_urls["domain"] = df_unique_urls["domain"].str.replace(r"^www\.", "", regex=True)

BAD = ["facebook", "instagram", "youtube", "twitter", "znanylekarz", "booksy",
       "allegro", "olx", "wikipedia", "medonet", "onet", "wp"]
GOOD = ["klinika", "clinic", "med", "derma", "estety", "uroda", "beauty", "laser", "gabinet"]

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
print(f"\n📌 Wybrano domen: {len(domains_df)}")

save_df(df_serp, f"{BASE_DIR}/phase2_serp_keyword_url.csv")
save_df(df_unique_urls, f"{BASE_DIR}/phase2_unique_urls.csv")
save_df(domains_df, f"{BASE_DIR}/domains.csv")
print()

# FAZA 3: SCRAPOWANIE
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

# FAZA 4: EKSTRAKCJA
print("="*70)
print("🔍 FAZA 4: EKSTRAKCJA ZABIEGÓW (LLM)")
print("="*70)

def extract_treatments_from_text(domain: str, text: str) -> List[str]:
    text_chunk = text[:8000]
    
    system = "Jesteś ekspertem medycyny estetycznej. Twoim zadaniem jest wyciągnięcie WSZYSTKICH nazw zabiegów z tekstu strony internetowej."
    user = f"""
Tekst ze strony: {domain}

---
{text_chunk}
---

Zadanie:
Wypisz WSZYSTKIE nazwy zabiegów medycyny estetycznej, które występują w tym tekście.

Zasady:
- Jedna nazwa w jednej linii
- Bez numeracji, bez cudzysłowów
- Bez marek urządzeń (np. Dermapen → mezoterapia mikroigłowa)
- Tylko konkretne zabiegi (nie kategorie typu "zabiegi na twarz")
- Przykłady DOBRYCH nazw:
  ✅ mezoterapia igłowa
  ✅ botoks bruksizmu
  ✅ liposukcja brzucha
  ✅ laser CO2 frakcyjny
  
Przykłady ZŁYCH (zbyt ogólne - POMIŃ):
  ❌ zabiegi na twarz
  ❌ medycyna estetyczna
  ❌ usługi kosmetyczne

Wypisz listę zabiegów:
"""
    
    try:
        response = or_chat([{"role":"system","content":system},{"role":"user","content":user}], temperature=0.1, max_tokens=1500)
        treatments = [clean_text(line) for line in response.split("\n") if clean_text(line)]
        return treatments
    except Exception as e:
        print(f"⚠️ Błąd dla {domain}: {e}")
        return []

all_treatments = []

for idx, row in tqdm(df_scraped.iterrows(), total=len(df_scraped), desc="Ekstrakcja zabiegów"):
    treatments = extract_treatments_from_text(row["domain"], row["text"])
    for t in treatments:
        all_treatments.append({
            "domain": row["domain"],
            "treatment": t
        })
    time.sleep(0.3)

df_raw_treatments = pd.DataFrame(all_treatments)
print(f"\n📌 Wyciągnięto {len(df_raw_treatments)} surowych zabiegów")

df_raw_treatments["treatment_norm"] = df_raw_treatments["treatment"].apply(norm_key)
df_raw_treatments = df_raw_treatments[df_raw_treatments["treatment_norm"].str.len() >= MIN_TEXT_LEN]
df_raw_treatments = df_raw_treatments[df_raw_treatments["treatment_norm"].str.len() <= MAX_TEXT_LEN]
df_raw_treatments = df_raw_treatments.drop_duplicates(subset=["treatment_norm"]).reset_index(drop=True)

print(f"📌 Po wstępnej deduplikacji: {len(df_raw_treatments)} unikalnych zabiegów")

save_df(df_raw_treatments, f"{BASE_DIR}/phase4_raw_treatments.csv")
print()

# FAZA 5: FILTROWANIE I NORMALIZACJA (ULEPSZONA)
print("="*70)
print("🧹 FAZA 5: FILTROWANIE I NORMALIZACJA")
print("="*70)

print("\n🔹 Usuwanie duplikatów semantycznych (threshold={})...".format(SEMANTIC_SIM_THRESHOLD))
treatments_list = df_raw_treatments["treatment"].tolist()
print(f"Generowanie embeddingów dla {len(treatments_list)} zabiegów...")
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

df_filtered = df_raw_treatments.drop(index=list(to_remove)).reset_index(drop=True)
print(f"📌 Po usunięciu duplikatów: {len(df_filtered)} zabiegów")

print("\n🔹 Normalizacja nazw przez LLM...")

def normalize_treatments_batch(treatments: List[str]) -> Dict[str, str]:
    treatments_str = "\n".join([f"{i+1}. {t}" for i, t in enumerate(treatments)])
    
    system = "Jesteś ekspertem medycyny estetycznej. Normalizujesz nazwy zabiegów do standardowej formy."
    user = f"""
Mam listę zabiegów. Znormalizuj je do poprawnej formy.

ZASADY NORMALIZACJI:
1. Wielka litera na początku każdego znaczącego słowa
2. Poprawna gramatyka polska (dopełniacz, etc.)
3. Bez marek urządzeń → zamień na ogólną nazwę
4. Skróty → rozwiń (np. "PRP" → "osoczem bogatopłytkowym")
5. Jeśli zabieg jest już poprawny → zostaw bez zmian

PRZYKŁADY:
"botox czoło" → "Botoks zmarszczek czoła"
"prp włosy" → "Terapia osoczem bogatopłytkowym na włosy"
"lifting hifu" → "Lifting HIFU"
"Mezoterapia twarzy" → "Mezoterapia twarzy" (bez zmian - OK)

Lista zabiegów:
{treatments_str}

Odpowiedź w formacie JSON:
{{
  "normalized": [
    "Znormalizowana nazwa 1",
    "Znormalizowana nazwa 2",
    ...
  ]
}}
"""
    
    result = or_chat_json(system, user, max_tokens=3000)
    normalized = result.get("normalized", [])
    
    mapping = {}
    for i, orig in enumerate(treatments):
        if i < len(normalized):
            mapping[orig] = normalized[i]
        else:
            mapping[orig] = orig
    return mapping

BATCH_SIZE = 30
all_mappings = {}

treatments_to_normalize = df_filtered["treatment"].tolist()
for i in tqdm(range(0, len(treatments_to_normalize), BATCH_SIZE), desc="Normalizacja"):
    batch = treatments_to_normalize[i:i+BATCH_SIZE]
    try:
        mapping = normalize_treatments_batch(batch)
        all_mappings.update(mapping)
    except Exception as e:
        print(f"⚠️ Błąd batch {i}: {e}")
        for t in batch:
            all_mappings[t] = t
    time.sleep(0.5)

df_filtered["treatment_normalized"] = df_filtered["treatment"].map(all_mappings)
df_filtered["norm_key"] = df_filtered["treatment_normalized"].apply(norm_key)
df_normalized = df_filtered.drop_duplicates(subset=["norm_key"]).reset_index(drop=True)

print(f"\n📌 Po normalizacji: {len(df_normalized)} unikalnych zabiegów")

save_df(df_normalized, f"{BASE_DIR}/phase5_normalized_treatments.csv")
print()

# FAZA 6: CLUSTERING (POPRAWIONA)
print("="*70)
print("🔗 FAZA 6: CLUSTERING I SYNONIMY")
print("="*70)

print("\n🔹 Clustering HDBSCAN...")
treatments_list = df_normalized["treatment_normalized"].tolist()
print(f"Generowanie embeddingów dla {len(treatments_list)} zabiegów...")
embeddings = embed_texts(treatments_list)

# Normalizuj embeddingi (L2) dla HDBSCAN
embeddings_normalized = normalize(embeddings, norm='l2')

clusterer = hdbscan.HDBSCAN(min_cluster_size=2, min_samples=1, metric="euclidean")
cluster_labels = clusterer.fit_predict(embeddings_normalized)

df_normalized["cluster"] = cluster_labels
print(f"📌 Znaleziono {len(set(cluster_labels)) - (1 if -1 in cluster_labels else 0)} klastrów")
print(f"📌 {sum(cluster_labels == -1)} zabiegów bez klastra")

print("\n🔹 Wybór reprezentantów klastrów...")

def select_cluster_representative(cluster_treatments: List[str]) -> str:
    if len(cluster_treatments) == 1:
        return cluster_treatments[0]
    
    if USE_JINA and len(cluster_treatments) > 2:
        try:
            query = " ".join(cluster_treatments)
            ranked = jina_rerank(query, cluster_treatments)
            top_indices = sorted(ranked, key=lambda x: x[1], reverse=True)[:3]
            cluster_treatments = [cluster_treatments[idx] for idx, _ in top_indices]
        except Exception:
            pass
    
    treatments_str = "\n".join([f"{i+1}. {t}" for i, t in enumerate(cluster_treatments)])
    system = "Jesteś ekspertem medycyny estetycznej."
    user = f"""
Mam grupę podobnych zabiegów. Wybierz JEDNĄ nazwę, która najlepiej reprezentuje całą grupę.

Grupa:
{treatments_str}

Zasady:
- Wybierz najbardziej ogólną i poprawną nazwę
- Preferuj krótszą nazwę jeśli są równoważne
- Zwróć tylko nazwę (bez numeru, bez komentarzy)

Odpowiedź (tylko nazwa zabiegu):
"""
    
    try:
        response = or_chat([{"role":"system","content":system},{"role":"user","content":user}], temperature=0, max_tokens=100)
        representative = clean_text(response)
        if representative not in cluster_treatments:
            representative = cluster_treatments[0]
        return representative
    except Exception:
        return cluster_treatments[0]

treatment_to_representative = {}

unique_clusters = [c for c in set(cluster_labels) if c != -1]
for cluster_id in tqdm(unique_clusters, desc="Wybór reprezentantów"):
    cluster_mask = df_normalized["cluster"] == cluster_id
    cluster_treatments = df_normalized[cluster_mask]["treatment_normalized"].tolist()
    
    representative = select_cluster_representative(cluster_treatments)
    
    for t in cluster_treatments:
        treatment_to_representative[t] = representative
    
    time.sleep(0.2)

outliers = df_normalized[df_normalized["cluster"] == -1]["treatment_normalized"].tolist()
for t in outliers:
    treatment_to_representative[t] = t

df_normalized["representative"] = df_normalized["treatment_normalized"].map(treatment_to_representative)

df_unique_treatments = df_normalized[["representative"]].drop_duplicates().rename(columns={"representative": "treatment"}).reset_index(drop=True)

print(f"\n📌 Po clusteringu: {len(df_unique_treatments)} unikalnych zabiegów")

save_df(df_normalized, f"{BASE_DIR}/phase6_clustered_treatments.csv")
save_df(df_unique_treatments, f"{BASE_DIR}/phase6_unique_treatments.csv")
print()

# ============================================================
# FAZA 7: BUDOWA TAKSONOMII (ULEPSZONA - HIERARCHICZNA)
# 🆕 Z elastycznym Level 4 (może być NULL)
# ============================================================

print("="*70)
print("🌳 FAZA 7: BUDOWA TAKSONOMII 4-POZIOMOWEJ (HIERARCHICZNA)")
print("="*70)

treatments_list = df_unique_treatments["treatment"].tolist()
print(f"\n🔹 Budowanie drzewa dla {len(treatments_list)} zabiegów...")

# KROK 1: LLM tworzy Level 1 + Level 2
print("\n📍 Krok 1/3: Tworzenie kategorii głównych (Level 1 + 2)...")

system_l1_l2 = """
Jesteś ekspertem medycyny estetycznej w Polsce. Tworzysz taksonomię zabiegów.

Zadanie: Utwórz strukturę Level 1 (główne kategorie) i Level 2 (podkategorie).

Level 1: GŁÓWNA KATEGORIA (np. Dermatologia, Kosmetologia, Chirurgia plastyczna, Trychologia, Ginekologia estetyczna, Stomatologia estetyczna)
   └─ Level 2: PODKATEGORIA (np. Dermatologia estetyczna, Dermatologia lecznicza, Zabiegi na twarz, Zabiegi na ciało)
"""

user_l1_l2 = """
Stwórz kompletną strukturę Level 1 → Level 2 dla medycyny estetycznej w Polsce.

Zwróć w formacie JSON:
{
  "categories": [
    {
      "level1": "Dermatologia",
      "level2": ["Dermatologia estetyczna", "Dermatologia lecznicza"]
    },
    {
      "level1": "Kosmetologia",
      "level2": ["Zabiegi na twarz", "Zabiegi na ciało", "Zabiegi na włosy"]
    },
    ...
  ]
}

WAŻNE:
- Pokryj wszystkie główne dziedziny medycyny estetycznej
- Level 2 powinno być logicznym podziałem Level 1
- Nazwy polskie, poprawna gramatyka
"""

try:
    result_l1_l2 = or_chat_json(system_l1_l2, user_l1_l2, max_tokens=2000)
    categories = result_l1_l2.get("categories", [])
    print(f"✅ Stworzono {len(categories)} kategorii Level 1")
except Exception as e:
    print(f"⚠️ Błąd tworzenia L1/L2: {e}")
    categories = []

time.sleep(1)

# KROK 2: LLM przypisuje zabiegi do Level 1 + Level 2
print("\n📍 Krok 2/3: Przypisywanie zabiegów do kategorii...")

all_tree_nodes = []

# Batch po 50 zabiegów
BATCH_SIZE = 50
for batch_idx in tqdm(range(0, len(treatments_list), BATCH_SIZE), desc="Przypisywanie do L1/L2"):
    batch = treatments_list[batch_idx:batch_idx+BATCH_SIZE]
    treatments_str = "\n".join([f"- {t}" for t in batch])
    
    # Przygotuj strukturę kategorii dla promptu
    categories_str = ""
    for cat in categories[:10]:  # max 10 kategorii w prompt
        l1 = cat.get("level1", "")
        l2_list = cat.get("level2", [])
        if l1 and l2_list:
            categories_str += f"\n{l1}:\n"
            for l2 in l2_list:
                categories_str += f"  - {l2}\n"
    
    system = "Jesteś ekspertem medycyny estetycznej. Przypisujesz zabiegi do odpowiednich kategorii."
    user = f"""
Mam listę zabiegów. Przypisz każdy do odpowiedniego Level 1 i Level 2.

Dostępne kategorie:
{categories_str}

Zabiegi do przypisania:
{treatments_str}

Zwróć w formacie JSON:
{{
  "assignments": [
    {{
      "treatment": "Mezoterapia igłowa",
      "level1": "Dermatologia",
      "level2": "Dermatologia estetyczna"
    }},
    ...
  ]
}}

WAŻNE:
- Każdy zabieg MUSI być przypisany
- Wybieraj najbardziej pasującą kategorię
- Jeśli nie ma idealnej kategorii, wybierz najbliższą
"""
    
    try:
        result = or_chat_json(system, user, max_tokens=3000)
        assignments = result.get("assignments", [])
        all_tree_nodes.extend(assignments)
    except Exception as e:
        print(f"⚠️ Błąd batch {batch_idx}: {e}")
        # Fallback: przypisz do "Dermatologia → Dermatologia estetyczna"
        for t in batch:
            all_tree_nodes.append({
                "treatment": t,
                "level1": "Dermatologia",
                "level2": "Dermatologia estetyczna"
            })
    
    time.sleep(1)

# KROK 3: LLM tworzy Level 3 i decyduje o Level 4
print("\n📍 Krok 3/3: Tworzenie Level 3 i Level 4...")

final_tree = []

# Grupuj zabiegi po (Level1, Level2)
df_assigned = pd.DataFrame(all_tree_nodes)
if "treatment" in df_assigned.columns and "level1" in df_assigned.columns:
    grouped = df_assigned.groupby(["level1", "level2"])["treatment"].apply(list).reset_index()
    
    for idx, row in tqdm(grouped.iterrows(), total=len(grouped), desc="Tworzenie L3/L4"):
        l1 = row["level1"]
        l2 = row["level2"]
        treats = row["treatment"]
        
        treats_str = "\n".join([f"- {t}" for t in treats[:100]])  # max 100 per group
        
        system = """
Jesteś ekspertem medycyny estetycznej. Tworzysz hierarchiczną taksonomię zabiegów.

Zadanie: Dla podanej listy zabiegów, stwórz Level 3 (rodziny zabiegów) i Level 4 (konkretne zabiegi).

KLUCZOWA ZASADA:
- Level 3 to RODZINA zabiegów (ogólna kategoria, np. "Mezoterapia igłowa", "Toksyna botulinowa")
- Level 4 to KONKRETNY zabieg (szczegóły, np. "Mezoterapia peptydowa twarzy", "Botoks zmarszczek czoła")

⚠️ WAŻNE: Level 4 może być PUSTE (null) jeśli Level 3 to już konkretny zabieg!

PRZYKŁADY:

✅ POPRAWNE (Level 3 to rodzina → Level 4 wypełnione):
Level 3: "Mezoterapia igłowa" (rodzina)
├─ Level 4: "Mezoterapia peptydowa twarzy"
├─ Level 4: "Mezoterapia witaminowa twarzy"
└─ Level 4: "Mezoterapia kwasem hialuronowym"

✅ POPRAWNE (Level 3 to konkret → Level 4 = NULL):
Level 3: "Przeszczep włosów" (już konkretny zabieg)
└─ Level 4: null

✅ POPRAWNE (Level 3 to rodzina → Level 4 wypełnione):
Level 3: "Lifting bezskalpelowy" (rodzina)
├─ Level 4: "Lifting twarzy metodą HIFU"
├─ Level 4: "Lifting HIFU 3D"
└─ Level 4: "Lifting ultradźwiękowy"

❌ ŹLE (Level 3 zbyt szczegółowe):
Level 3: "Mikroigłowa radiofrekwencja z PRP na twarz" ← TO POWINNO BYĆ LEVEL 4!
"""
        
        user = f"""
Kategoria: {l1} → {l2}

Lista zabiegów:
{treats_str}

Zadanie:
1. Pogrupuj zabiegi w RODZINY (Level 3)
2. Dla każdej rodziny zdecyduj:
   - Czy można ją podzielić dalej? → Level 4 wypełnione
   - Czy to już konkret? → Level 4 = null

Zwróć w formacie JSON:
{{
  "tree": [
    {{
      "level3": "Mezoterapia igłowa",
      "level4": "Mezoterapia peptydowa twarzy"
    }},
    {{
      "level3": "Przeszczep włosów",
      "level4": null
    }},
    ...
  ]
}}

WAŻNE:
- Każdy zabieg z listy MUSI być w drzewie
- Level 3 powinno być krótkie (2-5 słów)
- Level 4 może być null jeśli Level 3 to już konkret
- Bądź konsekwentny w nazewnictwie
"""
        
        try:
            result = or_chat_json(system, user, max_tokens=4000)
            tree_items = result.get("tree", [])
            
            for item in tree_items:
                final_tree.append({
                    "level1": l1,
                    "level2": l2,
                    "level3": item.get("level3"),
                    "level4": item.get("level4")
                })
        except Exception as e:
            print(f"⚠️ Błąd dla {l1}/{l2}: {e}")
            # Fallback: każdy zabieg jako osobny Level 3, Level 4 = null
            for t in treats[:50]:
                final_tree.append({
                    "level1": l1,
                    "level2": l2,
                    "level3": t,
                    "level4": None
                })
        
        time.sleep(0.8)

print("\n🔹 Konsolidacja drzewa...")

df_tree = pd.DataFrame(final_tree)
if "level1" in df_tree.columns:
    # Deduplikacja
    df_tree = df_tree.drop_duplicates(subset=["level1", "level2", "level3", "level4"]).reset_index(drop=True)
    
    # Zamień "null" string na prawdziwy None
    df_tree["level4"] = df_tree["level4"].replace(["null", "None", ""], None)
    
    print(f"📌 Drzewo zawiera {len(df_tree)} węzłów")
    print(f"📌 Level 1: {df_tree['level1'].nunique()} kategorii")
    print(f"📌 Level 2: {df_tree['level2'].nunique()} podkategorii")
    print(f"📌 Level 3: {df_tree['level3'].nunique()} rodzin")
    print(f"📌 Level 4: {df_tree['level4'].notna().sum()} konkretnych zabiegów")
    print(f"📌 Level 4 pustych: {df_tree['level4'].isna().sum()} (Level 3 to już konkrety)")
    
    save_df(df_tree, f"{BASE_DIR}/phase7_taxonomy_tree.csv")
else:
    print("⚠️ Błąd: brak danych w drzewie")
    df_tree = pd.DataFrame()

print()

# ============================================================
# FAZA 8: MAPOWANIE (ulepszone)
# ============================================================

print("="*70)
print("🗺️ FAZA 8: MAPOWANIE ZABIEGÓW DO DRZEWA")
print("="*70)

if len(df_tree) > 0:
    print("\n🔹 Mapowanie przez embeddings...")
    
    # Stwórz listę wszystkich unikalnych zabiegów w drzewie (L3 + L4)
    tree_items = []
    tree_items_meta = []
    
    for idx, row in df_tree.iterrows():
        l3 = row["level3"]
        l4 = row["level4"]
        
        # Dodaj Level 3
        if pd.notna(l3):
            tree_items.append(l3)
            tree_items_meta.append({
                "text": l3,
                "level1": row["level1"],
                "level2": row["level2"],
                "level3": l3,
                "level4": None
            })
        
        # Dodaj Level 4 jeśli istnieje
        if pd.notna(l4):
            tree_items.append(l4)
            tree_items_meta.append({
                "text": l4,
                "level1": row["level1"],
                "level2": row["level2"],
                "level3": l3,
                "level4": l4
            })
    
    print(f"Drzewo zawiera {len(tree_items)} unikalnych elementów (L3+L4)")
    
    print("Generowanie embeddingów dla drzewa...")
    tree_embeddings = embed_texts(tree_items)
    
    all_treatments = df_normalized["representative"].unique().tolist()
    print(f"Mapowanie {len(all_treatments)} zabiegów...")
    treatment_embeddings = embed_texts(all_treatments)
    
    similarity = cosine_similarity(treatment_embeddings, tree_embeddings)
    best_matches = np.argmax(similarity, axis=1)
    
    treatment_to_tree = {}
    for i, treatment in enumerate(all_treatments):
        matched_meta = tree_items_meta[best_matches[i]]
        treatment_to_tree[treatment] = matched_meta
    
    df_normalized["matched_level1"] = df_normalized["representative"].map(lambda x: treatment_to_tree.get(x, {}).get("level1"))
    df_normalized["matched_level2"] = df_normalized["representative"].map(lambda x: treatment_to_tree.get(x, {}).get("level2"))
    df_normalized["matched_level3"] = df_normalized["representative"].map(lambda x: treatment_to_tree.get(x, {}).get("level3"))
    df_normalized["matched_level4"] = df_normalized["representative"].map(lambda x: treatment_to_tree.get(x, {}).get("level4"))
    
    df_mapped = df_normalized.rename(columns={
        "matched_level1": "level1",
        "matched_level2": "level2",
        "matched_level3": "level3",
        "matched_level4": "level4"
    })
    
    print(f"\n📌 Zmapowano {len(df_mapped)} zabiegów")
    print(f"📌 Zabiegi bez przypisania: {df_mapped['level1'].isna().sum()}")
    
    save_df(df_mapped, f"{BASE_DIR}/phase8_treatments_mapped.csv")
else:
    print("⚠️ Pomijam mapowanie (brak drzewa)")
    df_mapped = df_normalized

print()

# ============================================================
# FAZA 9: GENEROWANIE OPISÓW
# ============================================================

print("="*70)
print("📝 FAZA 9: GENEROWANIE OPISÓW")
print("="*70)

if len(df_tree) > 0:
    print("\n🔹 Generowanie opisów...")
    
    def generate_description(level1: str, level2: str, level3: str, level4: Optional[str]) -> str:
        # Jeśli Level 4 istnieje, opisz to
        # Jeśli Level 4 = null, opisz Level 3
        subject = level4 if pd.notna(level4) and level4 else level3
        
        system = "Jesteś ekspertem medycyny estetycznej. Piszesz krótkie, przystępne opisy zabiegów dla pacjentów."
        user = f"""
Napisz krótki opis zabiegu (2-3 zdania) dla pacjenta.

Zabieg: {subject}
Kategoria: {level1} → {level2} → {level3}

Opis powinien zawierać:
- Co to za zabieg
- Jakie problemy rozwiązuje
- Krótko jak działa

Odpowiedź (tylko opis, bez nagłówków):
"""
        
        try:
            response = or_chat([{"role":"system","content":system},{"role":"user","content":user}], temperature=0.3, max_tokens=200)
            return clean_text(response)
        except Exception:
            return ""
    
    df_unique_paths = df_tree.drop_duplicates(subset=["level1", "level2", "level3", "level4"]).reset_index(drop=True)
    
    descriptions = []
    for idx, row in tqdm(df_unique_paths.iterrows(), total=len(df_unique_paths), desc="Generowanie opisów"):
        desc = generate_description(row["level1"], row["level2"], row["level3"], row.get("level4"))
        descriptions.append(desc)
        time.sleep(0.3)
    
    df_unique_paths["description"] = descriptions
    
    df_tree_with_desc = df_tree.merge(
        df_unique_paths[["level1", "level2", "level3", "level4", "description"]],
        on=["level1", "level2", "level3", "level4"],
        how="left"
    )
    
    print(f"\n📌 Wygenerowano opisy dla {len(df_unique_paths)} węzłów")
    
    save_df(df_tree_with_desc, f"{BASE_DIR}/phase9_tree_with_descriptions.csv")
else:
    print("⚠️ Pomijam opisy (brak drzewa)")
    df_tree_with_desc = df_tree

print()

# ============================================================
# FAZA 10: EKSPORT FINALNY
# ============================================================

print("="*70)
print("📦 FAZA 10: EKSPORT FINALNY")
print("="*70)

if len(df_tree_with_desc) > 0:
    # final_tree.csv
    df_tree_final = df_tree_with_desc.drop_duplicates(subset=["level1", "level2", "level3", "level4"]).reset_index(drop=True)
    df_tree_final = df_tree_final[["level1", "level2", "level3", "level4", "description"]]
    save_df(df_tree_final, f"{BASE_DIR}/final_tree.csv")
    print(f"✅ Zapisano final_tree.csv ({len(df_tree_final)} węzłów)")
    
    # final_treatments.csv
    df_treatments_final = df_mapped[["domain", "treatment", "representative", "level1", "level2", "level3", "level4"]]
    save_df(df_treatments_final, f"{BASE_DIR}/final_treatments.csv")
    print(f"✅ Zapisano final_treatments.csv ({len(df_treatments_final)} zabiegów)")
    
    # final_domains.csv
    domain_stats = df_treatments_final.groupby("domain").agg({
        "treatment": "count",
        "representative": "nunique"
    }).reset_index()
    domain_stats.columns = ["domain", "total_treatments", "unique_treatments"]
    
    df_domains_final = df_scraped[["domain", "num_pages"]].merge(domain_stats, on="domain", how="left")
    df_domains_final["total_treatments"] = df_domains_final["total_treatments"].fillna(0).astype(int)
    df_domains_final["unique_treatments"] = df_domains_final["unique_treatments"].fillna(0).astype(int)
    
    save_df(df_domains_final, f"{BASE_DIR}/final_domains.csv")
    print(f"✅ Zapisano final_domains.csv ({len(df_domains_final)} domen)")
    
    # final_tree.json (hierarchiczny)
    tree_json = {}
    for _, row in df_tree_final.iterrows():
        l1, l2, l3 = row["level1"], row["level2"], row["level3"]
        l4 = row["level4"] if pd.notna(row["level4"]) else None
        desc = row.get("description", "")
        
        if l1 not in tree_json:
            tree_json[l1] = {}
        if l2 not in tree_json[l1]:
            tree_json[l1][l2] = {}
        if l3 not in tree_json[l1][l2]:
            tree_json[l1][l2][l3] = []
        
        # Dodaj tylko jeśli Level 4 istnieje
        if l4:
            tree_json[l1][l2][l3].append({"name": l4, "description": desc})
        elif not tree_json[l1][l2][l3]:  # Jeśli L4=null i lista pusta, dodaj info
            tree_json[l1][l2][l3] = {"name": l3, "description": desc, "is_leaf": True}
    
    json_path = f"{BASE_DIR}/final_tree.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(tree_json, f, ensure_ascii=False, indent=2)
    print(f"✅ Zapisano final_tree.json")
    
    # Podsumowanie
    print("\n" + "="*70)
    print("🎉 GOTOWE! PODSUMOWANIE:")
    print("="*70)
    print(f"📊 Kategorie Level 1: {df_tree_final['level1'].nunique()}")
    print(f"📊 Podkategorie Level 2: {df_tree_final['level2'].nunique()}")
    print(f"📊 Rodziny Level 3: {df_tree_final['level3'].nunique()}")
    print(f"📊 Konkretne zabiegi Level 4: {df_tree_final['level4'].notna().sum()}")
    print(f"📊 Level 4 pustych (L3 to konkrety): {df_tree_final['level4'].isna().sum()}")
    print(f"📊 Wszystkich zabiegów: {len(df_treatments_final)}")
    print(f"📊 Unikalnych zabiegów: {df_treatments_final['representative'].nunique()}")
    print(f"📊 Domen: {len(df_domains_final)}")
    print(f"\n💾 Pliki finalne:")
    print(f"   - {BASE_DIR}/final_tree.csv")
    print(f"   - {BASE_DIR}/final_treatments.csv")
    print(f"   - {BASE_DIR}/final_domains.csv")
    print(f"   - {BASE_DIR}/final_tree.json")
    print(f"\n🎯 Możesz teraz pobrać pliki z folderu: {BASE_DIR}")
    
    # Wyświetl przykłady
    print("\n📋 Przykładowe drzewo:")
    print(df_tree_final[["level1", "level2", "level3", "level4"]].head(20).to_string(index=False))
else:
    print("⚠️ Brak danych do eksportu")

print("\n" + "="*70)
print("✅ PIPELINE V2 ZAKOŃCZONY!")
print("="*70)
