PYTHON ?= python
ARGS ?=
COLLECTION ?= ikans
CUSTOM_TYPE ?=

.PHONY: makemigrations migrate serve sync-content tests

makemigrations:
	$(PYTHON) manage.py makemigrations


migrate:
	$(PYTHON) manage.py migrate

serve:
	$(PYTHON) manage.py runserver

sync-content:
	$(PYTHON) manage.py sync_content --collection=$(COLLECTION) $(if $(CUSTOM_TYPE),--custom-type=$(CUSTOM_TYPE),) $(ARGS)

tests:
	$(PYTHON) manage.py test
