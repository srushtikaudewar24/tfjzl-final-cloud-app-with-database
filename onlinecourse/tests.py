"""Tests for the online course assessment feature."""
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Course, Lesson, Enrollment, Question, Choice, Submission


class ExamFeatureTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='student_demo', password='test-pass-123')
        self.other = User.objects.create_user(username='different_student', password='test-pass-123')
        self.course = Course.objects.create(
            name='Django Test Course', description='Test course',
            image='course_images/example.jpg',
        )
        self.lesson = Lesson.objects.create(
            course=self.course, title='Introduction', content='Lessons go here', order=0
        )
        self.enrollment = Enrollment.objects.create(user=self.user, course=self.course)
        self.question = Question.objects.create(
            course=self.course, lesson=self.lesson, question_text='What is Django?', grade=5
        )
        self.correct = Choice.objects.create(
            question=self.question, choice_text='A Python web framework', is_correct=True
        )
        self.wrong = Choice.objects.create(
            question=self.question, choice_text='A spreadsheet', is_correct=False
        )

    def test_course_details_show_exam_form(self):
        response = self.client.get(reverse('onlinecourse:course_details', args=[self.course.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.course.name)
        self.assertContains(response, self.lesson.title)

    def test_question_scoring_and_model_contract(self):
        self.assertTrue(self.question.is_get_score([self.correct.id]))
        self.assertFalse(self.question.is_get_score([self.wrong.id]))
        self.assertFalse(self.question.is_get_score([]))
        self.assertEqual(Choice._meta.get_field('choice_text').max_length, 100)
        submission = Submission.objects.create(enrollment=self.enrollment)
        self.assertIn(str(self.enrollment.id), str(submission))

    def test_result_route_and_template_context(self):
        self.client.force_login(self.user)
        submission = Submission.objects.create(enrollment=self.enrollment)
        submission.choices.add(self.correct)
        url = reverse('onlinecourse:show_exam_result', args=[self.course.id, submission.id])
        self.assertIn('/course/', url)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['possible'], 5)
        self.assertIn(self.correct.id, response.context['selected_ids'])

    def test_submit_and_congratulations(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse('onlinecourse:submit', args=[self.course.id]),
            {f'choice_{self.question.id}': str(self.correct.id)},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Congratulations')
        self.assertContains(response, '100.0%')
        submission = Submission.objects.get(enrollment=self.enrollment)
        self.assertEqual(list(submission.choices.all()), [self.correct])

    def test_incorrect_answer_shows_feedback(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse('onlinecourse:submit', args=[self.course.id]),
            {f'choice_{self.question.id}': str(self.wrong.id)},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Incorrect')
        self.assertContains(response, self.correct.choice_text)

    def test_student_cannot_read_others_results(self):
        submission = Submission.objects.create(enrollment=self.enrollment)
        self.client.force_login(self.other)
        response = self.client.get(reverse(
            'onlinecourse:show_exam_result', args=[self.course.id, submission.id]
        ))
        self.assertEqual(response.status_code, 404)

    def test_submit_requires_login(self):
        response = self.client.post(reverse('onlinecourse:submit', args=[self.course.id]))
        self.assertEqual(response.status_code, 302)
