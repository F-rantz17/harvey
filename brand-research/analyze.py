"""Run Harvey's own detectors over pages saved by capture.sh.

    python brand-research/analyze.py            # every brand in pages/
    python brand-research/analyze.py brand-one.example brand-two.example

Writes results/<date>.json and results/<date>.md (a table you can paste
into Notion). Reads only local files; sends nothing anywhere.
"""
import datetime, json, pathlib, sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from harvey.collectors.profile import ProfileCollector, META_PIXEL, GOOGLE_ADS, site_name_from_html  # noqa: E402
from harvey.collectors import people as P  # noqa: E402
from harvey.integrations import email_finder as EF  # noqa: E402

ICP = ["Founder", "Co-Founder", "Owner", "CEO", "President", "Creative Director", "Brand Director",
       "Director of Marketing", "Marketing Director", "Head of Marketing", "Head of Brand",
       "Brand Manager", "Marketing Manager", "Director of Creative"]
GENERIC = ("info@", "hello@", "support@", "contact@", "help@", "orders@", "care@", "hi@", "team@", "shop@")
pc = ProfileCollector(state=None)


def _title(html: str) -> str:
    import html as h, re
    m = re.search(r"(?is)<title[^>]*>(.*?)</title>", html)
    return re.split(r"\s[|–—-]\s|:", h.unescape(m.group(1)).strip())[0].strip() if m else ""


def load(domain_dir: pathlib.Path):
    pages = []
    urls = domain_dir / "urls.txt"
    for line in urls.read_text().splitlines() if urls.exists() else []:
        fname, _, url = line.partition(" ")
        f = domain_dir / fname
        if f.exists():
            pages.append((url.strip(), f.read_text(errors="replace")))
    return pages


def analyze(domain: str, pages):
    home = pages[0][1]
    name = site_name_from_html(home, domain) or _title(home) or domain
    people = P.find_people(pages, domain, name)
    emails = sorted({e for _, h in pages for e in P.emails_on_page(h)
                     if e.split("@")[-1].lower().removeprefix("www.").endswith(domain)})
    known, pattern, _ = EF.site_email_evidence(emails, [(p["first_name"], p["last_name"]) for p in people], domain)
    decision = [p for p in people if P.title_matches(p["title"], ICP, owner=p.get("owner", False))]
    top = decision[0] if decision else None
    guess = EF.build_email(pattern, top["first_name"], top["last_name"], domain) if top and pattern else None
    tech = pc.detect_tech(home)
    return {
        "brand": name, "domain": domain, "pages_read": len(pages),
        "meta_ads": bool(pc._any(home, META_PIXEL)), "google_ads": bool(pc._any(home, GOOGLE_ADS)),
        "tiktok_pixel": "TikTok Pixel" in tech, "pinterest_tag": "Pinterest Tag" in tech, "tech": tech,
        "decision_makers": [f"{p['full_name']} — {p['title']}" for p in decision],
        "other_people": [f"{p['full_name']} — {p['title']}" for p in people if p not in decision],
        "personal_emails": [e for e in emails if not e.lower().startswith(GENERIC)],
        "general_emails": [e for e in emails if e.lower().startswith(GENERIC)],
        "email_pattern": pattern or None,
        "email_guess": guess,  # unverified; check before sending
        "evidence": {p["full_name"]: p.get("evidence", "") for p in people},
    }


def main():
    pages_dir = HERE / "pages"
    wanted = sys.argv[1:] or sorted(d.name for d in pages_dir.iterdir() if d.is_dir()) if pages_dir.exists() else []
    results = []
    for domain in wanted:
        pages = load(pages_dir / domain)
        if not pages:
            print(f"{domain}: no saved pages (run capture.sh first)")
            continue
        results.append(analyze(domain, pages))
    if not results:
        return
    out = HERE / "results"; out.mkdir(exist_ok=True)
    stamp = datetime.date.today().isoformat()
    (out / f"{stamp}.json").write_text(json.dumps(results, indent=1, ensure_ascii=False))
    ads = lambda r: ", ".join(k for k, v in (("Meta", r["meta_ads"]), ("Google", r["google_ads"]),
                                              ("TikTok", r["tiktok_pixel"]), ("Pinterest", r["pinterest_tag"])) if v) or "—"
    rows = ["| Brand | Decision-maker | Ads running | Email on site | Guess (unverified) |", "|---|---|---|---|---|"]
    for r in sorted(results, key=lambda r: -(r["meta_ads"] + r["google_ads"] + r["tiktok_pixel"] + r["pinterest_tag"])):
        rows.append(f"| {r['brand']} | {'; '.join(r['decision_makers']) or '—'} | {ads(r)} | "
                    f"{', '.join(r['personal_emails'] + r['general_emails']) or '—'} | {r['email_guess'] or '—'} |")
    (out / f"{stamp}.md").write_text("\n".join(rows) + "\n")
    print("\n".join(rows))
    print(f"\nSaved: {out / (stamp + '.json')}")


if __name__ == "__main__":
    main()
