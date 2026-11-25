# TakeoverCheck — Test Log

All tests run on 2026-11-20, in `~/workspace/takeovercheck/`,
with `venv/bin/python` (Python 3.12, dnspython 2.9.2).
Lab-only: the lab zone is `lab_zone.json` (our own zone,
`acme-lab.test`). No real targets, nothing claimed.

## Environment note

- `pip install dnspython` in the system Python is blocked (PEP 668,
  externally managed), so a venv was created, same as APIGuard.
- This VM blocks outbound UDP port 53, so plain dnspython returns
  "NoNameservers". The tool tries dnspython first, then falls back
  to DNS-over-HTTPS (`https://dns.google/resolve`) — verified:
  `example.com` resolves to `104.20.23.154, 172.66.147.243`,
  matching a manual DoH lookup. Lab mode needs no network at all.

## Step 1 — Resolve one name — PASS

`test_step1.txt`
- `resolve_one.py example.com` → CNAME none, A
  `['104.20.23.154', '172.66.147.243']` — matches manual lookup.
- `resolve_one("www.example.com")` → same A records.

## Step 2 — Follow the chain — PASS

`test_step2_3_4_5.txt`
- `dev.acme-lab.test` → `dev.acme-lab.test -> dev2.acme-lab.test`,
  final A `10.0.0.5`. Both steps printed in order.

## Step 3 — Detect the dead end — PASS

`test_step2_3_4_5.txt`
- Live name `www.acme-lab.test` → dangling? False.
- Dead target `acme-blog.github.io` → NXDOMAIN, dangling? True.

## Step 4 — Fingerprint matching — PASS

`test_step2_3_4_5.txt`
- Saved GitHub Pages error page → `github-pages`.
- Saved normal page → `None`. Only the error page matches.

## Step 5 — Risk rating — PASS

`test_step2_3_4_5.txt` — one of each rating confirmed:
- `blog.acme-lab.test` → **high** (dangling + github-pages fingerprint)
- `staging.acme-lab.test` → **medium** (dangling, no fingerprint)
- `www.acme-lab.test` → **clear** (resolves normally)

## Step 6 — CLI arguments and report — PASS

`test_step6_7.txt`
- `takeovercheck.py -i subdomains.txt -o sample_report.txt
  --json sample_report.json --lab-zone lab_zone.json`
- Exit code 0. All 10 names appear in the report (txt + json).

## Step 7 — Test on your own lab zone — PASS

`sample_report.txt` / `sample_report.json` (full run, 10 names):
- **5 high, 1 medium, 4 clear.**
- High: blog (github-pages), shop (heroku), files (aws-s3),
  old (azure), docs (netlify).
- Medium: staging (dangling, generic 404, no fingerprint).
- Clear: www, dev (two-step chain), api, mail.
- Every planted record was flagged with the right rating.
- JSON report verified programmatically: 10 entries,
  Counter = {'high': 5, 'medium': 1, 'clear': 4}.

Real-DNS sanity check (`test_real.txt`): `example.com` and
`www.example.com` both **clear**, 0 high / 0 medium / 2 clear.
Read-only lookups only.

## Deliverables checklist

- [x] Working tool — runs and rates a 10-name list end to end
- [x] Must-have features — all six working (list input, CNAME
      chain, dangling detection, fingerprints, rating, report file)
- [x] Code clarity — small functions, clear names, short comments
- [x] Testing — each step tested before moving on, lab-only
- [x] README and demo — README.md, DEMO.md, sample report
- [ ] Publish on GitHub — needs umair's GitHub repo URL
