from django.core.management.base import BaseCommand
from courses.models import Course

COURSES = [
    # Year 1, Semester 1
    {'code': 'ENGL101', 'name': 'Core English I',             'credits': 2, 'year': 1, 'semester': '1', 'description': 'Foundation English language skills for academic communication.'},
    {'code': 'PHYS101', 'name': 'Core Physics I',             'credits': 4, 'year': 1, 'semester': '1', 'description': 'Fundamental concepts of physics including mechanics, heat, and waves.'},
    {'code': 'INFT101', 'name': 'Information Technology I',   'credits': 2, 'year': 1, 'semester': '1', 'description': 'Introduction to computing, software applications, and digital literacy.'},
    {'code': 'PHE101',  'name': 'Physical Education I',       'credits': 2, 'year': 1, 'semester': '1', 'description': 'Physical fitness, sports, and health education.'},
    {'code': 'AFST101', 'name': 'African Studies I',          'credits': 2, 'year': 1, 'semester': '1', 'description': 'Introduction to African history, culture, and contemporary issues.'},
    {'code': 'MATH111', 'name': 'Pre-Calculus I',             'credits': 4, 'year': 1, 'semester': '1', 'description': 'Set theory, relations and functions, linear and quadratic equations, inequalities, linear programming, remainder and factor theorems, binomial theorem, and mathematical induction.'},
    {'code': 'MATH121', 'name': 'Introduction to Calculus',   'credits': 4, 'year': 1, 'semester': '1', 'description': 'Limits, continuity, differentiation by first principles, rules of differentiation (sum, chain, product, quotient), differentiation of algebraic, trigonometric, exponential and logarithmic functions; applications to maxima and minima.'},
    {'code': 'MATH151', 'name': 'Applied Mathematics I',      'credits': 4, 'year': 1, 'semester': '1', 'description': 'Elementary dynamics and statics, motion with uniform acceleration, vectors, graphical representation of data, measures of central tendency.'},
    {'code': 'MATH171', 'name': 'Statistics I',               'credits': 4, 'year': 1, 'semester': '1', 'description': 'Measures of dispersion: range, interquartile range, mean deviation, variance, standard deviation, coefficient of variation, standard error of the mean.'},
    {'code': 'MATH181', 'name': 'Introduction to Probability','credits': 4, 'year': 1, 'semester': '1', 'description': 'Factorials, permutations and combinations, sample space, discrete and continuous probability distributions, conditional probability, Bayes theorem.'},
    {'code': 'MATH191', 'name': 'Coordinate Geometry I',      'credits': 3, 'year': 1, 'semester': '1', 'description': 'Straight lines, distance between points, midpoint, equations of a straight line; circles, equation of a circle, tangents and normals.'},

    # Year 1, Semester 2
    {'code': 'ENGL102', 'name': 'Core English II',            'credits': 2, 'year': 1, 'semester': '2', 'description': 'Advanced English communication skills, academic writing and comprehension.'},
    {'code': 'PHYS102', 'name': 'Core Physics II',            'credits': 4, 'year': 1, 'semester': '2', 'description': 'Electricity, magnetism, optics, and modern physics.'},
    {'code': 'INFT102', 'name': 'Information Technology II',  'credits': 2, 'year': 1, 'semester': '2', 'description': 'Intermediate computing skills, programming fundamentals, and information systems.'},
    {'code': 'PHE102',  'name': 'Physical Education II',      'credits': 2, 'year': 1, 'semester': '2', 'description': 'Advanced physical fitness, team sports, and health promotion.'},
    {'code': 'AFST102', 'name': 'African Studies II',         'credits': 2, 'year': 1, 'semester': '2', 'description': 'African political systems, economics, and development studies.'},
    {'code': 'MATH112', 'name': 'Pre-Calculus II',            'credits': 4, 'year': 1, 'semester': '2', 'description': 'Sequences and series (AP and GP), trigonometric identities, matrices and determinants, introduction to logic, connectives and truth tables, methods of proof.'},
    {'code': 'MATH122', 'name': 'Calculus I',                 'credits': 4, 'year': 1, 'semester': '2', 'description': 'Applications of differentiation (curve sketching, tangents and normals), integration (definite and indefinite integrals, integration techniques), applications of integration in mechanics, approximate methods of integration.'},
    {'code': 'MATH152', 'name': 'Applied Mathematics II',     'credits': 4, 'year': 1, 'semester': '2', 'description': 'Coplanar forces in equilibrium, Lami\'s theorem, polygon of forces and equilibrium.'},
    {'code': 'MATH172', 'name': 'Statistics II',              'credits': 4, 'year': 1, 'semester': '2', 'description': 'Simple sampling theory, types of sampling, sampling distributions, bivariate data, correlation and regression, Spearman\'s rank correlation.'},
    {'code': 'MATH182', 'name': 'Probability I',              'credits': 4, 'year': 1, 'semester': '2', 'description': 'Normal distribution, binomial, Poisson, geometric and hypergeometric distributions.'},
    {'code': 'MATH192', 'name': 'Coordinate Geometry II',     'credits': 3, 'year': 1, 'semester': '2', 'description': 'The parabola, equation of the parabola, sketching a parabola, tangents and normals to a parabola.'},

    # Year 2, Semester 1
    {'code': 'ENGL201', 'name': 'Core English III',           'credits': 2, 'year': 2, 'semester': '1', 'description': 'Advanced academic writing, research communication, and critical reading.'},
    {'code': 'INFT201', 'name': 'Information Technology III', 'credits': 2, 'year': 2, 'semester': '1', 'description': 'Advanced computing, data management, and mathematical software tools.'},
    {'code': 'MATH221', 'name': 'Integral Calculus',          'credits': 4, 'year': 2, 'semester': '1', 'description': 'Derivatives of trigonometric, implicit, exponential, logarithmic and inverse functions; Leibnitz theorem, Wallis formula, Newton\'s method; integration of trigonometric and exponential functions; integration by substitution and by parts; improper integrals; areas and volumes.'},
    {'code': 'MATH231', 'name': 'Abstract Algebra I',         'credits': 4, 'year': 2, 'semester': '1', 'description': 'Set functions and graphs, arbitrary cases of membership, Cartesian products, equivalence and partitions, graphs of harder functions.'},
    {'code': 'MATH241', 'name': 'Real Analysis I',            'credits': 4, 'year': 2, 'semester': '1', 'description': 'Naive point set theory, equivalence relations, functions and mapping.'},
    {'code': 'MATH251', 'name': 'Applied Mathematics III',    'credits': 4, 'year': 2, 'semester': '1', 'description': 'Vectors and scalars, addition of vectors, scalar and vector products, displacement, velocity and acceleration as vectors, relative velocity; forces as vectors, parallelogram of forces, triangle of forces, Lami\'s theorem.'},
    {'code': 'MATH271', 'name': 'Statistics III',             'credits': 3, 'year': 2, 'semester': '1', 'description': 'Hypothesis testing, types of error, statistical significance, confidence intervals, power and robustness, degrees of freedom, non-parametric analysis.'},
    {'code': 'MATH291', 'name': 'Geometry I',                 'credits': 2, 'year': 2, 'semester': '1', 'description': 'Conics: the ellipse, special properties; the hyperbola, special properties; conic sections, tangents and normals.'},

    # Year 2, Semester 2
    {'code': 'ENGL202', 'name': 'Core English IV',            'credits': 2, 'year': 2, 'semester': '2', 'description': 'Professional English communication, technical report writing, and presentations.'},
    {'code': 'INFT202', 'name': 'Information Technology IV',  'credits': 2, 'year': 2, 'semester': '2', 'description': 'Computational mathematics and programming for mathematical applications.'},
    {'code': 'MATH222', 'name': 'Calculus II',                'credits': 4, 'year': 2, 'semester': '2', 'description': 'Partial differentiation, chain rules, total differential, maxima and minima of functions of two or more variables; differential equations (first order, second order with constant coefficients, simultaneous), applications in science and engineering.'},
    {'code': 'MATH232', 'name': 'Abstract Algebra II',        'credits': 4, 'year': 2, 'semester': '2', 'description': 'Matrix operations, rank of a matrix and matrix inverses, systems of linear equations.'},
    {'code': 'MATH242', 'name': 'Real Analysis II',           'credits': 4, 'year': 2, 'semester': '2', 'description': 'Inequalities, arithmetic and geometric means, Cauchy triangle inequality; sequences (convergence, addition, multiplication, monotonic); series (supremum, limit infimum, Cauchy sequences); comparison, ratio and root tests; limits and continuity.'},
    {'code': 'MATH252', 'name': 'Applied Mathematics IV',     'credits': 4, 'year': 2, 'semester': '2', 'description': 'Forces: polygon of forces, moments and couples, reduction of coplanar forces; motion with constant acceleration, Newton\'s laws, projectiles.'},
    {'code': 'MATH272', 'name': 'Statistics IV',              'credits': 3, 'year': 2, 'semester': '2', 'description': 'Normal distribution, areas under the standard normal curve, working with normally distributed variables, normal approximations to the binomial distribution.'},
    {'code': 'MATH292', 'name': 'Geometry II',                'credits': 2, 'year': 2, 'semester': '2', 'description': 'Incidence geometry in planes and space, distance and congruence, angular measure, congruencies between triangles, geometric inequalities; elementary theory of areas and volumes, hyperbolic geometry, Euclidean geometry.'},

    # Year 3, Semester 1
    {'code': 'MATH321', 'name': 'Calculus III',               'credits': 3, 'year': 3, 'semester': '1', 'description': 'Differentiation of sums and products of differentiable functions, function of a function, power series; Rolle\'s theorem, first mean value theorem, Leibnitz theorem, Taylor\'s theorem, L\'Hopital\'s theorem.'},
    {'code': 'MATH341', 'name': 'Real Analysis III',          'credits': 3, 'year': 3, 'semester': '1', 'description': 'Cantor\'s diagonal process, natural numbers, negative and fractional numbers, countability of rational numbers, Dedekind\'s cuts and real numbers, bounds of sets, supremum and infimum.'},
    {'code': 'MATH351', 'name': 'Applied Mathematics V',      'credits': 4, 'year': 3, 'semester': '1', 'description': 'Gravity and friction, momentum and motion, centre of gravity, work, energy and power, conservation of energy and momentum, impulsive motion, oblique impact.'},
    {'code': 'MATH361', 'name': 'Number Theory I',            'credits': 3, 'year': 3, 'semester': '1', 'description': 'Integers: axioms, order, law of well ordering, mathematical induction; division algorithm, GCD and LCM, Euclidean algorithm, Euclid\'s lemma.'},
    {'code': 'MATH381', 'name': 'Probability II',             'credits': 3, 'year': 3, 'semester': '1', 'description': 'Various probability distributions: binomial, Poisson, multinomial, uniform, exponential, normal; importance of normal distribution.'},
    {'code': 'MATH391', 'name': 'Analytical Geometry',        'credits': 3, 'year': 3, 'semester': '1', 'description': 'Coordinates and loci, locus problems, transformation of coordinates, polar coordinates.'},
    {'code': 'REMT301', 'name': 'Research Methods I',         'credits': 1, 'year': 3, 'semester': '1', 'description': 'Introduction to research methodology, research design, data collection, and academic writing for mathematics.'},

    # Year 3, Semester 2
    {'code': 'MATH322', 'name': 'Calculus IV',                'credits': 4, 'year': 3, 'semester': '2', 'description': 'Riemann\'s integral, properties of exponential, trigonometric and logarithmic functions; multiple integration, iterated integrals, double integrals and volume, change of variables, polar coordinates, centre of mass and moments of inertia, surface area, triple integrals.'},
    {'code': 'MATH342', 'name': 'Real Analysis IV',           'credits': 3, 'year': 3, 'semester': '2', 'description': 'Continuity of functions, power series with radius of convergence, uniform convergence, theorems for continuous functions, Heine-Borel theorem.'},
    {'code': 'MATH352', 'name': 'Applied Mathematics VI',     'credits': 3, 'year': 3, 'semester': '2', 'description': 'Vectors: differentiation of a unit vector in coordinates; motion in a circle, simple harmonic motion, small oscillations; dynamics of a rigid body with fixed axis, normal modes.'},
    {'code': 'MATH362', 'name': 'Number Theory II',           'credits': 3, 'year': 3, 'semester': '2', 'description': 'Algorithms, integers and division, applications of integer algorithms.'},
    {'code': 'MATH372', 'name': 'Statistics V',               'credits': 3, 'year': 3, 'semester': '2', 'description': 'Variance tests: chi-square test of a single variance, F-tests of two variances, tests of homogeneity, Wilcoxon rank-sum/Mann-Whitney U test, sign test, contingency tables, Fisher\'s exact test, measures of association, McNemar\'s test.'},
    {'code': 'MATH392', 'name': 'Axiomatic Geometry',         'credits': 3, 'year': 3, 'semester': '2', 'description': 'Axiomatic geometry: axioms, theorems and proofs.'},
    {'code': 'REMT302', 'name': 'Research Methods II',        'credits': 1, 'year': 3, 'semester': '2', 'description': 'Advanced research methods, statistical analysis of research data, project proposal writing.'},

    # Year 4, Semester 2 (Semester 1 is Internship)
    {'code': 'MATH422', 'name': 'Calculus V',                 'credits': 4, 'year': 4, 'semester': '2', 'description': 'Multiple integration: triple integrals in cylindrical and spherical coordinates, change of variables, Jacobians; Beta and Gamma functions and their relationship; vector analysis, vector fields, conservative vector fields, Green\'s theorem, parametric surfaces.'},
    {'code': 'MATH432', 'name': 'Algebra',                    'credits': 4, 'year': 4, 'semester': '2', 'description': 'Groups and matrices: algebraic and geometric examples, geometric transformations, permutations, subgroups, cyclic groups; basic theorems, Lagrange\'s theorem, homomorphism, normal subgroups, quotient groups, isomorphism theorems.'},
    {'code': 'MATH462', 'name': 'Number Theory III',          'credits': 4, 'year': 4, 'semester': '2', 'description': 'Congruence and residue classes, composition of functions and permutations.'},
    {'code': 'MATH472', 'name': 'Statistics VI',              'credits': 4, 'year': 4, 'semester': '2', 'description': 'Analysis of variance: single-factor (one-way ANOVA), two-factor and higher-way ANOVA, block and fractional designs, methods of sampling.'},
    {'code': 'MATH482', 'name': 'Probability III',            'credits': 4, 'year': 4, 'semester': '2', 'description': 'Limit theorems, law of large numbers, Chebyshev\'s inequality.'},
]


class Command(BaseCommand):
    help = 'Populate the database with BSc Mathematics curriculum courses from the official ETUSL programme document.'

    def add_arguments(self, parser):
        parser.add_argument('--year', default='2024/2025', help='Academic year (default: 2024/2025)')
        parser.add_argument('--clear', action='store_true', help='Delete all existing courses before populating')

    def handle(self, *args, **options):
        academic_year = options['year']

        if options['clear']:
            count = Course.objects.all().count()
            Course.objects.all().delete()
            self.stdout.write(self.style.WARNING(f'Deleted {count} existing courses.'))

        created = 0
        skipped = 0

        for entry in COURSES:
            _, made = Course.objects.get_or_create(
                code=entry['code'],
                defaults={
                    'name': entry['name'],
                    'credits': entry['credits'],
                    'year_of_study': entry['year'],
                    'semester': entry['semester'],
                    'description': entry['description'],
                    'academic_year': academic_year,
                    'is_active': True,
                },
            )
            if made:
                created += 1
            else:
                skipped += 1

        self.stdout.write(self.style.SUCCESS(
            f'Done. Created: {created} courses, Skipped (already exist): {skipped} courses.'
        ))
