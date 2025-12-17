# 🏥 Wyszukiwarka zabiegów medycyny estetycznej

## 📋 Przegląd projektu

System automatycznie buduje **4-poziomowe drzewo taksonomiczne** zabiegów medycyny estetycznej w Polsce, wykorzystując:
- 🤖 **LLM** (OpenRouter) - ekstrakcja, normalizacja, taksonomia
- 🔍 **SERP data** (serpdata.io) - wyszukiwanie domen klinik
- 🧠 **Embeddings** (OpenAI) - deduplikacja semantyczna, clustering
- 🎯 **Jina rerank** (opcjonalnie) - ranking podobieństwa
- 🕷️ **Web scraping** - ekstrakcja ofert z domen

## 🌳 Struktura drzewa

```
Level 1: GŁÓWNA KATEGORIA
└─ Level 2: PODKATEGORIA
   └─ Level 3: RODZINA ZABIEGÓW
      └─ Level 4: KONKRETNY ZABIEG
```

**Przykład:**
```
Dermatologia
└─ Dermatologia estetyczna
   └─ Mezoterapia igłowa
      └─ Mezoterapia peptydowa twarzy
```

## 🚀 Pipeline (10 faz)

### **FAZA 0**: Setup
- Instalacja pakietów
- Konfiguracja kluczy API
- Helpery (clean_text, embeddings, LLM calls)

### **FAZA 1**: Generowanie keywordów (LLM)
- LLM generuje ~20 fraz SEO (np. "mezoterapia igłowa twarzy")
- Deduplikacja i normalizacja
- **Output**: `phase1_keywords.csv`

### **FAZA 2**: SERP → domeny
- Dla każdego keywordu: pobierz top 10 URL-i z serpdata.io
- Wyciągnij domeny i filtruj (tylko kliniki)
- **Output**: 
  - `phase2_serp_keyword_url.csv`
  - `phase2_unique_urls.csv`
  - `domains.csv`

### **FAZA 3**: Scrapowanie domen
- Dla każdej domeny: pobierz max. 12 stron
- Wyciągnij czysty tekst (BeautifulSoup)
- **Output**: `phase3_scraped_content.csv`

### **FAZA 4**: Ekstrakcja zabiegów (LLM)
- LLM wyciąga wszystkie nazwy zabiegów z tekstów
- Wstępna deduplikacja
- **Output**: `phase4_raw_treatments.csv`

### **FAZA 5**: Filtrowanie i normalizacja
- Usuń duplikaty semantyczne (embeddings + cosine similarity)
- LLM normalizuje nazwy (np. "botox czoło" → "Botoks zmarszczek czoła")
- **Output**: `phase5_normalized_treatments.csv`

### **FAZA 6**: Clustering i synonimy
- HDBSCAN clustering na embeddingach
- LLM wybiera reprezentanta klastra (opcjonalnie Jina rerank)
- **Output**: 
  - `phase6_clustered_treatments.csv`
  - `phase6_unique_treatments.csv`

### **FAZA 7**: Budowa taksonomii 4-poziomowej (LLM)
- LLM tworzy hierarchię Level1 → Level2 → Level3 → Level4
- Konsolidacja i deduplikacja ścieżek
- **Output**: `phase7_taxonomy_tree.csv`

### **FAZA 8**: Mapowanie zabiegów do drzewa
- Embeddings matching: każdy zabieg → najbliższy Level 4
- **Output**: `phase8_treatments_mapped.csv`

### **FAZA 9**: Generowanie opisów
- LLM generuje krótkie opisy (2-3 zdania) dla każdego Level 4
- **Output**: `phase9_tree_with_descriptions.csv`

### **FAZA 10**: Eksport finalny
- **Output**:
  - ✅ `final_tree.csv` - kompletne drzewo z opisami
  - ✅ `final_treatments.csv` - wszystkie zabiegi z przypisaniami
  - ✅ `final_domains.csv` - domeny z statystykami
  - ✅ `final_tree.json` (bonus) - hierarchiczny JSON

## 📦 Wymagania

### Pakiety Python
```bash
pip install openai pandas requests tqdm beautifulsoup4 scikit-learn scipy hdbscan
```

### Klucze API (Colab Secrets)
W Google Colab: **🔑 Obiekty tajne** (lewy sidebar)

Dodaj:
- `openrouter_api` - klucz OpenRouter (https://openrouter.ai)
- `serpdata_key` - klucz SerpData (https://serpdata.io)
- `jina_api` - klucz Jina AI (opcjonalnie, https://jina.ai)

## ⚙️ Konfiguracja

W notebooku możesz dostosować:

```python
# Limity
MAX_KEYWORDS = 20              # ile keywordów generować
SERP_TOP_N = 10               # ile URL-i per keyword
MAX_DOMAINS = 50              # ile domen scrapować
MAX_PAGES_PER_DOMAIN = 12     # ile stron per domena

# Filtry
MIN_TEXT_LEN = 5              # min długość nazwy zabiegu
MAX_TEXT_LEN = 120            # max długość nazwy zabiegu
SEMANTIC_SIM_THRESHOLD = 0.22 # próg deduplikacji (niższe = więcej duplikatów usuniętych)

# Jina rerank
USE_JINA = True               # czy używać Jina rerank
JINA_RERANK_THRESHOLD = 0.25  # próg dla rerankingu

# Modele
MODEL_NAME = "openai/gpt-4.1-mini"  # model LLM
EMBED_MODEL = "openai/text-embedding-3-small"  # model embeddingów
```

## 📊 Przykładowe wyniki

Po uruchomieniu otrzymasz:

**final_tree.csv:**
| level1 | level2 | level3 | level4 | description |
|--------|--------|--------|--------|-------------|
| Dermatologia | Dermatologia estetyczna | Mezoterapia igłowa | Mezoterapia peptydowa twarzy | Zabieg polegający na... |
| Dermatologia | Dermatologia estetyczna | Toksyna botulinowa | Botoks zmarszczek czoła | Iniekcje toksyny botulinowej... |

**final_treatments.csv:**
| domain | treatment | representative | level1 | level2 | level3 | level4 |
|--------|-----------|----------------|--------|--------|--------|--------|
| klinika-xyz.pl | botox czoło | Botoks zmarszczek czoła | Dermatologia | ... | ... | ... |

**final_domains.csv:**
| domain | num_pages | total_treatments | unique_treatments |
|--------|-----------|------------------|-------------------|
| klinika-xyz.pl | 12 | 45 | 32 |

## 🎯 Użycie

### Google Colab (zalecane)
1. Otwórz notebook w Colab
2. Dodaj klucze API do **Obiekty tajne**
3. Uruchom wszystkie komórki (**Runtime → Run all**)
4. Poczekaj ~20-60 minut (zależnie od liczby domen)
5. Pobierz pliki z `/content/baza_zabiegow_v0/`

### Lokalnie (Python)
```bash
# Zainstaluj Jupyter
pip install jupyter

# Ustaw zmienne środowiskowe
export OPENROUTER_API_KEY="..."
export SERPDATA_KEY="..."
export JINA_API_KEY="..."

# Uruchom notebook
jupyter notebook aesthetic_medicine_search_engine.ipynb
```

## 🔧 Rozwiązywanie problemów

### Błąd: "Brak secreta: openrouter_api"
- Dodaj klucz w Colab: **Obiekty tajne** → `openrouter_api`

### LLM zwraca złe JSON-y
- Zwiększ `max_tokens` w `or_chat_json()`
- Spróbuj innego modelu (np. `google/gemini-2.5-flash-preview-09-2025`)

### Za dużo/za mało zabiegów
- Dostosuj `SEMANTIC_SIM_THRESHOLD` (niższe = więcej duplikatów usuniętych)
- Dostosuj `MIN_TEXT_LEN` / `MAX_TEXT_LEN`

### Timeouty SerpData
- Zwiększ `time.sleep(2)` po każdym zapytaniu
- Zmniejsz `MAX_KEYWORDS`

### HDBSCAN nie znajduje klastrów
- Obniż `min_cluster_size` w HDBSCAN (np. do 1)
- Zwiększ liczbę zabiegów (więcej domen)

## 📈 Optymalizacja kosztów

**Szacunkowe koszty** (dla 50 domen, 20 keywordów):
- **OpenRouter**: ~$2-5 (zależnie od modelu)
- **SerpData**: ~$0.50 (20 zapytań × $0.025)
- **Jina AI**: ~$0.10 (reranking)

**Jak zmniejszyć koszty:**
- Użyj `openai/gpt-4.1-mini` zamiast GPT-5
- Zmniejsz `MAX_DOMAINS` i `MAX_KEYWORDS`
- Wyłącz Jina (`USE_JINA = False`)
- Użyj mniejszego modelu embeddingów (`text-embedding-3-small`)

## 🛠️ Dalszy rozwój

### Możliwe ulepszenia:
1. **Ceny zabiegów**: scraping cen + analiza rynku
2. **Lokalizacja**: geograficzne przypisanie domen (miasta)
3. **Wyszukiwarka**: FastAPI + Elasticsearch dla UX
4. **Dashboard**: Streamlit/Gradio do wizualizacji drzewa
5. **Aktualizacja**: automatyczne odświeżanie co miesiąc
6. **Multi-języki**: rozszerzenie na inne kraje (EN, DE, CZ)

### Integracje:
- **Elasticsearch**: indeksowanie + full-text search
- **PostgreSQL**: relacyjna baza danych (drzewa → tabele)
- **React/Next.js**: frontend wyszukiwarki
- **Zapier/n8n**: automatyzacja aktualizacji

## 📝 Licencja

MIT License - użyj jak chcesz!

## 🤝 Kontakt

Pytania? Issues? PRs welcome! 🚀

---

**Made with ❤️ by AI + Human**
