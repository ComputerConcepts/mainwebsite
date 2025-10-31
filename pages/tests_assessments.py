from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from decimal import Decimal
import json

from .models import Employee, OnboardingAssessment


class AssessmentSaveTests(TestCase):
    def setUp(self):
        # Create HR user and employee profile
        self.user = User.objects.create_user(username='hruser', email='hr@example.com', password='pass')
        Employee.objects.create(
            user=self.user,
            employee_id='E001',
            department='HR',
            position='HR Manager',
            phone='1234567890',
            role='admin'
        )
        self.client = Client()
        self.client.login(username='hruser', password='pass')

        self.assessment = OnboardingAssessment.objects.create(
            title='Sample Assessment',
            description='For testing',
            created_by=self.user,
            is_active=True,
        )

    def test_create_questions_with_correct_answer_and_points(self):
        url = reverse('save_assessment_questions', kwargs={'assessment_id': self.assessment.id})
        payload = {
            'fields': [
                {
                    'field_type': 'radio',
                    'field_label': 'What is 2+2?',
                    'field_options': ['1', '3', '4'],
                    'assessment_points': 2,
                    'correct_answer': 2,
                    'order': 0,
                },
                {
                    'field_type': 'textarea',
                    'field_label': 'Explain your choice',
                    'field_options': [],
                    'assessment_points': 3,
                    'order': 1,
                }
            ]
        }

        response = self.client.post(url, data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('success'))

        questions = list(self.assessment.questions.filter(is_active=True).order_by('order'))
        self.assertEqual(len(questions), 2)

        q1 = questions[0]
        self.assertEqual(q1.question_text, 'What is 2+2?')
        self.assertEqual(q1.points, Decimal('2'))
        # correct_answer stored as JSONField may be int
        self.assertEqual(q1.correct_answer, 2)
        self.assertFalse(q1.allow_multiple_answers)

        q2 = questions[1]
        self.assertEqual(q2.question_type, 'open')
        self.assertEqual(q2.points, Decimal('3'))
        self.assertFalse(q2.allow_multiple_answers)

    def test_update_existing_question_changes_points_and_correct_answer(self):
        # First create one question
        url = reverse('save_assessment_questions', kwargs={'assessment_id': self.assessment.id})
        initial = {
            'fields': [
                {
                    'field_type': 'radio',
                    'field_label': 'Pick one',
                    'field_options': ['A', 'B'],
                    'assessment_points': 1,
                    'correct_answer': 0,
                    'order': 0,
                }
            ]
        }
        resp = self.client.post(url, data=json.dumps(initial), content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        q = self.assessment.questions.filter(is_active=True).first()

        # Now update the same question by id
        update_payload = {
            'fields': [
                {
                    'assessment_question_id': str(q.id),
                    'field_type': 'radio',
                    'field_label': 'Pick one',
                    'field_options': ['A', 'B', 'C'],
                    'assessment_points': 2.5,
                    'correct_answer': [0, 2],
                    'order': 0,
                }
            ]
        }
        resp2 = self.client.post(url, data=json.dumps(update_payload), content_type='application/json')
        self.assertEqual(resp2.status_code, 200)
        q.refresh_from_db()
        self.assertEqual(q.points, Decimal('2.5'))
        self.assertEqual(q.correct_answer, [0, 2])
        self.assertFalse(q.allow_multiple_answers)

    def test_checkbox_field_sets_allow_multiple_answers(self):
        url = reverse('save_assessment_questions', kwargs={'assessment_id': self.assessment.id})
        payload = {
            'fields': [
                {
                    'field_type': 'checkbox',
                    'field_label': 'Select prime numbers',
                    'field_options': ['2', '3', '4', '5'],
                    'assessment_points': 4,
                    'correct_answer': [0, 1, 3],
                    'allow_multiple_answers': True,
                    'order': 0,
                }
            ]
        }
        resp = self.client.post(url, data=json.dumps(payload), content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        question = self.assessment.questions.filter(is_active=True).first()
        self.assertTrue(question.allow_multiple_answers)
        self.assertEqual(question.correct_answer, [0, 1, 3])
        self.assertEqual(question.points, Decimal('4'))
