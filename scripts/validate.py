"""Validate CV content, local links, metadata and the standalone PDF."""
import json, re
from html.parser import HTMLParser
from pathlib import Path
from pypdf import PdfReader
from content import resume_summary, resume_skill_text
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
for section in ['about','expertise','experience','education','contact']:assert section in doc.ids
assert 'projects' not in doc.ids and 'Selected work &amp; capabilities' not in html
assert 'ECTS' not in html
assert 'Hetzner Cloud' in html
assert 'linkedin' not in html.lower()
assert 'moldova' not in html.lower() and '>Location<' not in html
assert 'Senior DevOps' not in html
assert 'Infrastructure Operations | Technical Leadership | Cloud &amp; Platform Engineering' not in html
assert 'location' not in p['contact'] and 'positioning' not in p
assert not re.search(r'\{\{\w+\}\}',html)
assert p['name']+' | '+p['title'] in html.replace('&amp;','&')
assert f'<link rel="canonical" href="{p["contact"]["website"]}">' in html
schema=json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>',html,re.S).group(1))
assert schema['@type']=='Person' and schema['name']==p['name']
assert not any(k in schema for k in ['address','homeLocation','workLocation'])
assert 100 <= len(' '.join(p['about']).split()) <= 300,'About length'
assert 'Current interests' not in html and 'class="step-number"' not in html
assert 60 <= len(resume_summary(p).split()) <= 90,'PDF summary length'
for f in ['sitemap.xml','robots.txt','.nojekyll','build-info.json','assets/InterVariable.woff2','assets/Inter-LICENSE.txt','assets/social-card.png']:assert (SITE/f).exists(),f
assert p['contact']['tel']=='+380932441801'
assert p['contact']['whatsapp']=='https://wa.me/380932441801'
assert p['contact']['viber']=='viber://chat?number=%2B380932441801'
levels={entry['name'] for entry in p['proficiency']['levels']}
for group in p['skills']:
    assert group['technologies']==[item['name'] for item in group['items']]
    for item in group['items']:
        assert item['level'] in levels
        assert (SITE/'assets/skills'/(item['icon']+'.svg')).is_file()
assert 'Self-assessed proficiency' in html
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
assert ' '.join(resume_summary(p).split()) in flat, 'Current PDF summary'
for industry in p['industries']:assert industry in html.replace('&amp;','&') and industry in flat
for selection in p['pdf_skills']:
    assert ' '.join(resume_skill_text(p,selection).split()) in flat, selection['label']+' shared skill levels'
all_uris=[str(a.get_object()['/A'].get('/URI','')) for page in pdf.pages for a in page.get('/Annots',[]) if a.get_object().get('/A')]
for uri in [p['contact']['website'],p['contact']['github'],p['contact']['telegram'],'mailto:'+p['contact']['email'],'tel:'+p['contact']['tel'],p['contact']['whatsapp'],p['contact']['viber']]:assert uri in all_uris, uri
assert 'ECTS' not in combined and 'Selected project' not in combined
assert 'Hetzner Cloud' in combined
assert 'linkedin' not in combined.lower()
assert 'moldova' not in combined.lower() and 'location' not in combined.lower()
assert 'senior' not in (combined+' '+str(pdf.metadata)).lower()
assert 'Infrastructure Operations | Technical Leadership | Cloud & Platform Engineering' not in combined
assert p['contact']['website'] in texts[0] and p['contact']['email'] in texts[0]
assert p['contact']['phone'] in texts[0]
assert all(level in texts[0] for level in levels)
uris=[str(a.get_object()['/A'].get('/URI','')) for a in pdf.pages[0].get('/Annots',[]) if a.get_object().get('/A')]
assert p['contact']['whatsapp'] in uris and p['contact']['viber'] in uris
for language in p['languages']:
    assert language['name']+' — '+language['level'] in flat
for degree in p['education']:
    assert degree['qualification']+' — '+degree['field'] in flat
    assert ' '.join(degree['field'].split()) in flat
    assert ' '.join(degree['institution'].split()) in flat
    assert degree['dates'] in combined
    assert degree['field'] in html and degree['institution'] in html
assert p['contact']['github'] in [str(a.get_object()['/A'].get('/URI','')) for a in pdf.pages[1].get('/Annots',[]) if a.get_object().get('/A')]
for r in p['roles']:
    assert (SITE/r['logo']).is_file(), r['company']+' logo'
    assert r['company'] in combined and r['title'] in combined and r['dates'] in combined,(r['company'],'PDF chronology')
    assert r['company'] in html and r['dates'] in html,(r['company'],'website chronology')
    for bullet in r['pdf_bullets']:assert ' '.join(bullet.split()) in flat,(r['company'],'PDF bullet')
    assert all(b in ' '.join(doc.text) for b in r['responsibilities'])
print('PASS: content consistency, navigation, local assets, SEO, contacts, two A4 pages, selectable text, embedded fonts and PDF links.')
