"""Compile the explicit three-language message catalog. Standard library only."""
from pathlib import Path
import json
root=Path(__file__).resolve().parents[1]
data={}
for line in (root/'localization/messages.tsv').read_text(encoding='utf-8').splitlines():
    if not line: continue
    parts=line.split('\t')
    if len(parts)!=3: raise ValueError('Every message needs three explicit translations: '+line)
    if parts[0] in data: raise ValueError('Duplicate translation: '+parts[0])
    data[parts[0]]=parts[1:]
(root/'messages-data.js').write_text('/* Explicit Simplified Chinese, Traditional Chinese and English translations. */\n(function(root){const data='+json.dumps(data,ensure_ascii=False,separators=(',',':'))+';if(typeof module!=="undefined"&&module.exports)module.exports=data;root.I18nMessages=data;})(typeof globalThis!=="undefined"?globalThis:this);\n',encoding='utf-8')
