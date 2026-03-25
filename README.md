# Hangarin Task Management App

A modern, professional Django-based task management dashboard with advanced UI components and social authentication.

## 🚀 Getting Started

Follow these steps to set up and run the project locally.

### 1. Prerequisites
- Python 3.10+
- pip (Python package manager)
- venv (Python virtual environment)

### 2. Setup Virtual Environment
Create and activate a virtual environment to manage dependencies:

```powershell
# Windows
python -m venv venv
.\venv\Scripts\Activate
```

### 3. Install Dependencies
Install the required Python packages:

```powershell
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy the example environment file and update it with your settings:

```powershell
copy .env.example .env
```
_Edit `.env` and set `DJANGO_SECRET_KEY` and other credentials if needed._

### 5. Initialize Database
Run migrations to set up the SQLite database:

```powershell
python manage.py migrate
```

### 6. Seed Demo Data (Optional)
To quickly populate the dashboard with test data, run the custom seeding command:

```powershell
python manage.py seed_hangarin --tasks 10
```

### 7. Create Superuser (Admin Access)
To access the Django Unfold admin panel (`/admin/`):

```powershell
python manage.py createsuperuser
```

### 8. Run the Development Server
Start the local server:

```powershell
python manage.py runserver
```
Visit `http://127.0.0.1:8000/` in your browser.

## 🛠️ Tech Stack
- **Framework**: Django 6.0
- **Admin UI**: Django Unfold
- **Authentication**: Django Allauth (Google/GitHub Support)
- **Database**: SQLite3
- **Styling**: Vanilla CSS (Modern, Responsive)

## 🧪 Running Tests
To run the included unit tests:

```powershell
python manage.py test
```
