PYTHON ?= python

.PHONY: makemigrations migrate

makemigrations:
	$(PYTHON) manage.py makemigrations


migrate:
	$(PYTHON) manage.py migrate

