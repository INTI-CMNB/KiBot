#!/usr/bin/make
SPHINXOPTS    ?=
SPHINXBUILD   ?= sphinx-build
SOURCEDIR     = source
BUILDDIR      = build
SPHINXTARGETS = html dirhtml singlehtml pickle json htmlhelp qthelp devhelp epub latex latexpdf latexpdfja text man texinfo info gettext changes xml pseudoxml linkcheck doctest coverage clean


all: html samples/generic_plot.kibot.yaml ../kibot/resources/report_templates/report_full_svg.txt ../src/kibot-check ../tests/GUI/stats

../src/kibot-check: ../src/kibot-check.in replace_tags.pl ../kibot/out_*.py ../kibot/pre_*.py ../kibot/var_*.py ../kibot/registrable.py ../kibot/misc.py ../kibot/config_reader.py ../kibot/dep_downloader.py
	cat ../src/kibot-check.in | perl replace_tags.pl > ../src/kibot-check

samples/generic_plot.kibot.yaml: ../kibot/out_*.py ../kibot/pre_*.py ../kibot/config_reader.py
	rm -f example_template.kibot.yaml
	../src/kibot -v --example
	mv example_template.kibot.yaml $@

../kibot/resources/report_templates/report_full_svg.txt: ../kibot/resources/report_templates/report_full.txt
	cp $< $@


source/configuration/sup_outputs.rst: ../kibot/out_*.py ../kibot/config_reader.py
	../src/kibot --rst --help-outputs -d source/configuration/outputs/ > $@

source/dependencies.rst: ../kibot/out_*.py ../kibot/pre_*.py ../kibot/var_*.py ../kibot/registrable.py ../kibot/misc.py ../kibot/config_reader.py ../kibot/dep_downloader.py
	../src/kibot --rst --help-dependencies > $@

source/errors.rst: ../kibot/misc.py ../kibot/config_reader.py
	../src/kibot --rst --help-errors > $@

source/usage.txt: ../kibot/__main__.py
	../src/kibot --help > $@

source/configuration/sup_preflights.rst: ../kibot/pre_*.py ../kibot/config_reader.py
	../src/kibot --rst --help-preflights -d source/configuration/preflights/ > $@

source/configuration/sup_filters.rst: ../kibot/fil_*.py ../kibot/config_reader.py
	../src/kibot --rst --help-filters -d source/configuration/filters/ > $@

source/configuration/sup_variants.rst: ../kibot/var_*.py ../kibot/config_reader.py
	../src/kibot --rst --help-variants -d source/configuration/variants/ > $@

source/configuration/sup_globals.rst: ../kibot/globals.py ../kibot/config_reader.py
	../src/kibot --rst --help-global-options > $@

source/rotations.rst: ../kibot/misc.py ../kibot/config_reader.py
	../src/kibot --help-list-rotations > $@

source/offsets.rst: ../kibot/misc.py ../kibot/config_reader.py
	../src/kibot --help-list-offsets > $@

source/Changelog.rst: ../CHANGELOG.md
	pandoc -o tmp.rst $<
	cat changelog_pre.rst tmp.rst > $@
	rm tmp.rst

../tests/GUI/outputs ../tests/GUI/filters ../tests/GUI/preflights ../tests/GUI/variants ../tests/GUI/stats: ../kibot/fil_*.py ../kibot/out_*.py ../kibot/pre_*.py ../kibot/var_*.py ../kibot/config_reader.py
	../src/kibot -b ../tests/board_samples/kicad_8/light_control.kicad_pcb --internal-check -d ../tests/GUI > ../tests/GUI/stats

help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
$(SPHINXTARGETS): Makefile source/configuration/sup_outputs.rst source/dependencies.rst source/usage.txt source/configuration/sup_preflights.rst \
	source/configuration/sup_filters.rst source/configuration/sup_variants.rst source/configuration/sup_globals.rst source/errors.rst \
	source/rotations.rst source/offsets.rst source/Changelog.rst
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)


.PHONY: help Makefile $(SPHINXTARGETS)
