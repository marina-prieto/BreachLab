MAIN = main

.PHONY: all clean

all: $(MAIN).pdf

$(MAIN).pdf: $(MAIN).tex *.tex esi-tfm.cls custom.sty
	latexmk -pdf -interaction=nonstopmode $(MAIN).tex

clean:
	latexmk -C $(MAIN).tex
