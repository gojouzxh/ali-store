"""Serve the Aviary Ledger with Python, without client-side JavaScript.

Run from any directory with Python 3.9+: python3 script.py
Then open http://localhost:8000. No third-party packages are required.
Search, filters, and dossiers use GET requests; browser mouse effects and
JavaScript timers are omitted. The existing CSS supplies visual styling.
This local prototype still uses the original demonstration bird records.
"""

import argparse
from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import mimetypes
from pathlib import Path
from string import Template
from urllib.parse import parse_qs, unquote, urlencode, urlsplit


ROOT = Path(__file__).resolve().parent
birds = [{'id': 1,
  'tag': 'budgie',
  'name': 'Grey/White',
  'sci': None,
  'family': None,
  'hatch': 'March 12, 2025',
  'life': '7-12 years',
  'wing': '25-30 cm',
  'habitat': 'Spacious flight cage with natural perches, food and water bowls, and toys',
  'diet': 'Budgie seed mix or formulated pellets, leafy greens, and safe vegetables',
  'status': None,
  'statusText': None,
  'call': 'Soft chirping, tweeting, and contact calls',
  'stat': None,
  'notes': None,
  'photo': 'images/bird-01.jpg',
  'photoAlt': 'Grey and white budgie'},
 {'id': 2,
  'tag': 'budgie',
  'name': 'Pale Yellow Budgies',
  'sci': None,
  'family': None,
  'hatch': 'April 5, 2025',
  'life': '7-12 years',
  'wing': '25-30 cm',
  'habitat': 'Spacious flight cage with natural perches, food and water bowls, and toys',
  'diet': 'Budgie seed mix or formulated pellets, leafy greens, and safe vegetables',
  'status': None,
  'statusText': None,
  'call': 'Soft chirping, tweeting, and contact calls',
  'stat': None,
  'notes': None,
  'photo': 'images/bird-02.jpg',
  'photoAlt': 'Pale yellow budgies'},
 {'id': 3,
  'tag': 'budgie',
  'name': 'Lutino Yellow',
  'sci': None,
  'family': None,
  'hatch': 'January 20, 2025',
  'life': '7-12 years',
  'wing': '25-30 cm',
  'habitat': 'Secure flight cage with horizontal bars, perches, toys, and room to move',
  'diet': 'Quality budgie seed mix or pellets, leafy greens, carrots, and clean drinking water',
  'status': None,
  'statusText': None,
  'call': 'Cheerful chirps, whistles, and short chatter',
  'stat': None,
  'notes': None,
  'photo': 'images/bird-03.jpg',
  'photoAlt': 'Yellow lutino budgie'},
 {'id': 4,
  'tag': 'budgie',
  'name': 'Green Budgies',
  'sci': None,
  'family': None,
  'hatch': 'February 14, 2025',
  'life': '7-12 years',
  'wing': '25-30 cm',
  'habitat': 'Secure flight cage with horizontal bars, perches, toys, and room to move',
  'diet': 'Quality budgie seed mix or pellets, leafy greens, carrots, and clean drinking water',
  'status': None,
  'statusText': None,
  'call': 'Cheerful chirps, whistles, and short chatter',
  'stat': None,
  'notes': None,
  'photo': 'images/bird-04.jpg',
  'photoAlt': 'Green budgies'},
 {'id': 5,
  'tag': 'budgie',
  'name': 'Blue/Violet Budgie',
  'sci': None,
  'family': None,
  'hatch': 'May 8, 2025',
  'life': '7-12 years',
  'wing': '25-30 cm',
  'habitat': 'Flight cage with natural wood perches, enrichment toys, and daily opportunities for '
             'safe exercise',
  'diet': 'Budgie pellets or seed mix, leafy vegetables, and occasional safe fruit',
  'status': None,
  'statusText': None,
  'call': 'High-pitched chirping, whistles, and flock contact calls',
  'stat': None,
  'notes': None,
  'photo': 'images/bird-05.jpg',
  'photoAlt': 'Blue and violet budgie'},
 {'id': 6,
  'tag': 'budgie',
  'name': 'Yellow Lutino Budgie',
  'sci': None,
  'family': None,
  'hatch': 'June 18, 2025',
  'life': '7-12 years',
  'wing': '25-30 cm',
  'habitat': 'Spacious cage with perches at different heights, toys, and a shaded resting area',
  'diet': 'Budgie seed mix or pellets, fresh greens, and safe vegetables',
  'status': None,
  'statusText': None,
  'call': 'Light chirping, squeaks, and melodic whistles',
  'stat': None,
  'notes': None,
  'photo': 'images/bird-06.jpg',
  'photoAlt': 'Yellow lutino budgie'},
 {'id': 7,
  'tag': 'budgie',
  'name': 'Yellow Lutino (Pair record)',
  'sci': None,
  'family': None,
  'hatch': 'November 22, 2024',
  'life': '7-12 years',
  'wing': '25-30 cm',
  'habitat': 'Flight cage with multiple perches, enrichment toys, and separate feeding spaces',
  'diet': 'Balanced budgie seed mix or pellets, leafy greens, vegetables, and fresh water',
  'status': None,
  'statusText': None,
  'call': 'Chirping, whistles, and social chatter',
  'stat': None,
  'notes': None,
  'photo': 'images/bird-07.jpg',
  'photoAlt': 'Yellow lutino budgie pair'},
 {'id': 8,
  'tag': 'budgie',
  'name': 'Blue (Pair record)',
  'sci': None,
  'family': None,
  'hatch': 'December 10, 2024',
  'life': '7-12 years',
  'wing': '25-30 cm',
  'habitat': 'Flight cage with multiple perches, enrichment toys, and separate feeding spaces',
  'diet': 'Balanced budgie seed mix or pellets, leafy greens, vegetables, and fresh water',
  'status': None,
  'statusText': None,
  'call': 'Chirping, whistles, and social chatter',
  'stat': None,
  'notes': None,
  'photo': 'images/bird-08.jpg',
  'photoAlt': 'Blue budgie pair'},
 {'id': 9,
  'tag': 'lovebird',
  'name': 'Blue Lovebirds',
  'sci': None,
  'family': None,
  'hatch': 'July 19, 2025',
  'life': '10-15 years',
  'wing': '24-28 cm',
  'habitat': 'Secure cage with sturdy perches, chew toys, and space for climbing and flapping',
  'diet': 'Lovebird pellets or a balanced seed mix, leafy greens, safe vegetables, and clean water',
  'status': None,
  'statusText': None,
  'call': 'Loud chirps, squeaks, and short squawks',
  'stat': None,
  'notes': None,
  'photo': 'images/bird-09.jpg',
  'photoAlt': 'Blue lovebirds'}]


FILTERS = ('all', 'budgie', 'lovebird')


def has_value(value):
    return value is not None and value != ''


def text_element(tag, class_name, value):
    return f'<{tag} class="{class_name}">{escape(str(value))}</{tag}>'


def optional_text(tag, class_name, value):
    return text_element(tag, class_name, value) if has_value(value) else ''


def static_file(url_path):
    """Resolve only public styles and images, never application/source files."""
    if url_path != '/css/style.css' and not url_path.startswith('/images/'):
        return None
    try:
        path = (ROOT / url_path.lstrip('/')).resolve()
        directory = (ROOT / ('css' if url_path == '/css/style.css' else 'images')).resolve()
        if not path.is_relative_to(directory) or not path.is_file():
            return None
    except (OSError, ValueError):
        return None
    return path


def photo_frame(bird, class_name, element_id=''):
    photo = bird.get('photo')
    file_path = static_file('/' + photo) if isinstance(photo, str) else None
    if file_path is None:
        content = '<div class="photo-placeholder">Photo unavailable</div>'
    else:
        content = (
            f'<img class="bird-photo" src="{escape("/" + photo, quote=True)}" '
            f'alt="{escape(bird.get("photoAlt") or "", quote=True)}" loading="lazy">'
        )
    id_attribute = f' id="{element_id}"' if element_id else ''
    return f'<div class="{class_name}"{id_attribute}>{content}</div>'


def page_url(query='', active_filter='all', bird_id=None):
    params = {'q': query, 'f': active_filter}
    if bird_id is not None:
        params['bird'] = str(bird_id)
    fragment = '#dossier' if bird_id is not None else '#grid'
    return '/?' + urlencode(params) + fragment


def filter_birds(query, active_filter):
    query = query.strip().lower()
    return [
        bird for bird in birds
        if (active_filter == 'all' or bird['tag'] == active_filter)
        and (not query or query in ' '.join(
            str(bird[key]) for key in ('name', 'sci', 'family', 'habitat')
            if has_value(bird[key])
        ).lower())
    ]


def render_cards(bird_list, query, active_filter):
    cards = []
    for index, bird in enumerate(bird_list):
        url = escape(page_url(query, active_filter, bird['id']), quote=True)
        cards.append(
            f'<a class="card reveal" href="{url}" '
            f'style="display: block; text-decoration: none; animation-delay: {index * 0.06}s">'
            '<div class="specimen-no">'
            + text_element('span', '', f"SPECIMEN NO. {str(bird['id']).zfill(2)}")
            + text_element('span', '', bird['tag'].upper())
            + '</div>'
            + photo_frame(bird, 'card-illus')
            + text_element('h3', 'card-name', bird['name'])
            + optional_text('p', 'card-sci', bird['sci'])
            + optional_text('div', 'card-stat', bird['stat'])
            + '<div class="card-tap">Open Dossier →</div></a>'
        )
    return ''.join(cards) or '<p role="status">No birds match your search.</p>'


def status_class(status):
    return {'lc': 'status-lc', 'nt': 'status-nt'}.get(status, 'status-vu')


def render_dossier(bird, query, active_filter):
    if bird is None:
        return ''
    close_url = escape(page_url(query, active_filter), quote=True)
    identity = ' · '.join(str(bird[key]) for key in ('sci', 'family') if has_value(bird[key]))
    fields = []
    for label, key in (
        ('Hatched', 'hatch'), ('Typical Lifespan', 'life'), ('Wingspan', 'wing'),
        ('Habitat', 'habitat'), ('Diet', 'diet'), ('Call', 'call'),
    ):
        if has_value(bird[key]):
            fields.append(
                '<div class="field show">'
                + text_element('div', 'field-label', label)
                + text_element('div', 'field-val', bird[key])
                + '</div>'
            )
    if has_value(bird['statusText']):
        fields.append(
            '<div class="field full show"><div class="field-label">Conservation Status</div>'
            '<div class="field-val">'
            + text_element('span', f"status-tag {status_class(bird['status'])}", bird['statusText'])
            + '</div></div>'
        )
    notes = ''
    if has_value(bird['notes']):
        notes = (
            '<div class="notes-box show" id="dNotes"><div class="field-label">Field Notes</div>'
            + escape(str(bird['notes'])) + '</div>'
        )
    return (
        '<div class="scrim open" id="scrim">'
        f'<a href="{close_url}" aria-label="Close dossier backdrop" '
        'style="position: fixed; inset: 0"></a>'
        '<section class="dossier" id="dossier" role="dialog" aria-modal="true" '
        'aria-labelledby="dName" style="z-index: 1">'
        f'<a class="dossier-close" id="closeBtn" href="{close_url}" '
        'aria-label="Close dossier" style="text-decoration: none" autofocus>✕</a>'
        '<div class="stamp" id="stamp">EXAMINED</div><div class="dossier-head">'
        + photo_frame(bird, 'dossier-illus', 'dPhoto')
        + '<div><h2 class="dossier-name" id="dName">' + escape(bird['name']) + '</h2>'
        + (f'<div class="dossier-sci" id="dSci">{escape(identity)}</div>' if identity else '')
        + '</div></div><div class="fields" id="dFields">' + ''.join(fields)
        + '</div>' + notes + '</section></div>'
    )


def render_page(query='', active_filter='all', bird=None):
    return Template((ROOT / 'index.html').read_text(encoding='utf-8')).substitute(
        body_style=' style="overflow: hidden"' if bird else '',
        active_filter=escape(active_filter, quote=True),
        query=escape(query, quote=True),
        all_active=' active' if active_filter == 'all' else '',
        budgie_active=' active' if active_filter == 'budgie' else '',
        lovebird_active=' active' if active_filter == 'lovebird' else '',
        cards=render_cards(filter_birds(query, active_filter), query, active_filter),
        dossier=render_dossier(bird, query, active_filter),
    )


class AviaryHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.handle_request(send_body=True)

    def do_HEAD(self):
        self.handle_request(send_body=False)

    def handle_request(self, send_body):
        try:
            url = urlsplit(self.path)
        except ValueError:
            self.send_error(400, 'Invalid request URL')
            return
        path = unquote(url.path)
        if path in ('/', '/index.html'):
            try:
                params = parse_qs(url.query, keep_blank_values=True, max_num_fields=20)
            except ValueError:
                self.send_error(400, 'Too many query parameters')
                return
            query = params.get('q', [''])[-1]
            active_filter = params.get('filter', params.get('f', ['all']))[-1]
            if active_filter not in FILTERS:
                self.send_error(400, 'Unknown bird filter')
                return
            bird = None
            if 'bird' in params:
                bird_id = params['bird'][-1]
                bird = next((item for item in birds if str(item['id']) == bird_id), None)
                if bird is None:
                    self.send_error(404, 'Bird not found')
                    return
            content = render_page(query, active_filter, bird).encode('utf-8')
            content_type = 'text/html; charset=utf-8'
        else:
            file_path = static_file(path)
            if file_path is None:
                self.send_error(404, 'File not found')
                return
            content = file_path.read_bytes()
            content_type = mimetypes.guess_type(str(file_path))[0] or 'application/octet-stream'
        self.send_response(200)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(content)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        if send_body:
            self.wfile.write(content)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host', default='127.0.0.1', help='Bind address (default: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=8000, help='HTTP port (default: 8000)')
    args = parser.parse_args()
    with ThreadingHTTPServer((args.host, args.port), AviaryHandler) as server:
        print(f'Aviary Ledger running at http://{args.host}:{args.port}', flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == '__main__':
    main()
