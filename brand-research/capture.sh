#!/bin/bash
# Save each brand's homepage + About/Team/Contact/Press pages so Harvey can
# read them. Run this in your Mac's own Terminal (normal internet):
#
#   bash ~/"Claude Projects"/harvey/brand-research/capture.sh
#
# Brands come from brands.txt next to this script (one domain per line).
# Pages land in pages/<domain>/. Nothing is sent anywhere; it only downloads.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
LIST="${1:-$HERE/brands.txt}"
OUT="$HERE/pages"
UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15"
WANT='about|story|team|founder|people|contact|press|meet|who-we-are|our-brand'
SKIP='account|cart|login|policies|collections/|products/|blogs/[^"]|cdn|\.(jpg|png|webp|svg|css|js|pdf)'
MAX_PAGES=5

fetch() {  # fetch URL FILE -> prints final URL on success
  curl -sSL --compressed --max-time 20 -A "$UA" -o "$2" -w '%{http_code} %{url_effective}' "$1" 2>/dev/null
}

# Same-site About/Team/Contact links in a saved page. Kept in a function (not
# inside $( )) because macOS's bash 3.2 mis-parses case patterns there.
page_links() {  # page_links FILE BASE HOST
  grep -oiE 'href="[^"#]+"' "$1" | sed -E 's/^[hH][rR][eE][fF]="//; s/"$//; s/&amp;/\&/g' \
    | grep -iE "$WANT" | grep -viE "$SKIP" \
    | while IFS= read -r h; do
        case "$h" in
          (http*) h_host="$(echo "$h" | sed -E 's#^https?://##; s#/.*##; s#^www\.##')"
                  if [ "$h_host" = "$3" ]; then echo "$h"; fi ;;
          (//*|mailto:*|tel:*|javascript:*) : ;;
          (/*) echo "$2$h" ;;
          (*) echo "$2/$h" ;;
        esac
      done | sed -E 's#\?.*##; s#/$##' | awk '!seen[$0]++' | head -n "$MAX_PAGES"
}

[ -f "$LIST" ] || { echo "No brand list at $LIST"; exit 1; }
mkdir -p "$OUT"
ok=0; fail=0
while IFS= read -r line || [ -n "$line" ]; do
  line="$(echo "$line" | sed -E 's/#.*//; s/^[[:space:]]+//; s/[[:space:]]+$//')"
  [ -z "$line" ] && continue
  case "$line" in (http*) home="$line" ;; (*) home="https://$line" ;; esac
  home="${home%/}/"
  domain="$(echo "$home" | sed -E 's#^https?://##; s#/.*##; s#^www\.##')"
  dir="$OUT/$domain"; mkdir -p "$dir"; : > "$dir/urls.txt"
  printf '%-28s ' "$domain"
  res="$(fetch "$home" "$dir/00-home.html")"; code="${res%% *}"; final="${res#* }"
  if [ "$code" != "200" ] || [ ! -s "$dir/00-home.html" ]; then
    echo "could not load homepage (HTTP $code)"; rm -rf "$dir"; fail=$((fail+1)); continue
  fi
  echo "00-home.html $final" >> "$dir/urls.txt"
  base="$(echo "$final" | sed -E 's#^(https?://[^/]+).*#\1#')"
  host="$(echo "$base" | sed -E 's#^https?://##; s#^www\.##')"
  # About / team / contact links on the homepage, same site only.
  links="$(page_links "$dir/00-home.html" "$base" "$host")"
  n=0
  for u in $links; do
    n=$((n+1)); f="$(printf '%02d' "$n")-page.html"
    sleep 1
    res="$(fetch "$u" "$dir/$f")"; code="${res%% *}"
    if [ "$code" = "200" ] && [ -s "$dir/$f" ]; then echo "$f ${res#* }" >> "$dir/urls.txt"; else rm -f "$dir/$f"; n=$((n-1)); fi
  done
  echo "saved homepage + $n page(s)"; ok=$((ok+1))
  sleep 1
done < "$LIST"
echo; echo "Done: $ok brand(s) saved, $fail failed. Pages are in: $OUT"
echo "Next: tell Claude \"analyze the captured brands\"."
