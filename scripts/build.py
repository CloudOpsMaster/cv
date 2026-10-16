"""Generate the static CV, metadata and resume from data/profile.json."""
from pathlib import Path
from html import escape
import json, os
ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/profile.json'
def load_profile():
    return json.loads(DATA.read_text())
def esc(value):
    return escape(str(value), quote=True)
def tags(values):
    return '<ul class="tags" aria-label="Technologies and capabilities">' + ''.join('<li>'+esc(v)+'</li>' for v in values) + '</ul>'
def build_site():
    p=load_profile();c=p['contact'];site=ROOT/'site';site.mkdir(exist_ok=True)
    nav=''.join(f'<a href="#{x.lower()}">{x}</a>' for x in ['About','Expertise','Experience','Projects','Education','Contact'])
    category_paths={
        'cloud':'<path d="M7 18H6a4 4 0 0 1-.5-8A6.5 6.5 0 0 1 18 8a5 5 0 0 1 0 10H7z"/>',
        'containers':'<path d="M12 3l8 4.5v9L12 21l-8-4.5v-9L12 3zM4 7.5l8 4.5 8-4.5M12 12v9M8 5.2l8 4.5"/>',
        'automation':'<path d="M9 3h6l1 4 4 1v6l-4 1-1 4H9l-1-4-4-1V8l4-1z"/><circle cx="12" cy="11" r="3"/>',
        'delivery':'<path d="M12 12C7 3 2 7 2 12s5 9 10 0c5-9 10-5 10 0s-5 9-10 0z"/>',
        'observability':'<rect x="4" y="12" width="3" height="9" rx="1"/><rect x="10.5" y="7" width="3" height="14" rx="1"/><rect x="17" y="3" width="3" height="18" rx="1"/>',
        'systems':'<rect x="3" y="3" width="18" height="6" rx="2"/><rect x="3" y="9" width="18" height="6" rx="2"/><rect x="3" y="15" width="18" height="6" rx="2"/><path d="M7 6h.1M7 12h.1M7 18h.1"/>',
        'security':'<path d="M12 2l8 4v6c0 5-8 10-8 10S4 17 4 12V6l8-4z"/><path d="M12 6v12"/>',
        'ai':'<rect x="5" y="5" width="14" height="14" rx="2"/><path d="M9 1v4m6-4v4M9 19v4m6-4v4M1 9h4m-4 6h4M19 9h4m-4 6h4M9 15l2-6 2 6m-3-2h2m4-4v6"/>',
        'leadership':'<circle cx="9" cy="7" r="3"/><path d="M3 20v-2a6 6 0 0 1 12 0v2M16 4a3 3 0 0 1 0 6M17 14a5 5 0 0 1 4 4v2"/>'
    }
    expertise=''
    for i,skill in enumerate(p['skills']):
        theme=skill['theme']
        icon='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'+category_paths[theme]+'</svg>'
        rows=''
        for item in skill['items']:
            level=item['level'].lower()
            display_name=esc(item['name']).replace('/', '/<wbr>')
            rows+=f'<li class="skill-entry level-{level}"><img class="technology-icon" src="assets/skills/{esc(item["icon"])}.svg" alt="" width="25" height="25"><span class="skill-name">{display_name}</span><span class="skill-bar" aria-hidden="true"><span></span></span><span class="skill-level">{esc(item["level"])}</span></li>'
        expertise+=f'<article class="expertise-card proficiency-card category-{theme}" role="listitem"><div class="proficiency-card-heading"><span class="skill-category-number" aria-hidden="true">{i+1:02d}</span><span class="category-icon">{icon}</span><div><h3>{esc(skill["name"])}</h3><p>{esc(skill["description"])}</p></div></div><ul class="skill-entries" aria-label="{esc(skill["name"])} proficiency">{rows}</ul></article>'
    legend=''.join(f'<div class="legend-item level-{level["name"].lower()}"><span class="legend-swatch" aria-hidden="true"></span><div><strong>{esc(level["name"])}</strong><p>{esc(level["description"])}</p></div></div>' for level in p['proficiency']['levels'])
    experience=''
    for r in p['roles']:
        kind=f'<span class="employment-type">{esc(r["employment_type"])}</span>' if r['employment_type'] else ''
        experience+=f'<article class="experience-entry"><div class="experience-heading"><h3>{esc(r["company"])}</h3><p class="experience-dates">{esc(r["dates"])}</p></div><div class="job-meta"><p class="job-title">{esc(r["title"])}</p>{kind}</div><p class="job-context">{esc(r["context"])}</p><ul class="responsibilities">'+''.join('<li>'+esc(x)+'</li>' for x in r['responsibilities'])+'</ul>'+tags(r['technologies'])+'</article>'
    projects=''
    for project in p['projects']:
        link=f'<a class="inline-link" href="{esc(project["url"])}" target="_blank" rel="noopener noreferrer">View on GitHub <span aria-hidden="true">↗</span></a>' if project['url'] else ''
        projects+=f'<article class="project-card"><div class="project-heading"><h3>{esc(project["name"])}</h3><p class="project-type">{esc(project["type"])}</p></div><p>{esc(project["description"])}</p><p class="contribution"><strong>Contribution:</strong> {esc(project["contribution"])}</p><div class="project-bottom">{tags(project["technologies"])}{link}</div></article>'
    education=''.join(f'<article class="education-row"><div><h3>{esc(d["field"])}</h3><p>{esc(d["qualification"])} · {esc(d["dates"])}</p></div><time datetime="{d["graduation_year"]}">{d["graduation_year"]}</time></article>' for d in p['education'])
    person={'@context':'https://schema.org','@type':'Person','name':p['name'],'jobTitle':p['title'],'url':c['website'],'email':'mailto:'+c['email'],'telephone':c['tel'],'sameAs':[c['github'],c['telegram']],'knowsAbout':['AWS','Kubernetes','Terraform','DevOps','Infrastructure operations'],'alumniOf':{'@type':'CollegeOrUniversity','name':p['education'][0]['institution']}}
    values={**{k:esc(v) for k,v in c.items()},'name':esc(p['name']),'title':esc(p['title']),'it_years':p['it_years'],'devops_years':p['devops_years'],'hero_summary':esc(p['hero_summary']),'specialisms':' · '.join(map(esc,p['specialisms'])),'page_title':esc(p['name']+' | '+p['title']),'description':esc(p['meta']['description']),'navigation':nav,'structured_data':json.dumps(person,ensure_ascii=False).replace('<','\\u003c'),'about':''.join('<p>'+esc(a)+'</p>' for a in p['about']),'expertise':expertise,'proficiency_legend':legend,'proficiency_label':esc(p['proficiency']['label']),'experience':experience,'projects':projects,'institution':esc(p['education'][0]['institution']),'education':education,'languages':''.join('<div><dt>'+esc(l['name'])+'</dt><dd>'+esc(l['level'])+'</dd></div>' for l in p['languages'])}
    template=(ROOT/'templates/index.html').read_text()
    for key,value in values.items():template=template.replace('{{'+key+'}}',value)
    assert '{{' not in template,'Unresolved template variable'
    (site/'index.html').write_text(template)
    (site/'robots.txt').write_text('User-agent: *\nAllow: /\nSitemap: '+c['website']+'sitemap.xml\n')
    (site/'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>'+esc(c['website'])+'</loc></url></urlset>\n')
    (site/'.nojekyll').write_text('')
    (site/'build-info.json').write_text(json.dumps({'commit':os.environ.get('GITHUB_SHA','local'),'content_source':'data/profile.json'})+'\n')
    make_social_card(p)
    print('Generated website, SEO metadata and social image.')
def make_social_card(p):
    from PIL import Image,ImageDraw,ImageFont
    from reportlab import __file__ as reportlab_file
    fonts=Path(reportlab_file).parent/'fonts'
    regular=str(fonts/'Vera.ttf');bold=str(fonts/'VeraBd.ttf')
    im=Image.new('RGB',(1200,630),'#F8FBFF');d=ImageDraw.Draw(im)
    d.line((66,80,1134,80),fill='#E2E8F0',width=2)
    d.text((66,127),'PROFESSIONAL CV',font=ImageFont.truetype(regular,19),fill='#52647A')
    d.text((62,198),p['name'],font=ImageFont.truetype(bold,61),fill='#14213D')
    d.text((66,296),p['title'].split(' & ')[0]+' &' ,font=ImageFont.truetype(regular,37),fill='#2563EB')
    d.text((66,348),p['title'].split(' & ')[1],font=ImageFont.truetype(regular,37),fill='#2563EB')
    d.text((66,459),p['it_years']+' years in IT  /  '+p['devops_years']+' years in DevOps',font=ImageFont.truetype(regular,23),fill='#52647A')
    d.line((66,526,1134,526),fill='#E2E8F0',width=2)
    d.text((66,553),p['contact']['website'],font=ImageFont.truetype(regular,19),fill='#52647A')
    im.save(ROOT/'site/assets/social-card.png',optimize=True)
if __name__=='__main__':
    build_site()
    from build_pdf import build_pdf
    build_pdf()
