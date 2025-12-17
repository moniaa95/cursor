# 📁 Struktura projektu - wszystkie pliki

## 🎯 Główne pliki

### **aesthetic_medicine_search_engine.ipynb** ⭐
**Typ**: Google Colab Notebook  
**Rozmiar**: ~300 KB  
**Opis**: Kompletny pipeline 10-fazowy. To główny plik projektu.

**Zawiera**:
- Faza 0-10 (setup → eksport)
- Interactive progress bars
- Checkpointing po każdej fazie
- Markdown documentation w komórkach

**Użycie**:
```
1. Upload do Google Colab
2. Dodaj klucze API do Secrets
3. Runtime → Run all
```

---

### **standalone_version.py** 
**Typ**: Python script (CLI)  
**Rozmiar**: ~20 KB  
**Opis**: Lokalna wersja (fazy 1-4). Nie wymaga Colaba.

**Features**:
- Command-line arguments
- Environment variables dla kluczy
- Checkpointing (restart from phase N)

**Użycie**:
```bash
export OPENROUTER_API_KEY="..."
export SERPDATA_KEY="..."

python standalone_version.py \
  --output-dir ./output \
  --max-domains 50 \
  --start-from 1
```

**Argumenty**:
```
--project-name         Nazwa projektu (default: baza_zabiegow_v0)
--output-dir          Katalog wyjściowy (default: ./output)
--max-keywords        Liczba keywordów (default: 20)
--max-domains         Liczba domen (default: 50)
--max-pages           Stron per domena (default: 12)
--semantic-threshold  Próg podobieństwa (default: 0.22)
--use-jina           Włącz Jina rerank (flag)
--model              Model LLM (default: openai/gpt-4.1-mini)
--embed-model        Model embeddingów (default: text-embedding-3-small)
--start-from         Zacznij od fazy N (default: 1)
```

---

### **check_setup.py**
**Typ**: Helper script  
**Rozmiar**: ~5 KB  
**Opis**: Sprawdza konfigurację przed uruchomieniem.

**Sprawdza**:
- ✅ Wersja Python (≥3.8)
- ✅ Zainstalowane pakiety
- ✅ Klucze API w environment
- ✅ Połączenie z API (OpenRouter, SerpData, Jina)

**Użycie**:
```bash
python check_setup.py
```

---

## 📚 Dokumentacja

### **README.md** ⭐
**Typ**: Dokumentacja techniczna (EN/PL mix)  
**Rozmiar**: ~15 KB

**Zawiera**:
- Przegląd projektu
- Szczegółowy opis 10 faz
- Konfiguracja i parametry
- Troubleshooting
- Przykłady użycia

**Dla kogo**: Developerzy, technical users

---

### **PODSUMOWANIE.md** ⭐
**Typ**: Podsumowanie (PL)  
**Rozmiar**: ~12 KB

**Zawiera**:
- Co otrzymujesz (pliki wyjściowe)
- Jak uruchomić (Colab + lokalne)
- Oczekiwane wyniki
- Koszty
- Troubleshooting PL
- Przykłady zastosowań

**Dla kogo**: Non-technical users, klienci

---

### **QUICKSTART.md** ⭐
**Typ**: Quick start guide (PL)  
**Rozmiar**: ~3 KB

**Zawiera**:
- 3 kroki do uruchomienia
- Checklist
- Szybkie rozwiązania problemów

**Dla kogo**: Wszyscy (first-time users)

---

### **EXAMPLE_OUTPUT.md**
**Typ**: Przykłady danych  
**Rozmiar**: ~10 KB

**Zawiera**:
- Przykładowe `final_tree.csv`
- Przykładowe `final_treatments.csv`
- Przykładowe `final_domains.csv`
- Przykładowe `final_tree.json`
- Statystyki
- Przykłady użycia w kodzie (Python)

**Dla kogo**: Data scientists, developerzy

---

### **ADVANCED_TIPS.md**
**Typ**: Zaawansowane porady  
**Rozmiar**: ~15 KB

**Zawiera**:
- Optymalizacja jakości danych
- Optymalizacja LLM (prompting)
- Optymalizacja wydajności (caching, parallel)
- Validation i quality control
- Deployment (FastAPI, Elasticsearch, Streamlit)
- Troubleshooting zaawansowany

**Dla kogo**: Advanced users, production deployment

---

### **CHANGELOG.md**
**Typ**: Historia zmian  
**Rozmiar**: ~4 KB

**Zawiera**:
- v1.0.0 (current release)
- Planned features (v1.1, v1.2, v2.0)
- Known issues
- Migration guide

**Dla kogo**: Maintainers, contributors

---

### **PROJECT_FILES.md**
**Typ**: Ten plik (index)  
**Rozmiar**: ~8 KB

**Zawiera**:
- Opis wszystkich plików projektu
- Użycie i argumenty
- Hierarchia ważności

---

## ⚙️ Konfiguracja

### **requirements.txt**
**Typ**: Python dependencies  
**Rozmiar**: ~1 KB

**Zawiera**:
```
openai>=1.3.0
pandas>=2.0.0
numpy>=1.24.0
requests>=2.31.0
tqdm>=4.65.0
beautifulsoup4>=4.12.0
scikit-learn>=1.3.0
scipy>=1.11.0
hdbscan>=0.8.33
# + optional: fastapi, streamlit, elasticsearch...
```

**Instalacja**:
```bash
pip install -r requirements.txt
```

---

### **.env.example**
**Typ**: Example environment config  
**Rozmiar**: ~500 bytes

**Zawiera**:
```bash
OPENROUTER_API_KEY=sk-or-v1-...
SERPDATA_KEY=...
JINA_API_KEY=...
PROJECT_NAME=baza_zabiegow_v0
MAX_KEYWORDS=20
MAX_DOMAINS=50
```

**Użycie**:
```bash
cp .env.example .env
# Edytuj .env i dodaj swoje klucze
source .env  # lub export ...
```

---

### **.gitignore**
**Typ**: Git ignore rules  
**Rozmiar**: ~500 bytes

**Zawiera**:
- Python cache (`__pycache__`, `*.pyc`)
- Virtual environments (`venv/`, `env/`)
- Output data (`*.csv`, `*.json`)
- API keys (`.env`, `*.key`)
- OS files (`.DS_Store`, `Thumbs.db`)

---

### **LICENSE**
**Typ**: MIT License  
**Rozmiar**: ~1 KB

**Zawiera**: Standard MIT License text

---

## 📝 Inne pliki

### **skrypt** (Twój oryginalny plik)
**Typ**: Python/Colab script  
**Rozmiar**: ~10 KB  
**Opis**: Twój początkowy kod (FAZA 0-2). Zachowany dla porównania.

---

## 📊 Hierarchia ważności

### ⭐⭐⭐ MUST READ (zacznij tutaj)
1. **QUICKSTART.md** - 5 minut do pierwszego uruchomienia
2. **aesthetic_medicine_search_engine.ipynb** - główny notebook
3. **PODSUMOWANIE.md** - pełne wyjaśnienie po polsku

### ⭐⭐ SHOULD READ (jak masz pytania)
4. **README.md** - dokumentacja techniczna
5. **EXAMPLE_OUTPUT.md** - zobacz co dostaniesz
6. **check_setup.py** - sprawdź konfigurację

### ⭐ NICE TO READ (zaawansowane)
7. **ADVANCED_TIPS.md** - optymalizacje
8. **standalone_version.py** - lokalna wersja
9. **CHANGELOG.md** - co jest nowe

### 📋 Reference (jak potrzebujesz)
10. **requirements.txt** - lista zależności
11. **.env.example** - przykład konfiguracji
12. **PROJECT_FILES.md** - ten plik

---

## 🗂️ Sugerowana struktura katalogów

Po uruchomieniu będziesz mieć:

```
workspace/
├── aesthetic_medicine_search_engine.ipynb  ← OTWÓRZ TO PIERWSZE
├── QUICKSTART.md                           ← PRZECZYTAJ TO PIERWSZE
├── PODSUMOWANIE.md                         ← POTEM TO
├── README.md
├── EXAMPLE_OUTPUT.md
├── ADVANCED_TIPS.md
├── standalone_version.py
├── check_setup.py
├── requirements.txt
├── .env.example
├── .gitignore
├── LICENSE
└── CHANGELOG.md

# Po uruchomieniu Colaba:
/content/baza_zabiegow_v0/               ← WYNIKI TUTAJ
├── phase1_keywords.csv
├── phase2_serp_keyword_url.csv
├── phase2_unique_urls.csv
├── domains.csv
├── phase3_scraped_content.csv
├── phase4_raw_treatments.csv
├── phase5_normalized_treatments.csv
├── phase6_clustered_treatments.csv
├── phase6_unique_treatments.csv
├── phase7_taxonomy_tree.csv
├── phase8_treatments_mapped.csv
├── phase9_tree_with_descriptions.csv
├── final_tree.csv                        ← GŁÓWNY WYNIK
├── final_treatments.csv                  ← MAPOWANIE
├── final_domains.csv                     ← STATYSTYKI
└── final_tree.json                       ← JSON API
```

---

## 🎯 Quick Navigation

**Chcę zacząć**: → `QUICKSTART.md`  
**Chcę wiedzieć więcej**: → `PODSUMOWANIE.md`  
**Mam problem**: → `README.md` (Troubleshooting)  
**Chcę optymalizować**: → `ADVANCED_TIPS.md`  
**Chcę lokalnie**: → `standalone_version.py --help`  
**Sprawdzam setup**: → `python check_setup.py`  
**Przykłady danych**: → `EXAMPLE_OUTPUT.md`  
**Co jest nowe**: → `CHANGELOG.md`  

---

## 📞 Wsparcie

**Pytania techniczne**: Sprawdź `README.md`  
**Pytania ogólne**: Sprawdź `PODSUMOWANIE.md`  
**Błędy**: Sprawdź `CHANGELOG.md` (Known Issues)  
**Zaawansowane**: Sprawdź `ADVANCED_TIPS.md`  

---

**Last updated**: December 16, 2025

**Total project size**: ~500 KB (bez output data)  
**Lines of code**: ~5000 (notebook + standalone)  
**Documentation pages**: ~60 (wszystkie MD pliki)  
