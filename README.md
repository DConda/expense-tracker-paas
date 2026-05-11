# Daily Expense Tracker API

This is a simple Flask web application deployed on a PaaS platform.

## Features

- Add daily expenses
- View all expenses
- View expense summary
- Health check endpoint

## Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | / | Homepage |
| GET | /health | Health check |
| GET | /expenses | Get all expenses |
| POST | /expenses | Add expense |
| GET | /summary | Expense summary |

## Technology

- Python
- Flask
- Flask-SQLAlchemy
- PostgreSQL
- Railway
- Gunicorn