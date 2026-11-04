import re,base64
t=open('stream_all.txt',errors='ignore').read()
ms=re.findall(r'data:\s+"data":\s*"([A-Za-z0-9+/=]+)"',t)
print('events',len(ms))
s=base64.b64decode(ms[-1]).decode()
open('route.ses','w').write(s); print(len(s), s.count('(wire'), s.count('(via'))
