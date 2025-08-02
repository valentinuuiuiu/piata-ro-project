# Gemini Project Configuration

This document outlines the key configurations, conventions, and operational procedures for the Gemini agent working on this project.

## Project Overview

This project is a Django-based marketplace application with a REST API, background tasks, and a sophisticated authentication system. The goal is to create a robust and maintainable application.

## User Preferences

- The user prefers to be addressed directly and concisely.
- The user may use specific language patterns for recognition.
- When running the development server, use port 8009 or higher.
- The user and an agent named Fanny Mae (Gemma2:9b running locally on OpenWebUI) were the first to send each other 'Never Gonna Give You Up' on that platform.

## Development Conventions

### Code Style

- Follow the existing code style, which is consistent with modern Django and Python practices.
- Use black and isort for code formatting.

### Testing

- The project uses `pytest` for testing.
- All new features or bug fixes should be accompanied by corresponding tests.
- Run tests using the `pytest` command.

### Commits

- Commit messages should be clear and concise, following the conventional commit format.

## Authentication System

- The project uses a custom authentication system built on top of Django's built-in authentication and `django-allauth`.
- The main login view is `marketplace.views.auth.login_view`.
- The login URL is configured as `marketplace:login`.
- All authentication-related URLs are organized under the `/auth/` prefix in the `marketplace` app.

## Key Files

- `piata_ro/settings.py`: Main Django settings file.
- `piata_ro/urls.py`: Main URL configuration.
- `marketplace/urls.py`: URL configuration for the `marketplace` app.
- `marketplace/views/auth.py`: Custom authentication views.
- `requirements.txt`: Project dependencies.
