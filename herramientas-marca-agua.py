# -*- coding: utf-8 -*-
"""Prepara una foto para la web: redimensiona, marca de agua y WebP."""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os

LOGO = 'img/logo-mark.png'
ANCHO_WEB = 1200
FUENTES = ['/System/Library/Fonts/Supplemental/Futura.ttc',
           '/System/Library/Fonts/HelveticaNeue.ttc',
           '/System/Library/Fonts/Helvetica.ttc']

def _fuente(tam):
    for f in FUENTES:
        if os.path.exists(f):
            try: return ImageFont.truetype(f, tam)
            except Exception: pass
    return ImageFont.load_default()

def preparar(origen, destino, ancho=ANCHO_WEB):
    im = Image.open(origen).convert('RGB')
    im = im.resize((ancho, round(im.height * ancho / im.width)), Image.LANCZOS)

    # Logo en blanco: se lee igual sobre pared clara que sobre suelo oscuro
    logo = Image.open(LOGO).convert('RGBA')
    lw = round(ancho * 0.15)
    logo = logo.resize((lw, round(logo.height * lw / logo.width)), Image.LANCZOS)
    blanco = Image.new('RGBA', logo.size, (255,255,255,255))
    blanco.putalpha(logo.getchannel('A').point(lambda v: int(v*0.92)))

    texto = 'latriburooms.es'
    f = _fuente(round(ancho * 0.15 * 0.24))
    capa = Image.new('RGBA', im.size, (0,0,0,0))
    d = ImageDraw.Draw(capa)
    tw = d.textbbox((0,0), texto, font=f)[2]

    margen = round(ancho * 0.028)
    bloque = max(lw, tw)
    x = im.width - margen - bloque
    y = im.height - margen - logo.height - round(ancho*0.032)

    capa.paste(blanco, (x + (bloque-lw)//2, y), blanco)
    d.text((x + (bloque-tw)//2, y + logo.height + round(ancho*0.007)),
           texto, font=f, fill=(255,255,255,240))

    # sombra: copia oscura desenfocada debajo, para que se lea sobre blanco
    sombra = Image.new('RGBA', im.size, (0,0,0,0))
    sombra.paste(capa, (0,0), capa)
    sombra = Image.new('RGBA', im.size, (0,0,0,0)) if False else sombra
    negro = Image.new('RGBA', im.size, (0,0,0,0))
    negro.putalpha(capa.getchannel('A').point(lambda v: int(v*0.75)))
    negro = negro.filter(ImageFilter.GaussianBlur(7))

    salida = im.convert('RGBA')
    salida = Image.alpha_composite(salida, negro)
    salida = Image.alpha_composite(salida, capa)
    salida.convert('RGB').save(destino, 'WEBP', quality=82, method=6)
    return destino, round(os.path.getsize(destino)/1024)

if __name__ == '__main__':
    import sys
    print(preparar(sys.argv[1], sys.argv[2]))
