# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [1.0.0] - 2025-12-16

### ✨ Initial Release

#### Added
- **Complete 10-phase pipeline** for building aesthetic medicine treatment taxonomy
  - Phase 1: Keyword generation (LLM)
  - Phase 2: SERP scraping (serpdata.io)
  - Phase 3: Domain scraping (BeautifulSoup)
  - Phase 4: Treatment extraction (LLM)
  - Phase 5: Filtering and normalization (embeddings + LLM)
  - Phase 6: Clustering and synonyms (HDBSCAN + Jina)
  - Phase 7: 4-level taxonomy building (LLM)
  - Phase 8: Treatment mapping to tree (embeddings)
  - Phase 9: Description generation (LLM)
  - Phase 10: Final export (CSV + JSON)

- **Google Colab notebook** (`aesthetic_medicine_search_engine.ipynb`)
  - Full interactive pipeline
  - Progress bars and statistics
  - Automatic checkpointing

- **Standalone Python script** (`standalone_version.py`)
  - CLI version for local execution
  - Phases 1-4 implemented
  - Command-line arguments for configuration

- **Setup checker** (`check_setup.py`)
  - Validates dependencies
  - Checks API keys
  - Tests API connectivity

- **Documentation**
  - `README.md` - Technical documentation
  - `PODSUMOWANIE.md` - Polish summary and quickstart
  - `EXAMPLE_OUTPUT.md` - Example outputs and usage
  - `ADVANCED_TIPS.md` - Advanced optimization tips

- **Configuration**
  - `requirements.txt` - Python dependencies
  - `.env.example` - Example environment configuration
  - `.gitignore` - Git ignore rules

#### Features
- **Multi-source data collection**
  - Google SERP results via serpdata.io
  - Web scraping of clinic domains
  - LLM-based treatment extraction

- **Smart deduplication**
  - Semantic similarity using embeddings
  - Clustering with HDBSCAN
  - Optional Jina rerank for quality

- **4-level taxonomy**
  - Level 1: Main categories (Dermatology, Surgery, etc.)
  - Level 2: Subcategories
  - Level 3: Treatment families
  - Level 4: Specific treatments

- **Automatic descriptions**
  - LLM-generated patient-friendly descriptions
  - SEO-optimized content

- **Multiple export formats**
  - CSV for data analysis
  - JSON for web applications

#### Configuration Options
- Adjustable limits (keywords, domains, pages)
- Configurable thresholds (semantic similarity, reranking)
- Model selection (OpenRouter models)
- Optional Jina rerank

#### Supported APIs
- OpenRouter (OpenAI GPT-4.1, GPT-5, Gemini)
- SerpData.io (Google SERP)
- Jina AI (reranking, optional)

---

## [Planned Features]

### v1.1.0 (Future)
- [ ] Price extraction from domains
- [ ] Geographic mapping (cities/regions)
- [ ] Multi-language support (EN, DE, CZ)
- [ ] Elasticsearch integration
- [ ] FastAPI REST API
- [ ] Streamlit dashboard

### v1.2.0 (Future)
- [ ] Automatic monthly updates
- [ ] Email notifications
- [ ] Data quality metrics
- [ ] A/B testing for different LLM models
- [ ] Image extraction (before/after photos)

### v2.0.0 (Future)
- [ ] Full-stack web application
- [ ] User reviews integration
- [ ] Appointment booking system
- [ ] Mobile app (React Native)

---

## Known Issues

### Current Limitations
- **Phase 5-10 not in standalone version**: Only Colab has full pipeline
- **No price extraction**: Future feature
- **Polish only**: Multi-language support planned
- **Rate limits**: May need adjustments for large-scale scraping

### Workarounds
- Use Google Colab for full pipeline (recommended)
- Adjust `time.sleep()` values for rate limiting
- Use smaller models to reduce costs

---

## Migration Guide

### From Manual Process to v1.0.0
If you were doing this manually before:

1. **Export your existing data** to CSV
2. **Run Phase 1-2** to get domains
3. **Merge your data** with `final_treatments.csv`
4. **Re-run Phase 7-9** to rebuild taxonomy

### Updating from v1.0.0 to v1.1.0 (when released)
- New features will be backward-compatible
- Existing CSV files can be imported
- Configuration will be migrated automatically

---

## Contributors

- Initial development: Claude + Cursor collaboration
- Maintained by: [Your name/organization]

---

## License

MIT License - See [LICENSE](LICENSE) for details

---

## Support

- 📖 Documentation: See `README.md`
- 🐛 Issues: GitHub Issues
- 💬 Discussions: GitHub Discussions
- 📧 Email: [Your contact]

---

**Last updated**: December 16, 2025
