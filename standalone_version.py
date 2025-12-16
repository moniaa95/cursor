#!/usr/bin/env python3
"""
Standalone version - run locally (not in Colab)

Usage:
    export OPENROUTER_API_KEY="..."
    export SERPDATA_KEY="..."
    export JINA_API_KEY="..."  # optional
    
    python standalone_version.py --output-dir ./output --max-domains 50
"""

import os
import sys
import argparse
import json
import time
import re
import unicodedata
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from urllib.parse import urlparse

import numpy as np
import pandas as pd
import requests
from tqdm import tqdm
from bs4 import BeautifulSoup
from sklearn.metrics.pairwise import cosine_similarity
import hdbscan
from openai import OpenAI


# ============================================================
# Configuration
# ============================================================

class Config:
    def __init__(self, args):
        self.PROJECT_NAME = args.project_name
        self.BASE_DIR = args.output_dir
        self.MAX_KEYWORDS = args.max_keywords
        self.SERP_TOP_N = 10
        self.MAX_DOMAINS = args.max_domains
        self.MAX_PAGES_PER_DOMAIN = args.max_pages
        self.MIN_TEXT_LEN = 5
        self.MAX_TEXT_LEN = 120
        self.MIN_DOMAIN_COUNT = 2
        self.SEMANTIC_SIM_THRESHOLD = args.semantic_threshold
        self.USE_JINA = args.use_jina
        self.JINA_RERANK_THRESHOLD = 0.25
        self.MODEL_NAME = args.model
        self.EMBED_MODEL = args.embed_model
        
        # API keys
        self.OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
        self.SERPDATA_KEY = os.getenv("SERPDATA_KEY")
        self.JINA_API_KEY = os.getenv("JINA_API_KEY")
        
        if not self.OPENROUTER_API_KEY:
            raise ValueError("Missing OPENROUTER_API_KEY environment variable")
        if not self.SERPDATA_KEY:
            raise ValueError("Missing SERPDATA_KEY environment variable")
        if self.USE_JINA and not self.JINA_API_KEY:
            print("⚠️ USE_JINA=True but JINA_API_KEY not set → disabling Jina")
            self.USE_JINA = False
        
        # Create output dir
        os.makedirs(self.BASE_DIR, exist_ok=True)
        
        # OpenRouter client
        self.or_client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=self.OPENROUTER_API_KEY,
        )


# ============================================================
# Helpers
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
    print(f"💾 Saved: {path}")


def load_df(path: str) -> pd.DataFrame:
    return pd.read_csv(path, encoding="utf-8")


# ============================================================
# LLM functions
# ============================================================

def or_chat(config: Config, messages: List[Dict[str, str]], temperature: float = 0.2, max_tokens: int = 1200) -> str:
    resp = config.or_client.chat.completions.create(
        model=config.MODEL_NAME,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return resp.choices[0].message.content


def or_chat_json(config: Config, system_prompt: str, user_prompt: str, max_tokens: int = 2200) -> dict:
    resp = config.or_client.chat.completions.create(
        model=config.MODEL_NAME,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0,
        response_format={"type": "json_object"},
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


def embed_texts(config: Config, texts: List[str], batch_size: int = 64, sleep_s: float = 0.15) -> np.ndarray:
    out = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        resp = config.or_client.embeddings.create(model=config.EMBED_MODEL, input=batch)
        out.extend([d.embedding for d in resp.data])
        time.sleep(sleep_s)
    return np.array(out, dtype="float32")


def jina_rerank(config: Config, query: str, documents: List[str]) -> List[Tuple[int, float]]:
    url = "https://api.jina.ai/v1/rerank"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {config.JINA_API_KEY}"}
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


# ============================================================
# PHASE 1: Keywords
# ============================================================

def phase1_keywords(config: Config):
    print("\n" + "="*70)
    print("🔑 PHASE 1: KEYWORDS GENERATION")
    print("="*70)
    
    system = "Jesteś ekspertem SEO w branży medycyny estetycznej w Polsce."
    user = f"""
Wygeneruj {config.MAX_KEYWORDS} polskich fraz, które pacjenci wpisują w Google szukając konkretnych zabiegów.

Zasady:
- 2–5 słów w frazie
- bez numerowania, jedna fraza w jednej linii
- bez marek (np. Dermapen, PRX-T33, Nucleofill itp.)
- mają to być realne zapytania usługowe (np. 'mezoterapia igłowa twarzy', 'botoks bruksizm')
- pokryj różne dziedziny: dermatologia estetyczna, chirurgia plastyczna, kosmetologia, trychologia, ginekologia estetyczna

Wypisz same frazy.
"""
    
    raw = or_chat(config, [{"role": "system", "content": system}, {"role": "user", "content": user}], temperature=0.8, max_tokens=1200)
    keywords = [clean_text(x) for x in raw.split("\n") if clean_text(x)]
    
    # dedupe
    uniq = []
    seen = set()
    for k in keywords:
        nk = norm_key(k)
        if nk and nk not in seen:
            seen.add(nk)
            uniq.append(k)
    keywords = uniq[:config.MAX_KEYWORDS]
    
    print(f"✅ Generated {len(keywords)} keywords")
    for k in keywords[:10]:
        print(f"  - {k}")
    
    save_df(pd.DataFrame({"keyword": keywords}), f"{config.BASE_DIR}/phase1_keywords.csv")
    return keywords


# ============================================================
# PHASE 2: SERP → domains
# ============================================================

def fetch_serp_urls(config: Config, keyword: str, top_n: int = 10) -> List[str]:
    url = "https://api.serpdata.io/v1/search"
    headers = {"Authorization": f"Bearer {config.SERPDATA_KEY}"}
    params = {"keyword": keyword, "hl": "pl", "gl": "pl"}
    
    r = requests.get(url, headers=headers, params=params, timeout=60)
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


def is_clinic_domain(domain: str) -> bool:
    BAD = ["facebook", "instagram", "youtube", "twitter", "znanylekarz", "booksy",
           "allegro", "olx", "wikipedia", "medonet", "onet", "wp"]
    GOOD = ["klinika", "clinic", "med", "derma", "estety", "uroda", "beauty", "laser", "gabinet"]
    
    if not domain or any(b in domain for b in BAD):
        return False
    if any(g in domain for g in GOOD):
        return True
    return "." in domain and not domain.endswith((".gov", ".edu", ".org"))


def phase2_serp_domains(config: Config, keywords: List[str]):
    print("\n" + "="*70)
    print("🌐 PHASE 2: SERP → DOMAINS")
    print("="*70)
    
    all_rows = []
    for kw in tqdm(keywords, desc="Fetching SERPs"):
        try:
            urls = fetch_serp_urls(config, kw, top_n=10)
        except Exception as e:
            print(f"\n⚠️ Error for '{kw}': {e}")
            urls = []
        
        for url in urls:
            all_rows.append({"keyword": kw, "url": url})
        
        time.sleep(2)
    
    df_serp = pd.DataFrame(all_rows).drop_duplicates(subset=["keyword", "url"]).reset_index(drop=True)
    print(f"\n📌 Total (keyword, url) pairs: {len(df_serp)}")
    
    df_unique_urls = df_serp.drop_duplicates(subset=["url"]).reset_index(drop=True)
    print(f"📌 Unique URLs: {len(df_unique_urls)}")
    
    df_unique_urls["domain"] = df_unique_urls["url"].apply(lambda u: urlparse(u).netloc.lower().strip() if isinstance(u, str) else "")
    df_unique_urls["domain"] = df_unique_urls["domain"].str.replace(r"^www\.", "", regex=True)
    
    domain_counts = df_unique_urls["domain"].value_counts()
    candidate_domains = [d for d in domain_counts.index if is_clinic_domain(d)]
    clinic_domains = candidate_domains[:config.MAX_DOMAINS]
    
    domains_df = pd.DataFrame({"domain": clinic_domains})
    print(f"📌 Selected {len(domains_df)} domains")
    
    save_df(df_serp, f"{config.BASE_DIR}/phase2_serp_keyword_url.csv")
    save_df(df_unique_urls, f"{config.BASE_DIR}/phase2_unique_urls.csv")
    save_df(domains_df, f"{config.BASE_DIR}/domains.csv")
    
    return domains_df, df_unique_urls


# ============================================================
# PHASE 3: Scraping
# ============================================================

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


def phase3_scraping(config: Config, domains_df: pd.DataFrame, df_unique_urls: pd.DataFrame):
    print("\n" + "="*70)
    print("🕷️ PHASE 3: SCRAPING DOMAINS")
    print("="*70)
    
    scraped_data = []
    
    for domain in tqdm(domains_df["domain"], desc="Scraping domains"):
        domain_urls = df_unique_urls[df_unique_urls["domain"] == domain]["url"].tolist()
        domain_urls = domain_urls[:config.MAX_PAGES_PER_DOMAIN]
        
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
    print(f"\n📌 Successfully scraped {len(df_scraped)} domains")
    
    save_df(df_scraped, f"{config.BASE_DIR}/phase3_scraped_content.csv")
    return df_scraped


# ============================================================
# PHASE 4: Extraction
# ============================================================

def extract_treatments_from_text(config: Config, domain: str, text: str) -> List[str]:
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
- Przykłady: "mezoterapia igłowa", "botoks bruksizm", "liposukcja brzucha"

Wypisz listę zabiegów:
"""
    
    try:
        response = or_chat(config, [{"role": "system", "content": system}, {"role": "user", "content": user}], temperature=0.1, max_tokens=1500)
        treatments = [clean_text(line) for line in response.split("\n") if clean_text(line)]
        return treatments
    except Exception as e:
        print(f"⚠️ Error for {domain}: {e}")
        return []


def phase4_extraction(config: Config, df_scraped: pd.DataFrame):
    print("\n" + "="*70)
    print("🔍 PHASE 4: EXTRACTION WITH LLM")
    print("="*70)
    
    all_treatments = []
    
    for idx, row in tqdm(df_scraped.iterrows(), total=len(df_scraped), desc="Extracting treatments"):
        treatments = extract_treatments_from_text(config, row["domain"], row["text"])
        for t in treatments:
            all_treatments.append({
                "domain": row["domain"],
                "treatment": t
            })
        time.sleep(0.3)
    
    df_raw_treatments = pd.DataFrame(all_treatments)
    print(f"\n📌 Extracted {len(df_raw_treatments)} raw treatments")
    
    df_raw_treatments["treatment_norm"] = df_raw_treatments["treatment"].apply(norm_key)
    df_raw_treatments = df_raw_treatments[df_raw_treatments["treatment_norm"].str.len() >= config.MIN_TEXT_LEN]
    df_raw_treatments = df_raw_treatments[df_raw_treatments["treatment_norm"].str.len() <= config.MAX_TEXT_LEN]
    df_raw_treatments = df_raw_treatments.drop_duplicates(subset=["treatment_norm"]).reset_index(drop=True)
    
    print(f"📌 After initial deduplication: {len(df_raw_treatments)} unique treatments")
    
    save_df(df_raw_treatments, f"{config.BASE_DIR}/phase4_raw_treatments.csv")
    return df_raw_treatments


# ============================================================
# Main
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="Aesthetic Medicine Search Engine Builder")
    parser.add_argument("--project-name", default="baza_zabiegow_v0", help="Project name")
    parser.add_argument("--output-dir", default="./output", help="Output directory")
    parser.add_argument("--max-keywords", type=int, default=20, help="Max keywords to generate")
    parser.add_argument("--max-domains", type=int, default=50, help="Max domains to scrape")
    parser.add_argument("--max-pages", type=int, default=12, help="Max pages per domain")
    parser.add_argument("--semantic-threshold", type=float, default=0.22, help="Semantic similarity threshold")
    parser.add_argument("--use-jina", action="store_true", help="Use Jina rerank")
    parser.add_argument("--model", default="openai/gpt-4.1-mini", help="LLM model")
    parser.add_argument("--embed-model", default="openai/text-embedding-3-small", help="Embedding model")
    parser.add_argument("--start-from", type=int, default=1, help="Start from phase N (1-10)")
    
    args = parser.parse_args()
    
    print("="*70)
    print("🏥 AESTHETIC MEDICINE SEARCH ENGINE BUILDER")
    print("="*70)
    print(f"Project: {args.project_name}")
    print(f"Output: {args.output_dir}")
    print(f"Model: {args.model}")
    print("="*70)
    
    config = Config(args)
    
    # Phase 1
    if args.start_from <= 1:
        keywords = phase1_keywords(config)
    else:
        keywords = load_df(f"{config.BASE_DIR}/phase1_keywords.csv")["keyword"].tolist()
        print(f"✅ Loaded {len(keywords)} keywords from phase1_keywords.csv")
    
    # Phase 2
    if args.start_from <= 2:
        domains_df, df_unique_urls = phase2_serp_domains(config, keywords)
    else:
        domains_df = load_df(f"{config.BASE_DIR}/domains.csv")
        df_unique_urls = load_df(f"{config.BASE_DIR}/phase2_unique_urls.csv")
        print(f"✅ Loaded {len(domains_df)} domains from domains.csv")
    
    # Phase 3
    if args.start_from <= 3:
        df_scraped = phase3_scraping(config, domains_df, df_unique_urls)
    else:
        df_scraped = load_df(f"{config.BASE_DIR}/phase3_scraped_content.csv")
        print(f"✅ Loaded {len(df_scraped)} scraped domains from phase3_scraped_content.csv")
    
    # Phase 4
    if args.start_from <= 4:
        df_raw_treatments = phase4_extraction(config, df_scraped)
    else:
        df_raw_treatments = load_df(f"{config.BASE_DIR}/phase4_raw_treatments.csv")
        print(f"✅ Loaded {len(df_raw_treatments)} treatments from phase4_raw_treatments.csv")
    
    # Phases 5-10: TODO (implement if needed)
    print("\n⚠️ Phases 5-10 not implemented in standalone version yet.")
    print("💡 Use the Colab notebook for full pipeline.")
    
    print("\n" + "="*70)
    print("✅ DONE! (Phases 1-4)")
    print("="*70)


if __name__ == "__main__":
    main()
