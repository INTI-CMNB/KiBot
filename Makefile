#!/usr/bin/make
PY_COV?=python3-coverage
PYTEST?=pytest-3
REFDIR=tests/reference/5_1_7/
REFILL=tests/board_samples/zone-refill.kicad_pcb
CWD := $(abspath $(patsubst %/,%,$(dir $(abspath $(lastword $(MAKEFILE_LIST))))))
USER_ID=$(shell id -u)
GROUP_ID=$(shell id -g)

ifneq ("$(wildcard *.yaml)","")
$(error Move away any config file)
endif

ifneq ("$(wildcard *.sch)","")
$(error Move away any schematic file)
endif

ifneq ("$(wildcard tests/board_samples/bom.xml-bak*)","")
$(error Revert tests/board_samples/bom.xml-bak)
endif

deb:
	DEB_BUILD_OPTIONS=nocheck fakeroot dpkg-buildpackage -uc -b

deb_sig:
	DEB_BUILD_OPTIONS=nocheck fakeroot dpkg-buildpackage -b

lint: doc
	# flake8 --filename is broken
	ln -sf src/kiplot kiplot.py
	ln -sf src/kibot kibot.py
	# stop the build if there are Python syntax errors or undefined names
	flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	pre-commit run -a
	rm kiplot.py
	rm kibot.py

test_tmp: lint
	$(PY_COV) erase
	$(PYTEST)
	$(PY_COV) combine
	$(PY_COV) report

# lint
test:
	rm -rf output .cache
	rm -f example.kiplot.yaml
	rm -f example.kibot.yaml
	rm -f tests/.local
	$(PY_COV) erase
	# python3-pytest-xdist
	$(PYTEST) -m "not slow" -n 4 --test_dir=output
	$(PYTEST) -m "slow and (not indep)" --test_dir=output
	$(PYTEST) -m "slow and indep" --test_dir=output
	$(PY_COV) combine
	$(PY_COV) report
	$(PY_COV) html
	x-www-browser htmlcov/index.html

test1:
	rm -rf output
	rm -f example.kiplot.yaml
	rm -f example.kibot.yaml
	rm -f tests/.local
	$(PY_COV) erase
	$(PYTEST) --log-cli-level debug -k "test_bom_ok" --test_dir=output
	$(PY_COV) combine
	$(PY_COV) report
	$(PY_COV) html
	#x-www-browser htmlcov/index.html
	@echo "********************" Output
	@cat output/*/output.txt
	#@echo "********************" Error
	#@cat output/*/error.txt

t1k5: test_docker_local_1

test_docker_local_1:
	-rm -rf output
	-rm -f tests/.local
	$(PY_COV) erase
	# Run in the same directory to make the __pycache__ valid
	# Also change the owner of the files to the current user (we run as root like in GitHub)
	#docker run --rm -it -v $(CWD):$(CWD) --workdir="$(CWD)" setsoft/kicad_auto_test:latest '/bin/bash'
	docker run --rm -v $(CWD):$(CWD) --workdir="$(CWD)" ghcr.io/inti-cmnb/kicad_auto_test:ki5  \
		/bin/bash -c "flake8 . --count --statistics ; python3-coverage run -a src/kibot --help-outputs > /dev/null; pytest-3 --log-cli-level debug -k '$(SINGLE_TEST)' --test_dir=output ; $(PY_COV) html; chown -R $(USER_ID):$(GROUP_ID) output/ tests/ .coverage.* htmlcov/ .cache"
	#$(PY_COV) report
	#x-www-browser htmlcov/index.html
	# The coverage used in the image is incompatible
	#$(PY_COV) erase

test_docker_local_1_ki6:
	rm -rf output
	rm -f tests/.local
	#$(PY_COV) erase
	# Run in the same directory to make the __pycache__ valid
	# Also change the owner of the files to the current user (we run as root like in GitHub)
	docker run --rm -v $(CWD):$(CWD) --workdir="$(CWD)" ghcr.io/inti-cmnb/kicad_auto_test:ki6 \
		/bin/bash -c "flake8 . --count --statistics ; python3-coverage run src/kibot --help-outputs > /dev/null; pytest-3 --log-cli-level debug -k '$(SINGLE_TEST)' --test_dir=output ; $(PY_COV) html; chown -R $(USER_ID):$(GROUP_ID) output/ tests/ .coverage.* htmlcov/ .cache"
#	docker run --rm -it -v $(CWD):$(CWD) --workdir="$(CWD)" ghcr.io/inti-cmnb/kicad6_auto_full:latest
	#$(PY_COV) report
	#x-www-browser htmlcov/index.html
#	docker run --rm -v $(CWD):$(CWD) --workdir="$(CWD)" ghcr.io/inti-cmnb/kicad6_auto_full:latest \

test_docker_local_1_ki8:
	rm -rf output
	rm -f tests/.local
	docker run --rm -v $(CWD):$(CWD) --workdir="$(CWD)" ghcr.io/inti-cmnb/kicad_auto_test:ki8 \
		/bin/bash -c "flake8 . --count --statistics ; python3-coverage run src/kibot --help-outputs > /dev/null; pytest-3 --log-cli-level debug -k '$(SINGLE_TEST)' --test_dir=output ; $(PY_COV) html; chown -R $(USER_ID):$(GROUP_ID) output/ tests/ .coverage.* htmlcov/ .cache"

test_docker_local_1_ki10:
	rm -rf output
	rm -f tests/.local
	# Run in the same directory to make the __pycache__ valid
	# Also change the owner of the files to the current user (we run as root like in GitHub)
	docker run --rm -v $(CWD):$(CWD) --workdir="$(CWD)" ghcr.io/inti-cmnb/kicad_auto_test:ki10 \
		/bin/bash -c "flake8 . --count --statistics ; python3-coverage run src/kibot --help-outputs > /dev/null; pytest-3 --log-cli-level debug -k '$(SINGLE_TEST)' --test_dir=output ; $(PY_COV) html; chown -R $(USER_ID):$(GROUP_ID) output/ tests/ .coverage.* htmlcov/ .cache"

test_docker_local_1_ki7:
	rm -rf output
	rm -f tests/.local
	docker run --rm -v $(CWD):$(CWD) --workdir="$(CWD)" ghcr.io/inti-cmnb/kicad_auto_test:ki7 \
		/bin/bash -c "python3-coverage run src/kibot --help-outputs > /dev/null; pytest-3 --log-cli-level debug -k '$(SINGLE_TEST)' --test_dir=output ; $(PY_COV) html; chown -R $(USER_ID):$(GROUP_ID) output/ tests/ .coverage.* htmlcov/ .cache"

t1k7: test_docker_local_1_ki7

test_docker_local_1_ki9:
	rm -rf output
	rm -f tests/.local
	docker run --rm -v $(CWD):$(CWD) --workdir="$(CWD)" ghcr.io/inti-cmnb/kicad_auto_test:ki9 \
		/bin/bash -c "python3-coverage run src/kibot --help-outputs > /dev/null; pytest-3 --log-cli-level debug -k '$(SINGLE_TEST)' --test_dir=output ; $(PY_COV) html; chown -R $(USER_ID):$(GROUP_ID) output/ tests/ .coverage.* htmlcov/ .cache"

t1k9: single_test

# pip3 uninstall -y kiauto ; dpkg -i kiauto_2.2.5-1_all.deb ;
test_docker_local_1_n:
	rm -rf output
	rm -f tests/.local
	docker run --rm -v $(CWD):$(CWD) --workdir="$(CWD)" ghcr.io/inti-cmnb/kicad_auto_test:nightly \
		/bin/bash -c "src/kibot --help-outputs > /dev/null ; pytest-3 --log-cli-level debug -k '$(SINGLE_TEST)' --test_dir=output ; chown -R $(USER_ID):$(GROUP_ID) output/ tests/ .coverage.* htmlcov/ .cache"

test_docker_local_1_sn:
	rm -rf output .cache/
	rm -f tests/.local
	docker run --rm -v $(CWD):$(CWD) --workdir="$(CWD)" ghcr.io/inti-cmnb/kicad_auto_test:stable_nightly \
		/bin/bash -c "export KIBOT_COPY_REF=$(KIBOT_COPY_REF); src/kibot --help-outputs > /dev/null ; pytest-3 --log-cli-level debug -k '$(SINGLE_TEST)' --test_dir=output ; chown -R $(USER_ID):$(GROUP_ID) output/ tests/ .coverage.* htmlcov/ .cache"
# rm -R .cache/ ; KIBOT_COPY_REF="1" SINGLE_TEST=test_print_sch_variant_ni_2 make test_docker_local_1_sn

t1k8: test_docker_local_1_ki8

t1k10: test_docker_local_1_ki10

t1n: test_docker_local_1_n

test_docker_local:
	rm -rf output
	rm -f tests/.local
	$(PY_COV) erase
	# Run in the same directory to make the __pycache__ valid
	# Also change the owner of the files to the current user (we run as root like in GitHub)
	docker run --rm -v $(CWD):$(CWD) --workdir="$(CWD)" ghcr.io/inti-cmnb/kicad_auto_test:latest \
		/bin/bash -c "flake8 . --count --statistics ; python3-coverage run src/kibot --help-outputs ; pytest-3 --test_dir=output ; $(PY_COV) html; chown -R $(USER_ID):$(GROUP_ID) output/ tests/ .coverage.* htmlcov/ .cache"
	$(PY_COV) combine
	$(PY_COV) report
	x-www-browser htmlcov/index.html

test_docker_local_ki6:
	rm -rf output
	rm -f tests/.local
	$(PY_COV) erase
	# Run in the same directory to make the __pycache__ valid
	# Also change the owner of the files to the current user (we run as root like in GitHub)
	docker run --rm -v $(CWD):$(CWD) --workdir="$(CWD)" ghcr.io/inti-cmnb/kicad_auto_test:ki6 \
		/bin/bash -c "python3-coverage run src/kibot --help-outputs ; pytest-3 --test_dir=output ; $(PY_COV) html; chown -R $(USER_ID):$(GROUP_ID) output/ tests/ .coverage.* htmlcov/ .cache"
	$(PY_COV) combine
	$(PY_COV) report
	x-www-browser htmlcov/index.html

test_docker_local_ki7:
	rm -rf output
	rm -f tests/.local
	$(PY_COV) erase
	docker run --rm -v $(CWD):$(CWD) --workdir="$(CWD)" ghcr.io/inti-cmnb/kicad_auto_test:ki7 \
		/bin/bash -c "python3-coverage run src/kibot --help-outputs ; pytest-3 --test_dir=output ; $(PY_COV) html; chown -R $(USER_ID):$(GROUP_ID) output/ tests/ .coverage.* htmlcov/ .cache"
	$(PY_COV) combine
	$(PY_COV) report
	x-www-browser htmlcov/index.html

test_docker_local_ki8:
	rm -rf output
	rm -f tests/.local
	$(PY_COV) erase
	docker run --rm -v $(CWD):$(CWD) --workdir="$(CWD)" ghcr.io/inti-cmnb/kicad_auto_test:ki8 \
		/bin/bash -c "python3-coverage run src/kibot --help-outputs ; pytest-3 --test_dir=output ; $(PY_COV) html; chown -R $(USER_ID):$(GROUP_ID) output/ tests/ .coverage.* htmlcov/ .cache"
	$(PY_COV) combine
	$(PY_COV) report
	x-www-browser htmlcov/index.html

test_docker_local_manjaro:
	rm -rf output_manjaro
	rm -f tests/.local
	docker run --rm -v $(CWD):$(CWD) --workdir="$(CWD)" setsoft/kicad_auto:manjaro_k6 \
		/bin/bash -c "sudo pacman -S flake8 python-pytest python-pytest-xdist python-wheel diffutils fluxbox x11vnc wmctrl unzip zbar python-coverage wget --noconfirm ; sudo pacman -S --noconfirm  make python-pre-commit ; yay -S --noconfirm  python-xlsx2csv ; src/kibot --help-outputs ; pytest --test_dir=output_manjaro ; chown -R $(USER_ID):$(GROUP_ID) output_manjaro/ tests/"

docker_shell:
	docker run  -it --rm -v $(CWD):$(CWD) --workdir="$(CWD)" \
	-v /tmp/.X11-unix:/tmp/.X11-unix -e DISPLAY=$(DISPLAY) \
	--user $(USER_ID):$(GROUP_ID) \
	--volume="/etc/group:/etc/group:ro" \
	--volume="/etc/passwd:/etc/passwd:ro" \
	--volume="/etc/shadow:/etc/shadow:ro" \
	--volume="/home/$(USER):/home/$(USER):rw" \
	setsoft/kicad_auto_test:latest /bin/bash

t1k6: test_docker_local_1_ki6

single_test:
	rm -rf pp
	-$(PY_COV) run src/kibot --help-list-outputs > /dev/null
	-LANG=en_US.UTF-8 $(PYTEST) --ignore=experiments --log-cli-level debug -k "$(SINGLE_TEST)" --test_dir=pp
	@echo "********************" Output
	#@cat pp/*/output.txt
	@echo "********************" Error
	@tail -n 30 pp/*/error.txt
	@rm -f tests/input_samples/bom.ini
	@rm .coverage.*.*

single_tests:
	rm -rf pp
	# 12 threads, for a 6 core CPU w/HT. Almost 4 times faster for BoM tests.
	-$(PYTEST) -n 12 --log-cli-level debug -k "$(SINGLE_TEST)" --test_dir=pp
	@rm -f tests/input_samples/bom.ini

deb_clean:
	fakeroot debian/rules clean

gen_ref:
	# Reference outputs, must be manually inspected if regenerated
	pcbnew_do export --output_name bom-F_Cu+F_SilkS.pdf --scaling 4 --pads 0 --no-title --monochrome --separate tests/board_samples/bom.kicad_pcb $(REFDIR) F.Cu F.SilkS
	cp -a $(REFILL).refill $(REFILL)
	src/kibot -c tests/yaml_samples/pdf_zone-refill.kibot.yaml -b tests/board_samples/zone-refill.kicad_pcb -d $(REFDIR)
	src/kibot -c tests/yaml_samples/print_pcb_zone-refill.kibot.yaml -b tests/board_samples/zone-refill.kicad_pcb -d $(REFDIR)
	src/kibot -c tests/yaml_samples/print_pdf_no_inductors_1.kibot.yaml -e tests/board_samples/test_v5.sch -d $(REFDIR)
	mv "$(REFDIR)no_inductor/test_v5-schematic_(no_L).pdf" $(REFDIR)
	rmdir $(REFDIR)no_inductor/
	src/kibot -c tests/yaml_samples/print_svg_no_inductors_1.kibot.yaml -e tests/board_samples/test_v5.sch -d $(REFDIR)
	mv "$(REFDIR)no_inductor/test_v5-schematic_(no_L).svg" $(REFDIR)
	-@rm -rf $(REFDIR)no_inductor/
	src/kibot -b tests/board_samples/kibom-variant_4.kicad_pcb -c tests/yaml_samples/pdf_variant_1.kibot.yaml -d $(REFDIR)
	src/kibot -b tests/board_samples/kibom-variant_3.kicad_pcb -c tests/yaml_samples/pcbdraw_variant_1.kibot.yaml -d $(REFDIR)
	src/kibot -b tests/board_samples/kibom-variant_3.kicad_pcb -c tests/yaml_samples/pcbdraw_variant_2.kibot.yaml -d $(REFDIR)
	src/kibot -b tests/board_samples/kibom-variant_3.kicad_pcb -c tests/yaml_samples/print_pcb_variant_1.kibot.yaml -d $(REFDIR)
	cp -a $(REFILL).ok $(REFILL)

doc:
	make -C docs

py_build:
	python3 setup.py sdist bdist_wheel

pypi_upload: py_clean py_build
	python3 -m twine upload dist/*

py_clean:
	@rm -rf .pybuild build dist kibot.egg-info

# Update the Github Action
# /Dockerfile.* must be updated
update_gha:
	cp Dockerfile_k5 Dockerfile
	git commit -m "[CI/CD] Updating Github Action v2 for KiCad 5 latest [skip ci]" Dockerfile
	git push
	git tag -f -a v2 -m "GitHub Action v2 for KiCad 5"
	git push origin -f --tags
	cp Dockerfile_dk5 Dockerfile
	git commit -m "[CI/CD] Updating Github Action v2 for KiCad 5 development [skip ci]" Dockerfile
	git push
	git tag -f -a v2_d -m "GitHub Action v2 for KiCad 5 (development)"
	git tag -f -a v2_dk5 -m "GitHub Action v2 for KiCad 5 (development)"
	git push origin -f --tags
	cp Dockerfile_dk6 Dockerfile
	git commit -m "[CI/CD] Updating Github Action v2 for KiCad 6 development [skip ci]" Dockerfile
	git push
	git tag -f -a v2_dk6 -m "GitHub Action v2 for KiCad 6 (development)"
	git push origin -f --tags
	cp Dockerfile_k6 Dockerfile
	git commit -m "[CI/CD] Updating Github Action v2 for KiCad 6 latest [skip ci]" Dockerfile
	git push
	git tag -f -a v2_k6 -m "GitHub Action v2 for KiCad 6"
	git push origin -f --tags
	cp Dockerfile_dk7 Dockerfile
	git commit -m "[CI/CD] Updating Github Action v2 for KiCad 7 development [skip ci]" Dockerfile
	git push
	git tag -f -a v2_dk7 -m "GitHub Action v2 for KiCad 7 (development)"
	git push origin -f --tags
	cp Dockerfile_k7 Dockerfile
	git commit -m "[CI/CD] Updating Github Action v2 for KiCad 7 latest [skip ci]" Dockerfile
	git push
	git tag -f -a v2_k7 -m "GitHub Action v2 for KiCad 7"
	git push origin -f --tags
	cp Dockerfile_dk8 Dockerfile
	git commit -m "[CI/CD] Updating Github Action v2 for KiCad 8 development [skip ci]" Dockerfile
	git push
	git tag -f -a v2_dk8 -m "GitHub Action v2 for KiCad 8 (development) [skip ci]"
	git push origin -f --tags
	cp Dockerfile_k8 Dockerfile
	git commit -m "[CI/CD] Updating Github Action v2 for KiCad 8 latest [skip ci]" Dockerfile
	git push
	git tag -f -a v2_k8 -m "GitHub Action v2 for KiCad 8"
	git push origin -f --tags
	cp Dockerfile_dk9 Dockerfile
	git commit -m "[CI/CD] Updating Github Action v2 for KiCad 9 development [skip ci]" Dockerfile
	git push
	git tag -f -a v2_dk9 -m "GitHub Action v2 for KiCad 9 (development)"
	git push origin -f --tags
	cp Dockerfile_k9 Dockerfile
	git commit -m "[CI/CD] Updating Github Action v2 for KiCad 9 latest [skip ci]" Dockerfile
	git push
	git tag -f -a v2_k9 -m "GitHub Action v2 for KiCad 9"
	git push origin -f --tags
	cp Dockerfile_dk10 Dockerfile
	git commit -m "[CI/CD] Updating Github Action v2 for KiCad 10 development [skip ci]" Dockerfile
	git push
	git tag -f -a v2_dk10 -m "GitHub Action v2 for KiCad 10 (development)"
	git push origin -f --tags
	cp Dockerfile_k10 Dockerfile
	git commit -m "[CI/CD] Updating Github Action v2 for KiCad 10 latest [skip ci]" Dockerfile
	git push
	git tag -f -a v2_k10 -m "GitHub Action v2 for KiCad 10"
	git push origin -f --tags


i18n:
	cd kibot ; ../tools/geni18n.py

.PHONY: deb deb_clean lint test test_local gen_ref doc py_build pypi_upload py_clean i18n
