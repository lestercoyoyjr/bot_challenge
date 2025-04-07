# Development Setup and Guidelines

This document provides instructions for setting up a development environment and guidelines for contributing to the Survey Chatbot project.
Development Environment Setup
Prerequisites

Python 3.10 or later
Poetry (for dependency management)
Git

Installation Steps

Clone the repository

bashCopygit clone <repository-url>
cd survey-chatbot

Install dependencies using Poetry

Poetry is used for dependency management to ensure consistent environments.
bashCopy# Install Poetry if you don't have it
curl -sSL https://install.python-poetry.org | python3 -

# Install project dependencies

poetry install

Activate the virtual environment

bashCopypoetry shell

Run the development server

bashCopyuvicorn app.main:app --reload --host 0.0.0.0 --port 8000
The --reload flag enables auto-reloading when code changes are detected, making development more efficient.
