from decimal import Decimal
from django.db import models
from django.conf import settings


GRADE_SCALE = [
    (90, 'A',  Decimal('4.0')),
    (80, 'B+', Decimal('3.5')),
    (70, 'B',  Decimal('3.0')),
    (60, 'C+', Decimal('2.5')),
    (50, 'C',  Decimal('2.0')),
    (40, 'D',  Decimal('1.0')),
    (0,  'F',  Decimal('0.0')),
]


def score_to_grade(score):
    score = Decimal(str(score))
    for min_score, letter, points in GRADE_SCALE:
        if score >= min_score:
            return letter, points
    return 'F', Decimal('0.0')


def get_gpa_trend(student):
    """Returns per-semester GPA list for Chart.js: [{label, gpa}, ...]."""
    grades = Grade.objects.filter(
        registration__student=student,
        registration__status='approved',
        grade_point__isnull=False,
    ).select_related('registration__course')

    semesters = {}
    for g in grades:
        course = g.registration.course
        key = (course.academic_year, course.semester)
        if key not in semesters:
            semesters[key] = {'points': Decimal('0'), 'credits': 0}
        semesters[key]['points'] += g.grade_point * course.credits
        semesters[key]['credits'] += course.credits

    trend = []
    for (year, sem) in sorted(semesters.keys()):
        d = semesters[(year, sem)]
        if d['credits'] > 0:
            gpa = float((d['points'] / d['credits']).quantize(Decimal('0.01')))
            trend.append({'label': f"Sem {sem} ({year})", 'gpa': gpa})
    return trend


def calculate_gpa(student):
    grades = Grade.objects.filter(
        registration__student=student,
        registration__status='approved',
        grade_point__isnull=False,
    ).select_related('registration__course')

    total_points = Decimal('0')
    total_credits = 0

    for g in grades:
        credits = g.registration.course.credits
        total_points += g.grade_point * credits
        total_credits += credits

    if total_credits == 0:
        return Decimal('0.00')
    return (total_points / total_credits).quantize(Decimal('0.01'))


class Course(models.Model):
    SEMESTER_CHOICES = [('1', 'First Semester'), ('2', 'Second Semester')]

    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    credits = models.PositiveSmallIntegerField(default=3)
    lecturer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='courses_taught',
        limit_choices_to={'role__in': ['lecturer', 'hod']},
    )
    semester = models.CharField(max_length=1, choices=SEMESTER_CHOICES, default='1')
    academic_year = models.CharField(max_length=9, default='2024/2025')
    max_students = models.PositiveSmallIntegerField(default=50)
    year_of_study = models.PositiveSmallIntegerField(
        choices=[(i, f'Year {i}') for i in range(1, 6)],
        default=1,
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['code']

    def __str__(self):
        return f"{self.code} - {self.name}"

    @property
    def enrolled_count(self):
        return self.registrations.filter(status='approved').count()

    @property
    def is_full(self):
        return self.enrolled_count >= self.max_students


class CourseRegistration(models.Model):
    STATUS_CHOICES = [
        ('pending',  'Pending'),
        ('approved', 'Approved'),
        ('dropped',  'Dropped'),
        ('rejected', 'Rejected'),
    ]

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='registrations',
    )
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='registrations')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='approved')
    registered_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['student', 'course']
        ordering = ['-registered_at']

    def __str__(self):
        return f"{self.student.get_full_name()} → {self.course.code}"


class Grade(models.Model):
    registration = models.OneToOneField(
        CourseRegistration, on_delete=models.CASCADE, related_name='grade'
    )
    score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    coursework = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    assignments = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    tests = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    quizzes = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    exams = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    practical_marks = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    participation = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    total_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    letter_grade = models.CharField(max_length=2, blank=True)
    grade_point = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)
    graded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='grades_given',
    )
    graded_at = models.DateTimeField(auto_now=True)
    remarks = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        component_values = [
            self.coursework,
            self.assignments,
            self.tests,
            self.quizzes,
            self.exams,
            self.practical_marks,
            self.participation,
        ]
        components = [Decimal(str(value)) for value in component_values if value is not None]

        if self.total_score is None:
            if components:
                self.total_score = sum(components, Decimal('0.00'))
            elif self.score is not None:
                self.total_score = Decimal(str(self.score))

        if self.total_score is not None and self.score is None:
            self.score = self.total_score

        if self.score is not None:
            normalized_score = min(Decimal(str(self.score)), Decimal('100'))
            self.letter_grade, self.grade_point = score_to_grade(normalized_score)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.registration} — {self.letter_grade or 'Ungraded'}"
