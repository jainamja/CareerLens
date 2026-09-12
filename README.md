# CareerLens

**Resume & Job Intelligence Platform**

CareerLens is a modern career-tech SaaS application that analyzes resumes against job descriptions to provide skill coverage and text similarity metrics.

## Tech Stack
* Python
* Django & Django REST Framework
* PostgreSQL (production) & SQLite (local fallback)
* Vanilla JS & Bootstrap
* PyMuPDF (PDF extraction)
* scikit-learn (TF-IDF similarity)
* spaCy (NLP/skill extraction)

## Local Setup

1. **Clone and setup virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   ```

2. **Install requirements**
   ```bash
   pip install -r requirements/dev.txt
   ```

3. **Environment Setup**
   ```bash
   cp .env.example .env
   ```
   Update `.env` as necessary.

4. **Run migrations and start server**
   ```bash
   python manage.py migrate
   python manage.py runserver
   ```
