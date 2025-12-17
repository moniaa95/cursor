# ⚡ Quick Start - 5 minut

## 🎯 Cel
Zbudować 4-poziomowe drzewo zabiegów medycyny estetycznej w Polsce.

---

## 📋 Co potrzebujesz?

### 1. Klucze API
- **OpenRouter**: https://openrouter.ai/keys (~$3-5)
- **SerpData**: https://serpdata.io/api-keys (~$0.50)
- **Jina AI** (opcjonalnie): https://jina.ai/ (~$0.10)

### 2. Google Colab (GRATIS)
- Konto Google
- Przeglądarka

---

## 🚀 Start (3 kroki)

### Krok 1: Otwórz Colab
1. Idź do: https://colab.research.google.com/
2. Kliknij: **File → Upload notebook**
3. Wgraj: `aesthetic_medicine_search_engine.ipynb`

### Krok 2: Dodaj klucze
1. Kliknij: **🔑 ikona klucza** (lewy sidebar)
2. Dodaj 3 sekrety:
   - `openrouter_api` → Twój klucz OpenRouter
   - `serpdata_key` → Twój klucz SerpData
   - `jina_api` → Twój klucz Jina (opcjonalnie)

### Krok 3: Uruchom
1. Kliknij: **Runtime → Run all**
2. Czekaj ~30-60 minut ☕
3. Gotowe! 🎉

---

## 📦 Co otrzymujesz?

Po zakończeniu znajdziesz w `/content/baza_zabiegow_v0/`:

```
final_tree.csv         ← Drzewo zabiegów (Level 1-4 + opisy)
final_treatments.csv   ← Wszystkie zabiegi z przypisaniami
final_domains.csv      ← Statystyki domen/klinik
final_tree.json        ← Hierarchiczny JSON
```

---

## 📊 Przykładowy wynik

**final_tree.csv** (~200-500 zabiegów):

| level1 | level2 | level3 | level4 |
|--------|--------|--------|--------|
| Dermatologia | Dermatologia estetyczna | Mezoterapia | Mezoterapia peptydowa twarzy |
| Dermatologia | Dermatologia estetyczna | Botoks | Botoks zmarszczek czoła |
| Chirurgia | Chirurgia twarzy | Nos | Rinoplastyka |

---

## ⚙️ Konfiguracja (opcjonalnie)

W notebooku możesz zmienić:

```python
MAX_KEYWORDS = 20         # Ile keywordów (więcej = więcej czasu)
MAX_DOMAINS = 50          # Ile domen (więcej = więcej zabiegów)
MAX_PAGES_PER_DOMAIN = 12 # Ile stron per domena
```

---

## 💰 Koszty

Dla domyślnych ustawień (50 domen, 20 keywordów):
- **OpenRouter**: $2-5
- **SerpData**: $0.50
- **Jina**: $0.10
- **Razem**: ~$3-6

---

## 🐛 Problemy?

### "Brak secreta: openrouter_api"
→ Dodaj klucz w Colab (🔑 → Obiekty tajne)

### "Rate limit exceeded"
→ Zmniejsz `MAX_DOMAINS` do 20

### Za mało zabiegów
→ Zwiększ `MAX_DOMAINS` do 100

### Za dużo duplikatów
→ Zwiększ `SEMANTIC_SIM_THRESHOLD` do 0.35

---

## 📚 Więcej info?

- **Pełna dokumentacja**: `README.md`
- **Przykłady**: `EXAMPLE_OUTPUT.md`
- **Zaawansowane**: `ADVANCED_TIPS.md`
- **Podsumowanie PL**: `PODSUMOWANIE.md`

---

## ✅ Checklist

- [ ] Mam klucze API (OpenRouter + SerpData)
- [ ] Otworzyłem notebook w Colab
- [ ] Dodałem klucze do Sekretów
- [ ] Uruchomiłem "Run all"
- [ ] Czekam na wyniki (30-60 min)
- [ ] Pobieram pliki z `/content/baza_zabiegow_v0/`

---

**That's it! 🎉**

Jeśli coś nie działa: zerknij do `README.md` lub `PODSUMOWANIE.md`.
