#!/usr/bin/env bash
# Real runs of the 3 example graphs -> terminal SVG/PNG, HTML, OG PNG, badges. Needs google-chrome for SVG->PNG.
set -eu; cd "$(dirname "$0")/.."; OUT=${1:-shots}; mkdir -p "$OUT"; OUT=$(cd "$OUT" && pwd); BIN=${AGENTSIGNAL:-agentsignal}
CHROME=${CHROME:-google-chrome}; shot(){ timeout 60 "$CHROME" --headless=new --no-sandbox --disable-gpu --hide-scrollbars "$@" >/dev/null 2>&1; }
for g in naive safe idem; do
  "$BIN" check --graph tests.fixtures.${g}_graph:build --effect tests.fixtures.payments:charge --input '{"amount":1999}' \
    --json --svg "$OUT/$g-terminal.svg" --html "$OUT/$g-report.html" --png "$OUT/$g-og.png" \
    --badge "$OUT/$g-badge.svg" --badge-link https://tryagentsignal.com/check/ > "$OUT/$g-run.json" 2> "$OUT/$g-badge.md" || true
  vb=$(grep -oE 'viewBox="[^"]+"' "$OUT/$g-terminal.svg" | head -1 | tr -d '"' | cut -d= -f2)
  w=$(echo $vb | awk '{printf "%d",$3}'); h=$(echo $vb | awk '{printf "%d",$4}')
  printf '<html><body style="margin:0;background:#0b0d0c"><img src="%s-terminal.svg" style="display:block;width:%spx;height:%spx"></body></html>' $g $w $h > "$OUT/.$g-wrap.html"
  shot --force-device-scale-factor=2 --window-size=$w,$h --screenshot="$OUT/$g-terminal.png" "file://$OUT/.$g-wrap.html"
  shot --window-size=1000,1000 --screenshot="$OUT/$g-report-html.png" "file://$OUT/$g-report.html"
done
printf "<body style='background:#fff;margin:0;padding:16px'><img src='naive-badge.svg'><br><br><img src='safe-badge.svg'><br><br><img src='idem-badge.svg'></body>" > "$OUT/.badges.html"
shot --force-device-scale-factor=3 --window-size=320,120 --screenshot="$OUT/badges.png" "file://$OUT/.badges.html"
rm -f "$OUT"/.*.html; date -u +%FT%TZ > "$OUT/RUN_AT.txt"; echo "shots in $OUT"
