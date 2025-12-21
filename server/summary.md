## How to Generate and Submit HTML Branch Coverage Report

```bash
cd server
```


### Set Test Mode and Run Tests with Coverage

```bash
# On Linux/Mac:

export TEST_MODE=1
python -m pytest --cov=src --cov-report=html --cov-branch -v test/test_watermark_endpoints.py test/test_watermark_endpoints_additional.py

# On Windows (Command Prompt):
set TEST_MODE=1
python -m pytest --cov=src --cov-report=html --cov-branch -v test/test_watermark_endpoints.py test/test_watermark_endpoints_additional.py

# On Windows (PowerShell):
$env:TEST_MODE="1"
python -m pytest --cov=src --cov-report=html --cov-branch -v test/test_watermark_endpoints.py test/test_watermark_endpoints_additional.py

```

### Run the complete test suite with coverage and Mock DB
```bash
$env:TEST_MODE="1"; python -m pytest --cov=src --cov-report=html --cov-report=term
```

### To find missing lines
```bash
 python -m coverage report --show-missing --include="src/server.py"
 ```  

## Verify the HTML Report Was Generated

### On Linux/Mac:
ls -la htmlcov/

### On Windows:
dir htmlcov

## Quick Preview

### On Mac:
open htmlcov/index.html

### On Linux:
xdg-open htmlcov/index.html

### On Windows:
start htmlcov/index.html