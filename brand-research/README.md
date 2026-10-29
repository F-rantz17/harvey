# Brand research (fashion / beauty outreach)

Two steps. Nothing is ever emailed or sent anywhere.

1. **Capture** (your Mac's own Terminal, which has normal internet):

       bash ~/"Claude Projects"/harvey/brand-research/capture.sh

   Reads `brands.txt` (one website per line) and saves each brand's homepage plus
   its About / Team / Contact / Press pages into `pages/<domain>/`.

2. **Analyze** (ask Claude: "analyze the captured brands"), or run it yourself with
   Harvey's Python environment:

       python brand-research/analyze.py

   Runs Harvey's own detectors over the saved pages: decision-makers, ad pixels
   (Meta, Google, TikTok, Pinterest, including Shopify's pixel list), emails on the
   site, email pattern, and a guess for the top person. Writes
   `results/<date>.md` (a table to paste into Notion) and `results/<date>.json`.

Updating Harvey: `bash brand-research/update-harvey.sh` (or ask Claude to "update Harvey").

`brands.txt`, `pages/` and `results/` are git-ignored: your prospect list and
research stay on this Mac even though the code lives on GitHub.
Email guesses are unverified — check them before sending.
