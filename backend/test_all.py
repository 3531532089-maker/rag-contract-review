"""全功能测试脚本 - 上传、审查、问答、删除"""
import requests, sys, os, json

BASE = "http://localhost:8000"
PASSED = 0
FAILED = 0

def check(name, ok, detail=""):
    global PASSED, FAILED
    if ok:
        print(f"  PASS  {name} {detail}")
        PASSED += 1
    else:
        print(f"  FAIL  {name} {detail}")
        FAILED += 1

# 1. Public endpoints
print("=== Public endpoints ===")
r = requests.get(f"{BASE}/health")
check("Health", r.status_code == 200 and r.json()["status"] == "healthy")
r = requests.get(f"{BASE}/")
check("Root", r.status_code == 200)

# 2. Auth blocking
print("\n=== Auth blocking ===")
r1 = requests.post(f"{BASE}/api/chat/", json={"contract_id":"x","question":"x"})
check("No-token chat blocked", r1.status_code == 401, f"got {r1.status_code}")
r2 = requests.post(f"{BASE}/api/review/x")
check("No-token review blocked", r2.status_code == 401, f"got {r2.status_code}")
r3 = requests.delete(f"{BASE}/api/upload/contracts/x")
check("No-token delete blocked", r3.status_code == 401, f"got {r3.status_code}")

# 3. Login
print("\n=== Login ===")
r = requests.post(f"{BASE}/api/auth/login", json={"password": "2006528Qq."})
check("Correct password", r.status_code == 200 and "token" in r.json())
TOKEN = r.json()["token"]
r = requests.post(f"{BASE}/api/auth/login", json={"password": "wrong"})
check("Wrong password", r.status_code == 401)
AUTH = {"Authorization": f"Bearer {TOKEN}"}

# 4. Upload (use local copy without Chinese path)
print("\n=== Upload ===")
pdf = "test_contract.pdf"
if not os.path.exists(pdf):
    print("  SKIP: test_contract.pdf not found")
    sys.exit(1)

with open(pdf, "rb") as f:
    r = requests.post(f"{BASE}/api/upload/contract", files={"file": f}, headers=AUTH)
if r.status_code == 200:
    check("Upload", True, r.json().get("message", "")[:50])
    cid = r.json()["contract_id"]
elif r.status_code == 409:
    # Already exists - extract ID from error message
    cid = None
    check("Upload (duplicate)", True, "file already in DB, skipping")
else:
    cid = None
    detail = r.json().get("detail", str(r.text)[:100])
    check("Upload", False, f"status={r.status_code} detail={detail}")
    print(f"  Full response: {r.text[:300]}")

# If we didn't get a fresh cid from upload, list contracts and use the first one
if cid is None:
    r = requests.get(f"{BASE}/api/upload/contracts")
    if r.ok and r.json()["total"] > 0:
        cid = r.json()["contracts"][0]["id"]
        print(f"  Using existing contract: {cid[:8]}...")
    else:
        print("  No contracts available, skipping remaining tests")
        sys.exit(1)

# 5. Review
print("\n=== Review ===")
r = requests.post(f"{BASE}/api/review/{cid}", headers=AUTH, timeout=130)
if r.status_code == 200:
    d = r.json()
    check("Review success", True,
          f"type={d.get('contract_type')} score={d.get('risk_score')} risks={len(d.get('risks',[]))}")
    check("Type correct", d.get("contract_type") == "劳动合同")
    check("Score range", 0 <= d.get("risk_score", 0) <= 100)
    check("Risks found", len(d.get("risks", [])) >= 5,
          f"got {len(d.get('risks', []))} risks")
    check("Summary present", len(d.get("summary", "")) > 20)
else:
    detail = r.json().get("detail", str(r.text)[:200])
    check("Review success", False, f"status={r.status_code} detail={detail}")

# GET review
r = requests.get(f"{BASE}/api/review/{cid}")
check("View review", r.status_code == 200 and r.json().get("risk_score") is not None)

# 6. Chat
print("\n=== Chat ===")
r = requests.post(f"{BASE}/api/chat/", json={
    "contract_id": cid, "question": "试用期有什么法律风险？"
}, headers=AUTH, timeout=60)
if r.status_code == 200:
    d2 = r.json()
    check("Chat success", True, f"answer length: {len(d2.get('answer', ''))}")
    check("Has sources", len(d2.get("sources", [])) > 0)
else:
    detail = r.json().get("detail", r.text[:200])
    check("Chat success", False, f"status={r.status_code} detail={detail}")

# 7. List & detail
print("\n=== Query ===")
r = requests.get(f"{BASE}/api/upload/contracts")
check("List contracts", r.status_code == 200 and r.json()["total"] >= 1)
r = requests.get(f"{BASE}/api/upload/contracts/{cid}")
check("Contract detail", r.status_code == 200 and len(r.json().get("content", "")) > 100)

# 8. Delete
print("\n=== Delete ===")
r = requests.delete(f"{BASE}/api/upload/contracts/{cid}", headers=AUTH)
check("Delete contract", r.status_code == 200)

# Summary
print(f"\n{'='*40}")
print(f"PASS: {PASSED}  FAIL: {FAILED}")
if FAILED == 0:
    print("All tests passed!")
else:
    print("Some tests failed")
