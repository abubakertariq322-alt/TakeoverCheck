# TakeoverCheck — Demo

## Run it (one command)

```bash
cd takeovercheck
venv/bin/python takeovercheck.py -i subdomains.txt -o sample_report.txt \
    --json sample_report.json --lab-zone lab_zone.json
```

## What you will see

```
Subdomain: blog.acme-lab.test
  Chain:   blog.acme-lab.test -> acme-blog.github.io
  Final:   NXDOMAIN
  Dangling: YES
  Fingerprint: github-pages (HTTP 404)
  Rating:  HIGH — Dangling CNAME whose target matches the
           github-pages error page — the name can be claimed.
...
Summary: 5 high, 1 medium, 4 clear (of 10)
```

Full output is in `sample_report.txt` (and `sample_report.json`).

## One finding, explained

**`blog.acme-lab.test` — HIGH**

- The subdomain points with a CNAME to `acme-blog.github.io`.
- That target returns NXDOMAIN — the GitHub Pages site was deleted.
- Fetching the error page returns GitHub's own message:
  *"There isn't a GitHub Pages site here."* — a fingerprint match.
- So the name is claimable: anyone could create a GitHub Pages
  site called `acme-blog` and the company's subdomain would start
  serving their content.

**Fix:** delete the `blog` CNAME record, or point it at a live
service. The lesson is DNS hygiene — remove the record in the
same change as you delete the service.

## Step-by-step demo (for the viva)

1. Step 1: `venv/bin/python resolve_one.py example.com`
   — A records `104.20.23.154`, `172.66.147.243`, matching a manual lookup.
2. Step 2: `dev.acme-lab.test` follows a two-step chain
   `dev -> dev2 -> 10.0.0.5` (see `test_step2_3_4_5.txt`).
3. Step 4: only the saved GitHub Pages error page matches a
   fingerprint; the normal page does not.
4. Step 7: the full run above, on the lab zone in `lab_zone.json`.
