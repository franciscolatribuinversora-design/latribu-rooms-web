# -*- coding: utf-8 -*-
"""Genera la ficha de cada habitación de habitaciones.json y su tarjeta de portada.

    python3 generar-fichas.py                 # todas las de habitaciones.json
    python3 generar-fichas.py rio-duero-leganes-h4

Antes hay que importar sus fotos:
    python3 importar-fotos.py "/ruta/al/piso" <slug> <carpeta de la habitación>

En un piso compartido cada habitación tiene su propia ficha, por eso el slug lleva
el número de habitación (…-h4). La dirección exacta no se publica nunca: solo la
zona y el municipio, como en Idealista.
"""
import importlib.util, json, os, re, sys, urllib.parse
from PIL import Image

AQUI = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("marca", os.path.join(AQUI, "herramientas-marca-agua.py"))
marca = importlib.util.module_from_spec(spec); spec.loader.exec_module(marca)

WHATSAPP = '34635771908'
RATIO_TARJETA = 344 / 180


def wa(texto):
    return f'https://wa.me/{WHATSAPP}?text=' + urllib.parse.quote(texto, safe='')


def portada(slug, numero):
    """Recorta la foto de portada a la proporción de la tarjeta y la marca después,
    para que la marca de agua salga entera y siempre a la misma altura."""
    origen = f'img/{slug}/{numero}.webp'
    im = Image.open(origen).convert('RGB'); w, h = im.size
    if w / h > RATIO_TARJETA:
        nw = int(h * RATIO_TARJETA); caja = ((w - nw) // 2, 0, (w - nw) // 2 + nw, h)
    else:
        nh = int(w / RATIO_TARJETA)
        caja = (0, min(h - nh, int((h - nh) * 0.62)), w, min(h - nh, int((h - nh) * 0.62)) + nh)
    os.makedirs('img/portadas', exist_ok=True)
    tmp = f'/tmp/portada-{slug}.jpg'
    im.crop(caja).save(tmp, quality=95)
    destino = f'img/portadas/{slug}-{numero}.webp'
    marca.preparar(tmp, destino, ancho=900)
    return destino


def ficha(p):
    s = open('plantilla/ficha-base.html').read()
    fotos = json.load(open(f"img/{p['slug']}/manifiesto.json"))
    fotos.sort(key=lambda f: 0 if f['src'].endswith(f"/{p['portada']}.webp") else 1)
    # los pies se renumeran según el orden en que se van a ver
    base = {}
    for f in fotos:
        b = re.sub(r' \(\d+ de \d+\)$', '', f['pie'])
        base[b] = base.get(b, 0) + 1
    visto = {}
    for f in fotos:
        b = re.sub(r' \(\d+ de \d+\)$', '', f['pie'])
        visto[b] = visto.get(b, 0) + 1
        f['pie'] = b + (f' ({visto[b]} de {base[b]})' if base[b] > 1 else '')

    archivo = f"habitacion-{p['slug']}.html"
    enlace_wa = wa(f"Hola, me interesa la habitación de {p['calle']} ({p['municipio']}) — {p['precio']}€/mes")
    precio_txt = f"{p['precio']} €/mes" + (f" + {p['suministros']}€ de suministros" if p.get('suministros') else '')

    s = re.sub(r'<title>[^<]*</title>', f"<title>Habitación en {p['municipio']} — {p['precio']}€/mes | La Tribu Rooms</title>", s, 1)
    s = re.sub(r'<meta name="description" content="[^"]*">', f'<meta name="description" content="{p["meta"]}">', s, 1)
    s = s.replace('habitacion-ciudades-getafe.html', archivo)
    s = re.sub(r'<meta property="og:title" content="[^"]*">', f'<meta property="og:title" content="Habitación en {p["municipio"]} — {p["precio"]}€/mes">', s, 1)
    s = re.sub(r'<meta property="og:description" content="[^"]*">', f'<meta property="og:description" content="{p["titulo"]}. Sin honorarios de agencia.">', s, 1)
    s = s.replace('/img/ciudades-getafe/02.webp', f"/img/{p['slug']}/{p['portada']}.webp")

    s = re.sub(r'"name": "[^"]*"', f'"name": "{p["titulo"]} en {p["municipio"]}"', s, 1)
    s = re.sub(r'"description": "[^"]*"', f'"description": "Habitación individual amueblada en piso compartido de {p["piso"].split(",")[0]}."', s, 1)
    s = re.sub(r'  "floorSize": \{.*?\n  \},\n', '', s, 1, flags=re.S)
    s = re.sub(r'"streetAddress": "[^"]*"', f'"streetAddress": "{p["calle"]}"', s, 1)
    s = re.sub(r'"addressLocality": "[^"]*"', f'"addressLocality": "{p["municipio"]}"', s, 1)
    s = re.sub(r'"postalCode": "[^"]*"', f'"postalCode": "{p["cp"]}"', s, 1)
    amen = ',\n'.join('    {\n      "@type": "LocationFeatureSpecification",\n'
                      f'      "name": "{x}",\n      "value": true\n    }}' for x in p['habitacion'])
    s = re.sub(r'  "amenityFeature": \[.*?\n  \]\n', f'  "amenityFeature": [\n{amen}\n  ]\n', s, 1, flags=re.S)

    s = re.sub(r'<a class="nav-cta" href="[^"]*"', f'<a class="nav-cta" href="{enlace_wa}"', s, 1)
    s = re.sub(r'› [^<\n]*</p>', f'› {p["zona"]}</p>', s, 1)
    s = re.sub(r'<p class="zona">[^<]*</p>', f'<p class="zona">{p["zona"]}</p>', s, 1)
    s = re.sub(r'<span class="libre">[^<]*</span>',
               f'<span class="libre">Disponible {"ahora" if p["disponible"] == "Ahora" else "el " + p["disponible"]}</span>', s, 1)
    s = re.sub(r'<h1>[^<]*</h1>', f'<h1>{p["titulo"]}</h1>', s, 1)
    s = re.sub(r'<p class="precio">[^<]*<span class="mes">/mes</span></p>',
               f'<p class="precio">{p["precio"]}€<span class="mes">/mes</span></p>', s, 1)
    s = re.sub(r'<p class="claim-detalle">[^<]*</p>', f'<p class="claim-detalle">{p["claim"]}</p>', s, 1)
    s = re.sub(r'alt="[^"]*"', f'alt="{p["titulo"]}"', s, 1)
    s = re.sub(r'<span class="contador" id="contador">1 / \d+</span>',
               f'<span class="contador" id="contador">1 / {len(fotos)}</span>', s, 1)
    s = re.sub(r'<p class="pie-foto" id="pie">[^<]*</p>', f'<p class="pie-foto" id="pie">{p["titulo"]}</p>', s, 1)

    lista = lambda xs: '\n'.join(f'          <li>{x}</li>' for x in xs)
    s = re.sub(r'(<h2>Qué incluye la habitación</h2>\n        <ul class="lista">\n).*?(\n        </ul>)',
               lambda m: m.group(1) + lista(p['habitacion']) + m.group(2), s, 1, flags=re.S)
    s = re.sub(r'(<h2>Zonas comunes</h2>\n        <ul class="lista">\n).*?(\n        </ul>)',
               lambda m: m.group(1) + lista(p['comunes']) + m.group(2), s, 1, flags=re.S)

    s = re.sub(r'<span class="k">Precio</span><span class="v">[^<]*</span>',
               f'<span class="k">Precio</span><span class="v">{precio_txt}</span>', s, 1)
    s = re.sub(r'<span class="k">Disponible</span><span class="v">[^<]*</span>',
               f'<span class="k">Disponible</span><span class="v">{p["disponible"]}</span>', s, 1)
    s = re.sub(r'\s*<div class="ficha-row"><span class="k">La habitación</span>.*?</div>', '', s, 1)
    s = re.sub(r'<span class="k">El piso</span><span class="v">[^<]*</span>',
               f'<span class="k">El piso</span><span class="v">{p["piso"]}</span>', s, 1)
    s = re.sub(r'<span class="k">Planta</span><span class="v">[^<]*</span>',
               f'<span class="k">Planta</span><span class="v">{p["planta"]}</span>', s, 1)
    s = re.sub(r'<a class="btn btn-wa" href="[^"]*"', f'<a class="btn btn-wa" href="{enlace_wa}"', s, 1)
    s = re.sub(r'(<a class="btn btn-id" href="https://www\.idealista\.com/pro/novos-real-estate-madrid/inmueble/)\d+(/)',
               rf'\g<1>{p["idealista"]}\g<2>', s, 1)
    s = re.sub(r'<p class="nota">[^<]*</p>',
               f'<p class="nota">{p["nota"]} Te respondemos el mismo día; si no puedes venir en persona, te la enseñamos por videollamada.</p>', s, 1)

    arr = ',\n'.join("    {src:'%s', grupo:'%s', pie:'%s'}" % (f['src'], f['grupo'], f['pie']) for f in fotos)
    s = re.sub(r'  var FOTOS = \[.*?\n  \];', f'  var FOTOS = [\n{arr}\n  ];', s, 1, flags=re.S)

    open(archivo, 'w').write(s)
    return archivo, len(fotos)


def tarjeta(p, n_fotos, img_portada):
    enlace = f"/habitacion-{p['slug']}.html"
    return f'''        <div class="room-card reveal">
          <a class="room-photo" href="{enlace}"><img src="{img_portada}" alt="{p['titulo']}" loading="lazy"><span class="room-badge">Disponible</span></a>
          <div class="room-body">
            <p class="room-zone">{p['zona']}</p>
            <p class="room-title">{p['titulo']}</p>
            <p class="room-meta">{p.get('resumen', '🛏 Individual · ' + p['piso'])}</p>
            <div class="room-price"><strong>{p['precio']}€</strong><span class="per">/mes</span></div>
            <a class="room-link" href="{enlace}">Ver las {n_fotos} fotos →</a>
            <a class="room-link secundario" href="https://www.idealista.com/pro/novos-real-estate-madrid/inmueble/{p['idealista']}/" target="_blank" rel="noopener">También en Idealista</a>
          </div>
        </div>
'''


if __name__ == '__main__':
    datos = json.load(open('habitaciones.json'))
    pedidos = sys.argv[1:]
    if pedidos:
        datos = [d for d in datos if d['slug'] in pedidos]

    index = open('index.html').read()
    for p in datos:
        img = portada(p['slug'], p['portada'])
        archivo, n = ficha(p)
        nueva = tarjeta(p, n, img)
        enlace = f"/habitacion-{p['slug']}.html"
        # si ya tenía tarjeta se sustituye; si no, se añade al bloque de disponibles
        anterior = re.search(r'        <div class="room-card reveal[^"]*">\n          <a class="room-photo" href="'
                             + re.escape(enlace) + r'".*?\n        </div>\n', index, re.S)
        if anterior:
            index = index.replace(anterior.group(0), nueva)
        else:
            marca_fin = '      </div>\n\n      <div class="reservadas-head">'
            if '<div class="sin-libres">' in index:
                index = re.sub(r'      <div class="sin-libres">.*?      </div>\n\n',
                               '      <div class="rooms-grid">\n\n' + nueva + marca_fin.split('\n')[0] + '\n\n',
                               index, 1, flags=re.S)
            else:
                index = index.replace(marca_fin, nueva + marca_fin)
        print('ficha:', archivo, f'({n} fotos)')
    open('index.html', 'w').write(index)
