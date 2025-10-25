import requests
import json

BASE_URL = 'http://127.0.0.1:8000/api'

def print_response(title, response):
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")
    print(f"Status Code: {response.status_code}")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except:
        print(f"Response: {response.text}")

def get_first_teacher_id(token):
    """Get the first available teacher ID"""
    url = f"{BASE_URL}/courses/teachers/search/"
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        teachers = data.get('results', data) if isinstance(data, dict) else data
        if teachers and len(teachers) > 0:
            return teachers[0]['id']
    return None

def test_session_creation(token):
    """Test creating a session with dynamic teacher ID"""
    print("\n🧪 Testing Session Creation...")
    
    # First, get an available teacher
    teacher_id = get_first_teacher_id(token)
    
    if not teacher_id:
        print("❌ No teachers available. Please run create_test_data.py first!")
        return
    
    print(f"✓ Found teacher ID: {teacher_id}")
    
    url = f"{BASE_URL}/courses/sessions/"
    headers = {"Authorization": f"Bearer {token}"}
    
    from datetime import date, timedelta
    tomorrow = (date.today() + timedelta(days=2)).isoformat()
    
    data = {
        "teacher": teacher_id,  # Use dynamically fetched ID
        "title": "Test Session",
        "description": "Testing session booking",
        "session_type": "ONLINE",
        "scheduled_date": tomorrow,
        "start_time": "14:00:00",
        "end_time": "15:00:00",
        "duration_minutes": 60
    }
    
    response = requests.post(url, json=data, headers=headers)
    print_response("Session Creation", response)

def test_registration():
    """Test user registration with email verification"""
    print("\n🧪 Testing Registration...")
    
    url = f"{BASE_URL}/auth/register/"
    data = {
        "email": "newstudent@test.com",
        "password": "SecurePass123!@#",
        "password_confirm": "SecurePass123!@#",
        "first_name": "Test",
        "last_name": "Student",
        "role": "STUDENT",
        "phone_number": "+919999999999"
    }
    
    response = requests.post(url, json=data)
    print_response("Registration Response", response)

def test_login(email, password):
    """Test user login"""
    print("\n🧪 Testing Login...")
    
    url = f"{BASE_URL}/auth/login/"
    data = {
        "email": email,
        "password": password
    }
    
    response = requests.post(url, json=data)
    print_response("Login Response", response)
    
    if response.status_code == 200:
        return response.json()['tokens']['access']
    return None

def test_student_dashboard(token):
    """Test student dashboard"""
    print("\n🧪 Testing Student Dashboard...")
    
    url = f"{BASE_URL}/courses/student/dashboard/"
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(url, headers=headers)
    print_response("Student Dashboard", response)

def test_teacher_search(token):
    """Test teacher search with filters"""
    print("\n🧪 Testing Teacher Search...")
    
    url = f"{BASE_URL}/courses/teachers/search/"
    headers = {"Authorization": f"Bearer {token}"}
    params = {
        "subject": "Mathematics",
        "min_rating": "4.0"
    }
    
    response = requests.get(url, headers=headers, params=params)
    print_response("Teacher Search Results", response)

def test_resources(token):
    """Test resource listing"""
    print("\n🧪 Testing Resources...")
    
    url = f"{BASE_URL}/courses/resources/"
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(url, headers=headers)
    print_response("Resources List", response)

def run_all_tests():
    print("\n" + "="*60)
    print("🚀 STARTING API TESTS")
    print("="*60)
    
    # Test 1: Registration (optional - comment out if user exists)
    # test_registration()
    
    # Test 2: Login with existing student
    print("\nℹ️  Using student1@test.com for testing")
    token = test_login("student1@test.com", "Test123!@#")
    
    if not token:
        print("\n❌ Login failed. Make sure you've run create_test_data.py")
        return
    
    # Test 3: Student Dashboard
    test_student_dashboard(token)
    
    # Test 4: Teacher Search
    test_teacher_search(token)
    
    # Test 5: Resources
    test_resources(token)
    
    # Test 6: Session Creation (now with dynamic teacher ID)
    test_session_creation(token)
    
    print("\n" + "="*60)
    print("✅ ALL TESTS COMPLETED")
    print("="*60)

if __name__ == '__main__':
    run_all_tests()
