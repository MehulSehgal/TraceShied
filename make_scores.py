import json
from detoxify import Detoxify

m = Detoxify("original")
out = {}
for f in ["data/hero_conversation.json", "data/benign_conversation.json"]:
    for x in json.load(open(f, encoding="utf-8")):
        out[x["text"]] = round(float(m.predict(x["text"])["toxicity"]), 3)

json.dump(out, open("detoxify_scores.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(len(out), "scores written")