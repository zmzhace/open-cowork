# Contributing to Open-Cowork

Thank you for your interest in contributing to Open-Cowork! This document provides guidelines and instructions for contributing.

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help others learn and grow

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/open-cowork.git`
3. Create a branch: `git checkout -b feature/your-feature-name`
4. Make your changes
5. Run tests: `cd backend && PYTHONPATH=. pytest tests/ -v`
6. Commit your changes following our commit convention
7. Push to your fork: `git push origin feature/your-feature-name`
8. Open a Pull Request

## Commit Convention

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

### Examples
```
feat(llm): add support for Gemini API

Add GeminiProvider class that implements the LLMProvider interface.
Includes tests and documentation.

Closes #123
```

```
fix(tools): handle file not found error in FileReadTool

Previously would crash when file doesn't exist. Now returns
a proper error message.
```

## Development Workflow

### Backend Development

1. Set up virtual environment:
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. Run tests:
```bash
PYTHONPATH=. pytest tests/ -v
```

3. Run with auto-reload:
```bash
uvicorn src.main:app --reload
```

### Frontend Development

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Run dev server:
```bash
npm run dev
```

3. Run Electron:
```bash
npm start
```

## Testing Guidelines

- Write tests for all new features
- Maintain test coverage above 80%
- Use descriptive test names
- Follow TDD when possible

### Test Structure
```python
def test_feature_name():
    """Test description"""
    # Arrange
    setup_code()

    # Act
    result = function_to_test()

    # Assert
    assert result == expected_value
```

## Code Style

### Python
- Follow PEP 8
- Use type hints
- Maximum line length: 100 characters
- Use descriptive variable names

### JavaScript/React
- Use ES6+ features
- Functional components with hooks
- Use meaningful component names
- Keep components small and focused

## Pull Request Process

1. Update documentation if needed
2. Add tests for new features
3. Ensure all tests pass
4. Update CHANGELOG.md
5. Request review from maintainers

### PR Title Format
```
<type>: <description>
```

Example: `feat: add Gemini LLM provider`

## Questions?

Feel free to open an issue for:
- Bug reports
- Feature requests
- Questions about the codebase
- Suggestions for improvements

Thank you for contributing! 🎉
