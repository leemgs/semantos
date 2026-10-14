"""Check every bib entry against its official record.

Sources: ACL Anthology BibTeX, Crossref, the arXiv API, OpenReview (ICLR, ICML,
NeurIPS) and publisher landing pages (citation_* meta tags). Reports title,
author surnames, year, pages and venue mismatches; DBLP and Semantic Scholar
are not used because they block or rate-limit scripted access.

    python3 scripts/check_references.py paper/reference-data.bib [cited-keys.txt]
"""
import json, re, sys, time, unicodedata, urllib.parse, urllib.request
import xml.etree.ElementTree as ET
import bibtexparser

def get(url, accept=None, tries=5):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'refcheck/1.0 (mailto:research@example.org)',
                                                       **({'Accept': accept} if accept else {})})
            with urllib.request.urlopen(req, timeout=40) as r:
                return r.status, r.read().decode('utf-8', 'replace')
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503) and i < tries - 1:
                time.sleep(15 * (i + 1)); continue
            return e.code, ''
        except Exception as e:
            if i < tries - 1: time.sleep(3); continue
            return None, str(e)

def norm(s):
    s = unicodedata.normalize('NFKD', s or '')
    s = re.sub(r"""\\[`'"^~=.]\{?([a-zA-Z])\}?""", r'\1', s)  # LaTeX accents
    s = re.sub(r'\\[a-zA-Z]+|[{}$\\]', '', s)
    s = ''.join(c for c in s if not unicodedata.combining(c))
    return re.sub(r'[^a-z0-9]+', ' ', s.lower()).strip()

def last(name):
    name = name.strip()
    return norm(name.split(',')[0] if ',' in name else name.split()[-1]).replace(' ', '')

def surnames(authors):
    return [last(a) for a in re.split(r'\s+and\s+', authors or '') if a.strip()]

def cmp_authors(bib, rec):
    b, r = surnames(bib), [last(x) for x in rec if norm(x)]
    if not r: return None
    if 'others' in b: b = [x for x in b if x != 'others']; r = r[:len(b)]
    if b == r: return None
    return f'authors bib={b[:6]}{"..." if len(b)>6 else ""}({len(b)}) rec={r[:6]}{"..." if len(r)>6 else ""}({len(r)})'

db = bibtexparser.load(open(sys.argv[1]))
cited = set(open(sys.argv[2]).read().split()) if len(sys.argv) > 2 else None
for e in db.entries:
    key, title, url = e['ID'], e.get('title', ''), re.search(r'refurl\{([^}]*)\}', e.get('note', ''))
    url = url.group(1) if url else e.get('url', '')
    issues, src = [], ''
    year = e.get('year', '')
    venue = e.get('booktitle', e.get('journal', ''))
    pages = e.get('pages', '').replace('--', '-')
    rec_title, rec_auth, rec_year, rec_venue, rec_pages = None, [], None, None, None
    m = re.search(r'aclanthology\.org/([^/]+)/?', url)
    if m:
        src = 'ACL Anthology'
        st, b = get(f'https://aclanthology.org/{m.group(1)}.bib')
        if st != 200: issues.append(f'anthology {st}')
        else:
            r = bibtexparser.loads(b).entries[0]
            rec_title, rec_auth, rec_year = r.get('title'), re.split(r'\s+and\s+', r.get('author', '')), r.get('year')
            rec_venue, rec_pages = r.get('booktitle', r.get('journal')), r.get('pages', '').replace('--', '-')
    elif 'doi.org/' in url:
        src = 'Crossref'
        doi = url.split('doi.org/')[1]
        st, b = get('https://api.crossref.org/works/' + urllib.parse.quote(doi))
        if st != 200: issues.append(f'crossref {st}')
        else:
            r = json.loads(b)['message']
            rec_title = (r.get('title') or [''])[0]
            rec_auth = [a.get('family', a.get('name', '')) for a in r.get('author', [])]
            dp = (r.get('published-print') or r.get('published-online') or r.get('issued'))['date-parts'][0]
            rec_year = str(dp[0]); rec_venue = (r.get('container-title') or [''])[0]; rec_pages = r.get('page', '')
    elif 'arxiv.org/abs/' in url:
        src = 'arXiv'
        aid = url.split('arxiv.org/abs/')[1].strip('/')
        st, b = get('http://export.arxiv.org/api/query?id_list=' + aid)
        if st != 200: issues.append(f'arxiv {st}')
        else:
            ns = {'a': 'http://www.w3.org/2005/Atom'}
            ent = ET.fromstring(b).find('a:entry', ns)
            if ent is None or ent.find('a:title', ns) is None: issues.append('arxiv id not found')
            else:
                rec_title = ' '.join(ent.find('a:title', ns).text.split())
                rec_auth = [a.find('a:name', ns).text for a in ent.findall('a:author', ns)]
                if e['ENTRYTYPE'] == 'misc': rec_year = ent.find('a:published', ns).text[:4]
        time.sleep(6)
    elif url:
        src = 'landing page'
        st, b = get(url)
        if st != 200: issues.append(f'url {st}')
        else:
            mt = re.search(r'<meta name="citation_title" content="([^"]*)"', b) or re.search(r'<title>(.*?)</title>', b, re.S)
            rec_title = mt.group(1) if mt else None
            rec_auth = re.findall(r'<meta name="citation_author" content="([^"]*)"', b)
            my = re.search(r'<meta name="citation_(?:publication_)?date" content="(\d{4})', b)
            rec_year = my.group(1) if my else None
    if rec_title is not None:
        nt, nr = norm(title), norm(rec_title)
        if nt != nr and not (src == 'landing page' and nt in nr):
            issues.append(f'title bib="{title[:70]}" rec="{rec_title[:70]}"')
    if rec_auth and e.get('author'):
        a = cmp_authors(e['author'], rec_auth)
        if a: issues.append(a)
    if rec_year and year and rec_year != year: issues.append(f'year bib={year} rec={rec_year}')
    if rec_pages and pages and rec_pages != pages: issues.append(f'pages bib={pages} rec={rec_pages}')
    if rec_venue and venue and norm(rec_venue) != norm(venue) and src == 'ACL Anthology':
        issues.append(f'venue bib="{venue[:60]}" rec="{rec_venue[:60]}"')
    # Venue check for published entries linked via arXiv: OpenReview (ICLR/ICML/NeurIPS) or Crossref
    if e['ENTRYTYPE'] != 'misc' and src == 'arXiv':
        found = None
        if re.search(r'Learning Representations|Machine Learning|Neural Information', venue):
            st, b = get('https://api2.openreview.net/notes/search?limit=25&term=' + urllib.parse.quote(title))
            if st == 200:
                for n in json.loads(b).get('notes', []):
                    c = n.get('content', {})
                    t = c.get('title', {}); t = t.get('value') if isinstance(t, dict) else t
                    v = c.get('venue', {}); v = v.get('value') if isinstance(v, dict) else v
                    if norm(t or '') == norm(title) and v and 'Submitted' not in v and 'Withdrawn' not in v:
                        found = v; break
            if found:
                src += f' + OpenReview[{found}]'
                if year not in found: issues.append(f'OpenReview venue {found!r} vs bib year {year}')
            else:
                issues.append(f'OpenReview: no accepted record for {venue[:45]!r}')
        else:
            st, b = get('https://api.crossref.org/works?rows=5&query.bibliographic=' + urllib.parse.quote(title))
            if st == 200:
                for it in json.loads(b)['message']['items']:
                    if norm((it.get('title') or [''])[0]) == norm(title) and 'arxiv' not in (it.get('publisher') or '').lower():
                        dp = (it.get('published-print') or it.get('published-online') or it.get('issued'))['date-parts'][0]
                        found = ((it.get('container-title') or [''])[0], str(dp[0]), it.get('page', ''), it.get('DOI'))
                        break
            if found:
                src += f' + Crossref[{found[0][:40]} {found[1]} {found[3]}]'
                if found[1] != year: issues.append(f'Crossref year {found[1]} vs bib {year}')
                if found[2] and pages and found[2] != pages: issues.append(f'Crossref pages {found[2]} vs bib {pages}')
            else:
                issues.append(f'Crossref: no published record for {venue[:45]!r}')
        time.sleep(1)
    flag = 'OK ' if not issues else 'CHK'
    unc = '' if cited is None or key in cited else ' (not cited)'
    print(f'{flag} {key}{unc} [{src or "no URL"}]' + ''.join(f'\n      - {x}' for x in issues), flush=True)
