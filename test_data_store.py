import urllib.request
import json

def api_post(endpoint, payload):
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        f'http://127.0.0.1:5000{endpoint}',
        data=data,
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    with urllib.request.urlopen(req) as resp:
        return resp.status, json.loads(resp.read().decode('utf-8'))

def api_get(endpoint):
    req = urllib.request.Request(f'http://127.0.0.1:5000{endpoint}')
    with urllib.request.urlopen(req) as resp:
        return resp.status, json.loads(resp.read().decode('utf-8'))

print("=================================================================")
print(" 1. ADDING SAMPLE DATA TO CLOUD FIRESTORE ('tourist_data')")
print("=================================================================")

firestore_test_records = [
    {
        "location": "Goa Calangute Beach",
        "district": "North Goa",
        "state": "Goa",
        "visit_date": "2026-10-02",
        "visitor_count": 5420,
        "visitor_type": "Domestic",
        "revenue": 1250000
    },
    {
        "location": "Manali Solang Valley",
        "district": "Kullu",
        "state": "Himachal Pradesh",
        "visit_date": "2026-10-03",
        "visitor_count": 3890,
        "visitor_type": "Domestic",
        "revenue": 980000
    }
]

created_doc_ids = []
for item in firestore_test_records:
    status, res = api_post('/api/tourists', item)
    doc_id = res.get('id')
    created_doc_ids.append(doc_id)
    print(f"[OK] Stored in Firestore -> HTTP {status} | Doc ID: {doc_id} | Location: {item['location']}")

print("\n=================================================================")
print(" 2. RETRIEVING ALL DOCUMENTS DIRECTLY FROM FIRESTORE")
print("=================================================================")

status, all_tourists = api_get('/api/tourists')
print(f"Total documents currently in Firestore 'tourist_data': {len(all_tourists)}\n")
for idx, doc in enumerate(all_tourists, start=1):
    print(f"  {idx}. ID: {doc['id']}")
    print(f"     Location:     {doc.get('location')} ({doc.get('district')}, {doc.get('state')})")
    print(f"     Visit Date:   {doc.get('visit_date')}")
    print(f"     Visitors:     {doc.get('visitor_count'):,}")
    print(f"     Revenue:      Rs. {doc.get('revenue'):,}")
    print(f"     Visitor Type: {doc.get('visitor_type')}")
    print("-" * 50)

print("\n=================================================================")
print(" 3. ADDING RECORD TO MONTHLY ANALYTICS DATABASE (SQL / CRUD)")
print("=================================================================")

db_sample = {
    "month": "October",
    "year": 2026,
    "visitors": 6850,
    "revenue": 1420000,
    "category": "Hill Stations"
}

status, db_res = api_post('/api/tourism', db_sample)
new_db_id = db_res['data']['id']
print(f"[OK] Stored in database table 'monthly_analytics' -> HTTP {status} | Record ID: {new_db_id}")

print("\n=================================================================")
print(" 4. VERIFYING RETRIEVAL FROM DATABASE VIA GET /api/tourism/<id>")
print("=================================================================")

status, fetched = api_get(f'/api/tourism/{new_db_id}')
rec = fetched['data']
print(f"Record successfully retrieved from database:")
print(f"  ID:       {rec['id']}")
print(f"  Month:    {rec['month']} {rec['year']}")
print(f"  Visitors: {rec['visitors']:,}")
print(f"  Revenue:  Rs. {rec['revenue']:,.2f}")
print(f"  Category: {rec['category']}")
print(f"  Created:  {rec['created_at']}")
print("=================================================================")
