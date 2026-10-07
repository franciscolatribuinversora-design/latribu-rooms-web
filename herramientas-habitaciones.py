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
AVISO = """
  <div class="aviso-reservada">
    <strong>Esta habitación ya está reservada</strong>
    <p>No está disponible para alquilar. Puedes verla para hacerte una idea de cómo son nuestros pisos y, si te encaja, escríbenos: te avisamos en cuanto quede libre una parecida.</p>
  </div>
"""

def _tarjetas(html):
    ini = html.index('      <div class="rooms-grid">')
    fin = html.index('      <p class="rooms-note">')
    bloque = html[ini:fin]
    return ini, fin, re.findall(r'        <div class="room-card reveal.*?\n        </div>\n', bloque, re.S)

def _recolocar(html):
    """Deja las disponibles en el primer grid y las reservadas en el segundo."""
    ini, fin, tarjetas = _tarjetas(html)
    libres = [t for t in tarjetas if 'is-reservada' not in t]
    reservadas = [t for t in tarjetas if 'is-reservada' in t]
    cabecera = re.search(r'      <div class="reservadas-head">.*?      </div>\n', html[ini:fin], re.S).group(0)
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
    open('index.html','w').write(_recolocar(s))

    p = open(ficha).read()
    p = re.sub(r'<span class="libre">[^<]*</span>', '<span class="reservada-tag">Reservada · no disponible</span>', p)
    if 'aviso-reservada">' not in p:
        p = re.sub(r'(<p class="migas">.*?</p>\n)', r'\1' + AVISO, p, count=1, flags=re.S)
    p = re.sub(r'(<span class="k">Disponible</span><span class="v">)[^<]*(</span>)', r'\1Reservada\2', p)
    p = re.sub(r'<a class="btn btn-wa" href="[^"]*"([^>]*)>[^<]*</a>',
               f'<a class="btn btn-wa" href="{WA_ESPERA}"\\1>Avísame si queda libre →</a>', p)
    p = re.sub(r'\n\s*<a class="btn btn-id" href="https://www\.idealista\.com[^"]*"[^>]*>[^<]*</a>', '', p)
    p = re.sub(r'<title>(?!Reservada)', '<title>Reservada · ', p, count=1)
    p = re.sub(r'(<meta property="og:title" content=")(?!Reservada)', r'\1Reservada · ', p, count=1)
    open(ficha,'w').write(p)
    print('reservada:', ficha)

if __name__ == '__main__':
    if len(sys.argv) < 3 or sys.argv[1] != 'reservar':
        print(__doc__); sys.exit(1)
    for f in sys.argv[2:]:
        reservar(f)
