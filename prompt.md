Role: Senior DevOps & Python Architect (always write Chinese frontend and respond in Chinese)
Project Name: SmartHome-Mock-AI

Objective: Initialize a Python project for an LLM-controlled home automation system. 
Constraint: Since I do not have physical hardware, we are building a "Simulation First" architecture.

Task 1: Project Setup & CI/CD
1. Initialize a git repository in the current directory.
2. Set up the project structure using `poetry` or standard `pip` with a `src/` and `tests/` layout.
3. Create a `.github/workflows/ci.yml` file immediately. This workflow must:
   - Run on `push` and `pull_request`.
   - Install Python 3.10+.
   - Install dependencies.
   - Run `ruff` or `flake8` for linting (Enforce strict standards).
   - Run `pytest` for testing.
4. Create a `README.md` explaining the architecture (LLM -> Intent Parser -> Virtual Device Manager).
5. Push this initial setup to a new GitHub repository named 'smarthome-mock-ai'.

Note: Do not write the application logic yet. I want to see the CI/CD pipeline pass with a dummy test first.
