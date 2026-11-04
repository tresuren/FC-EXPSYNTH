#!/bin/bash
# usage: rr.sh  (starts API server, routes route.dsn, collector -> stream_all.txt)
cd "$(dirname "$0")"
python3 -c "
import pcbnew
bd=pcbnew.LoadBoard('FC-EXPSYNTH.kicad_pcb')
for z in list(bd.Zones()):
    if z.GetLayer()==pcbnew.In2_Cu: bd.Remove(z)
print(pcbnew.ExportSpecctraDSN(bd,'route.dsn'))"
python3 - <<'P'
import base64,json
json.dump({'filename':'route.dsn','data':base64.b64encode(open('route.dsn','rb').read()).decode()},open('inp2.json','w'))
P
B=http://127.0.0.1:37864; H1="Freerouting-Profile-ID: 3f2b8c1e-5a7d-4e19-9c3a-1d2e4f6a8b0c"; H2="Freerouting-Environment-Host: KiCad/7.0"
if ! curl -s $B/v1/system/status >/dev/null; then
  setsid nohup java -Xmx3g -jar ../tools/fr.jar --api_server-enabled=true > fr_api.log 2>&1 < /dev/null &
  for i in $(seq 1 20); do sleep 2; curl -s $B/v1/system/status >/dev/null && break; done
fi
S=$(curl -s -X POST $B/v1/sessions/create -H "$H1" -H "$H2" | python3 -c "import sys,json;print(json.load(sys.stdin)['id'])")
JID=$(curl -s -X POST $B/v1/jobs/enqueue -H "$H1" -H "$H2" -H 'Content-Type: application/json' -d "{\"session_id\":\"$S\",\"name\":\"r\",\"priority\":\"NORMAL\"}" | python3 -c "import sys,json;print(json.load(sys.stdin)['id'])")
echo $JID > jid.txt
curl -s -X POST $B/v1/jobs/$JID/input -H "$H1" -H "$H2" -H 'Content-Type: application/json' --data-binary @inp2.json >/dev/null
curl -s -X POST $B/v1/jobs/$JID/settings -H "$H1" -H "$H2" -H 'Content-Type: application/json' -d '{"max_passes":45,"job_timeout":"01:00:00"}' >/dev/null
rm -f stream_all.txt
setsid nohup bash -c "curl -s -N $B/v1/jobs/$JID/output/stream -H '$H1' -H '$H2' > stream_all.txt" >/dev/null 2>&1 < /dev/null &
curl -s -X PUT $B/v1/jobs/$JID/start -H "$H1" -H "$H2" | python3 -c "import sys,json;print(json.load(sys.stdin)['state'])"
