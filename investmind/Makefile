.PHONY: all models docx pdf clean

PY ?= python3
MODELS_DIR = models/python_models
BUILD_DIR = build

models:
	cd $(MODELS_DIR) && \
	for f in 01_*.py 02_*.py 03_*.py 04_*.py 05_*.py 06_*.py 07_*.py 08_*.py 09_*.py 10_*.py 11_*.py 12_*.py; do \
	    echo "── Running $$f ──" ; \
	    $(PY) "$$f" || exit 1 ; \
	done

docx:
	$(PY) $(BUILD_DIR)/render_docx.py

pdf:
	$(PY) $(BUILD_DIR)/render_pdf.py

all: models docx pdf

clean:
	rm -rf $(MODELS_DIR)/outputs
	rm -f docs/images/charts/*.png
	rm -f investmind_business_plan.docx investmind_business_plan.pdf
