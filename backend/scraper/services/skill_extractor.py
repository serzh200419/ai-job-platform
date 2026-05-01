"""
Keyword-based skill extractor.
No external NLP library required — pure Python set membership.
"""
import re

# Canonical skill names (display form). Matching is case-insensitive.
KNOWN_SKILLS: set[str] = {
    # Languages
    "Python", "JavaScript", "TypeScript", "Java", "Kotlin", "Swift",
    "Go", "Golang", "Rust", "C", "C++", "C#", "PHP", "Ruby", "Scala",
    "R", "Perl", "Dart", "Elixir", "Haskell", "Lua", "MATLAB",

    # Web / Frontend
    "HTML", "CSS", "React", "Vue", "Angular", "Next.js", "Nuxt.js",
    "Svelte", "jQuery", "Bootstrap", "Tailwind", "Tailwind CSS",
    "SASS", "SCSS", "Redux", "GraphQL", "REST", "REST API",

    # Backend / Frameworks
    "Django", "Flask", "FastAPI", "Node.js", "Express", "Spring",
    "Spring Boot", "Laravel", "Rails", "Ruby on Rails", "ASP.NET",
    ".NET", "Gin", "Echo",

    # Databases
    "SQL", "PostgreSQL", "MySQL", "SQLite", "MongoDB", "Redis",
    "Elasticsearch", "Cassandra", "DynamoDB", "Oracle", "MSSQL",
    "MariaDB", "Firebase", "Firestore", "Supabase",

    # DevOps / Cloud
    "Docker", "Kubernetes", "AWS", "GCP", "Azure", "Terraform",
    "Ansible", "Jenkins", "GitHub Actions", "GitLab CI", "CI/CD",
    "Linux", "Nginx", "Apache", "Bash", "Shell", "PowerShell",
    "Helm", "ArgoCD",

    # Data / ML / AI
    "Machine Learning", "Deep Learning", "NLP", "Computer Vision",
    "TensorFlow", "PyTorch", "Keras", "scikit-learn", "Pandas",
    "NumPy", "Spark", "Hadoop", "Kafka", "Airflow", "dbt",
    "Tableau", "Power BI", "Data Analysis", "ETL",

    # Mobile
    "Android", "iOS", "React Native", "Flutter", "Xamarin",

    # Tools & Practices
    "Git", "GitHub", "GitLab", "JIRA", "Confluence", "Figma",
    "Postman", "Swagger", "OpenAPI", "Agile", "Scrum", "TDD",
    "Unit Testing", "Selenium", "Cypress", "Jest", "Pytest",

    # Networking / Security
    "TCP/IP", "HTTP", "gRPC", "OAuth", "JWT", "SSL/TLS",
    "Cybersecurity", "Penetration Testing",
}

# Pre-build a lowercase → canonical map for fast lookup
_SKILL_MAP: dict[str, str] = {s.lower(): s for s in KNOWN_SKILLS}

# Pattern splits text on whitespace and common punctuation
_SPLIT_RE = re.compile(r"[\s,;/|•\-–()[\]]+")


def extract_skills(text: str) -> list[str]:
    """
    Return a deduplicated list of canonical skill names found in text.
    Preserves insertion order (first occurrence wins).
    """
    if not text:
        return []

    found: dict[str, None] = {}  # ordered set via dict

    words = _SPLIT_RE.split(text)
    # Check single tokens and two-word phrases
    for i, word in enumerate(words):
        w = word.lower().strip(".")
        if w in _SKILL_MAP:
            found[_SKILL_MAP[w]] = None
        # Two-word phrase (e.g. "machine learning", "react native")
        if i + 1 < len(words):
            phrase = (w + " " + words[i + 1].lower().strip("."))
            if phrase in _SKILL_MAP:
                found[_SKILL_MAP[phrase]] = None

    return list(found.keys())
