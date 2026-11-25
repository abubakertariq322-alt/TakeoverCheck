# TakeoverCheck — Your Own Subdomain Takeover Checker

**PNY Trainings · Cyber Security Department · Reconnaissance track**
Student: Abubaker Tariq · Instructor: Abdul Mannan · Deadline: Tuesday, 25 November 2026

A command-line tool in Python that finds DNS records pointing at
cloud services nobody owns any more. When a company deletes a cloud
service but forgets the DNS record, the name hangs in the air — and
anyone can claim it. This tool finds those records before anyone
else does.

## How it works

1. Read a subdomain list (one name per line).
2. Resolve each name, following CNAME records to the end of the chain.
3. Flag chains whose final target does not resolve — the classic dangling record.
4. For flagged names, fetch the HTTP error page and match it against
   provider fingerprints (GitHub Pages, Heroku, AWS S3, Azure, Netlify, Shopify).
5. Rate each subdomain:
   - **high** — dangling + matching provider fingerprint
   - **medium** — dangling, no fingerprint matched
   - **clear** — resolves normally
6. Print and save a report with chains, ratings and evidence.

It only **reads** DNS and public error pages. It never claims,
registers or takes over anything.

## Setup

```bash
cd takeovercheck
python3 -m venv venv
venv/bin/pip install -r requirements.txt   # dnspython, requests
```

## Run it

Lab zone (Step 7 — deterministic, no network needed):

```bash
venv/bin/python takeovercheck.py -i subdomains.txt -o sample_report.txt \
    --json sample_report.json --lab-zone lab_zone.json
```

Real DNS (read-only, public names only):

```bash
venv/bin/python takeovercheck.py -i subdomains_real.txt -o report.txt
```

Step 1 on its own:

```bash
venv/bin/python resolve_one.py example.com
```

## Files

| File | What it is |
|---|---|
| `takeovercheck.py` | The tool — Steps 1–6 in one file, small functions |
| `resolve_one.py` | Step 1 standalone: resolve one name |
| `lab_zone.json` | Lab DNS zone we control, with planted dangling records (Step 7) |
| `subdomains.txt` | 10-name lab list |
| `subdomains_real.txt` | Public names for the real-DNS test only |
| `tests/github_pages_error.html` | Saved GitHub Pages error page (Step 4 test) |
| `tests/normal_page.html` | Saved normal page (Step 4 test — must NOT match) |
| `sample_report.txt` / `.json` | Real full-run report from the lab zone |
| `TakeoverCheck-Lab-Report.pdf` | 7-page professional lab report (5 high, 1 medium, 4 clear) |
| `LICENSE` | MIT License |
| `test_step1.txt`, `test_step2_3_4_5.txt`, `test_step6_7.txt` | Per-step test evidence |
| `TEST_LOG.md` | What was tested, and the result of every step |
| `DEMO.md` | Demo script + one finding explained |

## Sample result (lab zone, 10 names)

**5 high, 1 medium, 4 clear.**

- High: `blog` (GitHub Pages), `shop` (Heroku), `files` (AWS S3),
  `old` (Azure), `docs` (Netlify) — dangling CNAMEs whose targets
  return the provider's "service gone" error page.
- Medium: `staging` — dangling, but only a generic 404, no provider
  fingerprint, so it needs manual verification.
- Clear: `www`, `dev` (two-step CNAME chain), `api`, `mail` — all resolve.

## Screenshots

![Full lab run](screenshots/screenshot-1-terminal-run.png)

![Sample report — blog HIGH](screenshots/screenshot-2-sample-report.png)

![Project files](screenshots/screenshot-3-project-files.png)

## One defensive lesson

**DNS hygiene: remove the record when you delete the service.**
Every high finding here happened the same way — the cloud service
was deleted, the CNAME was left behind. A cleanup checklist on
service deletion (delete the DNS record in the same change as the
service) closes the whole class of findings.

## Lab rules

Build and test only on systems you own or have written permission
to test, inside an isolated lab environment. Never test systems
belonging to others without explicit written authorization.
Unauthorized access is a criminal offence under the Prevention of
Electronic Crimes Act, 2016 (Pakistan). Never attempt to register
or claim a dangling cloud service — checking for the weakness is
the job; claiming it is unauthorized access.

## DNS note

This VM blocks outbound UDP port 53, so the dnspython (UDP)
lookup is tried first and, if the network refuses it, the tool
falls back to DNS-over-HTTPS (`https://dns.google/resolve`) —
still a read-only public DNS lookup. Lab mode (`--lab-zone`)
needs no network at all.
