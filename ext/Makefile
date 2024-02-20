SHELL := /usr/bin/bash

LIB := browsermob-proxy
VER := 2.1.4
PKG := $(LIB)-$(VER)
ZIP := $(PKG)-bin.zip
URL := https://github.com/lightbody/$(LIB)/releases/download/$(PKG)/$(ZIP)


.PHONY: install clean wipe

.DEFAULT_GOAL := install


$(ZIP):
	@wget $(URL)


$(PKG)/bin/$(LIB): $(ZIP)
	@unzip $(ZIP) && [ -f $@ ] && touch $@

install: $(PKG)/bin/$(LIB)
	@[ $$EUID -ne 0 ]					&& \
	echo 'Warn: Install requires sudo/root privileges!' >&2 && \
	exit 1 || exit 0
	@apt -y install chromium-chromedriver


clean:
	@rm -rf ./$(PKG)

wipe: clean
	@rm -f $(ZIP)
