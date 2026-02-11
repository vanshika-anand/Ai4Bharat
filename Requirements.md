# MemoryThread: Python Dependencies

## Core Dependencies

```
# Web Framework
Flask==3.0.0
Flask-CORS==4.0.0

# Database
SQLAlchemy==2.0.23

# Authentication & Security
PyJWT==2.8.0
bcrypt==4.1.2

# AI & ML
openai==1.6.1
numpy==1.26.2

# Environment Management
python-dotenv==1.0.0

# HTTP Requests
requests==2.31.0

# Date/Time Utilities
python-dateutil==2.8.2
```

## Development Dependencies

```
# Testing
pytest==7.4.3
pytest-flask==1.3.0
pytest-cov==4.1.0

# Code Quality
flake8==6.1.0
black==23.12.1

# Type Checking
mypy==1.7.1
```

## Installation

```bash
pip install -r requirements.txt
```

## Python Version

- Python 3.9 or higher required
- Recommended: Python 3.11

## Notes

- All dependencies use stable, production-ready versions
- OpenAI SDK version supports latest embedding and chat models
- Flask chosen for simplicity and rapid development
- SQLAlchemy provides database abstraction for easy migration
