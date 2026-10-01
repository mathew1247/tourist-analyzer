import os
import json
import unittest
from backend.app import app
from backend.database.db import init_db


class BackendIntegrationTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Initialize DB and seeds
        init_db()
        app.config['TESTING'] = True
        cls.client = app.test_client()

        # Ensure default test user exists idempotently
        from backend.database.db import get_db_connection
        from werkzeug.security import generate_password_hash
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("UPDATE users SET email = %s, username = %s, password = %s WHERE id = 1", 
                       ('admin@tourism.com', 'Admin', generate_password_hash('Admin@123')))
        conn.commit()
        cursor.close()
        conn.close()

    def test_01_health_check(self):
        res = self.client.get('/api/health')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertIn('Tourism Analytics API is running', data['message'])
        print("[PASS] Health check endpoint")

    def test_02_auth_login_success(self):
        res = self.client.post('/api/login', json={
            'email': 'admin@tourism.com',
            'password': 'Admin@123'
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertEqual(data['user']['role'], 'admin')
        print("[PASS] Auth login success")

    def test_03_auth_login_invalid(self):
        res = self.client.post('/api/login', json={
            'email': 'admin@tourism.com',
            'password': 'WrongPassword999'
        })
        self.assertEqual(res.status_code, 401)
        data = res.get_json()
        self.assertFalse(data['success'])
        print("[PASS] Auth login invalid rejection")

    def test_04_auth_login_missing(self):
        res = self.client.post('/api/login', json={})
        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertFalse(data['success'])
        print("[PASS] Auth login missing fields rejection")

    def test_05_tourism_crud(self):
        # 1. CREATE
        new_record = {
            'month': 'April',
            'year': 2025,
            'visitors': 5430,
            'revenue': 890000,
            'category_id': 2
        }
        res = self.client.post('/api/tourism', json=new_record)
        self.assertEqual(res.status_code, 201)
        create_data = res.get_json()
        self.assertTrue(create_data['success'])
        created_id = create_data['data']['id']
        self.assertIsNotNone(created_id)
        print(f"[PASS] Tourism CREATE (id={created_id})")

        # 2. GET ALL
        res = self.client.get('/api/tourism?year=2025')
        self.assertEqual(res.status_code, 200)
        get_all_data = res.get_json()
        self.assertTrue(get_all_data['success'])
        self.assertGreater(len(get_all_data['data']), 0)
        print(f"[PASS] Tourism GET ALL (count={len(get_all_data['data'])})")

        # 3. GET ONE
        res = self.client.get(f'/api/tourism/{created_id}')
        self.assertEqual(res.status_code, 200)
        one_data = res.get_json()
        self.assertTrue(one_data['success'])
        self.assertEqual(one_data['data']['visitors'], 5430)
        print(f"[PASS] Tourism GET ONE")

        # 4. UPDATE
        update_payload = {
            'visitors': 5500,
            'revenue': 910000
        }
        res = self.client.put(f'/api/tourism/{created_id}', json=update_payload)
        self.assertEqual(res.status_code, 200)
        up_data = res.get_json()
        self.assertTrue(up_data['success'])
        self.assertEqual(up_data['data']['visitors'], 5500)
        print(f"[PASS] Tourism UPDATE")

        # 5. DELETE
        res = self.client.delete(f'/api/tourism/{created_id}')
        self.assertEqual(res.status_code, 200)
        del_data = res.get_json()
        self.assertTrue(del_data['success'])
        print(f"[PASS] Tourism DELETE")

        # Verify 404 after delete
        res_404 = self.client.get(f'/api/tourism/{created_id}')
        self.assertEqual(res_404.status_code, 404)
        print(f"[PASS] Tourism 404 verification")

    def test_06_tourism_validation_errors(self):
        # Negative visitors
        res = self.client.post('/api/tourism', json={
            'month': 'May',
            'year': 2025,
            'visitors': -50,
            'revenue': 50000
        })
        self.assertEqual(res.status_code, 400)

        # Invalid month
        res = self.client.post('/api/tourism', json={
            'month': 'InvalidMonthName',
            'year': 2025,
            'visitors': 1000,
            'revenue': 50000
        })
        self.assertEqual(res.status_code, 400)
        print("[PASS] Input validation error handling")

    def test_07_dashboard_api(self):
        res = self.client.get('/api/dashboard?year=2025')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertIn('summary', data)
        self.assertIn('total_visitors', data['summary'])
        self.assertIn('total_revenue', data['summary'])
        self.assertIn('monthly_visitors', data)
        self.assertIn('monthly_revenue', data)
        self.assertIn('peak_month', data)
        self.assertIn('lowest_month', data)
        print(f"[PASS] Dashboard API: Total Visitors={data['summary']['total_visitors']:,}, Total Revenue={data['summary']['total_revenue']:,}")

    def test_08_analytics_api(self):
        res = self.client.get('/api/analytics?year=2025')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertIn('visitor_trend', data)
        self.assertIn('revenue_trend', data)
        self.assertIn('growth', data)
        self.assertIn('insights', data)
        self.assertGreater(len(data['insights']), 0)
        print(f"[PASS] Analytics API: Insights count={len(data['insights'])}")

    def test_09_prediction_api(self):
        for p in ['1', '3', '6', 'next_month', 'next_3_months']:
            res = self.client.get(f'/api/prediction?period={p}')
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            self.assertTrue(data['success'])
            self.assertIn('predicted_visitors', data['prediction'])
            self.assertIn('predicted_revenue', data['prediction'])
        print("[PASS] Prediction API for periods 1, 3, 6")

    def test_10_reports_api(self):
        for r_type in ['monthly', 'yearly', 'revenue', 'visitor']:
            res = self.client.get(f'/api/reports?type={r_type}&month=January&year=2025')
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            self.assertTrue(data['success'])
            self.assertIn('report', data)
            self.assertIn('total_visitors', data['report'])
        print("[PASS] Reports API for all 4 report types")

    def test_11_profile_api(self):
        # GET
        res = self.client.get('/api/profile')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])

        # PUT
        res_put = self.client.put('/api/profile', json={
            'username': 'Admin Updated',
            'email': 'admin-updated@tourism.com'
        })
        self.assertEqual(res_put.status_code, 200)
        put_data = res_put.get_json()
        self.assertTrue(put_data['success'])
        self.assertEqual(put_data['data']['username'], 'Admin Updated')
        print("[PASS] Profile GET and PUT")

    def test_12_firestore_tourists_get(self):
        res = self.client.get('/api/tourists')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)
        # Check first document has required fields including id
        first_doc = data[0]
        self.assertIn('id', first_doc)
        self.assertIn('location', first_doc)
        self.assertIn('visitor_count', first_doc)
        self.assertIn('revenue', first_doc)
        print(f"[PASS] Firestore GET /api/tourists: Returned {len(data)} documents. First ID={first_doc['id']}")

    def test_13_firestore_tourists_post_and_validation(self):
        # Validation failure: missing location
        fail_res = self.client.post('/api/tourists', json={
            'visitor_count': 100,
            'revenue': 20000,
            'visit_date': '2026-10-01'
        })
        self.assertEqual(fail_res.status_code, 400)
        self.assertFalse(fail_res.get_json()['success'])

        # Validation failure: negative visitor count
        fail_res2 = self.client.post('/api/tourists', json={
            'location': 'Test Loc',
            'visitor_count': -10,
            'revenue': 20000,
            'visit_date': '2026-10-01'
        })
        self.assertEqual(fail_res2.status_code, 400)
        self.assertFalse(fail_res2.get_json()['success'])

        # Successful POST
        post_res = self.client.post('/api/tourists', json={
            'location': 'Munnar',
            'district': 'Idukki',
            'state': 'Kerala',
            'visit_date': '2026-10-01',
            'visitor_count': 2400,
            'visitor_type': 'Domestic',
            'revenue': 720000
        })
        self.assertEqual(post_res.status_code, 201)
        res_data = post_res.get_json()
        self.assertTrue(res_data['success'])
        self.assertIn('id', res_data)
        doc_id = res_data['id']
        print(f"[PASS] Firestore POST /api/tourists: Created document with ID={doc_id}")

        # Verify GET single
        get_res = self.client.get(f'/api/tourists/{doc_id}')
        self.assertEqual(get_res.status_code, 200)
        single_doc = get_res.get_json()
        self.assertEqual(single_doc['location'], 'Munnar')
        self.assertEqual(single_doc['visitor_count'], 2400)
        print(f"[PASS] Firestore GET /api/tourists/{doc_id} verified")


if __name__ == '__main__':
    unittest.main()

