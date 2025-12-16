# 🚀 Zaawansowane porady i optymalizacje

## 🎯 Optymalizacja jakości danych

### 1. Lepsze keywordy → lepsza baza
**Problem**: LLM generuje zbyt ogólne lub marketingowe frazy

**Rozwiązanie**:
```python
# FAZA 1: Dodaj więcej przykładów do prompta
user = f"""
Wygeneruj {MAX_KEYWORDS} polskich fraz...

DOBRE przykłady:
- mezoterapia igłowa twarzy
- botoks bruksizm
- liposukcja brzucha
- laser CO2 na blizny
- peeling kwasem migdałowym

ZŁE przykłady (UNIKAJ):
- medycyna estetyczna
- zabiegi odmładzające
- piękna skóra
- profesjonalne zabiegi
"""
```

### 2. Filtrowanie "śmieciowych" domen
**Problem**: W wynikach SERP są portale typu Booksy, ZnanyLekarz

**Rozwiązanie**: Rozszerz listę BAD:
```python
BAD = [
    # agregatory
    "facebook", "instagram", "youtube", "twitter", "tiktok", "pinterest",
    "znanylekarz", "booksy", "doctorfox", "znamilekarze", "medonet",
    # e-commerce
    "allegro", "olx", "ceneo", "empik", "rossmann",
    # media
    "onet", "wp", "interia", "gazeta", "tvn", "polsat",
    # inne
    "wikipedia", "wikihow", "reddit", "quora",
]

REQUIRED = ["klinika", "clinic", "med", "derma", "laser", "gabinet", "centrum"]

def is_clinic_domain(domain: str) -> bool:
    if any(b in domain for b in BAD):
        return False
    # WYMAGA przynajmniej 1 słowa kluczowego
    if not any(r in domain for r in REQUIRED):
        return False
    return True
```

### 3. Głębsze scrapowanie (substrony)
**Problem**: Główna strona nie zawiera oferty zabiegów

**Rozwiązanie**: Dodaj crawling
```python
def get_treatment_pages(domain: str) -> List[str]:
    """Znajdź substrony z ofertą zabiegów."""
    url = f"https://{domain}"
    try:
        r = requests.get(url, timeout=10)
        soup = BeautifulSoup(r.content, "html.parser")
        
        # Szukaj linków zawierających słowa kluczowe
        keywords = ["oferta", "zabiegi", "uslugi", "cennik", "treatments"]
        links = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if any(k in href.lower() for k in keywords):
                full_url = urljoin(url, href)
                links.append(full_url)
        
        return links[:MAX_PAGES_PER_DOMAIN]
    except:
        return [url]

# W FAZA 3:
for domain in tqdm(domains_df["domain"], desc="Scrapowanie"):
    urls = get_treatment_pages(domain)
    # ... scraping logic
```

---

## 🧠 Optymalizacja LLM

### 1. Few-shot prompting dla lepszej ekstrakcji
**Problem**: LLM wyciąga kategorie zamiast konkretnych zabiegów

**Rozwiązanie**:
```python
# FAZA 4: Dodaj przykłady do prompta
user = f"""
Tekst ze strony: {domain}
---
{text_chunk}
---

Przykłady DOBRYCH nazw zabiegów:
✅ mezoterapia peptydowa twarzy
✅ botoks bruksizmu
✅ peeling PRX-T33
✅ laser CO2 frakcyjny na blizny

Przykłady ZŁE (zbyt ogólne):
❌ zabiegi na twarz
❌ medycyna estetyczna
❌ usługi kosmetyczne
❌ terapie odmładzające

Wypisz WSZYSTKIE konkretne zabiegi z tekstu:
"""
```

### 2. Batch processing z context preservation
**Problem**: LLM traci kontekst przy dużych batchach

**Rozwiązanie**:
```python
def normalize_with_context(treatments: List[str], prev_normalized: List[str] = None) -> List[str]:
    """Normalizuj z zachowaniem kontekstu poprzedniego batcha."""
    context = ""
    if prev_normalized:
        context = f"\\nPoprzednio znormalizowane (dla spójności):\\n" + "\\n".join(prev_normalized[-10:])
    
    user = f"""
Znormalizuj zabiegi:{context}

Nowe do normalizacji:
{chr(10).join([f"{i+1}. {t}" for i, t in enumerate(treatments)])}
...
"""
    # ... rest of logic
```

### 3. Hierarchiczna budowa taksonomii (zamiast flat)
**Problem**: LLM ma problem z przypisaniem 500 zabiegów naraz

**Rozwiązanie**: Buduj drzewo krok po kroku
```python
# FAZA 7 (ulepszona):

# Krok 1: LLM tworzy Level 1 + Level 2
level1_2 = create_level_1_and_2(treatments_list)

# Krok 2: Dla każdej Level 2 → LLM tworzy Level 3
for l1, l2 in level1_2:
    treatments_subset = [t for t in treatments_list if belongs_to(t, l1, l2)]
    level3_list = create_level_3(treatments_subset, l1, l2)
    
    # Krok 3: Dla każdej Level 3 → przypisz zabiegi do Level 4
    for l3 in level3_list:
        treatments_final = [t for t in treatments_subset if belongs_to(t, l3)]
        assign_to_level_4(treatments_final, l1, l2, l3)
```

---

## ⚡ Optymalizacja wydajności

### 1. Caching embeddingów
**Problem**: Regenerowanie embeddingów przy każdym uruchomieniu

**Rozwiązanie**:
```python
import hashlib
import pickle

EMBEDDINGS_CACHE = f"{BASE_DIR}/embeddings_cache.pkl"

def embed_texts_cached(texts: List[str]) -> np.ndarray:
    """Embeddingi z cachowaniem."""
    # Load cache
    cache = {}
    if os.path.exists(EMBEDDINGS_CACHE):
        with open(EMBEDDINGS_CACHE, "rb") as f:
            cache = pickle.load(f)
    
    embeddings = []
    to_embed = []
    to_embed_indices = []
    
    for i, text in enumerate(texts):
        text_hash = hashlib.md5(text.encode()).hexdigest()
        if text_hash in cache:
            embeddings.append(cache[text_hash])
        else:
            to_embed.append(text)
            to_embed_indices.append(i)
            embeddings.append(None)
    
    # Embed only new texts
    if to_embed:
        new_embeddings = embed_texts(to_embed)
        for i, emb in zip(to_embed_indices, new_embeddings):
            text_hash = hashlib.md5(texts[i].encode()).hexdigest()
            cache[text_hash] = emb
            embeddings[i] = emb
    
    # Save cache
    with open(EMBEDDINGS_CACHE, "wb") as f:
        pickle.dump(cache, f)
    
    return np.array(embeddings)
```

### 2. Parallel scraping
**Problem**: Scrapowanie 50 domen trwa 30+ minut

**Rozwiązanie**:
```python
from concurrent.futures import ThreadPoolExecutor, as_completed

def scrape_domain(domain: str) -> dict:
    """Scrapuj jedną domenę (thread-safe)."""
    urls = get_treatment_pages(domain)
    texts = []
    for url in urls:
        text = scrape_url(url)
        if text:
            texts.append(text)
        time.sleep(0.5)
    
    return {
        "domain": domain,
        "text": " ".join(texts)[:50000],
        "num_pages": len(texts)
    }

# FAZA 3 (parallel):
scraped_data = []
with ThreadPoolExecutor(max_workers=5) as executor:
    futures = {executor.submit(scrape_domain, d): d for d in domains_df["domain"]}
    
    for future in tqdm(as_completed(futures), total=len(futures), desc="Scraping (parallel)"):
        try:
            result = future.result()
            scraped_data.append(result)
        except Exception as e:
            print(f"Error: {e}")
```

### 3. Streaming LLM responses
**Problem**: Czekanie na długie odpowiedzi LLM

**Rozwiązanie**:
```python
def or_chat_stream(messages: List[Dict], model: str = MODEL_NAME):
    """LLM z streamingiem (progress bar)."""
    resp = or_client.chat.completions.create(
        model=model,
        messages=messages,
        stream=True,
        temperature=0.2,
    )
    
    full_text = ""
    for chunk in resp:
        if chunk.choices[0].delta.content:
            content = chunk.choices[0].delta.content
            full_text += content
            print(content, end="", flush=True)
    
    print()  # newline
    return full_text
```

---

## 🔍 Validation i Quality Control

### 1. Automatyczne sprawdzanie kompletności drzewa
```python
def validate_tree(df_tree: pd.DataFrame, df_treatments: pd.DataFrame):
    """Sprawdź jakość drzewa."""
    print("\\n🔍 WALIDACJA DRZEWA:")
    
    # 1. Czy wszystkie zabiegi są w drzewie?
    treatments_in_tree = set(df_tree["level4"].unique())
    treatments_total = set(df_treatments["representative"].unique())
    missing = treatments_total - treatments_in_tree
    
    print(f"✅ Zabiegów w drzewie: {len(treatments_in_tree)}")
    print(f"❌ Zabiegów poza drzewem: {len(missing)}")
    if missing:
        print(f"   Przykłady: {list(missing)[:5]}")
    
    # 2. Czy są puste Level 3 (bez dzieci)?
    level3_counts = df_tree.groupby(["level1", "level2", "level3"]).size()
    empty_level3 = level3_counts[level3_counts < 2]
    print(f"⚠️ Level 3 z < 2 zabiegami: {len(empty_level3)}")
    
    # 3. Balans drzewa
    level1_counts = df_tree.groupby("level1").size().sort_values(ascending=False)
    print(f"\\n📊 Rozkład zabiegów per Level 1:")
    for l1, count in level1_counts.head(10).items():
        print(f"   {l1}: {count}")
    
    # 4. Najczęstsze słowa w Level 4 (sanity check)
    from collections import Counter
    words = " ".join(df_tree["level4"]).lower().split()
    common = Counter(words).most_common(10)
    print(f"\\n🔤 Najczęstsze słowa w Level 4: {common}")

# Po FAZA 7:
validate_tree(df_tree, df_unique_treatments)
```

### 2. Human-in-the-loop corrections
```python
def manual_corrections():
    """Ręczne poprawki po walidacji."""
    corrections = {
        "Level 3": {
            "Toksyna botulinowa": "Botoks i dysport",  # rename
            "Kwas hialuronowy": "Wypełniacze",
        },
        "Level 4": {
            "Botox": "Botoks (toksyna botulinowa)",
            "filler": "Wypełniacz kwasem hialuronowym",
        }
    }
    
    df_tree = load_df(f"{BASE_DIR}/phase7_taxonomy_tree.csv")
    
    for level, mappings in corrections.items():
        if level == "Level 3":
            df_tree["level3"] = df_tree["level3"].replace(mappings)
        elif level == "Level 4":
            df_tree["level4"] = df_tree["level4"].replace(mappings)
    
    save_df(df_tree, f"{BASE_DIR}/phase7_taxonomy_tree_corrected.csv")

# Po walidacji:
manual_corrections()
```

### 3. A/B testing różnych modeli
```python
def compare_models(treatments_sample: List[str]):
    """Porównaj jakość różnych modeli LLM."""
    models = [
        "openai/gpt-4.1-mini",
        "google/gemini-2.5-flash-preview-09-2025",
        "anthropic/claude-3.5-sonnet",
    ]
    
    results = {}
    for model in models:
        print(f"\\nTesting {model}...")
        normalized = normalize_treatments_batch(treatments_sample, model=model)
        results[model] = normalized
    
    # Porównaj
    print("\\n📊 PORÓWNANIE:")
    for i, orig in enumerate(treatments_sample[:5]):
        print(f"\\nOryginalny: {orig}")
        for model in models:
            print(f"  {model}: {results[model].get(orig, 'ERROR')}")

# Przed FAZA 5:
sample = df_raw["treatment"].sample(20).tolist()
compare_models(sample)
```

---

## 💾 Backup i wersjonowanie

### 1. Automatyczne backupy po każdej fazie
```python
import shutil
from datetime import datetime

def backup_phase(phase_num: int, files: List[str]):
    """Backup plików z danej fazy."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = f"{BASE_DIR}/backups/phase{phase_num}_{timestamp}"
    os.makedirs(backup_dir, exist_ok=True)
    
    for file in files:
        src = f"{BASE_DIR}/{file}"
        if os.path.exists(src):
            shutil.copy(src, backup_dir)
    
    print(f"💾 Backup: {backup_dir}")

# Po FAZA 5:
backup_phase(5, ["phase5_normalized_treatments.csv"])
```

### 2. Git integration (dla advanced users)
```python
def git_commit_phase(phase_num: int, message: str):
    """Commituj wyniki fazy do git."""
    os.system(f"cd {BASE_DIR} && git add .")
    os.system(f"cd {BASE_DIR} && git commit -m 'FAZA {phase_num}: {message}'")

# Po każdej fazie:
git_commit_phase(5, "Normalizacja zabiegów zakończona")
```

---

## 🌐 Deployment i produkcja

### 1. API endpoint dla wyszukiwarki
```python
from fastapi import FastAPI
import pandas as pd

app = FastAPI()

df_tree = pd.read_csv("final_tree.csv")
df_treatments = pd.read_csv("final_treatments.csv")

@app.get("/search")
def search(query: str, limit: int = 10):
    """Wyszukaj zabiegi."""
    # Simple full-text search
    results = df_tree[
        df_tree["level4"].str.contains(query, case=False, na=False) |
        df_tree["level3"].str.contains(query, case=False, na=False)
    ].head(limit)
    
    return results.to_dict(orient="records")

@app.get("/category/{level1}")
def get_category(level1: str):
    """Pokaż całą kategorię."""
    return df_tree[df_tree["level1"] == level1].to_dict(orient="records")

# Run: uvicorn main:app --reload
```

### 2. Elasticsearch indexing
```python
from elasticsearch import Elasticsearch

es = Elasticsearch(["http://localhost:9200"])

def index_tree_to_elasticsearch():
    """Zaindeksuj drzewo w Elasticsearch."""
    df = load_df(f"{BASE_DIR}/final_tree.csv")
    
    for idx, row in df.iterrows():
        doc = {
            "level1": row["level1"],
            "level2": row["level2"],
            "level3": row["level3"],
            "level4": row["level4"],
            "description": row["description"],
            "hierarchy": f"{row['level1']} > {row['level2']} > {row['level3']} > {row['level4']}"
        }
        
        es.index(index="treatments", id=idx, body=doc)
    
    print(f"✅ Indexed {len(df)} documents")

# Po FAZA 10:
index_tree_to_elasticsearch()
```

### 3. Streamlit dashboard
```python
import streamlit as st
import pandas as pd

st.title("🏥 Wyszukiwarka zabiegów medycyny estetycznej")

df_tree = pd.read_csv("final_tree.csv")

# Sidebar filters
level1 = st.sidebar.selectbox("Kategoria", ["Wszystkie"] + df_tree["level1"].unique().tolist())
level2 = st.sidebar.selectbox("Podkategoria", ["Wszystkie"] + df_tree["level2"].unique().tolist())

# Filter
filtered = df_tree.copy()
if level1 != "Wszystkie":
    filtered = filtered[filtered["level1"] == level1]
if level2 != "Wszystkie":
    filtered = filtered[filtered["level2"] == level2]

# Search
query = st.text_input("Szukaj zabiegu:")
if query:
    filtered = filtered[filtered["level4"].str.contains(query, case=False, na=False)]

# Display
st.dataframe(filtered[["level1", "level2", "level3", "level4", "description"]])

# Stats
st.sidebar.metric("Wszystkich zabiegów", len(df_tree))
st.sidebar.metric("Wyniki", len(filtered))

# Run: streamlit run dashboard.py
```

---

## 🐛 Troubleshooting

### Problem: "JSONDecodeError" w or_chat_json
**Rozwiązanie**:
```python
def or_chat_json_safe(system: str, user: str, max_retries: int = 3):
    """or_chat_json z retry logic."""
    for attempt in range(max_retries):
        try:
            return or_chat_json(system, user)
        except json.JSONDecodeError as e:
            print(f"⚠️ JSON error (attempt {attempt+1}/{max_retries}): {e}")
            if attempt == max_retries - 1:
                # Last attempt: return empty
                return {}
            time.sleep(2)
```

### Problem: "Rate limit exceeded" (OpenRouter)
**Rozwiązanie**:
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(5), wait=wait_exponential(min=1, max=60))
def or_chat_with_retry(messages, **kwargs):
    """LLM call z automatic retry."""
    return or_chat(messages, **kwargs)
```

### Problem: HDBSCAN "No clusters found"
**Rozwiązanie**:
```python
# Obniż min_cluster_size
clusterer = hdbscan.HDBSCAN(
    min_cluster_size=1,  # zamiast 2
    min_samples=1,
    metric="cosine",
    cluster_selection_epsilon=0.1  # więcej klastrów
)
```

---

## 📚 Dodatkowe zasoby

### Literatura
- [HDBSCAN documentation](https://hdbscan.readthedocs.io/)
- [OpenAI embeddings guide](https://platform.openai.com/docs/guides/embeddings)
- [BeautifulSoup tutorial](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)

### Podobne projekty
- [Medical taxonomy datasets](https://www.nlm.nih.gov/research/umls/)
- [HealthTerm - medical ontology](https://www.healthterm.com/)

### Społeczność
- Reddit: r/MachineLearning, r/LanguageModels
- Discord: OpenAI, LangChain

---

**Happy coding! 🚀**
