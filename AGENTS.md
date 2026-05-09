# AGENTS.md

## Project Overview
This repository contains a retail checkout service prototype.

## Coding Standards
- Use clear variable names
- Keep functions small and readable
- Add tests for new functionality
- Avoid logging sensitive customer information

## Security Rules
- Never expose customer email addresses in logs
- Never hardcode secrets
- Flag insecure payment flows

## Review Expectations
When reviewing pull requests:
- Check for missing tests
- Check for PII exposure
- Check for maintainability
- Check for security concerns

## Commands
Run server:
python3 -m uvicorn app.main:app --reload

Run tests:
pytest

Run linting:
ruff check .
