PYTHON ?= python3

.PHONY: test reference microarch coverage rtl rtl-coverage rtl-code-coverage rtl-perf lint synth asic formal ci clean

test:
	$(PYTHON) scripts/run_all_checks.py

reference:
	$(PYTHON) scripts/gen_directed_tests.py
	$(PYTHON) scripts/run_reference_regression.py

microarch:
	$(PYTHON) scripts/run_microarchitecture_regression.py

coverage:
	$(PYTHON) scripts/reference_functional_coverage.py

ci:
	REQUIRE_EDA=1 $(PYTHON) scripts/run_all_checks.py

rtl:
	$(PYTHON) scripts/run_rtl_regression.py

rtl-coverage:
	$(PYTHON) scripts/analyze_rtl_coverage.py

rtl-code-coverage:
	$(PYTHON) scripts/run_verilator_code_coverage.py

rtl-perf:
	$(PYTHON) scripts/run_rtl_performance_compare.py

lint:
	$(PYTHON) scripts/run_lint.py

synth:
	$(PYTHON) scripts/run_synthesis.py

asic:
	$(PYTHON) scripts/run_asic_timing.py

formal:
	$(PYTHON) scripts/run_formal.py

clean:
	rm -f sim/*.vvp sim/*.vcd
