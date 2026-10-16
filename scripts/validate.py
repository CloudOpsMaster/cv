"""Validate CV content, local links, metadata and the standalone PDF."""
import json, re
from html.parser import HTMLParser
from pathlib import Path
from pypdf import PdfReader
ROOT=Path(__file__).resolve().parents[1];SITE=ROOT/'site'
p=json.loads((ROOT/'data/profile.json').read_text())
class Document(HTMLParser):
    def __init__(self):super().__init__();self.ids=[];self.links=[];self.resources=[];self.text=[]
    def handle_starttag(self,tag,attrs):
        d=dict(attrs)
        if 'id' in d:self.ids.append(d['id'])
        if 'href' in d:self.links.append(d['href'])
        if 'src' in d:self.resources.append(d['src'])
    def handle_data(self,data):self.text.append(data)
html=(SITE/'index.html').read_text();doc=Document();doc.feed(html)
assert len(doc.ids)==len(set(doc.ids)),'Duplicate HTML IDs'
for ref in doc.links+doc.resources:
    if ref.startswith('#'):assert ref[1:] in doc.ids,ref
    elif ':' not in ref:assert (SITE/ref).is_file(),ref
for section in ['about','expertise','experience','projects','education','contact']:assert section in doc.ids
assert 'linkedin' not in html.lower()
assert not re.search(r'\{\{\w+\}\}',html)
assert p['name']+' | '+p['title'] in html.replace('&amp;','&')
assert f'<link rel="canonical" href="{p["contact"]["website"]}">' in html
schema=json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>',html,re.S).group(1))
assert schema['@type']=='Person' and schema['name']==p['name']
assert 150 <= len(' '.join(p['about']).split()) <= 220,'About length'
assert 60 <= len(p['pdf_summary'].split()) <= 90,'PDF summary length'
for f in ['sitemap.xml','robots.txt','.nojekyll','build-info.json','assets/InterVariable.woff2','assets/Inter-LICENSE.txt','assets/social-card.png']:assert (SITE/f).exists(),f
pdf=PdfReader(SITE/'Vadym_Pyrozhenko_CV.pdf')
assert len(pdf.pages)==2,f'Expected 2 pages, got {len(pdf.pages)}'
texts=[]
for page in pdf.pages:
    assert abs(float(page.mediabox.width)-595.276)<1 and abs(float(page.mediabox.height)-841.89)<1,'A4 size'
    text=page.extract_text();assert len(text)>1000,'Selectable text';texts.append(text)
    uris=[str(a.get_object()['/A'].get('/URI','')) for a in page.get('/Annots',[]) if a.get_object().get('/A')]
    assert p['contact']['website'] in uris,'Website footer link on every page'
    for font in page['/Resources']['/Font'].values():
        font=font.get_object();descriptor=font.get('/FontDescriptor')
        assert descriptor and descriptor.get_object().get('/FontFile2'),'All PDF fonts must be embedded TrueType'
combined=' '.join(texts);flat=' '.join(combined.split())
assert 'linkedin' not in combined.lower()
assert p['contact']['website'] in texts[0] and p['contact']['email'] in texts[0]
for r in p['roles']:
    assert r['company'] in combined and r['title'] in combined and r['dates'] in combined,(r['company'],'PDF chronology')
    assert r['company'] in html and r['dates'] in html,(r['company'],'website chronology')
    for bullet in r['pdf_bullets']:assert ' '.join(bullet.split()) in flat,(r['company'],'PDF bullet')
    assert all(b in ' '.join(doc.text) for b in r['responsibilities'])
print('PASS: content consistency, navigation, local assets, SEO, contacts, two A4 pages, selectable text, embedded fonts and PDF links.')
