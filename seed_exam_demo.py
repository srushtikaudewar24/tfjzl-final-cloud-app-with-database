"""Create a sample course and two exam questions for screenshots and grading."""
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
import django
django.setup()

from onlinecourse.models import Course, Lesson, Question, Choice

course, _ = Course.objects.get_or_create(
    name='Django Fundamentals',
    defaults={'description':'An introductory course with a short assessment.',
              'image':'course_images/demo.jpg', 'total_enrollment':0},
)
lesson, _ = Lesson.objects.get_or_create(
    course=course, title='Python and Django Basics',
    defaults={'order':0, 'content':'Learn Django, URLs, templates, and models.'},
)
questions = [
    ('Which framework is used to build this Online Course application?',
     [('Django', True), ('Flask', False), ('React', False)]),
    ('What is a Django model used for?',
     [('Defining application data and database structure', True),
      ('Changing the browser theme only', False),
      ('Installing Python', False)]),
]
for prompt, choices in questions:
    question, _ = Question.objects.get_or_create(
        course=course, lesson=lesson, question_text=prompt, defaults={'grade': 1},
    )
    for text, correct in choices:
        Choice.objects.get_or_create(question=question, choice_text=text,
                                     defaults={'is_correct':correct})
print('Sample course created. Enroll through the UI; answer both questions correctly for Congratulations.')
print('Course ID:', course.pk)
