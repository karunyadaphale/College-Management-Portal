"""
Automated Test Suite for College Management Portal.
Validates all requirements outlined in Section 19 of the PBL specifications.
"""

import os
import django
from django.test import TestCase, Client
from django.urls import reverse
from database.mongodb import get_db, check_connection
from academics.services import calculate_attendance_percentage, calculate_exam_percentage
from students.services import check_student_duplicates
from faculty.services import check_faculty_duplicates


class CollegePortalComprehensiveTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.db = get_db()

    def test_01_mongodb_connectivity(self):
        """Validates that MongoDB is connected and responsive."""
        connected, msg = check_connection()
        self.assertTrue(connected, f"MongoDB connection check failed: {msg}")

    def test_02_invalid_login_attempt(self):
        """Tests that invalid login returns an error message."""
        response = self.client.post(reverse('accounts:login'), {
            'username': 'non_existent_user',
            'password': 'WrongPassword123'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invalid username or password")

    def test_03_valid_admin_login_and_redirect(self):
        """Tests admin login and role-based redirect to /admin/dashboard/."""
        response = self.client.post(reverse('accounts:login'), {
            'username': 'admin',
            'password': 'Admin@123'
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('user_id', self.client.session)
        self.assertEqual(self.client.session.get('role'), 'admin')
        self.assertContains(response, "Administrative Dashboard")

    def test_04_faculty_login_and_redirect(self):
        """Tests faculty login and redirect to faculty dashboard."""
        client = Client()
        response = client.post(reverse('accounts:login'), {
            'username': 'fac001',
            'password': 'Faculty@123'
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(client.session.get('role'), 'faculty')
        self.assertContains(response, "Faculty Academic Dashboard")

    def test_05_student_login_and_redirect(self):
        """Tests student login and redirect to student dashboard."""
        client = Client()
        response = client.post(reverse('accounts:login'), {
            'username': 'stu001',
            'password': 'Student@123'
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(client.session.get('role'), 'student')
        self.assertContains(response, "My Dashboard")

    def test_06_unauthorized_access_protection(self):
        """Students must not access administrative dashboard."""
        client = Client()
        # Log in as student
        client.post(reverse('accounts:login'), {
            'username': 'stu001',
            'password': 'Student@123'
        })
        # Attempt to access admin dashboard
        response = client.get(reverse('accounts:admin_dashboard'), follow=True)
        self.assertContains(response, "Access Denied")

    def test_07_duplicate_student_id_prevention(self):
        """Ensures duplicate student ID and roll number detection works."""
        is_dup_id, err_id = check_student_duplicates('STU001', 'RANDOM_ROLL')
        self.assertTrue(is_dup_id)
        self.assertIn("STU001", err_id)

        is_dup_roll, err_roll = check_student_duplicates('RANDOM_ID', 'CS202401')
        self.assertTrue(is_dup_roll)
        self.assertIn("CS202401", err_roll)

    def test_08_attendance_percentage_calculation_with_zero_safety(self):
        """Tests the attendance percentage formula and division-by-zero protection."""
        # Zero conducted classes should return 0.0 without crash
        self.assertEqual(calculate_attendance_percentage(0, 0), 0.0)

        # Standard calculation: (3 / 4) * 100 = 75.0%
        self.assertEqual(calculate_attendance_percentage(3, 4), 75.0)

        # (2 / 3) * 100 = 66.7%
        self.assertEqual(calculate_attendance_percentage(2, 3), 66.7)

    def test_09_examination_percentage_calculation(self):
        """Tests percentage formula: (marks_obtained / max_marks) * 100."""
        self.assertEqual(calculate_exam_percentage(85.0, 100.0), 85.0)
        self.assertEqual(calculate_exam_percentage(0, 0), 0.0)
        self.assertEqual(calculate_exam_percentage(45.0, 50.0), 90.0)

    def test_10_student_search(self):
        """Tests searching for student by name or roll number."""
        # Login as admin
        self.client.post(reverse('accounts:login'), {'username': 'admin', 'password': 'Admin@123'})
        response = self.client.get(reverse('students:list') + '?search=Aarav')
        self.assertContains(response, "Aarav Mehta")
        self.assertContains(response, "CS202401")

    def test_11_empty_form_submission_validation(self):
        """Tests validation on empty student addition form."""
        self.client.post(reverse('accounts:login'), {'username': 'admin', 'password': 'Admin@123'})
        response = self.client.post(reverse('students:add'), {
            'student_id': '',
            'name': '',
        })
        self.assertContains(response, "Please fill in all mandatory fields")

    def test_12_add_and_delete_announcement(self):
        """Tests adding and deleting an announcement as admin."""
        self.client.post(reverse('accounts:login'), {'username': 'admin', 'password': 'Admin@123'})
        response = self.client.post(reverse('academics:announcement_add'), {
            'title': 'Automated Test Notice',
            'description': 'Notice published during test execution.',
            'category': 'General',
            'publication_date': '2026-10-09'
        }, follow=True)
        self.assertContains(response, "Automated Test Notice")

        # Cleanup
        announcement = self.db.announcements.find_one({'title': 'Automated Test Notice'})
        if announcement:
            del_response = self.client.post(
                reverse('academics:announcement_delete', args=[str(announcement['_id'])]),
                follow=True
            )
            self.assertContains(del_response, "Announcement removed successfully")
