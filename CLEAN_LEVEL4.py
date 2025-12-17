# ============================================================
# SKRYPT DO CZYSZCZENIA LEVEL 4
# 
# ⚠️ UWAGA: To jest OSOBNY skrypt!
# 
# JAK UŻYĆ:
# 1. Uruchom CAŁY pipeline COLAB_READY_V2.py (FAZA 0-10)
# 2. Poczekaj aż się zakończy
# 3. POTEM skopiuj TEN SKRYPT jako NOWĄ komórkę w Colabie
# 4. Uruchom tę nową komórkę (Shift+Enter)
# 
# NIE WKLEJAJ tego do pliku COLAB_READY_V2.py!
# To ma być osobna komórka uruchomiona PÓŹNIEJ!
# ============================================================

import pandas as pd
import re
import os
from difflib import SequenceMatcher

print("="*70)
print("🧹 CZYSZCZENIE LEVEL 4 (usuwanie zbędnych)")
print("="*70)

# Wczytaj final_tree.csv (używa BASE_DIR z głównego kodu)
# BASE_DIR jest już zdefiniowane wcześniej w kodzie!

# Sprawdź czy plik istnieje
file_path = f"{BASE_DIR}/final_tree.csv"

if not os.path.exists(file_path):
    print(f"❌ BŁĄD: Plik nie istnieje: {file_path}")
    print(f"\n💡 Sprawdź:")
    print(f"   1. Czy BASE_DIR jest poprawne: {BASE_DIR}")
    print(f"   2. Czy FAZA 10 się wykonała (plik powinien być zapisany)")
    print(f"   3. Dostępne pliki w {BASE_DIR}:")
    if os.path.exists(BASE_DIR):
        for f in os.listdir(BASE_DIR):
            print(f"      - {f}")
    else:
        print(f"      Katalog {BASE_DIR} nie istnieje!")
    raise FileNotFoundError(f"Brak pliku: {file_path}")

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
    "konsultacja", "diagnostyka", "badanie", "wizyta",
    
    # Konkretne zabiegi (nie rodziny)
    "depilacja", "woskowanie",
    "blefaroplastyka", "otoplastyka", "rinoplastyka",
    "liposukcja", "abdominoplastyka",
    "przeszczep", "transplantacja",
    "baby doll lips", "russian lips",
    "otoplastyka",
    "mammoplastyka",
    
    # Zabiegi których nie da się podzielić
    "test", "analiza", "ocena",
]

FAMILY_KEYWORDS = [
    # To są RODZINY (powinny mieć Level 4)
    "mezoterapia", "mikronakłuwanie",
    "toksyna botulinowa", "botoks", "botox",
    "wypełniacze", "fillery",
    "peeling", "peelingi",
    "laser", "lasery", "laserowe",
    "lifting", "nici",
    "osocze", "prp",
    "radiofrekwencja", "rf",
    "ultradźwięki", "hifu",
    "zabiegi", "terapia", "leczenie",
]

# ============================================================
# REGUŁY CZYSZCZENIA
# ============================================================

cleaned_count = 0

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
    if l4_norm and l4_norm in l3_norm:
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
    
    # REGUŁA 5: Level 3 ma >6 słów (już bardzo szczegółowe)
    if word_count(str(l3)) > 6:
        should_clean = True
        reason = "Level 3 zbyt szczegółowe (>6 słów)"
    
    # REGUŁA 6: Level 4 to samo słowo co ostatnie w Level 3
    l3_words = str(l3).lower().split()
    l4_words = str(l4).lower().split()
    if l3_words and l4_words and l3_words[-1] == l4_words[0]:
        should_clean = True
        reason = "Level 4 powtarza ostatnie słowo L3"
    
    # Wykonaj czyszczenie
    if should_clean:
        df.at[idx, 'level4'] = None
        cleaned_count += 1
        
        # Debug: pokaż pierwsze 10 wyczyszczonych
        if cleaned_count <= 10:
            print(f"\n✂️ Wyczyszczono #{cleaned_count}:")
            print(f"   Level 3: {l3}")
            print(f"   Level 4: {l4} → NULL")
            print(f"   Powód: {reason}")

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

# Zapisz
output_path = f"{BASE_DIR}/final_tree_cleaned.csv"
df.to_csv(output_path, index=False, encoding='utf-8')
print(f"\n💾 Zapisano: {output_path}")

# Pokaż przykłady PRZED/PO
print("\n📋 Przykłady wyczyszczonych wierszy (PRZED → PO):")
print("-"*70)

sample_cleaned = df[df['level4'].isna()].sample(min(10, len(df[df['level4'].isna()]))).copy()

# Wczytaj oryginalny plik żeby pokazać różnicę
df_original = pd.read_csv(f"{BASE_DIR}/final_tree.csv")

for idx in sample_cleaned.index:
    l1 = sample_cleaned.loc[idx, 'level1']
    l2 = sample_cleaned.loc[idx, 'level2']
    l3 = sample_cleaned.loc[idx, 'level3']
    l4_old = df_original.loc[idx, 'level4']
    
    print(f"\n{l1} → {l2}")
    print(f"  Level 3: {l3}")
    print(f"  Level 4: '{l4_old}' → NULL ✂️")

print("\n" + "="*70)
print("✅ CZYSZCZENIE ZAKOŃCZONE!")
print("="*70)
print(f"\nMożesz teraz użyć pliku: final_tree_cleaned.csv")
print("Lub nadpisać oryginalny:")
print(f"  df.to_csv('{BASE_DIR}/final_tree.csv', index=False)")
