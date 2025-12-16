# 📊 Przykładowa struktura wyjściowa

## 1. final_tree.csv

**Kolumny**: `level1`, `level2`, `level3`, `level4`, `description`

```csv
level1,level2,level3,level4,description
Dermatologia,Dermatologia estetyczna,Mezoterapia igłowa,Mezoterapia peptydowa twarzy,"Zabieg polegający na iniekcjach peptydów bezpośrednio w skórę twarzy. Stymuluje produkcję kolagenu, poprawia nawilżenie i jędrność skóry."
Dermatologia,Dermatologia estetyczna,Toksyna botulinowa,Botoks zmarszczek czoła,"Iniekcje toksyny botulinowej w mięśnie czoła, które relaksują mięśnie i wygładzają zmarszczki mimiczne. Efekt widoczny po 7-14 dniach."
Dermatologia,Dermatologia estetyczna,Toksyna botulinowa,Botoks bruksizmu,"Zastosowanie toksyny botulinowej w mięśnie żwaczy w celu redukcji zgrzytania zębami i bólu szczęki. Dodatkowo wyszczupla owal twarzy."
Dermatologia,Dermatologia estetyczna,Peelingi chemiczne,Peeling kwasami AHA,"Zabieg złuszczający naskórek za pomocą kwasów owocowych (AHA). Rozjaśnia przebarwienia, wygładza teksturę skóry i pobudza odnowę komórkową."
Dermatologia,Dermatologia lecznicza,Leczenie trądziku,Terapia izotretynoiną,"Leczenie ciężkiego trądziku preparatem izotretynoiny doustnie. Zmniejsza wydzielanie sebum i zapobiega powstawaniu wykwitów."
Kosmetologia,Zabiegi na twarz,Oczyszczanie wodorowe,Hydrafacial,"Wieloetapowy zabieg oczyszczająco-nawilżający z użyciem wody wodorowej. Usuwa zanieczyszczenia, regeneruje i nawilża skórę."
Kosmetologia,Zabiegi na twarz,Mikroigłowa mezoterapia,Mezoterapia mikroigłowa z kwasem hialuronowym,"Zabieg polegający na wprowadzeniu kwasu hialuronowego za pomocą mikroigieł. Intensywnie nawilża, poprawia elastyczność i napręża skórę."
Kosmetologia,Zabiegi na ciało,Redukcja tkanki tłuszczowej,Kriolipoliza,"Nieinwazyjny zabieg zmniejszający tkankę tłuszczową przez zamrażanie komórek tłuszczowych. Efekt widoczny po 2-3 miesiącach."
Kosmetologia,Zabiegi na ciało,Modelowanie sylwetki,Lipoliza iniekcyjna,"Iniekcje substancji rozkładających komórki tłuszczowe w określonych partiach ciała. Stosowana lokalnie, np. na podbródek czy boczki."
Chirurgia plastyczna,Chirurgia twarzy,Operacje nosa,Rinoplastyka,"Operacja korekcyjna nosa mająca na celu poprawę estetyki lub funkcji. Zmienia kształt, rozmiar lub proporcje nosa."
Chirurgia plastyczna,Chirurgia twarzy,Operacje powiek,Blefaroplastyka górnych powiek,"Zabieg chirurgiczny usuwający nadmiar skóry z górnych powiek. Poprawia wygląd oczu i pole widzenia."
Chirurgia plastyczna,Chirurgia ciała,Liposukcja,Liposukcja brzucha,"Zabieg chirurgiczny polegający na odsysaniu tkanki tłuszczowej z okolicy brzucha. Modeluje sylwetkę i redukuje lokalne tyłki."
Chirurgia plastyczna,Chirurgia piersi,Powiększenie piersi,Powiększenie piersi implantami,"Operacja wszczepienia implantów piersiowych w celu zwiększenia objętości biustu. Poprawia proporcje sylwetki i pewność siebie."
Trychologia,Leczenie łysienia,Mezoterapia owłosionej skóry głowy,Mezoterapia na łysienie,"Iniekcje substancji odżywczych (witaminy, peptydy) bezpośrednio w skórę głowy. Wzmacnia cebulki włosowe i stymuluje wzrost włosów."
Trychologia,Leczenie łysienia,Osocze bogatopłytkowe,PRP na włosy,"Zabieg polegający na iniekcjach osocza bogatopłytkowego (PRP) w skórę głowy. Regeneruje mieszki włosowe i poprawia zagęszczenie włosów."
Ginekologia estetyczna,Zabiegi na okolicę intymną,Lasery intymne,Laserowe leczenie atrofii pochwy,"Zabieg laserowy stymulujący produkcję kolagenu w ścianach pochwy. Poprawia nawilżenie, elastyczność i funkcje seksualne."
Ginekologia estetyczna,Zabiegi na okolicę intymną,Wypełniacze intymne,Wypełnienie warg sromowych kwasem hialuronowym,"Iniekcje kwasu hialuronowego w wargi sromowe większe w celu poprawy objętości i estetyki. Efekt natychmiastowy, trwa 12-18 miesięcy."
Medycyna estetyczna,Zabiegi laserowe,Usuwanie owłosienia,Depilacja laserowa,"Trwałe usuwanie owłosienia za pomocą lasera, który niszczy cebulki włosowe. Wymaga kilku sesji, efekt długotrwały."
Medycyna estetyczna,Zabiegi laserowe,Usuwanie przebarwień,Laser frakcyjny na przebarwienia,"Zabieg laserowy usuwający przebarwienia i wyrównujący koloryt skóry. Stymuluje odnowę skóry i produkcję kolagenu."
Medycyna estetyczna,Zabiegi ultradźwiękowe,HIFU,HIFU lifting twarzy,"Nieinwazyjny lifting za pomocą ultradźwięków HIFU. Napina skórę, poprawia owal twarzy i redukuje obwisanie bez skalpela."
```

---

## 2. final_treatments.csv

**Kolumny**: `domain`, `treatment`, `representative`, `level1`, `level2`, `level3`, `level4`

```csv
domain,treatment,representative,level1,level2,level3,level4
klinika-abc.pl,botox czoło,Botoks zmarszczek czoła,Dermatologia,Dermatologia estetyczna,Toksyna botulinowa,Botoks zmarszczek czoła
klinika-abc.pl,mezoterapia twarzy,Mezoterapia peptydowa twarzy,Dermatologia,Dermatologia estetyczna,Mezoterapia igłowa,Mezoterapia peptydowa twarzy
klinika-abc.pl,peeling kwasowy,Peeling kwasami AHA,Dermatologia,Dermatologia estetyczna,Peelingi chemiczne,Peeling kwasami AHA
klinika-xyz.pl,botoks bruksizm,Botoks bruksizmu,Dermatologia,Dermatologia estetyczna,Toksyna botulinowa,Botoks bruksizmu
klinika-xyz.pl,hydrafacial,Hydrafacial,Kosmetologia,Zabiegi na twarz,Oczyszczanie wodorowe,Hydrafacial
klinika-xyz.pl,kriolipoliza,Kriolipoliza,Kosmetologia,Zabiegi na ciało,Redukcja tkanki tłuszczowej,Kriolipoliza
gabinet-estetyka.pl,mezoterapia włosy,Mezoterapia na łysienie,Trychologia,Leczenie łysienia,Mezoterapia owłosionej skóry głowy,Mezoterapia na łysienie
gabinet-estetyka.pl,PRP włosy,PRP na włosy,Trychologia,Leczenie łysienia,Osocze bogatopłytkowe,PRP na włosy
klinika-chirurgia.pl,powiększanie piersi,Powiększenie piersi implantami,Chirurgia plastyczna,Chirurgia piersi,Powiększenie piersi,Powiększenie piersi implantami
klinika-chirurgia.pl,rinoplastyka,Rinoplastyka,Chirurgia plastyczna,Chirurgia twarzy,Operacje nosa,Rinoplastyka
klinika-chirurgia.pl,liposukcja brzuch,Liposukcja brzucha,Chirurgia plastyczna,Chirurgia ciała,Liposukcja,Liposukcja brzucha
centrum-laser.pl,depilacja laserowa,Depilacja laserowa,Medycyna estetyczna,Zabiegi laserowe,Usuwanie owłosienia,Depilacja laserowa
centrum-laser.pl,laser przebarwienia,Laser frakcyjny na przebarwienia,Medycyna estetyczna,Zabiegi laserowe,Usuwanie przebarwień,Laser frakcyjny na przebarwienia
centrum-laser.pl,hifu lifting,HIFU lifting twarzy,Medycyna estetyczna,Zabiegi ultradźwiękowe,HIFU,HIFU lifting twarzy
klinika-ginekologia.pl,laser intymny,Laserowe leczenie atrofii pochwy,Ginekologia estetyczna,Zabiegi na okolicę intymną,Lasery intymne,Laserowe leczenie atrofii pochwy
klinika-ginekologia.pl,kwas hialuronowy wargi sromowe,Wypełnienie warg sromowych kwasem hialuronowym,Ginekologia estetyczna,Zabiegi na okolicę intymną,Wypełniacze intymne,Wypełnienie warg sromowych kwasem hialuronowym
```

---

## 3. final_domains.csv

**Kolumny**: `domain`, `num_pages`, `total_treatments`, `unique_treatments`

```csv
domain,num_pages,total_treatments,unique_treatments
klinika-abc.pl,12,45,32
klinika-xyz.pl,10,38,28
gabinet-estetyka.pl,8,25,18
klinika-chirurgia.pl,11,52,35
centrum-laser.pl,9,30,22
klinika-ginekologia.pl,7,18,14
klinika-derma.pl,12,48,33
centrum-medyczne.pl,6,15,12
gabinet-kosmetyczny.pl,10,35,25
klinika-uroda.pl,11,42,30
```

---

## 4. final_tree.json (hierarchiczny)

```json
{
  "Dermatologia": {
    "Dermatologia estetyczna": {
      "Mezoterapia igłowa": [
        {
          "name": "Mezoterapia peptydowa twarzy",
          "description": "Zabieg polegający na iniekcjach peptydów bezpośrednio w skórę twarzy. Stymuluje produkcję kolagenu, poprawia nawilżenie i jędrność skóry."
        }
      ],
      "Toksyna botulinowa": [
        {
          "name": "Botoks zmarszczek czoła",
          "description": "Iniekcje toksyny botulinowej w mięśnie czoła, które relaksują mięśnie i wygładzają zmarszczki mimiczne. Efekt widoczny po 7-14 dniach."
        },
        {
          "name": "Botoks bruksizmu",
          "description": "Zastosowanie toksyny botulinowej w mięśnie żwaczy w celu redukcji zgrzytania zębami i bólu szczęki. Dodatkowo wyszczupla owal twarzy."
        }
      ],
      "Peelingi chemiczne": [
        {
          "name": "Peeling kwasami AHA",
          "description": "Zabieg złuszczający naskórek za pomocą kwasów owocowych (AHA). Rozjaśnia przebarwienia, wygładza teksturę skóry i pobudza odnowę komórkową."
        }
      ]
    },
    "Dermatologia lecznicza": {
      "Leczenie trądziku": [
        {
          "name": "Terapia izotretynoiną",
          "description": "Leczenie ciężkiego trądziku preparatem izotretynoiny doustnie. Zmniejsza wydzielanie sebum i zapobiega powstawaniu wykwitów."
        }
      ]
    }
  },
  "Kosmetologia": {
    "Zabiegi na twarz": {
      "Oczyszczanie wodorowe": [
        {
          "name": "Hydrafacial",
          "description": "Wieloetapowy zabieg oczyszczająco-nawilżający z użyciem wody wodorowej. Usuwa zanieczyszczenia, regeneruje i nawilża skórę."
        }
      ],
      "Mikroigłowa mezoterapia": [
        {
          "name": "Mezoterapia mikroigłowa z kwasem hialuronowym",
          "description": "Zabieg polegający na wprowadzeniu kwasu hialuronowego za pomocą mikroigieł. Intensywnie nawilża, poprawia elastyczność i napręża skórę."
        }
      ]
    },
    "Zabiegi na ciało": {
      "Redukcja tkanki tłuszczowej": [
        {
          "name": "Kriolipoliza",
          "description": "Nieinwazyjny zabieg zmniejszający tkankę tłuszczową przez zamrażanie komórek tłuszczowych. Efekt widoczny po 2-3 miesiącach."
        }
      ],
      "Modelowanie sylwetki": [
        {
          "name": "Lipoliza iniekcyjna",
          "description": "Iniekcje substancji rozkładających komórki tłuszczowe w określonych partiach ciała. Stosowana lokalnie, np. na podbródek czy boczki."
        }
      ]
    }
  },
  "Chirurgia plastyczna": {
    "Chirurgia twarzy": {
      "Operacje nosa": [
        {
          "name": "Rinoplastyka",
          "description": "Operacja korekcyjna nosa mająca na celu poprawę estetyki lub funkcji. Zmienia kształt, rozmiar lub proporcje nosa."
        }
      ],
      "Operacje powiek": [
        {
          "name": "Blefaroplastyka górnych powiek",
          "description": "Zabieg chirurgiczny usuwający nadmiar skóry z górnych powiek. Poprawia wygląd oczu i pole widzenia."
        }
      ]
    },
    "Chirurgia ciała": {
      "Liposukcja": [
        {
          "name": "Liposukcja brzucha",
          "description": "Zabieg chirurgiczny polegający na odsysaniu tkanki tłuszczowej z okolicy brzucha. Modeluje sylwetkę i redukuje lokalne tyłki."
        }
      ]
    },
    "Chirurgia piersi": {
      "Powiększenie piersi": [
        {
          "name": "Powiększenie piersi implantami",
          "description": "Operacja wszczepienia implantów piersiowych w celu zwiększenia objętości biustu. Poprawia proporcje sylwetki i pewność siebie."
        }
      ]
    }
  },
  "Trychologia": {
    "Leczenie łysienia": {
      "Mezoterapia owłosionej skóry głowy": [
        {
          "name": "Mezoterapia na łysienie",
          "description": "Iniekcje substancji odżywczych (witaminy, peptydy) bezpośrednio w skórę głowy. Wzmacnia cebulki włosowe i stymuluje wzrost włosów."
        }
      ],
      "Osocze bogatopłytkowe": [
        {
          "name": "PRP na włosy",
          "description": "Zabieg polegający na iniekcjach osocza bogatopłytkowego (PRP) w skórę głowy. Regeneruje mieszki włosowe i poprawia zagęszczenie włosów."
        }
      ]
    }
  },
  "Ginekologia estetyczna": {
    "Zabiegi na okolicę intymną": {
      "Lasery intymne": [
        {
          "name": "Laserowe leczenie atrofii pochwy",
          "description": "Zabieg laserowy stymulujący produkcję kolagenu w ścianach pochwy. Poprawia nawilżenie, elastyczność i funkcje seksualne."
        }
      ],
      "Wypełniacze intymne": [
        {
          "name": "Wypełnienie warg sromowych kwasem hialuronowym",
          "description": "Iniekcje kwasu hialuronowego w wargi sromowe większe w celu poprawy objętości i estetyki. Efekt natychmiastowy, trwa 12-18 miesięcy."
        }
      ]
    }
  },
  "Medycyna estetyczna": {
    "Zabiegi laserowe": {
      "Usuwanie owłosienia": [
        {
          "name": "Depilacja laserowa",
          "description": "Trwałe usuwanie owłosienia za pomocą lasera, który niszczy cebulki włosowe. Wymaga kilku sesji, efekt długotrwały."
        }
      ],
      "Usuwanie przebarwień": [
        {
          "name": "Laser frakcyjny na przebarwienia",
          "description": "Zabieg laserowy usuwający przebarwienia i wyrównujący koloryt skóry. Stymuluje odnowę skóry i produkcję kolagenu."
        }
      ]
    },
    "Zabiegi ultradźwiękowe": {
      "HIFU": [
        {
          "name": "HIFU lifting twarzy",
          "description": "Nieinwazyjny lifting za pomocą ultradźwięków HIFU. Napina skórę, poprawia owal twarzy i redukuje obwisanie bez skalpela."
        }
      ]
    }
  }
}
```

---

## 📊 Statystyki przykładowe

Po uruchomieniu pipeline'u na **50 domen** i **20 keywordach** możesz spodziewać się:

- **Level 1 (kategorie główne)**: 6-10 kategorii
  - Np: Dermatologia, Kosmetologia, Chirurgia plastyczna, Trychologia, Ginekologia estetyczna, Medycyna estetyczna

- **Level 2 (podkategorie)**: 20-40 podkategorii
  - Np: Dermatologia estetyczna, Dermatologia lecznicza, Zabiegi na twarz, Zabiegi na ciało, Chirurgia twarzy...

- **Level 3 (rodziny zabiegów)**: 50-100 rodzin
  - Np: Mezoterapia igłowa, Toksyna botulinowa, Peelingi chemiczne, Lasery ablacyjne, Nici liftingujące...

- **Level 4 (konkretne zabiegi)**: 200-500 zabiegów
  - Np: Mezoterapia peptydowa twarzy, Botoks zmarszczek czoła, Peeling PRX-T33, CO2 laser frakcyjny...

- **Total zabiegów (przed deduplikacją)**: 1000-3000
  - Zależne od liczby scrapowanych stron i jakości treści

- **Unikalnych zabiegów (po clusteringu)**: 200-500
  - Po usunięciu duplikatów i synonimów

---

## 🎯 Użycie w aplikacji

### Przykład 1: Wyszukiwanie po nazwie
```python
import pandas as pd

df = pd.read_csv("final_tree.csv")

# Wyszukaj wszystkie zabiegi zawierające "botoks"
results = df[df["level4"].str.contains("botoks", case=False, na=False)]
print(results[["level1", "level2", "level3", "level4"]])
```

### Przykład 2: Przeglądanie hierarchii
```python
# Pokaż wszystkie zabiegi z kategorii "Dermatologia"
category = df[df["level1"] == "Dermatologia"]
print(category.groupby("level2")["level3"].nunique())
```

### Przykład 3: Rekomendacje
```python
# Znajdź podobne zabiegi (ta sama level3)
treatment = "Botoks zmarszczek czoła"
row = df[df["level4"] == treatment].iloc[0]
similar = df[df["level3"] == row["level3"]]
print("Podobne zabiegi:", similar["level4"].tolist())
```

---

**To tylko przykłady!** Rzeczywiste wyniki będą się różnić w zależności od:
- Liczby scrapowanych domen
- Jakości treści na stronach
- Ustawień filtrów (SEMANTIC_SIM_THRESHOLD itp.)
- Wybranego modelu LLM
