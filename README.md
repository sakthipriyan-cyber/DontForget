# Don'tForget – Smart Departure Assistant

A Python-based smart departure assistant designed to help users organize daily tasks, manage reminders, and prepare for upcoming activities.

## Features

- **Checklist:** Create and manage daily tasks.
- **Smart Insights:** View insights based on task activity.
- **Departure Reminders:** Manage reminders for planned departures.
- **History:** Review previous activity.
- **Settings:** Customize application settings.
- **Web Interface:** Access features through a Flask-based web application.

## Technologies Used

- Python
- Flask
- SQLite
- HTML
- CSS
- JavaScript
- Pytest

## Project Structure

```text
DontForget/
├── core/
├── tests/
├── web/
│   ├── static/
│   ├── templates/
│   ├── app.py
│   ├── database.py
│   └── migration.py
├── gui.py
├── main.py
├── run_web.py
├── test_dontforget.py
└── README.md
```

## Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/sakthipriyan-cyber/DontForget.git
cd DontForget
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

### 3. Activate the virtual environment

**Windows PowerShell:**

```powershell
.venv\Scripts\Activate.ps1
```

### 4. Install dependencies

Install the project's required Python packages. Add a `requirements.txt` file if one is not already available.

### 5. Run the application

```bash
python run_web.py
```

Open your browser and visit:

```text
http://127.0.0.1:5000
```

## Running Tests

```bash
pytest
```

## Project Status

The web application has been developed, and core functionality and tests have been implemented. Further improvements and hardware integration may be added in future versions.

## Author

**Sakthi Priyan**

GitHub: https://github.com/sakthipriyan-cyber