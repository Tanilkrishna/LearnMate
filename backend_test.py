import requests
import sys
import json
from datetime import datetime

class LearnMateAPITester:
    def __init__(self, base_url="https://studybuddy-319.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.session_token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.session = requests.Session()

    def run_test(self, name, method, endpoint, expected_status, data=None, cookies=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = self.session.get(url, headers=headers, cookies=cookies)
            elif method == 'POST':
                response = self.session.post(url, json=data, headers=headers, cookies=cookies)
            elif method == 'PUT':
                response = self.session.put(url, json=data, headers=headers, cookies=cookies)

            print(f"   Status: {response.status_code}")
            success = response.status_code == expected_status
            
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    print(f"   Response: {json.dumps(response_data, indent=2)[:200]}...")
                    return True, response_data
                except:
                    return True, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Error: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_topics_endpoint(self):
        """Test topics endpoint (public)"""
        success, response = self.run_test(
            "Get Topics",
            "GET",
            "topics",
            200
        )
        if success and 'topics' in response:
            topics = response['topics']
            print(f"   Found {len(topics)} topics")
            expected_topics = ['Mathematics', 'Python Programming', 'Biology', 'English', 'History', 'Physics', 'Chemistry', 'Art & Design']
            for topic in topics:
                if topic['name'] in expected_topics:
                    print(f"   ✓ Topic found: {topic['name']}")
        return success

    def test_auth_me_without_session(self):
        """Test /auth/me without session (should fail)"""
        success, response = self.run_test(
            "Get Current User (No Session)",
            "GET",
            "auth/me",
            401
        )
        return success

    def test_protected_endpoints_without_auth(self):
        """Test protected endpoints without authentication"""
        endpoints = [
            ("chat", "POST", {"message": "test", "topic": "Math"}),
            ("progress", "GET", None),
            ("quiz/generate", "POST", {"topic": "Math", "num_questions": 5}),
            ("chat/history", "GET", None)
        ]
        
        all_passed = True
        for endpoint, method, data in endpoints:
            success, _ = self.run_test(
                f"Protected {endpoint} (No Auth)",
                method,
                endpoint,
                401,
                data
            )
            if not success:
                all_passed = False
        
        return all_passed

    def test_invalid_session_processing(self):
        """Test session processing with invalid session_id"""
        success, response = self.run_test(
            "Process Invalid Session",
            "POST",
            "auth/session",
            400,
            {"session_id": "invalid_session_id_12345"}
        )
        return success

    def test_logout_without_session(self):
        """Test logout without session"""
        success, response = self.run_test(
            "Logout Without Session",
            "POST",
            "auth/logout",
            200
        )
        return success

    def test_summarize_without_auth(self):
        """Test summarize endpoint without auth"""
        success, response = self.run_test(
            "Summarize Without Auth",
            "POST",
            "summarize",
            401,
            {"content": "This is test content to summarize"}
        )
        return success

    def test_quiz_save_without_auth(self):
        """Test quiz save without auth"""
        success, response = self.run_test(
            "Save Quiz Without Auth",
            "POST",
            "quiz/save",
            401,
            {
                "topic": "Math",
                "score": 3,
                "total": 5,
                "questions": []
            }
        )
        return success

    def test_update_interests_without_auth(self):
        """Test update interests without auth"""
        success, response = self.run_test(
            "Update Interests Without Auth",
            "PUT",
            "auth/interests",
            401,
            {"interests": ["Math", "Science"]}
        )
        return success

def main():
    print("🚀 Starting LearnMate API Tests")
    print("=" * 50)
    
    # Setup
    tester = LearnMateAPITester()
    
    # Test public endpoints
    print("\n📋 Testing Public Endpoints")
    print("-" * 30)
    tester.test_topics_endpoint()
    
    # Test authentication endpoints
    print("\n🔐 Testing Authentication")
    print("-" * 30)
    tester.test_auth_me_without_session()
    tester.test_invalid_session_processing()
    tester.test_logout_without_session()
    
    # Test protected endpoints without auth
    print("\n🛡️ Testing Protected Endpoints (No Auth)")
    print("-" * 40)
    tester.test_protected_endpoints_without_auth()
    tester.test_summarize_without_auth()
    tester.test_quiz_save_without_auth()
    tester.test_update_interests_without_auth()

    # Print results
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {tester.tests_passed}/{tester.tests_run} passed")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All tests passed!")
        return 0
    else:
        print(f"⚠️  {tester.tests_run - tester.tests_passed} tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())