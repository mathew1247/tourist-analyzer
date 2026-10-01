import urllib.request
import json
import sqlite3
from backend.database.db import SQLITE_DB_PATH

BASE_URL = 'http://127.0.0.1:5000'

def make_request(url, method='GET', data=None):
    body = json.dumps(data).encode('utf-8') if data is not None else None
    headers = {'Content-Type': 'application/json'} if data is not None else {}
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode())


def run_crud_checks():
    print("=" * 60)
    print(" STARTING DATABASE CRUD OPERATIONS VERIFICATION")
    print("=" * 60)

    # ---------------------------------------------------------
    # 1. SQL DATABASE CRUD: /api/tourism (Monthly Analytics)
    # ---------------------------------------------------------
    print("\n--- [1] SQL TOURISM CRUD (monthly_analytics) ---")

    # A) CREATE
    create_payload = {
        'month': 'September',
        'year': 2026,
        'visitors': 4500,
        'revenue': 675000,
        'category_name': 'Adventure'
    }
    status, res = make_request(f"{BASE_URL}/api/tourism", 'POST', create_payload)
    print(f" [CREATE] POST /api/tourism -> HTTP {status}")
    assert status == 201, f"Expected 201, got {status}"
    new_id = res['data']['id']
    print(f"          Record Created Successfully with ID: {new_id}")

    # Verify directly in SQLite file
    conn = sqlite3.connect(SQLITE_DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id, month, year, visitors, revenue FROM monthly_analytics WHERE id = ?", (new_id,))
    db_row = cur.fetchone()
    print(f"          Direct SQLite DB verification: {db_row}")
    assert db_row[0] == new_id
    assert db_row[3] == 4500
    conn.close()

    # B) READ ONE
    status, res = make_request(f"{BASE_URL}/api/tourism/{new_id}", 'GET')
    print(f" [READ ONE] GET /api/tourism/{new_id} -> HTTP {status}")
    assert status == 200
    rec = res['data']
    print(f"            Month: {rec['month']}, Year: {rec['year']}, Visitors: {rec['visitors']}, Revenue: {rec['revenue']}")
    assert rec['visitors'] == 4500
    assert rec['category'] == 'Adventure'

    # C) READ ALL & FILTER
    status, res = make_request(f"{BASE_URL}/api/tourism?year=2026", 'GET')
    print(f" [READ ALL] GET /api/tourism?year=2026 -> HTTP {status}")
    assert status == 200
    matching = [r for r in res['data'] if r['id'] == new_id]
    assert len(matching) == 1
    print(f"            Successfully queried list, found created record #{new_id}")

    # D) UPDATE
    update_payload = {
        'month': 'September',
        'year': 2026,
        'visitors': 5200,
        'revenue': 810000,
        'category_name': 'Hill Stations'
    }
    status, res = make_request(f"{BASE_URL}/api/tourism/{new_id}", 'PUT', update_payload)
    print(f" [UPDATE] PUT /api/tourism/{new_id} -> HTTP {status}")
    assert status == 200
    assert res['data']['visitors'] == 5200

    # Verify UPDATE persisted in DB
    status, res = make_request(f"{BASE_URL}/api/tourism/{new_id}", 'GET')
    assert res['data']['visitors'] == 5200
    assert res['data']['category'] == 'Hill Stations'
    print(f"          Verified Update in DB: Visitors updated to {res['data']['visitors']}, Category to {res['data']['category']}")

    # E) DELETE
    status, res = make_request(f"{BASE_URL}/api/tourism/{new_id}", 'DELETE')
    print(f" [DELETE] DELETE /api/tourism/{new_id} -> HTTP {status}")
    assert status == 200

    # F) VERIFY DELETION
    status, res = make_request(f"{BASE_URL}/api/tourism/{new_id}", 'GET')
    print(f" [VERIFY DELETION] GET /api/tourism/{new_id} -> HTTP {status} (Expected 404)")
    assert status == 404

    # ---------------------------------------------------------
    # 2. CLOUD FIRESTORE CRUD: /api/tourists (tourist_data)
    # ---------------------------------------------------------
    print("\n--- [2] CLOUD FIRESTORE CRUD (tourist_data) ---")

    # A) CREATE
    fs_payload = {
        'location': 'Kodaikanal Lake',
        'district': 'Dindigul',
        'state': 'Tamil Nadu',
        'visit_date': '2026-09-15',
        'visitor_count': 120,
        'visitor_type': 'Domestic',
        'revenue': 18000
    }
    status, res = make_request(f"{BASE_URL}/api/tourists", 'POST', fs_payload)
    print(f" [FIRESTORE CREATE] POST /api/tourists -> HTTP {status}")
    assert status == 201
    doc_id = res['id']
    print(f"                    Created Firestore Doc ID: {doc_id}")

    # B) READ ONE
    status, res = make_request(f"{BASE_URL}/api/tourists/{doc_id}", 'GET')
    print(f" [FIRESTORE READ ONE] GET /api/tourists/{doc_id} -> HTTP {status}")
    assert status == 200
    assert res['location'] == 'Kodaikanal Lake'
    assert res['revenue'] == 18000

    # C) READ ALL
    status, res = make_request(f"{BASE_URL}/api/tourists", 'GET')
    print(f" [FIRESTORE READ ALL] GET /api/tourists -> HTTP {status}")
    assert status == 200
    doc_exists = any(d['id'] == doc_id for d in res)
    assert doc_exists
    print(f"                     Found document in list of {len(res)} items")

    # D) DELETE
    status, res = make_request(f"{BASE_URL}/api/tourists/{doc_id}", 'DELETE')
    print(f" [FIRESTORE DELETE] DELETE /api/tourists/{doc_id} -> HTTP {status}")
    assert status == 200

    # E) VERIFY DELETION
    status, res = make_request(f"{BASE_URL}/api/tourists/{doc_id}", 'GET')
    print(f" [FIRESTORE VERIFY DELETION] GET /api/tourists/{doc_id} -> HTTP {status} (Expected 404)")
    assert status == 404

    # ---------------------------------------------------------
    # 3. USER PROFILE CRUD: /api/profile (users table)
    # ---------------------------------------------------------
    print("\n--- [3] USER PROFILE CRUD (users table) ---")
    status, res = make_request(f"{BASE_URL}/api/profile", 'GET')
    print(f" [READ PROFILE] GET /api/profile -> HTTP {status}")
    assert status == 200
    print(f"                Active user: {res['data']['fullName']} ({res['data']['email']}), Phone: {res['data']['phone']}")

    print("\n" + "=" * 60)
    print(" ALL CRUD OPERATIONS VERIFIED SUCCESSFULLY: 100% OPERATIONAL")
    print("=" * 60)

if __name__ == '__main__':
    run_crud_checks()
