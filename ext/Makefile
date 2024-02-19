
LIB := browsermob-proxy
VER := 2.1.4
PKG := $(LIB)-$(VER)
ZIP := $(PKG)-bin.zip
URL := https://github.com/lightbody/$(LIB)/releases/download/$(PKG)/$(ZIP)


.PHONY: install clean wipe


$(ZIP):
	@wget $(URL)


install: $(ZIP)
	@unzip $(ZIP)


clean:
	@rm -rf ./$(PKG)

wipe: clean
	@rm -f $(ZIP)
