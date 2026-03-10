# 🔐 TEACHVERSE Auth

**Production-ready authentication & hierarchical authorization (RBAC/IAM) for FastAPI microservices.**

[![PyPI version](https://badge.fury.io/py/teachverse-auth.svg)](https://badge.fury.io/py/teachverse-auth)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## ✨ Why TeachVerse Auth?
TeachVerse Auth moves beyond basic CRUD authentication. It implements an **Hierarchical granular permission system** that allows your microservices to manage complex, multi-tenant hierarchies with zero boilerplate.

## 🚀 Quick Start
```bash
pip install teachverse-auth
teachverse-auth setup   # Interactive wizard to create .env
teachverse-auth migrate # Initialize DB
teachverse-auth runserver