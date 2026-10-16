"""Build a conventional two-page A4 CV with embedded TrueType fonts."""
from pathlib import Path
from html import escape
import json
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, KeepTogether
import reportlab
ROOT=Path(__file__).resolve().parents[1]
NAVY=colors.HexColor('#14213D');BLUE=colors.HexColor('#2563EB');MUTED=colors.HexColor('#52647A')
def e(s): return escape(s)
def build_pdf():
    p=json.loads((ROOT/'data/profile.json').read_text());c=p['contact']
    fonts=Path(reportlab.__file__).parent/'fonts'
    pdfmetrics.registerFont(TTFont('CV',str(fonts/'Vera.ttf')))
    pdfmetrics.registerFont(TTFont('CV-Bold',str(fonts/'VeraBd.ttf')))
    pdfmetrics.registerFontFamily('CV',normal='CV',bold='CV-Bold',italic='CV',boldItalic='CV-Bold')
    def style(name,size=9.7,leading=13.5,**kw):return ParagraphStyle(name,fontName='CV',fontSize=size,leading=leading,textColor=NAVY,**kw)
    body=style('body',9.7,13.5,spaceAfter=4)
    bullet=style('bullet',9.7,13.5,leftIndent=10,firstLineIndent=-8,spaceAfter=3)
    small=style('small',9.0,12.5,spaceAfter=4)
    section=ParagraphStyle('section',fontName='CV-Bold',fontSize=9.5,leading=13,textColor=BLUE,spaceBefore=10,spaceAfter=7)
    role_style=ParagraphStyle('role',fontName='CV-Bold',fontSize=10,leading=13,textColor=NAVY,spaceAfter=3)
    def P(t,s=body):return Paragraph(t,s)
    def heading(t):return P(e(t.upper()),section)
    def role(r):
        kind=' ('+r['employment_type']+')' if r['employment_type'] else ''
        parts=[P(e(r['company']+' | '+r['title']+kind),role_style),P(e(r['dates']),small)]
        parts.extend(P('• '+e(b),bullet) for b in r['pdf_bullets'])
        parts.append(Spacer(1,5))
        return KeepTogether(parts)
    story=[P(e(p['name']),ParagraphStyle('name',fontName='CV-Bold',fontSize=23,leading=29,textColor=NAVY,spaceAfter=5)),P(e(p['title']),style('title',11,15,spaceAfter=6)),P('<link href="'+e(c['website'])+'" color="#2563EB">'+e(c['website'])+'</link>',style('website',9.5,13,spaceAfter=5)),P('<link href="tel:'+c['tel']+'">'+e(c['phone'])+'</link> | <link href="mailto:'+e(c['email'])+'">'+e(c['email'])+'</link>',small),P('<link href="'+e(c['github'])+'">'+e(c['github'])+'</link> | <link href="'+e(c['telegram'])+'">'+e(c['telegram'])+'</link>',small),heading('Professional summary'),P(e(p['pdf_summary'])),heading('Core technical skills')]
    for skill in p['pdf_skills']:story.append(P('<b>'+e(skill['label'])+':</b> '+e(skill['text']),small))
    story.append(heading('Professional experience'))
    for r in p['roles'][:3]:story.append(role(r))
    story+=[PageBreak(),P(e(p['name'])+' | Professional experience continued',style('continued',10,15,spaceAfter=9))]
    for r in p['roles'][3:]:story.append(role(r))
    story+=[heading('Selected project'),P('<b>PipeForge</b> — '+e(p['pdf_project_summary'])),P('<link href="'+e(p['projects'][0]['url'])+'" color="#2563EB">'+e(p['projects'][0]['url'])+'</link>',small),heading('Education'),P(e(p['education'][0]['institution']),role_style)]
    for degree in p['education']:
        story.append(P(e(degree['qualification']+', '+degree['field']+' | '+degree['dates']),small))
    story+=[heading('Languages'),P(' | '.join(e(l['name']+' — '+l['level']) for l in p['languages'])),P('<b>GitHub:</b> <link href="'+e(c['github'])+'">'+e(c['github'])+'</link>',small)]
    def footer(cv,doc):
        cv.saveState();cv.setStrokeColor(colors.HexColor('#E2E8F0'));cv.setLineWidth(.5);cv.line(43,38,A4[0]-43,38)
        cv.setFillColor(MUTED);cv.setFont('CV',8)
        cv.drawString(43,24,c['website']);width=pdfmetrics.stringWidth(c['website'],'CV',8)
        cv.linkURL(c['website'],(43,21,43+width,33),relative=0,thickness=0)
        cv.drawRightString(A4[0]-43,24,f'{p["name"]} | {doc.page} / 2');cv.restoreState()
    class ResumeCanvas(canvas.Canvas):
        def __init__(self,*args,**kw):kw.update(invariant=1,initialFontName='CV');super().__init__(*args,**kw)
    dest=ROOT/'site/Vadym_Pyrozhenko_CV.pdf'
    doc=SimpleDocTemplate(str(dest),pagesize=A4,rightMargin=43,leftMargin=43,topMargin=35,bottomMargin=49,title=p['name']+' | '+p['title'],author=p['name'],subject='Professional resume',pageCompression=1)
    doc.build(story,onFirstPage=footer,onLaterPages=footer,canvasmaker=ResumeCanvas)
    (ROOT/'Vadym_Pyrozhenko_CV.pdf').write_bytes(dest.read_bytes())
    print('Generated A4 resume with embedded Vera fonts.')
if __name__=='__main__':build_pdf()
