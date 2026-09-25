# -*- coding: utf-8 -*-
"""Prepara las fotos de un piso para la web.

Uso:
    python3 importar-fotos.py "/ruta/a/la/carpeta del piso" slug-del-piso

Coge las fotos de la carpeta (y sus subcarpetas: habitacion, cocina, baño, salon,
terraza), les pone la marca de agua, las guarda como img/<slug>/NN.webp y escribe
img/<slug>/manifiesto.json con el grupo y el pie de cada una.

Detalles que costaron un rato en su momento y por eso están resueltos aquí:
  - Las fotos del iPhone llevan la orientación en los datos EXIF: hay que aplicarla
    (exif_transpose) o salen giradas.
  - Los HEIC no los lee Pillow: se convierten antes con sips.
  - macOS guarda los acentos descompuestos, así que "baño" no coincide con "baño"
    si no se normaliza (NFC).
  - Solo se descarta un HEIC cuando existe el MISMO nombre en jpeg. Nombres
    parecidos ("BAÑO 1.jpg" y "BAÑO1.JPG") son fotos distintas.
"""
import importlib.util, json, os, subprocess, sys, unicodedata
from PIL import Image, ImageOps

AQUI = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("marca", os.path.join(AQUI, "herramientas-marca-agua.py"))
marca = importlib.util.module_from_spec(spec); spec.loader.exec_module(marca)

EXTS = ('.jpg', '.jpeg', '.png', '.heic')
GRUPO = {"habitacion": "habitacion", "cocina": "comunes", "baño": "comunes",
         "salon": "comunes", "terraza": "comunes", "comunes": "comunes"}
PIE = {"habitacion": "La habitación", "cocina": "La cocina", "baño": "El baño",
       "salon": "El salón", "terraza": "La terraza", "comunes": "El piso"}
ORDEN = {"habitacion": 0, "salon": 1, "cocina": 2, "baño": 3, "terraza": 4, "comunes": 9}

norm = lambda s: unicodedata.normalize('NFC', s).lower()


def clasifica(ruta):
    """De la carpeta más profunda hacia fuera: 'h1/baño' es baño, no habitación."""
    for parte in reversed([norm(x) for x in ruta.split(os.sep)]):
        for clave in ("baño", "bano", "cocina", "salon", "terraza", "habitacion"):
            if clave in parte:
                return "baño" if clave == "bano" else clave
    return "comunes"


def normalizar(origen, temporal):
    """Devuelve una ruta jpeg derecha y legible por Pillow."""
    if origen.lower().endswith('.heic'):
        subprocess.run(['sips', '-s', 'format', 'jpeg', origen, '--out', temporal],
                       check=True, capture_output=True)
        origen = temporal
    im = ImageOps.exif_transpose(Image.open(origen)).convert('RGB')
    im.save(temporal, quality=95)
    return temporal


def importar(carpeta, slug, destino_base=AQUI):
    fotos = []
    for dirpath, _, files in os.walk(carpeta):
        for f in sorted(files):
            if not f.startswith('.') and os.path.splitext(f)[1].lower() in EXTS:
                fotos.append(os.path.join(dirpath, f))

    jpegs = {norm(os.path.splitext(f)[0]) for f in fotos if not f.lower().endswith('.heic')}
    fotos = [f for f in fotos
             if not (f.lower().endswith('.heic') and norm(os.path.splitext(f)[0]) in jpegs)]
    fotos.sort(key=lambda f: (ORDEN.get(clasifica(f), 9), norm(f)))

    destino = os.path.join(destino_base, 'img', slug)
    os.makedirs(destino, exist_ok=True)
    tmp = os.path.join('/tmp', 'importar-fotos')
    os.makedirs(tmp, exist_ok=True)

    total = {}
    for f in fotos:
        c = clasifica(f)
        total[c] = total.get(c, 0) + 1

    manifiesto, visto = [], {}
    for i, f in enumerate(fotos, start=1):
        listo = normalizar(f, os.path.join(tmp, f'{slug}_{i}.jpg'))
        marca.preparar(listo, os.path.join(destino, f'{i:02d}.webp'))
        c = clasifica(f)
        visto[c] = visto.get(c, 0) + 1
        pie = PIE.get(c, 'El piso') + (f' ({visto[c]} de {total[c]})' if total[c] > 1 else '')
        manifiesto.append({'src': f'/img/{slug}/{i:02d}.webp',
                           'grupo': GRUPO.get(c, 'comunes'), 'pie': pie})

    with open(os.path.join(destino, 'manifiesto.json'), 'w') as fh:
        json.dump(manifiesto, fh, ensure_ascii=False, indent=1)
    return manifiesto


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)
    m = importar(sys.argv[1], sys.argv[2])
    print(f'{len(m)} fotos en img/{sys.argv[2]}/')
    for x in m:
        print(' ', x['src'], '·', x['pie'])
