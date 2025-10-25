import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from accounts.models import User, StudentProfile, TeacherProfile
from courses.models import Course, Session, Resource, Enrollment
from datetime import date, time, timedelta

def create_test_data():
    print("🚀 Creating test data...\n")
    
    # Clear existing test data (optional - comment out if you want to keep existing data)
    # User.objects.filter(email__contains='test.com').delete()
    
    # Create Students
    print("Creating students...")
    try:
        student1 = User.objects.create_user(
            email='student1@test.com',
            password='Test123!@#',
            first_name='John',
            last_name='Doe',
            role='STUDENT',
            is_active=True,
            is_email_verified=True,
            phone_number='+919876543210',
            city='Mumbai'
        )
        StudentProfile.objects.get_or_create(
            user=student1,
            defaults={
                'grade_level': '12th Grade',
                'subjects_interested': ['Mathematics', 'Physics'],
                'learning_goals': 'Prepare for JEE'
            }
        )
        print(f"  ✓ Created student: {student1.email} (ID: {student1.id})")
    except Exception as e:
        print(f"  ⚠ Student1 already exists or error: {e}")
        student1 = User.objects.get(email='student1@test.com')
    
    try:
        student2 = User.objects.create_user(
            email='student2@test.com',
            password='Test123!@#',
            first_name='Alice',
            last_name='Smith',
            role='STUDENT',
            is_active=True,
            is_email_verified=True,
            city='Delhi'
        )
        StudentProfile.objects.get_or_create(user=student2)
        print(f"  ✓ Created student: {student2.email} (ID: {student2.id})")
    except Exception as e:
        print(f"  ⚠ Student2 already exists or error: {e}")
        student2 = User.objects.get(email='student2@test.com')
    
    # Create Teachers
    print("\nCreating teachers...")
    try:
        teacher1 = User.objects.create_user(
            email='teacher1@test.com',
            password='Test123!@#',
            first_name='Dr. Rajesh',
            last_name='Kumar',
            role='TEACHER',
            is_active=True,
            is_email_verified=True,
            phone_number='+919876543211',
            city='Mumbai',
            bio='Experienced mathematics teacher with 10 years of expertise'
        )
        TeacherProfile.objects.get_or_create(
            user=teacher1,
            defaults={
                'highest_degree': 'PhD in Mathematics',
                'university': 'IIT Bombay',
                'specialization': 'Advanced Mathematics',
                'years_of_experience': 10,
                'subjects_taught': ['Mathematics', 'Physics', 'Statistics'],
                'teaching_languages': ['English', 'Hindi'],
                'hourly_rate': 1500.00,
                'is_verified': True,
                'available_for_online': True,
                'available_for_offline': True,
                'average_rating': 4.8,
                'total_reviews': 45,
                'total_sessions': 120
            }
        )
        print(f"  ✓ Created teacher: {teacher1.email} (ID: {teacher1.id})")
    except Exception as e:
        print(f"  ⚠ Teacher1 already exists or error: {e}")
        teacher1 = User.objects.get(email='teacher1@test.com')
    
    try:
        teacher2 = User.objects.create_user(
            email='teacher2@test.com',
            password='Test123!@#',
            first_name='Prof. Sarah',
            last_name='Johnson',
            role='TEACHER',
            is_active=True,
            is_email_verified=True,
            city='Bangalore',
            bio='Full stack developer and educator'
        )
        TeacherProfile.objects.get_or_create(
            user=teacher2,
            defaults={
                'highest_degree': 'Masters in Computer Science',
                'university': 'Stanford University',
                'years_of_experience': 7,
                'subjects_taught': ['Programming', 'Web Development', 'Data Science'],
                'teaching_languages': ['English'],
                'hourly_rate': 2000.00,
                'is_verified': True,
                'available_for_online': True,
                'average_rating': 4.9,
                'total_reviews': 30,
                'total_sessions': 85
            }
        )
        print(f"  ✓ Created teacher: {teacher2.email} (ID: {teacher2.id})")
    except Exception as e:
        print(f"  ⚠ Teacher2 already exists or error: {e}")
        teacher2 = User.objects.get(email='teacher2@test.com')
    
    # Create Courses
    print("\nCreating courses...")
    course1, created = Course.objects.get_or_create(
        title='Advanced Mathematics for JEE',
        teacher=teacher1,
        defaults={
            'description': 'Complete JEE Mathematics preparation with problem-solving techniques',
            'category': 'Mathematics',
            'level': 'ADVANCED',
            'price': 5000.00,
            'duration_weeks': 12,
            'is_active': True
        }
    )
    if created:
        print(f"  ✓ Created course: {course1.title} (ID: {course1.id})")
    else:
        print(f"  ⚠ Course already exists: {course1.title} (ID: {course1.id})")
    
    course2, created = Course.objects.get_or_create(
        title='Full Stack Web Development',
        teacher=teacher2,
        defaults={
            'description': 'Learn Django and Next.js from scratch to deployment',
            'category': 'Programming',
            'level': 'INTERMEDIATE',
            'price': 8000.00,
            'duration_weeks': 16,
            'is_active': True
        }
    )
    if created:
        print(f"  ✓ Created course: {course2.title} (ID: {course2.id})")
    else:
        print(f"  ⚠ Course already exists: {course2.title} (ID: {course2.id})")
    
    # Create Enrollments
    print("\nCreating enrollments...")
    enrollment1, created = Enrollment.objects.get_or_create(
        student=student1,
        course=course1,
        defaults={'progress': 35.50}
    )
    if created:
        print(f"  ✓ Enrolled {student1.email} in {course1.title}")
    else:
        print(f"  ⚠ Enrollment already exists")
    
    enrollment2, created = Enrollment.objects.get_or_create(
        student=student2,
        course=course2,
        defaults={'progress': 15.00}
    )
    if created:
        print(f"  ✓ Enrolled {student2.email} in {course2.title}")
    else:
        print(f"  ⚠ Enrollment already exists")
    
    # Create Sessions
    print("\nCreating sessions...")
    tomorrow = date.today() + timedelta(days=1)
    next_week = date.today() + timedelta(days=7)
    
    session1, created = Session.objects.get_or_create(
        student=student1,
        teacher=teacher1,
        scheduled_date=tomorrow,
        start_time=time(10, 0),
        defaults={
            'course': course1,
            'title': 'Calculus Problem Solving',
            'description': 'Advanced integration and differentiation techniques',
            'session_type': 'ONLINE',
            'end_time': time(11, 0),
            'duration_minutes': 60,
            'meeting_link': 'https://meet.google.com/abc-def-ghi',
            'status': 'CONFIRMED',
            'price': 1500.00,
            'is_paid': True
        }
    )
    if created:
        print(f"  ✓ Created session: {session1.title}")
    else:
        print(f"  ⚠ Session already exists")
    
    session2, created = Session.objects.get_or_create(
        student=student2,
        teacher=teacher2,
        scheduled_date=next_week,
        start_time=time(14, 0),
        defaults={
            'course': course2,
            'title': 'Django REST API Development',
            'description': 'Building RESTful APIs with Django',
            'session_type': 'ONLINE',
            'end_time': time(15, 30),
            'duration_minutes': 90,
            'meeting_link': 'https://zoom.us/j/123456789',
            'status': 'PENDING',
            'price': 2000.00,
            'is_paid': False
        }
    )
    if created:
        print(f"  ✓ Created session: {session2.title}")
    else:
        print(f"  ⚠ Session already exists")
    
    # Create Resources
    print("\nCreating resources...")
    resource1, created = Resource.objects.get_or_create(
        title='JEE Mathematics Formula Sheet',
        defaults={
            'description': 'Complete formula reference for JEE Main and Advanced',
            'resource_type': 'PDF',
            'course': course1,
            'category': 'Reference Material',
            'is_free': True,
            'requires_enrollment': False,
            'external_link': 'https://example.com/formulas.pdf',
            'tags': ['mathematics', 'jee', 'formulas']
        }
    )
    if created:
        print(f"  ✓ Created resource: {resource1.title}")
    else:
        print(f"  ⚠ Resource already exists")
    
    resource2, created = Resource.objects.get_or_create(
        title='Python Programming Basics',
        defaults={
            'description': 'Free Python tutorial for absolute beginners',
            'resource_type': 'VIDEO',
            'category': 'Programming',
            'is_free': True,
            'requires_enrollment': False,
            'external_link': 'https://youtube.com/watch?v=example',
            'tags': ['python', 'programming', 'basics']
        }
    )
    if created:
        print(f"  ✓ Created resource: {resource2.title}")
    else:
        print(f"  ⚠ Resource already exists")
    
    resource3, created = Resource.objects.get_or_create(
        title='Advanced Django Patterns',
        defaults={
            'description': 'Advanced design patterns for Django applications',
            'resource_type': 'ARTICLE',
            'course': course2,
            'category': 'Web Development',
            'is_free': False,
            'requires_enrollment': True,
            'external_link': 'https://example.com/django-patterns',
            'tags': ['django', 'patterns', 'advanced']
        }
    )
    if created:
        print(f"  ✓ Created resource: {resource3.title}")
    else:
        print(f"  ⚠ Resource already exists")
    
    print("\n" + "="*60)
    print("✅ Test data created successfully!")
    print("="*60)
    
    # Print summary
    print("\n📊 DATABASE SUMMARY:")
    print(f"  Total Users: {User.objects.count()}")
    print(f"  Students: {User.objects.filter(role='STUDENT').count()}")
    print(f"  Teachers: {User.objects.filter(role='TEACHER').count()}")
    print(f"  Courses: {Course.objects.count()}")
    print(f"  Enrollments: {Enrollment.objects.count()}")
    print(f"  Sessions: {Session.objects.count()}")
    print(f"  Resources: {Resource.objects.count()}")
    
    print("\n🔑 TEST CREDENTIALS:")
    print("="*60)
    print("Students:")
    print("  • student1@test.com / Test123!@#")
    print("  • student2@test.com / Test123!@#")
    print("\nTeachers:")
    print("  • teacher1@test.com / Test123!@#")
    print("  • teacher2@test.com / Test123!@#")
    print("="*60)
    
    print("\n📋 TEACHER IDs FOR API TESTING:")
    teachers = User.objects.filter(role='TEACHER')
    for teacher in teachers:
        print(f"  • {teacher.email}: ID = {teacher.id}")
    print("="*60)

if __name__ == '__main__':
    create_test_data()
