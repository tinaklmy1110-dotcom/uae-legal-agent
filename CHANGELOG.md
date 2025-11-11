## 2025-11-11

- Added Abu Dhabi real estate laws and 2023 Official Gazette editions to `data/law_manifest.json`, regenerated `data/seed_samples.json`, and re-seeded the database so searches cover local statutes.
- Implemented translation microservice integration and frontend translation panel (translator service, backend `/translate`, frontend API & UI).
- Updated frontend results cards and details page to show full structural breadcrumbs (`Part / Chapter / Article`) and clearer headings.
- Enhanced search relevance: added phrase-first matching, jurisdiction-aware ranking boosts, and Abu Dhabi-specific topic tags to ensure queries like "Abu Dhabi real estate register" prioritize local laws.
- Added render boot script to auto-run `seed_loader` on deployment and documented configuration for Render/Next.js services.
- Search query state now persists in the URL; returning from detail pages restores the previous query automatically and the “返回检索” link now uses that preserved state.
