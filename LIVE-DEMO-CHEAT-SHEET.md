# TakeoverCheck — Live Demo Cheat Sheet
# Class mein ye file saamne rakh kar parho. Demo 2-3 minute ka hai.
# Lab mode hai — internet nahi chahiye.

## Demo se pehle (ek dafa, ghar par)
1. Zip extract karo, takeovercheck folder laptop par ho.
2. Us folder mein cmd kholo:
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
3. Ek dafa test run karo:
   python takeovercheck.py -i subdomains.txt -o sample_report.txt --json sample_report.json --lab-zone lab_zone.json
   Neeche aana chahiye: Summary: 5 high, 1 medium, 4 clear (of 10)

## Class mein — bolna kya hai, karna kya hai

### 1. Intro (20 second)
Bolo: "Ye TakeoverCheck hai, mera subdomain takeover checker, Python mein.
Ye subdomains ki list leta hai, har naam ka CNAME chain follow karta hai,
dangling record dhoondhta hai, aur high / medium / clear rate karta hai."

### 2. Step 1 — ek naam resolve karo
Command:
  python resolve_one.py example.com
Dikhega:
  Domain: example.com
  CNAME: none
  A: ['104.20.23.154', '172.66.147.243']
Bolo: "Ye ek naam resolve karta hai, A records dikhata hai."

### 3. Full run — 10 naam, lab zone
Command:
  python takeovercheck.py -i subdomains.txt -o sample_report.txt --json sample_report.json --lab-zone lab_zone.json
Dikhega (aakhir mein):
  Summary: 5 high, 1 medium, 4 clear (of 10)
Bolo: "10 naam check kiye, 5 high, 1 medium, 4 clear aaye."

### 4. Report kholo, ek finding samjhao
Command:
  notepad sample_report.txt
Bolo: "Blog high hai — blog.acme-lab.test GitHub Pages ki taraf point
karta hai, lekin wo site delete ho chuki hai, NXDOMAIN aata hai, aur
error page par GitHub ka fingerprint match hota hai. Matlab ye naam
claim ho sakta tha. Fix ye hai ke service delete karte waqt uska
DNS record bhi delete karo."

## Agar live kuch fail ho jaye
Ghabrao mat. sample_report.txt pehle se bani hui hai — usko khol kar
dikha do aur kaho: "Yehi report abhi ke run ki hai."
Teacher ko result chahiye, dobara run karna zaroori nahi.

## Result yaad rakhne ke liye
High (5): blog — GitHub Pages, shop — Heroku, files — AWS S3,
         old — Azure, docs — Netlify
Medium (1): staging — dangling, lekin fingerprint nahi
Clear (4): www, dev, api, mail
