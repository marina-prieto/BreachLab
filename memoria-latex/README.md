# Memoria del TFM en LaTeX

Migración de `Marina-Prieto-TFM.docx` a la clase oficial UCLM/ESI
`esi-tfm.cls` (del repositorio
[UCLM-ESI/esi-tfg](https://github.com/UCLM-ESI/esi-tfg)).

## Qué se ha hecho

- El contenido (resumen, capítulos 1–9, bibliografía, glosario, contenido
  del repositorio y los dos anexos) es una transcripción fiel del texto del
  Word, reestructurada en ficheros `.tex` separados.
- `esi-tfm.cls` es la clase oficial del repo, parcheada solo en lo
  imprescindible:
  - Las tres referencias a logos que dependían de un paquete Debian interno
    de la universidad (`informatica_gray.pdf`, `uclm_logomarca_1.pdf`,
    `esi.pdf`, no incluidos en el repo público) se sustituyeron por el
    escudo de la UCLM extraído de tu propio `.docx`
    (`figures/uclm_escudo.png`).
  - Se añadieron los macros `\school{}` y `\degree{}` para no dejar
    hardcodeado el nombre de la escuela/máster (se rellenan en
    `metadata.tex`).
- Los títulos de capítulo/sección se normalizaron a mayúscula inicial y
  numeración automática de LaTeX (el Word mezclaba capítulo 1 en VERSALES
  con numeración manual "2.1., 3.2., ..." en el resto — un ejemplo de por
  qué el Word se veía "roto").

## Compilar

Ya compilado y verificado con MiKTeX (pdfTeX) → PDF sin errores. La
bibliografía usa citas reales (`\citelib{}`/`\citelink{}`, del
paquete `multibib`) contra `referencias.bib`, procesadas con `bibtex`
clásico (no `biber`) y el estilo `es-alpha` — cada referencia enlaza a su
entrada en el PDF vía `hyperref`.

Con `latexmk` (requiere Perl instalado además de MiKTeX): detecta y ejecuta
`bibtex` sobre `lib.aux`/`link.aux` automáticamente, no hay que hacer nada
manual.
```
latexmk -pdf main.tex
```

Sin Perl (sin `latexmk`), hay que llamar a `bibtex` a mano dos veces —una
por cada categoría de la bibliografía— entre pasadas de `pdflatex`:
```
pdflatex -interaction=nonstopmode main.tex
bibtex lib
bibtex link
pdflatex -interaction=nonstopmode main.tex
pdflatex -interaction=nonstopmode main.tex
```

Si alguna vez editas `referencias.bib` o cambias qué se cita, repite esta
secuencia completa (no basta con relanzar `pdflatex` solo).

`atbeginend.sty` va incluido en esta carpeta porque no está en el
repositorio de paquetes de MiKTeX/CTAN (es un fichero local del repo
esi-tfg del que depende `esi-tfm.cls`).

La clase añade automáticamente al final del documento una página de
atribución a `esi-tfm` (tradición del repositorio). Para quitarla,
descomenta la línea correspondiente en `custom.sty`.
