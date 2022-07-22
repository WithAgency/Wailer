PYTHON_BIN ?= poetry run python

format: isort black

black:
	$(PYTHON_BIN) -m black --target-version py38 --exclude '/(\.git|\.hg|\.mypy_cache|\.nox|\.tox|\.venv|_build|buck-out|build|dist|node_modules|webpack_bundles)/' src

isort:
	$(PYTHON_BIN) -m isort src

celery_worker:
	$(PYTHON_BIN) -m celery -A kourse.django.celery:app worker -l DEBUG

celery_beat:
	$(PYTHON_BIN) -m celery -A kourse.django.celery:app beat -l DEBUG
