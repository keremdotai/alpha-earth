# Alpha-Earth

## 1. Installation Guide

This project uses **uv** as the package manager and **Python 3.11**.

### 1.1. Prerequisites

1. **Install uv (if not already installed)**:

    ```bash
    # On macOS/Linux
    curl -LsSf https://astral.sh/uv/install.sh | sh

    # On Windows
    powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
    ```

2. **Install Python 3.11**:

   ```bash
   # Using uv to install Python 3.11
   uv python install 3.11

   # Check installed Python versions
   uv python list
   ```

### 1.2. Project Setup

1. **Clone the repository**:

    ```bash
    git clone https://github.com/keremdotai/alpha-earth
    cd alpha-earth
    ```

2. **Create virtual environment with Python 3.11**:

    ```bash
    uv venv --python 3.11
    ```

3. **Activate the virtual environment**:

    ```bash
    # On macOS/Linux
    source .venv/bin/activate

    # On Windows
    .venv\Scripts\activate
    ```

4. **Install dependencies**:

    ```bash
    uv pip install -r install/requirements.txt

    # Install development packages
    uv pip install -r install/requirements-dev.txt
    ```

5. **Verify installation**:

    ```bash
    python --version  # Should show Python 3.11
    uv --version      # Should show uv version
    ```

### 1.3. Pre-commit Hooks

This project uses pre-commit hooks to ensure code quality and consistency.
Pre-commit hooks run automatically before each commit to check your code for issues.

1. **Install pre-commit along with other development packages (if not already installed)**:

   ```bash
   uv pip install -r install/requirements-dev.txt
   ```

2. **Install the pre-commit hooks**:

   ```bash
   pre-commit install
   ```

3. **Run pre-commit on all files** (optional, for initial setup):

   ```bash
   pre-commit run --all-files
   ```

4. **Manual pre-commit run** (useful for testing):

   ```bash
   pre-commit run
   ```

The pre-commit configuration includes:

- **Code formatting**: Automatic code formatting with black and isort.
- **Linting**: Code quality checks with flake8.
- **Import sorting**: Automatic import organization.
- **File validation**: Checks for common issues like trailing whitespace.
