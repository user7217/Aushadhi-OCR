import csv, requests

def precision_at_k(golds, preds, k=3):
    correct = 0
    for gold, topk in zip(golds, preds):
        names = [m["name"].lower() for m in topk[:k]]
        correct += int(gold.lower() in names)
    return correct / len(golds) if golds else 0.0

rows = [r for r in csv.DictReader(open("backend/data/val_set.csv")) if not r["image_path"].startswith("#")]
golds, preds = [], []

for r in rows:
    with open(r["image_path"], "rb") as f:
        files = {"file": f}
        data = {"top_k": "5", "threshold": "85", "ocr_backend": "roboflow"}
        js = requests.post("http://localhost:8000/infer", data=data, files=files, timeout=60).json()
        preds.append(js["top_k"])
        golds.append(r["gold_name"])

for k in [1,3,5]:
    print(f"P@{k} = {precision_at_k(golds, preds, k):.3f}")
