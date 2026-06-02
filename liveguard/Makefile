.PHONY: all models assemble docx clean

PY ?= python
MODELS_DIR = models/python_models
BUILD_DIR = bp_build

models:
	cd $(MODELS_DIR) && $(PY) run_all.py

assemble:
	$(PY) $(BUILD_DIR)/assemble_md.py

docx: assemble
	$(PY) $(BUILD_DIR)/render_docx.py

all: models assemble docx

clean:
	rm -rf $(MODELS_DIR)/outputs
	rm -f docs/images/charts/*.png
	rm -f ../守播LiveGuard_商业计划书_v4.0.docx ../守播LiveGuard_商业计划书_v4.0.md
