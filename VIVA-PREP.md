# TakeoverCheck — Viva Prep

Deadline: Tuesday 25 November 2026. Prepared 20 November 2026 from the real
run in `sample_report.txt`, `TEST_LOG.md` and `DEMO.md`. Lab only
(`acme-lab.test` zone in `lab_zone.json`) — no real domain was tested,
nothing was claimed or registered.

## 1-minute intro (bolne ke liye)

> "TakeoverCheck mera apna subdomain takeover checker hai, Python mein. Ye
> subdomains ki list leta hai, har naam ka CNAME chain dnspython se follow
> karta hai, aur dangling record dhoondhta hai — CNAME jiska target NXDOMAIN
> de ya resolve hi na ho. Phir dangling wale ka HTTP error page provider ke
> fingerprint se match karta hai, aur har naam ko high, medium ya clear rate
> karta hai. Meri lab zone par 10 naam ka full run mein 5 high, 1 medium aur
> 4 clear aaye. Blog GitHub Pages par high tha, shop Heroku par, files AWS S3
> par, old Azure par, docs Netlify par — har ek ka target delete ho chuka tha
> lekin DNS record reh gaya tha. Staging medium tha kyunki wo dangling to tha,
> lekin kisi provider ka fingerprint match nahi hua. Ye sirf check karta hai,
> claim nahi karta — fix ye hai ke service delete karte waqt uska DNS record
> bhi delete karo."

## Likely questions — short answers

**1. TakeoverCheck kya karta hai?**
Subdomains ki file se list leta hai, har naam ka CNAME chain follow karta
hai, dangling record detect karta hai, error page ko provider fingerprint se
match karta hai, aur har naam ko high / medium / clear rate karta hai —
evidence ke saath, text report (`sample_report.txt`) aur JSON report
(`sample_report.json`) mein.

**2. Subdomain takeover hota kya hai?**
Company ne website cloud par banayi, phir service delete kar di, lekin DNS
record delete karna bhool gayi. Ab subdomain kisi taraf point kar raha hai jo
exist hi nahi karta — koi aur us naam ko claim karke us par apni site chala
sakta hai. Tool aisi hi records dhoondhta hai.

**3. Full lab run ka result kya tha?**
10 naam: 5 high, 1 medium, 4 clear. High: blog (GitHub Pages), shop
(Heroku), files (AWS S3), old (Azure), docs (Netlify). Medium: staging
(dangling, lekin fingerprint nahi). Clear: www, dev, api, mail.

**4. High, medium aur clear ka farq kya hai?**
High = dangling + provider fingerprint match (claimable, prove ho gaya).
Medium = dangling lekin fingerprint nahi (verify karna baaki hai).
Clear = naam theek se resolve hota hai, koi dangling record nahi.

**5. CNAME chain kaise follow ki? (Step 2)**
`follow_chain()` CNAME ko end tak follow karta hai jab tak A record ya dead
end na mil jaye. Example: `dev.acme-lab.test -> dev2.acme-lab.test -> A
10.0.0.5` — do steps, order mein print hote hain. Max 10 hops, loop se
bachne ke liye.

**6. Dangling kaise detect kiya? (Step 3)**
Final target NXDOMAIN de ya koi answer na de to dangling hai. Live naam
`www.acme-lab.test` dangling nahi; dead target `acme-blog.github.io`
NXDOMAIN hai, is liye `blog.acme-lab.test` dangling hai.

**7. Fingerprint matching kaise kaam karta hai? (Step 4)**
Har provider ka error page ek khaas string deta hai, jo normal page par
kabhi nahi hoti — jaise GitHub Pages: "There isn't a GitHub Pages site
here", Heroku: "No such app", S3: "NoSuchBucket". Saved error page match
karta hai, normal page nahi karta — test mein yehi prove hua. 6 providers:
GitHub Pages, Heroku, AWS S3, Azure, Netlify, Shopify.

**8. Ek finding explain karo — blog kyun high hai?**
`blog.acme-lab.test` ka CNAME `acme-blog.github.io` ki taraf hai. Wo target
NXDOMAIN deta hai — GitHub Pages site delete ho chuki hai. Error page par
GitHub ka message milta hai, fingerprint match hota hai. Matlab koi
`acme-blog` naam ki GitHub Pages site bana kar is subdomain par apni content
serve kar sakta hai. Fix: `blog` wala CNAME record delete karo.

**9. Staging medium kyun hai, high kyun nahi?**
`staging.acme-lab.test` dangling hai — target `staging-gone.example.net`
NXDOMAIN hai — lekin uska error page generic 404 hai, kisi provider ka
fingerprint match nahi hua. Is liye high nahi, medium hai: verify manually.

**10. Lab zone kya hai, aur real domain par kyun nahi chalaya? (Step 7)**
`lab_zone.json` apni khud ki zone hai (`acme-lab.test`) — usme planted
dangling records hain, aur har planted record sahi rating ke saath flag hua.
Real domain par sirf read-only check theek hai; kisi dangling service ko
register ya claim karna unauthorized access hai, is liye kabhi nahi karna.

**11. Is VM par DNS ka masla kya tha?**
Ye VM outbound UDP port 53 block karti hai, to plain dnspython
"NoNameservers" deta hai. Tool pehle dnspython try karta hai, phir
DNS-over-HTTPS (`https://dns.google/resolve`) se fallback leta hai — ye bhi
read-only public DNS lookup hai. Lab mode (`--lab-zone`) ko network ki
zaroorat hi nahi. Apni machine par UDP bhi chalega.

**12. Defensive lesson kya hai?**
DNS hygiene: service delete karte waqt uska DNS record bhi usi change mein
delete karo. Record reh gaya to naam claimable rehta hai — is liye
decommission ka checklist mein DNS cleanup hona chahiye.

## Live demo (viva mein chalane ke liye)

```bash
cd ~/workspace/takeovercheck

# Step 1 — ek naam resolve karo
venv/bin/python resolve_one.py example.com

# Full run — lab zone (deterministic, no network needed)
venv/bin/python takeovercheck.py -i subdomains.txt -o sample_report.txt \
    --json sample_report.json --lab-zone lab_zone.json

# Real-DNS sanity check (read-only)
venv/bin/python takeovercheck.py -i subdomains_real.txt -o test_real.txt
```

## GitHub publish — file list (20 Nov 2026 ko check kiya)

**Commit karein:** `takeovercheck.py`, `resolve_one.py`, `README.md`,
`DEMO.md`, `TEST_LOG.md`, `VIVA-PREP.md`, `lab_zone.json`,
`subdomains.txt`, `subdomains_real.txt`, `requirements.txt`,
`sample_report.txt`, `sample_report.json`, `.gitignore`.

**Exclude (`.gitignore` mein hai):** `venv/`, `__pycache__/`, `*.pyc`.

**Test files — faisla:** `test_step1*.txt`, `test_step2_3_4_5.txt`,
`test_step6_7.txt`, `test_real.txt` har step ka alag evidence hain, lekin
unka summary `TEST_LOG.md` mein pehle se hai — delete karein ya raw evidence
ke tor par rakhein, dono theek hain. `tests/` folder mein saved error page
aur normal page hain (Step 4 ka test data) — ye rakhne ke qabil hain.

**Abhi bhi chahiye:** GitHub repo URL — uske baghair `git push` nahi ho sakta.
APIGuard ka bhi publish usi ka intezar kar raha hai; dono projects ki
deadline ek hi hai — Tuesday 25 November 2026.
