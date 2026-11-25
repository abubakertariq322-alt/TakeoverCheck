#!/usr/bin/env python3
"""
TakeoverCheck — Your Own Subdomain Takeover Checker.
PNY Trainings, Cyber Security Department, Reconnaissance track.
Student: Abubaker Tariq. Instructor: Abdul Mannan.

What it does
------------
Reads a list of subdomains from a file, follows each CNAME chain
with DNS queries, detects dangling records (a CNAME target that no
longer resolves), matches HTTP error pages against provider
fingerprints, and rates each subdomain high / medium / clear,
with the evidence for every verdict. It only READS DNS and public
error pages. It never claims, registers or takes over anything.

Lab-only rule: test only on a DNS zone you own / control, or on the
supplied lab zone (--lab-zone). Never test systems belonging to
others without explicit written authorization.

Usage
-----
    python takeovercheck.py -i subdomains.txt -o report.txt
    python takeovercheck.py -i subdomains.txt -o report.txt --json report.json
    python takeovercheck.py -i subdomains.txt -o report.txt --lab-zone lab_zone.json

DNS note: this VM blocks outbound UDP port 53, so the dnspython
(UDP) lookup is tried first and, if the network refuses it, the
tool falls back to DNS-over-HTTPS (https://dns.google/resolve),
which is still a read-only public DNS lookup. Lab mode
(--lab-zone) needs no network at all and is the deterministic
Step 7 test.
"""

import argparse
import json
import sys
import urllib.request

try:
    import dns.resolver
    import dns.exception
    HAVE_DNSPYTHON = True
except ImportError:  # pragma: no cover - dnspython is in requirements.txt
    HAVE_DNSPYTHON = False

# ---------------------------------------------------------------------------
# Fingerprints: provider error-page signatures (Step 4).
# Each provider maps to strings that appear only on its "service gone"
# error page, never on a normal live page.
# ---------------------------------------------------------------------------
FINGERPRINTS = {
    "github-pages": [
        "There isn't a GitHub Pages site here",
        "404: There isn't a GitHub Pages site here",
    ],
    "heroku": [
        "No such app",
        "There's nothing here, yet",
    ],
    "aws-s3": [
        "NoSuchBucket",
        "The specified bucket does not exist",
    ],
    "azure": [
        "404 Web Site not found",
        "This web app is not available",
    ],
    "netlify": [
        "Not Found - Request ID",
    ],
    "shopify": [
        "Sorry, this shop is currently unavailable",
    ],
}

DOH_URL = "https://dns.google/resolve"


# ---------------------------------------------------------------------------
# Step 1 — Resolve one name
# ---------------------------------------------------------------------------
def query_dns(name, rdtype):
    """Return (answers, error).

    answers: list of strings for `rdtype` ('A' or 'CNAME').
    error: None, 'NXDOMAIN', 'NOANSWER', or 'ERROR: ...'.
    Tries dnspython (UDP) first, then DNS-over-HTTPS as a fallback.
    """
    name = name.rstrip(".")
    if HAVE_DNSPYTHON:
        try:
            resolver = dns.resolver.Resolver()
            resolver.timeout = 5
            resolver.lifetime = 5
            answers = resolver.resolve(name, rdtype)
            return [str(r).rstrip(".") for r in answers], None
        except dns.resolver.NXDOMAIN:
            return [], "NXDOMAIN"
        except dns.resolver.NoAnswer:
            return [], "NOANSWER"
        except Exception as exc:  # network blocked etc. -> try DoH below
            doh_error = str(exc)
        else:
            doh_error = None
    else:
        doh_error = "dnspython not installed"

    # DNS-over-HTTPS fallback (read-only public DNS lookup).
    try:
        url = "%s?name=%s&type=%s" % (DOH_URL, name, 5 if rdtype == "CNAME" else 1)
        with urllib.request.urlopen(url, timeout=8) as resp:
            data = json.load(resp)
    except Exception as exc:
        return [], "ERROR: %s (UDP failed: %s)" % (exc, doh_error)

    status = data.get("Status")
    if status == 3:  # NXDOMAIN
        return [], "NXDOMAIN"
    answers = [a["data"].rstrip(".") for a in data.get("Answer", [])]
    if not answers:
        return [], "NOANSWER"
    return answers, None


def resolve_one(name):
    """Step 1: print a name's A and CNAME records.

    Returns {'name': ..., 'a': [...], 'cname': [...], 'error': ...}.
    """
    cname, cname_err = query_dns(name, "CNAME")
    if cname:
        return {"name": name, "a": [], "cname": cname, "error": None}
    if cname_err == "NXDOMAIN":
        return {"name": name, "a": [], "cname": [], "error": "NXDOMAIN"}
    a, a_err = query_dns(name, "A")
    if a:
        return {"name": name, "a": a, "cname": [], "error": None}
    return {"name": name, "a": [], "cname": [],
            "error": a_err or cname_err or "NOANSWER"}


# ---------------------------------------------------------------------------
# Step 2 — Follow the chain
# ---------------------------------------------------------------------------
def follow_chain(name, max_hops=10):
    """Follow CNAME records until an A record or a dead end.

    Returns (chain, final_result) where chain is a list like
    ['blog.acme-lab.test', 'acme-blog.github.io'] and final_result
    is the resolve_one() dict for the last name in the chain.
    """
    chain = [name.rstrip(".")]
    current = chain[0]
    for _ in range(max_hops):
        result = resolve_one(current)
        if result["cname"]:
            nxt = result["cname"][0]
            if nxt in chain:  # loop guard
                return chain, {"name": nxt, "a": [], "cname": [],
                               "error": "LOOP"}
            chain.append(nxt)
            current = nxt
            continue
        return chain, result
    return chain, {"name": current, "a": [], "cname": [],
                   "error": "TOO_MANY_HOPS"}


# ---------------------------------------------------------------------------
# Step 3 — Detect the dead end
# ---------------------------------------------------------------------------
def is_dangling(final_result):
    """True when the end of the chain does not resolve.

    Dangling = NXDOMAIN, empty answer, or an error with no A record.
    """
    if final_result["a"]:
        return False
    return True


# ---------------------------------------------------------------------------
# Step 4 — Fingerprint matching
# ---------------------------------------------------------------------------
def match_fingerprint(body):
    """Return the provider name whose signature is in `body`, or None.

    `body` is the HTTP error page text. Only an error page matches;
    a normal page contains none of these strings.
    """
    if not body:
        return None
    for provider, signatures in FINGERPRINTS.items():
        for sig in signatures:
            if sig in body:
                return provider
    return None


def fetch_error_page(name, timeout=5):
    """Fetch http://<name>/ and return (status, body).

    Only used for dangling names, to collect their error page.
    Returns (None, '') when the host cannot be reached at all.
    """
    for scheme in ("http://", "https://"):
        try:
            req = urllib.request.Request(
                scheme + name + "/",
                headers={"User-Agent": "TakeoverCheck/1.0 (lab)"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.status, resp.read().decode("utf-8", "ignore")
        except urllib.error.HTTPError as exc:
            # An error page (404 etc.) is exactly what we want to read.
            return exc.code, exc.read().decode("utf-8", "ignore")
        except Exception:
            continue
    return None, ""


# ---------------------------------------------------------------------------
# Step 5 — Risk rating
# ---------------------------------------------------------------------------
def rate_subdomain(dangling, fingerprint):
    """Combine dangling status + fingerprint into a rating.

    high   = dangling record WITH a matching provider fingerprint
    medium = dangling record WITHOUT a fingerprint
    clear  = not dangling
    Returns (rating, reason).
    """
    if dangling and fingerprint:
        return "high", ("Dangling CNAME whose target matches the "
                        "%s error page — the name can be claimed." % fingerprint)
    if dangling:
        return "medium", ("Dangling CNAME, but no provider fingerprint "
                          "matched — verify the target manually.")
    return "clear", "Resolves normally; no dangling record found."


# ---------------------------------------------------------------------------
# Lab zone (Step 7) — a DNS zone we control, as a JSON file.
# ---------------------------------------------------------------------------
class LabResolver:
    """Resolves names from a lab-zone JSON file, no network needed.

    File format:
      {"records": {"name": {"A": [...], "CNAME": [...]}},
       "http": {"target-name": {"status": 404, "body": "..."}}}
    A name missing from "records" is NXDOMAIN, like a deleted service.
    """

    def __init__(self, path):
        with open(path, encoding="utf-8") as fh:
            self.zone = json.load(fh)
        self.records = self.zone.get("records", {})
        self.http = self.zone.get("http", {})

    def resolve_one(self, name):
        name = name.rstrip(".")
        rec = self.records.get(name)
        if rec is None:
            return {"name": name, "a": [], "cname": [], "error": "NXDOMAIN"}
        return {"name": name, "a": rec.get("A", []),
                "cname": rec.get("CNAME", []), "error": None}

    def fetch(self, name):
        page = self.http.get(name.rstrip("."))
        if page is None:
            return None, ""
        return page.get("status"), page.get("body", "")


# ---------------------------------------------------------------------------
# Full check for one subdomain (Steps 1-5 together)
# ---------------------------------------------------------------------------
def check_subdomain(name, lab=None):
    """Check one subdomain end to end. Returns a result dict."""
    if lab is not None:
        # Lab mode: same steps, resolver reads the lab zone file.
        chain = [name.rstrip(".")]
        current = chain[0]
        final = lab.resolve_one(current)
        for _ in range(10):
            if final["cname"]:
                nxt = final["cname"][0]
                if nxt in chain:
                    final = {"name": nxt, "a": [], "cname": [], "error": "LOOP"}
                    break
                chain.append(nxt)
                current = nxt
                final = lab.resolve_one(current)
                continue
            break
        dangling = is_dangling(final)
        fingerprint = None
        http_status, http_body = None, ""
        if dangling:
            target = chain[-1]
            http_status, http_body = lab.fetch(target)
            fingerprint = match_fingerprint(http_body)
    else:
        chain, final = follow_chain(name)
        dangling = is_dangling(final)
        fingerprint = None
        http_status, http_body = None, ""
        if dangling:
            http_status, http_body = fetch_error_page(name)
            fingerprint = match_fingerprint(http_body)

    rating, reason = rate_subdomain(dangling, fingerprint)
    return {
        "subdomain": name,
        "chain": chain,
        "final_target": chain[-1],
        "final_error": final.get("error"),
        "final_a": final.get("a", []),
        "dangling": dangling,
        "http_status": http_status,
        "fingerprint": fingerprint,
        "rating": rating,
        "reason": reason,
    }


# ---------------------------------------------------------------------------
# Step 6 — CLI arguments and report
# ---------------------------------------------------------------------------
def load_subdomains(path):
    """Read one subdomain per line, skipping blanks and # comments."""
    names = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line and not line.startswith("#"):
                names.append(line)
    return names


def format_report(results):
    """Plain-text report: every subdomain, its chain, rating, evidence."""
    lines = ["TakeoverCheck Report", "=" * 20, ""]
    counts = {"high": 0, "medium": 0, "clear": 0}
    for r in results:
        counts[r["rating"]] += 1
        lines.append("Subdomain: %s" % r["subdomain"])
        lines.append("  Chain:   %s" % " -> ".join(r["chain"]))
        if r["final_a"]:
            lines.append("  Final A: %s" % ", ".join(r["final_a"]))
        if r["final_error"]:
            lines.append("  Final:   %s" % r["final_error"])
        lines.append("  Dangling: %s" % ("YES" if r["dangling"] else "no"))
        if r["fingerprint"]:
            lines.append("  Fingerprint: %s (HTTP %s)"
                         % (r["fingerprint"], r["http_status"]))
        elif r["dangling"]:
            lines.append("  Fingerprint: none (HTTP %s)" % r["http_status"])
        lines.append("  Rating:  %s — %s" % (r["rating"].upper(), r["reason"]))
        lines.append("")
    lines.append("Summary: %d high, %d medium, %d clear (of %d)"
                 % (counts["high"], counts["medium"], counts["clear"],
                    len(results)))
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="TakeoverCheck — subdomain takeover checker (lab only).")
    parser.add_argument("-i", "--input", required=True,
                        help="file with one subdomain per line")
    parser.add_argument("-o", "--output", required=True,
                        help="report file to write")
    parser.add_argument("--json", dest="json_out", default=None,
                        help="also write a JSON report to this file")
    parser.add_argument("--lab-zone", default=None,
                        help="lab zone JSON file (Step 7, no network)")
    args = parser.parse_args(argv)

    lab = LabResolver(args.lab_zone) if args.lab_zone else None
    names = load_subdomains(args.input)
    results = [check_subdomain(n, lab=lab) for n in names]

    report = format_report(results)
    print(report)
    with open(args.output, "w", encoding="utf-8") as fh:
        fh.write(report + "\n")
    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as fh:
            json.dump(results, fh, indent=2)
    print("Report saved to %s" % args.output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
