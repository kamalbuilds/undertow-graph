# Spike: citation contexts are available at usable scale

Claim: for a high-profile retracted paper, at least 20% of citing works expose the citing sentence via a free API.

Run 2026-10-18 ~13:00 IST against Semantic Scholar Graph API v1, no key:
`GET /graph/v1/paper/DOI:10.1038/nature04533/citations?fields=title,year,externalIds,isInfluential,intents,contexts&limit=1000&offset=N`

Result: CONFIRMED.
- citers = 2630 (OpenAlex says 2769 cited_by_count; Nature page reportedly 2539; three sources disagree, S2 is what we ingest)
- with_contexts = 804 (30.6%), 796 of them published before 2024 (pre-retraction)
- isInfluential = 83; intents: background 597, methodology 58, result 31
- Raw: lesne_citations.json

Negative case seen in first page: context "The now retracted paper in question..." (acknowledges retraction) and a reproducibility paper citing it as an example (mention, no dependency). Classifier must separate these from dependence.

Caveats:
- 69% of citers have no context; they enter graph as paper-level edges with confidence=unknown, never as claim dependencies.
- Unauthenticated S2 returns 429 often; retry with backoff worked (6 retries total). Free API key recommended (user places in .env).
- OpenAlex unauthenticated budget is $0.10/day shared per IP; free key needed for OpenAlex enrichment.
