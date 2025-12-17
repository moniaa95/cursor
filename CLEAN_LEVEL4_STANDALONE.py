# ============================================================
# SKRYPT DO CZYSZCZENIA LEVEL 4 - STANDALONE
# Wklej jako NOWĄ komórkę w Colabie (na końcu, po pipeline)
# ============================================================

import pandas as pd
import re
import os
from difflib import SequenceMatcher

print("="*70)
print("🧹 CZYSZCZENIE LEVEL 4 (usuwanie zbędnych)")
print("="*70)

# ⚠️ ZMIEŃ NA SWOJĄ ŚCIEŻKĘ jeśli inna!
BASE_DIR = "/content/baza_zabiegow_v0"  # Twój folder z danymi

# Wczytaj final_tree.csv
file_path = f"{BASE_DIR}/final_tree.csv"

if not os.path.exists(file_path):
    print(f"❌ BŁĄD: Plik nie istnieje: {file_path}")
    print(f"\n💡 Dostępne pliki w {BASE_DIR}:")
    if os.path.exists(BASE_DIR):
        for f in os.listdir(BASE_DIR):
            if f.endswith('.csv'):
                print(f"      ✅ {f}")
    else:
        print(f"      ❌ Katalog {BASE_DIR} nie istnieje!")
        print(f"\n📁 Dostępne katalogi w /content/:")
        for d in os.listdir('/content/'):
            if os.path.isdir(f'/content/{d}'):
                print(f"      - {d}")
    raise FileNotFoundError(f"Brak pliku: {file_path}")

print(f"\n📂 Wczytuję: {file_path}")
df = pd.read_csv(file_path)

print(f"\n📊 PRZED czyszczeniem:")
print(f"   Wszystkich wierszy: {len(df)}")
print(f"   Level 4 wypełnionych: {df['level4'].notna().sum()}")
print(f"   Level 4 pustych: {df['level4'].isna().sum()}")

# ============================================================
# FUNKCJE POMOCNICZE
# ============================================================

def text_similarity(a, b):
    """Oblicza podobieństwo tekstowe (0-1)"""
    if not isinstance(a, str) or not isinstance(b, str):
        return 0
    a = a.lower().strip()
    b = b.lower().strip()
    return SequenceMatcher(None, a, b).ratio()

def normalize_text(s):
    """Normalizuje tekst (lowercase, bez diakrytyki)"""
    if not isinstance(s, str):
        return ""
    s = s.lower().strip()
    # usuń znaki specjalne
    s = re.sub(r'[^a-ząćęłńóśźż\s]', '', s)
    return s

def word_count(s):
    """Liczy słowa"""
    if not isinstance(s, str):
        return 0
    return len(s.split())

# ============================================================
# SŁOWA KLUCZOWE (atomowe zabiegi)
# ============================================================

ATOMIC_KEYWORDS = [
    # Konsultacje i diagnostyka
    "konsultacja", "diagnostyka", "badanie", "wizyta", "ocena",
    
    # Konkretne zabiegi (nie rodziny)
    "depilacja", "woskowanie",
    "blefaroplastyka", "otoplastyka", "rinoplastyka",
    "liposukcja", "abdominoplastyka",
    "przeszczep", "transplantacja",
    "baby doll", "russian lips",
    "otoplastyka",
    "mammoplastyka",
    "test", "analiza",
    
    # Zabiegi jednorazowe
    "implant", "wszczep",
]

FAMILY_KEYWORDS = [
    # To są RODZINY (powinny mieć Level 4)
    "mezoterapia", "mikronakłuwanie",
    "toksyna botulinowa", "botoks", "botox",
    "wypełniacze", "fillery", "kwas hialuronowy",
    "peeling", "peelingi",
    "laser", "lasery", "laserowe",
    "lifting", "nici",
    "osocze", "prp",
    "radiofrekwencja", "rf",
    "ultradźwięki", "hifu",
    "zabiegi", "terapia", "leczenie",
    "usuwanie", "modelowanie",
]

# ============================================================
# REGUŁY CZYSZCZENIA
# ============================================================

cleaned_count = 0
cleaned_examples = []

for idx, row in df.iterrows():
    l3 = row['level3']
    l4 = row['level4']
    
    # Skip jeśli Level 4 już jest puste
    if pd.isna(l4) or l4 == "" or str(l4).lower() in ["null", "none", "nan"]:
        continue
    
    should_clean = False
    reason = ""
    
    # REGUŁA 1: Level 3 i Level 4 bardzo podobne (>85% podobieństwa)
    similarity = text_similarity(str(l3), str(l4))
    if similarity > 0.85:
        should_clean = True
        reason = f"Podobieństwo {similarity:.0%}"
    
    # REGUŁA 2: Level 4 jest zawarty w Level 3 (duplikat)
    l3_norm = normalize_text(str(l3))
    l4_norm = normalize_text(str(l4))
    if l4_norm and l4_norm in l3_norm and len(l4_norm) > 3:
        should_clean = True
        reason = "Level 4 zawarty w Level 3"
    
    # REGUŁA 3: Level 3 zawiera słowo atomowe (konkretny zabieg)
    for keyword in ATOMIC_KEYWORDS:
        if keyword in l3_norm:
            # CHYBA ŻE Level 3 też zawiera słowo rodzinne
            has_family = any(fam in l3_norm for fam in FAMILY_KEYWORDS)
            if not has_family:
                should_clean = True
                reason = f"Atomowy zabieg: '{keyword}'"
                break
    
    # REGUŁA 4: Level 4 jest bardzo krótkie (<3 słowa) i podobne
    if word_count(str(l4)) < 3 and similarity > 0.7:
        should_clean = True
        reason = "Krótkie i podobne"
    
    # REGUŁA 5: Level 3 ma >7 słów (już bardzo szczegółowe)
    if word_count(str(l3)) > 7:
        should_clean = True
        reason = "Level 3 zbyt szczegółowe (>7 słów)"
    
    # REGUŁA 6: Level 4 to samo słowo co ostatnie w Level 3
    l3_words = str(l3).lower().split()
    l4_words = str(l4).lower().split()
    if l3_words and l4_words and len(l3_words) > 1:
        if l3_words[-1] == l4_words[0] or l3_words[-1] == l4_words[-1]:
            should_clean = True
            reason = "Level 4 powtarza słowo z L3"
    
    # Wykonaj czyszczenie
    if should_clean:
        df.at[idx, 'level4'] = None
        cleaned_count += 1
        
        # Zapisz przykłady
        if cleaned_count <= 15:
            cleaned_examples.append({
                'l1': row['level1'],
                'l2': row['level2'],
                'l3': l3,
                'l4': l4,
                'reason': reason
            })

# ============================================================
# PODSUMOWANIE I ZAPIS
# ============================================================

print("\n" + "="*70)
print("📊 PODSUMOWANIE CZYSZCZENIA:")
print("="*70)
print(f"✅ Wyczyszczono Level 4: {cleaned_count} wierszy")
print(f"\n📊 PO czyszczeniu:")
print(f"   Wszystkich wierszy: {len(df)}")
print(f"   Level 4 wypełnionych: {df['level4'].notna().sum()}")
print(f"   Level 4 pustych: {df['level4'].isna().sum()}")
print(f"   Procent pustych: {df['level4'].isna().sum() / len(df) * 100:.1f}%")

# Zapisz
output_path = f"{BASE_DIR}/final_tree_cleaned.csv"
df.to_csv(output_path, index=False, encoding='utf-8')
print(f"\n💾 Zapisano: {output_path}")

# Pokaż przykłady
if cleaned_examples:
    print("\n📋 Przykłady wyczyszczonych wierszy (pierwsze 15):")
    print("-"*70)
    
    for i, ex in enumerate(cleaned_examples, 1):
        print(f"\n{i}. {ex['l1']} → {ex['l2']}")
        print(f"   Level 3: {ex['l3']}")
        print(f"   Level 4: '{ex['l4']}' → NULL ✂️")
        print(f"   Powód: {ex['reason']}")

print("\n" + "="*70)
print("✅ CZYSZCZENIE ZAKOŃCZONE!")
print("="*70)
print(f"\n📁 Nowy plik: {output_path}")
print(f"\n💡 Możesz teraz:")
print(f"   1. Pobrać: final_tree_cleaned.csv")
print(f"   2. Lub nadpisać oryginalny:")
print(f"      import shutil")
print(f"      shutil.copy('{output_path}', '{file_path}')")

# Statystyki per kategoria
print("\n📊 Statystyki czyszczenia per Level 1:")
print("-"*70)
stats = df.groupby('level1').agg({
    'level4': lambda x: x.isna().sum()
}).reset_index()
stats.columns = ['Kategoria', 'Level 4 pustych']
stats['Total'] = df.groupby('level1').size().values
stats['% pustych'] = (stats['Level 4 pustych'] / stats['Total'] * 100).round(1)
print(stats.to_string(index=False))
