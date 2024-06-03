# MSSP multitenant new design

## Installation

Python Environment Setup

```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Redis Setup

```
sudo apt-get install redis-server
redis-server
```

## Usage

To start the server, run the following command:

```bash
uvicorn app.main:myapp --reload
```

## Format code

```bash
black --line-length 120 .
isort --gitignore .
```

## Testing

```
pytest app/tests/test_mssp_operator.py
pytest app/tests/test_task.py
```
