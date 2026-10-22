# -*- coding: utf-8 -*-
"""Pasar habitaciones de disponible a reservada (y al revés) en la web.

    python3 herramientas-habitaciones.py reservar habitacion-albacete-getafe.html
    python3 herramientas-habitaciones.py liberar  habitacion-polvoranca-fuenlabrada.html

Toca la tarjeta de index.html (la mueve al bloque que le toca) y la ficha de la
habitación (aviso, etiqueta, título de Google y botones). Al final recoloca las
tarjetas y actualiza los contadores del inicio.
"""
import re, sys, os

WA_ESPERA = ('https://wa.me/34635771908?text=Hola%2C%20me%20interesa%20una%20habitaci%C3%B3n%20como%20'
             'esta%20cuando%20quede%20libre')
CABECERA = """      <div class="reservadas-head">
        <h3>Ahora mismo reservadas</h3>
        <p>Estas habitaciones ya están ocupadas, no se pueden alquilar. Las dejamos visibles para que veas cómo son nuestros pisos: si te encaja alguna, escríbenos y te avisamos en cuanto quede libre.</p>
      </div>
"""
AVISO = """
  <div class="aviso-reservada">
    <strong>Esta habitación ya está reservada</strong>
    <p>No está disponible para alquilar. Puedes verla para hacerte una idea de cómo son nuestros pisos y, si te encaja, escríbenos: te avisamos en cuanto quede libre una parecida.</p>
  </div>
"""

def _tarjetas(html):
    """Delimita el bloque de habitaciones: empieza en el primer grid o, si no hay libres,
    en el aviso «sin libres»; termina en la nota final. Así la cabecera de reservadas
    queda siempre dentro aunque no haya ninguna habitación disponible."""
    candidatos = [i for i in (html.find('      <div class="rooms-grid">'), html.find('      <div class="sin-libres">')) if i >= 0]
    if not candidatos:
        raise SystemExit('index.html: no encuentro el bloque de habitaciones')
    ini = min(candidatos)
    fin = html.index('      <p class="rooms-note">')
    bloque = html[ini:fin]
    return ini, fin, re.findall(r'        <div class="room-card reveal.*?\n        </div>\n', bloque, re.S)

def _recolocar(html):
    """Deja las disponibles en el primer grid y las reservadas en el segundo."""
    ini, fin, tarjetas = _tarjetas(html)
    libres = [t for t in tarjetas if 'is-reservada' not in t]
    reservadas = [t for t in tarjetas if 'is-reservada' in t]
    m = re.search(r'      <div class="reservadas-head">.*?      </div>\n', html[ini:fin], re.S)
    cabecera = m.group(0) if m else CABECERA
    if libres:
        arriba = '      <div class="rooms-grid">\n\n' + ''.join(libres) + '      </div>\n\n'
    else:
        # Sin habitaciones libres, mejor un aviso que un hueco en blanco
        arriba = ('      <div class="sin-libres">\n'
                  '        <h3>Ahora mismo no tenemos habitaciones libres</h3>\n'
                  '        <p>Se alquilan rápido y entran nuevas cada semana. Escríbenos y te avisamos '
                  'en cuanto salga una que encaje contigo.</p>\n'
                  '        <a class="btn-primary" href="' + WA_ESPERA + '" target="_blank" rel="noopener">'
                  'Avisadme cuando salga una →</a>\n'
                  '      </div>\n\n')
    nuevo = (arriba + cabecera + '\n      <div class="rooms-grid">\n\n' + ''.join(reservadas) + '      </div>\n')
    html = html[:ini] + nuevo + html[fin:]

    precios = [int(p) for p in re.findall(r'<div class="room-price"><strong>(\d+)€', ''.join(libres))]
    html = re.sub(r'(<span class="k">Habitaciones libres</span><span class="v">)\d+(</span>)',
                  rf'\g<1>{len(libres)}\g<2>', html)
    html = re.sub(r'(<span class="k">Reservadas</span><span class="v">)\d+(</span>)',
                  rf'\g<1>{len(reservadas)}\g<2>', html)
    if precios:
        html = re.sub(r'(<span class="k">Desde</span><span class="v">)[^<]*(</span>)',
                      rf'\g<1>{min(precios)} €/mes\g<2>', html)
    return html

def _escribir(ruta, contenido):
    """Escribe en un temporal y renombra: si algo falla antes, el archivo original no se toca."""
    tmp = ruta + '.tmp'
    with open(tmp, 'w') as f:
        f.write(contenido)
    os.replace(tmp, ruta)


def _datos(ficha):
    """Datos de la habitación en habitaciones.json (calle, municipio, precio, idealista), si está."""
    slug = ficha.replace('habitacion-', '').replace('.html', '')
    try:
        import json
        d = json.load(open('habitaciones.json'))
        items = d if isinstance(d, list) else d.get('habitaciones', list(d.values()))
        return next((h for h in items if h.get('slug') == slug), {})
    except Exception:
        return {}


def _wa_interesa(ficha, p):
    from urllib.parse import quote
    h = _datos(ficha)
    precio = re.search(r'<strong>(\d+)€', p) or re.search(r'(\d+) ?€/mes', p)
    precio = h.get('precio') or (precio.group(1) if precio else '')
    if h.get('calle'):
        texto = f"Hola, me interesa la habitación de {h['calle']} ({h['municipio']}) — {precio}€/mes"
    else:
        titulo = re.search(r'<title>(?:Reservada · )?([^|—]*)', p)
        texto = f"Hola, me interesa la {titulo.group(1).strip() if titulo else 'habitación'} — {precio}€/mes"
    return 'https://wa.me/34635771908?text=' + quote(texto, safe='')


def liberar(ficha):
    """Lo contrario de reservar: la habitación vuelve a estar disponible en portada y en su ficha."""
    s = open('index.html').read()
    ini, fin, tarjetas = _tarjetas(s)
    h = _datos(ficha)
    for t in tarjetas:
        if ficha in t and 'is-reservada' in t:
            n = t.replace('<div class="room-card reveal is-reservada">', '<div class="room-card reveal">')
            n = n.replace('<span class="room-badge reservada">Reservada</span>', '<span class="room-badge">Disponible</span>')
            if h.get('idealista'):
                enlace = (f'<a class="room-link secundario" href="https://www.idealista.com/pro/novos-real-estate-madrid/inmueble/{h["idealista"]}/" '
                          'target="_blank" rel="noopener">También en Idealista</a>')
            else:
                enlace = f'<a class="room-link secundario" href="{_wa_interesa(ficha, t)}" target="_blank" rel="noopener">Quiero verla →</a>'
            n = re.sub(r'<a class="room-link secundario" href="[^"]*"[^>]*>[^<]*</a>', enlace, n)
            s = s.replace(t, n)
            break
    else:
        print(f'  (aviso: {ficha} ya estaba disponible en la portada)')
    nuevo = _recolocar(s)
    _escribir('index.html', nuevo)

    p = open(ficha).read()
    wa = _wa_interesa(ficha, p)
    p = re.sub(r'<span class="reservada-tag">[^<]*</span>', '<span class="libre">Disponible ahora</span>', p)
    p = re.sub(r'\n  <div class="aviso-reservada">.*?\n  </div>\n', '', p, count=1, flags=re.S)
    p = re.sub(r'(<span class="k">Disponible</span><span class="v">)[^<]*(</span>)', r'\1Ahora\2', p)
    p = re.sub(r'<a class="btn btn-wa" href="[^"]*"([^>]*)>[^<]*</a>', f'<a class="btn btn-wa" href="{wa}"\\1>Quiero verla →</a>', p)
    if h.get('idealista') and 'btn btn-id' not in p:
        p = re.sub(r'(<a class="btn btn-wa"[^>]*>[^<]*</a>)',
                   r'\1' + f'\n        <a class="btn btn-id" href="https://www.idealista.com/pro/novos-real-estate-madrid/inmueble/{h["idealista"]}/" target="_blank" rel="noopener">Ver también en Idealista</a>', p, count=1)
    p = re.sub(r'<a class="nav-cta" href="[^"]*"', f'<a class="nav-cta" href="{wa}"', p, count=1)
    p = p.replace('<title>Reservada · ', '<title>', 1)
    p = p.replace('<meta property="og:title" content="Reservada · ', '<meta property="og:title" content="', 1)
    _escribir(ficha, p)
    print('disponible:', ficha)


def reservar(ficha):
    s = open('index.html').read()
    ini, fin, tarjetas = _tarjetas(s)
    for t in tarjetas:
        if ficha in t and 'is-reservada' not in t:
            n = t.replace('<div class="room-card reveal">', '<div class="room-card reveal is-reservada">')
            n = n.replace('<span class="room-badge">Disponible</span>', '<span class="room-badge reservada">Reservada</span>')
            n = re.sub(r'\n            <a class="room-link secundario" href="https://www\.idealista\.com[^"]*"[^>]*>[^<]*</a>',
                       f'\n            <a class="room-link secundario" href="{WA_ESPERA}" target="_blank" rel="noopener">Avísame si queda libre →</a>', n)
            s = s.replace(t, n)
            break
    else:
        print(f'  (aviso: {ficha} ya estaba reservada en la portada)')
    nuevo = _recolocar(s)
    _escribir('index.html', nuevo)

    p = open(ficha).read()
    p = re.sub(r'<span class="libre">[^<]*</span>', '<span class="reservada-tag">Reservada · no disponible</span>', p)
    if 'aviso-reservada">' not in p:
        p = re.sub(r'(<p class="migas">.*?</p>\n)', r'\1' + AVISO, p, count=1, flags=re.S)
    p = re.sub(r'(<span class="k">Disponible</span><span class="v">)[^<]*(</span>)', r'\1Reservada\2', p)
    p = re.sub(r'<a class="btn btn-wa" href="[^"]*"([^>]*)>[^<]*</a>',
               f'<a class="btn btn-wa" href="{WA_ESPERA}"\\1>Avísame si queda libre →</a>', p)
    p = re.sub(r'\n\s*<a class="btn btn-id" href="https://www\.idealista\.com[^"]*"[^>]*>[^<]*</a>', '', p)
    p = re.sub(r'<a class="nav-cta" href="[^"]*"', f'<a class="nav-cta" href="{WA_ESPERA}"', p, count=1)
    p = re.sub(r'<title>(?!Reservada)', '<title>Reservada · ', p, count=1)
    p = re.sub(r'(<meta property="og:title" content=")(?!Reservada)', r'\1Reservada · ', p, count=1)
    _escribir(ficha, p)
    print('reservada:', ficha)

if __name__ == '__main__':
    if len(sys.argv) < 3 or sys.argv[1] not in ('reservar', 'liberar'):
        print(__doc__); sys.exit(1)
    for f in sys.argv[2:]:
        if not os.path.exists(f):
            raise SystemExit(f'no existe la ficha {f}')
        (reservar if sys.argv[1] == 'reservar' else liberar)(f)
