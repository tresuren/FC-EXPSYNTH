#!/bin/bash
cd "$(dirname "$0")/.."
export FR_JAR=${FR_JAR:-/path/to/freerouting.jar}
bash scripts/rr.sh
JID=$(cat jid.txt); B=http://127.0.0.1:37864; H1="Freerouting-Profile-ID: 3f2b8c1e-5a7d-4e19-9c3a-1d2e4f6a8b0c"; H2="Freerouting-Environment-Host: KiCad/7.0"
for i in $(seq 1 400); do
  st=$(curl -s $B/v1/jobs/$JID -H "$H1" -H "$H2" | python3 -c "import sys,json;d=json.load(sys.stdin);print(d.get('state'))" 2>/dev/null)
  echo "$(date +%T) $st" >> poll.log
  case "$st" in COMPLETED|CANCELLED|TERMINATED|FAILED|TIMED_OUT) break;; esac
  sleep 15
done
curl -s $B/v1/jobs/$JID/output -H "$H1" -H "$H2" > out.json
python3 -c "
import json,base64
d=json.load(open('out.json')); s=base64.b64decode(d['data']).decode(); open('route.ses','w').write(s); print('ses',len(s),s.count('(wire'),s.count('(via'))"
echo DONE $st
