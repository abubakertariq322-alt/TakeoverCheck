"""TakeoverCheck — Step 1: Resolve one name.

Prints the A and CNAME records for one domain.
Uses takeovercheck.resolve_one(), which tries dnspython (UDP) first
and falls back to DNS-over-HTTPS — this VM blocks outbound UDP
port 53, so plain dnspython alone returns nothing here.
Usage:  python resolve_one.py <domain>
Example: python resolve_one.py example.com
Lab-only: read-only DNS lookups, no claiming anything.
"""

import sys

from takeovercheck import resolve_one


def main():
    if len(sys.argv) != 2:
        print("Usage: python resolve_one.py <domain>")
        sys.exit(1)

    result = resolve_one(sys.argv[1])
    print(f"Domain: {result['name']}")
    print(f"CNAME: {result['cname'] if result['cname'] else 'none'}")
    print(f"A:     {result['a'] if result['a'] else 'none'}")
    if result["error"]:
        print(f"Error: {result['error']}")


if __name__ == "__main__":
    main()
