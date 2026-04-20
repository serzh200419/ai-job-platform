"""
Management command: seed_jobs
─────────────────────────────
Creates realistic mock data for testing the job platform.

Usage:
    python manage.py seed_jobs            # create everything
    python manage.py seed_jobs --clear    # wipe seed data first, then recreate

Idempotent: running without --clear will skip records that already exist.
"""
import random
from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from jobs.models import Company, Job, JobSkill
from users.models import Profile, UserEducation, UserExperience, UserSkill

User = get_user_model()

# ── Seed marker ──────────────────────────────────────────────────────────────
# All seeded companies share this suffix so --clear can find them safely.
SEED_MARKER = "[SEED]"


# ── Master data ───────────────────────────────────────────────────────────────

COMPANIES = [
    ("Picsart",          "Technology",    "Yerevan",   "https://picsart.com"),
    ("EPAM Systems",     "Technology",    "Yerevan",   "https://epam.com"),
    ("ServiceTitan",     "Software",      "Yerevan",   "https://servicetitan.com"),
    ("Krisp",            "AI / Audio",    "Yerevan",   "https://krisp.ai"),
    ("Renderforest",     "SaaS",          "Yerevan",   "https://renderforest.com"),
    ("Synergy Int",      "Outsourcing",   "Yerevan",   "https://synergy.am"),
    ("DataArt",          "Technology",    "Gyumri",    "https://dataart.com"),
    ("Teamable",         "HR Tech",       "Remote",    "https://teamable.com"),
    ("Mentor Graphics",  "EDA",           "Yerevan",   "https://mentor.com"),
    ("Joom",             "E-Commerce",    "Remote",    "https://joom.com"),
    ("Smartclick",       "AdTech",        "Yerevan",   "https://smartclick.ai"),
    ("Coda",             "Productivity",  "Remote",    "https://coda.io"),
    ("Loomly",           "Marketing",     "Remote",    "https://loomly.com"),
    ("Gorgias",          "SaaS / CX",     "Remote",    "https://gorgias.com"),
    ("Hexact",           "QA Tech",       "Yerevan",   "https://hexact.io"),
    ("Armbuild",         "Construction",  "Yerevan",   ""),
    ("Ucom",             "Telecom",       "Yerevan",   "https://ucom.am"),
    ("ArmSoft",          "ERP",           "Yerevan",   "https://armsoft.am"),
    ("VivaCell-MTS",     "Telecom",       "Yerevan",   ""),
    ("GlobeCore",        "FinTech",       "Remote",    "https://globecore.io"),
    ("DesignLab",        "Design",        "Vanadzor",  ""),
    ("CloudSec",         "Cybersecurity", "Remote",    "https://cloudsec.io"),
    ("NovaDev",          "Software",      "Gyumri",    ""),
    ("Insight Analytics","Analytics",     "Yerevan",   ""),
    ("ShipFast",         "Logistics",     "Hybrid",    ""),
]

LOCATIONS = ["Yerevan", "Gyumri", "Vanadzor", "Remote", "Hybrid",
             "Berlin (Remote)", "Amsterdam (Remote)", "London (Remote)"]

SKILL_POOLS = {
    "backend":    ["Python", "Django", "REST API", "PostgreSQL", "Docker",
                   "Redis", "Celery", "Git", "Linux", "SQL", "FastAPI", "AWS"],
    "frontend":   ["JavaScript", "TypeScript", "Vue", "React", "HTML", "CSS",
                   "Tailwind CSS", "Webpack", "Git", "REST API", "GraphQL"],
    "fullstack":  ["Python", "Django", "JavaScript", "Vue", "React", "PostgreSQL",
                   "Docker", "REST API", "Git", "TypeScript", "Redis"],
    "data":       ["Python", "SQL", "PostgreSQL", "Pandas", "NumPy", "Tableau",
                   "Power BI", "Excel", "Machine Learning", "Git", "Spark"],
    "qa":         ["Selenium", "Python", "Jest", "Pytest", "Git", "Postman",
                   "SQL", "CI/CD", "JIRA", "Test Planning", "REST API"],
    "devops":     ["Docker", "Kubernetes", "AWS", "CI/CD", "Linux", "Git",
                   "Terraform", "Ansible", "Python", "Bash", "Nginx"],
    "java":       ["Java", "Spring Boot", "Hibernate", "SQL", "Maven",
                   "Docker", "Git", "REST API", "PostgreSQL", "Kafka"],
    "product":    ["Product Management", "Agile", "Scrum", "JIRA", "Figma",
                   "SQL", "Analytics", "Roadmapping", "Stakeholder Management"],
    "design":     ["Figma", "Adobe XD", "Sketch", "Photoshop", "Illustrator",
                   "Prototyping", "User Research", "Wireframing", "CSS"],
    "marketing":  ["SEO", "Google Ads", "Facebook Ads", "Content Marketing",
                   "Analytics", "Copywriting", "Email Marketing", "CRM"],
    "sales":      ["CRM", "Salesforce", "Cold Calling", "Negotiation",
                   "B2B Sales", "Lead Generation", "HubSpot", "Excel"],
    "security":   ["Penetration Testing", "Linux", "Python", "Network Security",
                   "SIEM", "Docker", "Git", "SQL", "Bash"],
}

JOB_TEMPLATES = [
    # (title_pattern, category, level, desc_snippet, req_snippet)
    # ── Backend ──────────────────────────────────────────────────────────────
    ("Junior Python Developer",       "backend",   "junior",  "Build and maintain REST APIs using Django and DRF.", "1+ year Python experience, familiarity with Django."),
    ("Python Developer",              "backend",   "mid",     "Design scalable backend services and integrate third-party APIs.", "3+ years Python/Django, PostgreSQL, Docker."),
    ("Senior Python Developer",       "backend",   "senior",  "Lead backend architecture decisions and mentor junior engineers.", "5+ years Python, Django, Redis, AWS, leadership skills."),
    ("Backend Engineer",              "backend",   "mid",     "Develop high-performance APIs and optimize database queries.", "3+ years backend experience, strong SQL knowledge."),
    ("Senior Backend Engineer",       "backend",   "senior",  "Architect distributed systems handling millions of requests.", "6+ years, Python or Go, Kafka, Kubernetes."),
    ("Python Backend Intern",         "backend",   "intern",  "Assist the team in building features and fixing bugs.", "Basic Python, some knowledge of web frameworks, Git."),
    # ── Frontend ─────────────────────────────────────────────────────────────
    ("Junior Frontend Developer",     "frontend",  "junior",  "Implement responsive UI components using Vue.js.", "1+ year JavaScript/Vue, HTML, CSS."),
    ("Frontend Developer",            "frontend",  "mid",     "Build pixel-perfect interfaces and collaborate with designers.", "3+ years Vue or React, TypeScript, REST API integration."),
    ("Senior Frontend Developer",     "frontend",  "senior",  "Own frontend architecture and drive performance improvements.", "5+ years, Vue 3 or React, Webpack, CI/CD."),
    ("React Developer",               "frontend",  "mid",     "Develop SPAs using React and integrate with GraphQL APIs.", "3+ years React, TypeScript, GraphQL."),
    ("Frontend Intern",               "frontend",  "intern",  "Learn and contribute to UI component library.", "Basic HTML/CSS/JavaScript, eagerness to learn."),
    # ── Full Stack ────────────────────────────────────────────────────────────
    ("Full Stack Developer",          "fullstack", "mid",     "Develop end-to-end features across Django backend and Vue frontend.", "3+ years Python, JavaScript, Vue/React, PostgreSQL."),
    ("Senior Full Stack Engineer",    "fullstack", "senior",  "Lead full-stack development of core platform features.", "6+ years, Python, Vue, Docker, AWS."),
    ("Full Stack Engineer",           "fullstack", "mid",     "Own complete feature delivery from database to UI.", "4+ years full-stack, REST API, Docker."),
    ("Junior Full Stack Developer",   "fullstack", "junior",  "Build features across the stack under senior guidance.", "1+ year full-stack experience, Python, JavaScript."),
    # ── Data ─────────────────────────────────────────────────────────────────
    ("Data Analyst",                  "data",      "mid",     "Analyze user behavior and business metrics, build dashboards.", "3+ years SQL, Python, Tableau or Power BI."),
    ("Junior Data Analyst",           "data",      "junior",  "Support senior analysts in data gathering and reporting.", "1+ year SQL, Excel, basic Python."),
    ("Senior Data Analyst",           "data",      "senior",  "Define KPIs, own data pipelines, present insights to executives.", "5+ years, SQL, Python, Spark, visualization tools."),
    ("Data Engineer",                 "data",      "mid",     "Build and maintain ETL pipelines and data warehouses.", "3+ years Python, SQL, Spark, AWS Redshift."),
    # ── QA ───────────────────────────────────────────────────────────────────
    ("QA Engineer",                   "qa",        "mid",     "Design and execute manual and automated test plans.", "3+ years QA, Selenium or Playwright, Pytest."),
    ("Junior QA Engineer",            "qa",        "junior",  "Write and execute test cases under senior guidance.", "1+ year QA experience, basic Selenium or Pytest."),
    ("Senior QA Engineer",            "qa",        "senior",  "Lead QA strategy, build automation frameworks from scratch.", "5+ years, Python, Selenium, CI/CD integration."),
    ("QA Automation Engineer",        "qa",        "mid",     "Build and maintain automated regression test suites.", "3+ years Pytest, Selenium, CI/CD, Git."),
    # ── DevOps ───────────────────────────────────────────────────────────────
    ("DevOps Engineer",               "devops",    "mid",     "Manage CI/CD pipelines and cloud infrastructure.", "3+ years Docker, Kubernetes, AWS or GCP."),
    ("Senior DevOps Engineer",        "devops",    "senior",  "Design resilient infrastructure and drive platform reliability.", "6+ years, Terraform, Kubernetes, AWS, monitoring."),
    ("Cloud Engineer",                "devops",    "mid",     "Deploy and optimize cloud-native applications on AWS.", "3+ years AWS, Docker, Terraform, Linux."),
    # ── Java ─────────────────────────────────────────────────────────────────
    ("Java Developer",                "java",      "mid",     "Build microservices using Spring Boot and Hibernate.", "3+ years Java, Spring Boot, SQL."),
    ("Senior Java Developer",         "java",      "senior",  "Architect high-throughput Java services at scale.", "6+ years Java, Spring, Kafka, PostgreSQL."),
    ("Junior Java Developer",         "java",      "junior",  "Implement features in existing Java Spring Boot services.", "1+ year Java, basic Spring Boot, Git."),
    # ── Product ───────────────────────────────────────────────────────────────
    ("Product Manager",               "product",   "mid",     "Own the product roadmap and work closely with engineering.", "3+ years PM, Agile, JIRA, data-driven."),
    ("Senior Product Manager",        "product",   "senior",  "Define product vision and drive cross-functional execution.", "6+ years PM, SaaS, stakeholder management."),
    ("Junior Product Manager",        "product",   "junior",  "Support the PM team in spec writing and backlog management.", "1+ year in product or project coordination role."),
    # ── Design ───────────────────────────────────────────────────────────────
    ("UI/UX Designer",                "design",    "mid",     "Design intuitive user experiences for web and mobile.", "3+ years Figma, user research, prototyping."),
    ("Senior UI/UX Designer",         "design",    "senior",  "Lead design system and mentor junior designers.", "5+ years Figma, design system experience."),
    ("Junior UI/UX Designer",         "design",    "junior",  "Create wireframes and contribute to the design system.", "1+ year Figma or Adobe XD, portfolio required."),
    # ── Marketing ────────────────────────────────────────────────────────────
    ("Digital Marketing Specialist",  "marketing", "mid",     "Run paid and organic campaigns to drive user acquisition.", "3+ years SEO, Google Ads, content marketing."),
    ("Marketing Manager",             "marketing", "senior",  "Lead the marketing team and own growth strategy.", "5+ years marketing, B2B or SaaS preferred."),
    ("Junior Marketing Specialist",   "marketing", "junior",  "Assist in content creation and social media management.", "1+ year marketing experience, copywriting skills."),
    # ── Sales ────────────────────────────────────────────────────────────────
    ("Sales Manager",                 "sales",     "mid",     "Own an outbound pipeline and close B2B deals.", "3+ years B2B sales, CRM, target-driven."),
    ("Senior Sales Manager",          "sales",     "senior",  "Lead a sales team and define go-to-market strategy.", "6+ years sales, team leadership, SaaS preferred."),
    ("Sales Representative",          "sales",     "junior",  "Generate leads and schedule demos for the sales team.", "1+ year sales or customer-facing role."),
    # ── Security ─────────────────────────────────────────────────────────────
    ("Security Engineer",             "security",  "mid",     "Protect infrastructure and respond to security incidents.", "3+ years security, Linux, Python, pen-testing."),
    ("Senior Security Engineer",      "security",  "senior",  "Lead security audits and build threat detection systems.", "6+ years, SIEM, Kubernetes, penetration testing."),
]

SALARY_BY_LEVEL = {
    "intern": (500,   900),
    "junior": (800,   1800),
    "mid":    (1500,  3500),
    "senior": (3000,  6000),
}

JOB_TYPE_WEIGHTS = {
    "remote":  0.35,
    "hybrid":  0.30,
    "onsite":  0.35,
}

# ── Test users ────────────────────────────────────────────────────────────────

TEST_USERS = [
    {
        "email": "ara.petrosyan@test.am",
        "full_name": "Ara Petrosyan",
        "profession": "Python Developer",
        "summary": "Backend developer with 4 years of experience building Django APIs.",
        "years_experience": 4,
        "desired_salary": 2500,
        "location": "Yerevan",
        "skills": [
            ("Python", "advanced"), ("Django", "advanced"), ("REST API", "advanced"),
            ("PostgreSQL", "intermediate"), ("Docker", "intermediate"),
            ("Git", "advanced"), ("Redis", "beginner"),
        ],
        "experience": [
            ("Renderforest", "Python Developer", "Built REST APIs, integrated payment providers.", 2021, 2023),
            ("Synergy Int", "Junior Python Developer", "Developed internal tools in Django.", 2019, 2021),
        ],
        "education": [("YSU", "Bachelor of Science", "Computer Science", 2015, 2019)],
    },
    {
        "email": "nare.hakobian@test.am",
        "full_name": "Nare Hakobian",
        "profession": "Frontend Developer",
        "summary": "Vue.js and React developer focused on performant, accessible UIs.",
        "years_experience": 3,
        "desired_salary": 2000,
        "location": "Yerevan",
        "skills": [
            ("JavaScript", "advanced"), ("Vue", "advanced"), ("TypeScript", "intermediate"),
            ("HTML", "advanced"), ("CSS", "advanced"), ("Tailwind CSS", "intermediate"),
            ("Git", "intermediate"), ("REST API", "intermediate"),
        ],
        "experience": [
            ("Picsart", "Frontend Developer", "Built reusable component library.", 2021, 2024),
            ("Smartclick", "Junior Frontend Developer", "Implemented landing pages.", 2020, 2021),
        ],
        "education": [("NPUA", "Bachelor", "Information Systems", 2016, 2020)],
    },
    {
        "email": "davit.mkhitarian@test.am",
        "full_name": "Davit Mkhitarian",
        "profession": "Full Stack Developer",
        "summary": "Full stack engineer specializing in Python/Django + Vue.",
        "years_experience": 5,
        "desired_salary": 3000,
        "location": "Yerevan",
        "skills": [
            ("Python", "advanced"), ("Django", "advanced"), ("Vue", "advanced"),
            ("JavaScript", "advanced"), ("PostgreSQL", "intermediate"),
            ("Docker", "intermediate"), ("REST API", "advanced"), ("Git", "advanced"),
        ],
        "experience": [
            ("EPAM Systems", "Full Stack Developer", "Delivered full product features.", 2019, 2024),
        ],
        "education": [("AUA", "Bachelor", "Computer Science", 2015, 2019)],
    },
    {
        "email": "liana.sargsyan@test.am",
        "full_name": "Liana Sargsyan",
        "profession": "Data Analyst",
        "summary": "Data analyst with strong SQL and Python skills, expert in BI tools.",
        "years_experience": 3,
        "desired_salary": 1800,
        "location": "Yerevan",
        "skills": [
            ("Python", "intermediate"), ("SQL", "advanced"), ("PostgreSQL", "intermediate"),
            ("Pandas", "intermediate"), ("Tableau", "advanced"), ("Excel", "advanced"),
            ("Git", "beginner"),
        ],
        "experience": [
            ("Insight Analytics", "Data Analyst", "Built KPI dashboards for clients.", 2021, 2024),
            ("ArmSoft", "Junior Analyst", "Supported reporting team.", 2020, 2021),
        ],
        "education": [("YSU", "Bachelor", "Mathematics", 2016, 2020)],
    },
    {
        "email": "tigran.vardanyan@test.am",
        "full_name": "Tigran Vardanyan",
        "profession": "DevOps Engineer",
        "summary": "Cloud infrastructure engineer, AWS certified.",
        "years_experience": 4,
        "desired_salary": 3000,
        "location": "Remote",
        "skills": [
            ("Docker", "advanced"), ("Kubernetes", "advanced"), ("AWS", "advanced"),
            ("CI/CD", "advanced"), ("Linux", "advanced"), ("Terraform", "intermediate"),
            ("Python", "intermediate"), ("Git", "advanced"), ("Bash", "advanced"),
        ],
        "experience": [
            ("CloudSec", "DevOps Engineer", "Managed AWS infrastructure for 10+ clients.", 2020, 2024),
        ],
        "education": [("SEUA", "Bachelor", "Computer Engineering", 2016, 2020)],
    },
    {
        "email": "mariam.abrahamyan@test.am",
        "full_name": "Mariam Abrahamyan",
        "profession": "QA Engineer",
        "summary": "Automation QA with expertise in Python and Selenium.",
        "years_experience": 3,
        "desired_salary": 1600,
        "location": "Yerevan",
        "skills": [
            ("Python", "intermediate"), ("Selenium", "advanced"), ("Pytest", "advanced"),
            ("Git", "intermediate"), ("SQL", "intermediate"), ("Postman", "advanced"),
            ("CI/CD", "beginner"), ("JIRA", "intermediate"),
        ],
        "experience": [
            ("Hexact", "QA Engineer", "Built automated regression suite.", 2021, 2024),
        ],
        "education": [("RAU", "Bachelor", "Software Engineering", 2017, 2021)],
    },
    {
        "email": "hayk.grigoryan@test.am",
        "full_name": "Hayk Grigoryan",
        "profession": "Java Developer",
        "summary": "Java developer experienced in Spring Boot microservices.",
        "years_experience": 4,
        "desired_salary": 2800,
        "location": "Yerevan",
        "skills": [
            ("Java", "advanced"), ("Spring Boot", "advanced"), ("Hibernate", "advanced"),
            ("SQL", "intermediate"), ("PostgreSQL", "intermediate"),
            ("Docker", "intermediate"), ("Git", "advanced"), ("Maven", "intermediate"),
        ],
        "experience": [
            ("DataArt", "Java Developer", "Developed fintech microservices.", 2020, 2024),
        ],
        "education": [("YSU", "Bachelor", "Computer Science", 2016, 2020)],
    },
    {
        "email": "anna.hovhannisyan@test.am",
        "full_name": "Anna Hovhannisyan",
        "profession": "UI/UX Designer",
        "summary": "Product designer with a focus on user research and design systems.",
        "years_experience": 3,
        "desired_salary": 1800,
        "location": "Yerevan",
        "skills": [
            ("Figma", "advanced"), ("Adobe XD", "intermediate"), ("Prototyping", "advanced"),
            ("User Research", "advanced"), ("Wireframing", "advanced"),
            ("CSS", "beginner"), ("Illustrator", "intermediate"),
        ],
        "experience": [
            ("DesignLab", "UI/UX Designer", "Led design for SaaS products.", 2021, 2024),
        ],
        "education": [("NPUA", "Bachelor", "Design", 2017, 2021)],
    },
    {
        "email": "vahan.poghosyan@test.am",
        "full_name": "Vahan Poghosyan",
        "profession": "Product Manager",
        "summary": "PM with strong technical background and Agile experience.",
        "years_experience": 5,
        "desired_salary": 3200,
        "location": "Yerevan",
        "skills": [
            ("Product Management", "advanced"), ("Agile", "advanced"), ("Scrum", "advanced"),
            ("JIRA", "advanced"), ("SQL", "intermediate"), ("Analytics", "intermediate"),
            ("Figma", "beginner"), ("Roadmapping", "advanced"),
        ],
        "experience": [
            ("Krisp", "Product Manager", "Owned core product roadmap.", 2019, 2024),
        ],
        "education": [("AUA", "MBA", "Business Administration", 2017, 2019)],
    },
    {
        "email": "empty.user@test.am",
        "full_name": "Empty User",
        "profession": "",
        "summary": "",
        "years_experience": 0,
        "desired_salary": None,
        "location": "",
        "skills": [],
        "experience": [],
        "education": [],
    },
]


class Command(BaseCommand):
    help = "Seed the database with realistic mock jobs, companies, and test users."

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete all seeded records before recreating them.",
        )

    def handle(self, *args, **options):
        if options["clear"]:
            self._clear()

        with transaction.atomic():
            companies = self._seed_companies()
            self._seed_jobs(companies)
            self._seed_users()

        self.stdout.write(self.style.SUCCESS("\nSeeding complete."))
        self.stdout.write(f"  Companies : {Company.objects.count()}")
        self.stdout.write(f"  Jobs      : {Job.objects.count()}")
        self.stdout.write(f"  Users     : {User.objects.count()}")

    # ── Clear ──────────────────────────────────────────────────────────────────

    def _clear(self):
        self.stdout.write("Clearing seeded data…")
        deleted_jobs, _ = Job.objects.filter(company__name__endswith=SEED_MARKER).delete()
        deleted_cos, _  = Company.objects.filter(name__endswith=SEED_MARKER).delete()
        emails = [u["email"] for u in TEST_USERS]
        deleted_users, _ = User.objects.filter(email__in=emails).delete()
        self.stdout.write(
            f"  Removed {deleted_cos} companies, {deleted_jobs} jobs, {deleted_users} users."
        )

    # ── Companies ─────────────────────────────────────────────────────────────

    def _seed_companies(self):
        self.stdout.write("Seeding companies…")
        created = 0
        companies = []
        for name, industry, location, website in COMPANIES:
            marked_name = f"{name} {SEED_MARKER}"
            obj, new = Company.objects.get_or_create(
                name=marked_name,
                defaults={
                    "industry": industry,
                    "location": location,
                    "website": website,
                    "description": (
                        f"{name} is a leading {industry.lower()} company based in {location}. "
                        f"We build innovative solutions for modern businesses."
                    ),
                },
            )
            companies.append(obj)
            if new:
                created += 1
        self.stdout.write(f"  {created} new companies (total {len(companies)})")
        return companies

    # ── Jobs ──────────────────────────────────────────────────────────────────

    def _seed_jobs(self, companies):
        self.stdout.write("Seeding jobs…")
        created = 0
        job_types = list(JOB_TYPE_WEIGHTS.keys())
        weights   = list(JOB_TYPE_WEIGHTS.values())

        for t_idx, template in enumerate(JOB_TEMPLATES):
            title, category, level, desc, req = template
            skill_pool = SKILL_POOLS[category]
            sal_min_base, sal_max_base = SALARY_BY_LEVEL[level]
            num_variants = self._variants_for_level(level)

            for i in range(num_variants):
                # Deterministic company assignment so reruns are idempotent
                company = companies[(t_idx * 7 + i * 3) % len(companies)]
                job_type = random.choices(job_types, weights=weights, k=1)[0]
                location = self._pick_location(job_type)
                sal_min, sal_max = self._salary(sal_min_base, sal_max_base)
                suffix = f" #{i+1}" if i > 0 else ""
                marked_title = f"{title}{suffix} {SEED_MARKER}"

                job, new = Job.objects.get_or_create(
                    title=marked_title,
                    company=company,
                    defaults={
                        "description": self._expand_desc(desc, company.name, level),
                        "requirements": req,
                        "salary_min": sal_min,
                        "salary_max": sal_max,
                        "location": location,
                        "job_type": job_type,
                    },
                )

                if new:
                    # Attach 3-6 skills from pool
                    num_skills = random.randint(3, min(6, len(skill_pool)))
                    for skill_name in random.sample(skill_pool, num_skills):
                        JobSkill.objects.get_or_create(job=job, skill_name=skill_name)
                    created += 1

        # ── Edge-case jobs ────────────────────────────────────────────────────
        self._seed_edge_cases(companies)

        self.stdout.write(f"  {created} new jobs created")

    def _variants_for_level(self, level):
        """More mid/senior roles to make matching richer."""
        return {"intern": 1, "junior": 2, "mid": 3, "senior": 3}[level]

    def _pick_location(self, job_type):
        if job_type == "remote":
            return random.choice(["Remote", "Remote (Armenia)", "Remote (EU)", "Remote (Worldwide)"])
        if job_type == "hybrid":
            return random.choice(["Yerevan (Hybrid)", "Gyumri (Hybrid)", "Vanadzor (Hybrid)"])
        return random.choice(["Yerevan", "Gyumri", "Vanadzor"])

    def _salary(self, low, high):
        sal_min = random.randrange(low, high, 100)
        sal_max = sal_min + random.choice([300, 500, 700, 1000, 1500])
        return sal_min, min(sal_max, 7000)

    def _expand_desc(self, snippet, company_name, level):
        level_str = {
            "intern": "internship", "junior": "junior", "mid": "mid-level", "senior": "senior"
        }[level]
        return (
            f"We are looking for a passionate {level_str} professional to join our team at "
            f"{company_name}.\n\n{snippet}\n\n"
            "What we offer:\n"
            "• Competitive salary and performance bonuses\n"
            "• Flexible work schedule\n"
            "• Professional development budget\n"
            "• Health insurance\n"
            "• Friendly and collaborative team culture"
        )

    def _seed_edge_cases(self, companies):
        """Jobs specifically designed to test edge cases."""
        company = companies[-1]  # always last company — deterministic

        edge_cases = [
            # (title, salary_min, salary_max, job_type, location, skills)
            # Very low salary (intern-level edge)
            ("Unpaid Intern Backend [EDGE] " + SEED_MARKER, 0, 0, "onsite", "Yerevan",
             ["Python", "Git"]),
            # Very high salary
            ("Principal Engineer (Staff) [EDGE] " + SEED_MARKER, 6000, 10000, "remote", "Remote",
             ["Python", "Kubernetes", "AWS", "Architecture", "Leadership"]),
            # Missing optional fields (no salary, no location)
            ("Mystery Developer [EDGE] " + SEED_MARKER, None, None, "onsite", "",
             ["Python"]),
            # Remote in different country
            ("Backend Engineer (Berlin) [EDGE] " + SEED_MARKER, 4000, 6000, "remote", "Berlin (Remote)",
             ["Python", "Django", "Docker", "PostgreSQL"]),
            # Duplicate-like title but different requirements
            ("Python Developer (Finance) [EDGE] " + SEED_MARKER, 2000, 3500, "onsite", "Yerevan",
             ["Python", "SQL", "Excel", "Bloomberg API", "REST API"]),
            ("Python Developer (Healthcare) [EDGE] " + SEED_MARKER, 2000, 3500, "hybrid", "Yerevan (Hybrid)",
             ["Python", "Django", "HIPAA", "PostgreSQL", "Docker"]),
            # Very strong match for Ara (Python/Django)
            ("Python Django Expert Needed [EDGE] " + SEED_MARKER, 2000, 3500, "remote", "Remote",
             ["Python", "Django", "REST API", "PostgreSQL", "Docker", "Redis", "Git"]),
            # Very weak match for Ara (completely unrelated)
            ("Mechanical Design Engineer [EDGE] " + SEED_MARKER, 1500, 2500, "onsite", "Yerevan",
             ["AutoCAD", "SolidWorks", "Mechanical Engineering", "CATIA"]),
            # High salary, no skills listed
            ("Stealth Mode CTO [EDGE] " + SEED_MARKER, 5000, 8000, "remote", "Remote (Worldwide)",
             []),
        ]

        for title, sal_min, sal_max, jtype, loc, skills in edge_cases:
            job, new = Job.objects.get_or_create(
                title=title,
                company=company,
                defaults={
                    "description": "Edge case job for testing purposes.",
                    "requirements": "",
                    "salary_min": sal_min,
                    "salary_max": sal_max,
                    "location": loc,
                    "job_type": jtype,
                },
            )
            if new and skills:
                for s in skills:
                    JobSkill.objects.get_or_create(job=job, skill_name=s)

    # ── Users ─────────────────────────────────────────────────────────────────

    def _seed_users(self):
        self.stdout.write("Seeding test users…")
        created = 0

        for data in TEST_USERS:
            user, new = User.objects.get_or_create(
                email=data["email"],
                defaults={"full_name": data["full_name"]},
            )
            if new:
                user.set_password("testpass123")
                user.save()
                created += 1

            # Profile (upsert)
            Profile.objects.update_or_create(
                user=user,
                defaults={
                    "profession": data["profession"],
                    "summary": data["summary"],
                    "years_experience": data["years_experience"],
                    "desired_salary": data["desired_salary"],
                    "location": data["location"],
                },
            )

            # Skills (add missing, skip existing)
            existing = set(user.skills.values_list("skill_name", flat=True))
            for skill_name, level in data["skills"]:
                if skill_name not in existing:
                    UserSkill.objects.create(user=user, skill_name=skill_name, skill_level=level)

            # Experience
            if not user.experience.exists():
                for company, position, desc, start_y, end_y in data["experience"]:
                    UserExperience.objects.create(
                        user=user,
                        company=company,
                        position=position,
                        description=desc,
                        start_date=date(start_y, 1, 1),
                        end_date=date(end_y, 6, 1) if end_y else None,
                    )

            # Education
            if not user.education.exists():
                for inst, degree, field, start_y, end_y in data["education"]:
                    UserEducation.objects.create(
                        user=user,
                        institution=inst,
                        degree=degree,
                        field_of_study=field,
                        start_date=date(start_y, 9, 1),
                        end_date=date(end_y, 6, 1),
                    )

        self.stdout.write(f"  {created} new users (total {len(TEST_USERS)})")
        self.stdout.write("  Password for all test users: testpass123")
