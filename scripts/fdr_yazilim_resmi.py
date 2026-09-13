#!/usr/bin/env python3
"""NEDEN: FDR yazılım bölümünü DDR tipografisiyle, ölçüm sınırlarını koruyarak dizmek."""
import json
import re
from pathlib import Path
from xml.sax.saxutils import escape
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image, Flowable
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from pypdf import PdfReader

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'FDR/FDR_YZLM_003H_icerik.json'
OUT=ROOT/'FDR/pdf/FDR_YZLM_003H.pdf'
FONT=Path('/usr/share/fonts/google-carlito-fonts')
for n,f in [('C','Carlito-Regular.ttf'),('CB','Carlito-Bold.ttf'),('CI','Carlito-Italic.ttf')]:
    pdfmetrics.registerFont(TTFont(n,str(FONT/f)))
pdfmetrics.registerFontFamily('C',normal='C',bold='CB',italic='CI',boldItalic='CB')
W,H=A4; M=70.87; CW=W-2*M
BLUE=colors.HexColor('#2E5E88'); DARK=colors.HexColor('#24425C'); PALE=colors.HexColor('#EDF1F4')
ST={
'p':ParagraphStyle('p',fontName='C',fontSize=11,leading=14.2,spaceAfter=8,alignment=TA_JUSTIFY),
'h':ParagraphStyle('h',fontName='CB',fontSize=15,leading=18,spaceBefore=0,spaceAfter=13,textColor=BLUE,keepWithNext=True),
'sub':ParagraphStyle('sub',fontName='CB',fontSize=12,leading=15,spaceBefore=10,spaceAfter=7,keepWithNext=True),
'cap':ParagraphStyle('cap',fontName='CI',fontSize=9.5,leading=11.8,spaceBefore=5,spaceAfter=10,alignment=TA_CENTER),
'note':ParagraphStyle('note',fontName='C',fontSize=9.6,leading=12.2,spaceAfter=8),
'cell':ParagraphStyle('cell',fontName='C',fontSize=9.7,leading=12),
'head':ParagraphStyle('head',fontName='CB',fontSize=9.7,leading=12,textColor=colors.white),
'cover':ParagraphStyle('cover',fontName='CB',fontSize=24,leading=29,spaceAfter=10),
}
CITE_RE=re.compile(r'\[(\d+(?:,\d+)*)\]')
REF_LEAD_RE=re.compile(r'^\[(\d+)\]')
def _supercite(t):
    def repl(m):
        return ''.join(f'<super><a href="#ref{n}" color="#2E5E88">[{n}]</a></super>' for n in m.group(1).split(','))
    return CITE_RE.sub(repl,t)
def p(s,style='p'):
    t=escape(s)
    lead=REF_LEAD_RE.match(s)
    if lead and style=='note':
        n=lead.group(1);tag=f'[{n}]'
        t=f'<a name="ref{n}"/>{tag}{_supercite(t[len(tag):])}'
    else:
        t=_supercite(t)
    return Paragraph(t.replace('\n','<br/>'),ST[style])

class Chart(Flowable):
    def __init__(self,rows): self.rows=rows; self.width=CW; self.height=30+len(rows)*43
    def draw(self):
        c=self.canv;start=173; span=CW-start-51
        for i,(label,n,d) in enumerate(self.rows):
            y=self.height-33-i*43
            c.setFont('C',10);c.setFillColor(colors.black);c.drawString(0,y+4,label)
            c.setFillColor(PALE);c.rect(start,y,span,18,fill=1,stroke=0)
            c.setFillColor(BLUE);c.rect(start,y,span*n/d,18,fill=1,stroke=0)
            c.setFillColor(colors.black);c.setFont('CB',10);c.drawString(start+span+7,y+4,f'{n}/{d}')
        c.setFont('C',9);c.setFillColor(colors.HexColor('#555555'))
        c.drawString(start,2,'Başarı oranı: 0%');c.drawRightString(start+span,2,'100%')

class Chain(Flowable):
    def __init__(self,labels):self.labels=labels;self.width=CW;self.height=len(labels)*44-10
    def draw(self):
        c=self.canv;bw=CW-92;x=46
        for i,label in enumerate(self.labels):
            y=self.height-34-i*44
            c.setFillColor(PALE);c.setStrokeColor(DARK);c.setLineWidth(.6);c.roundRect(x,y,bw,34,4,fill=1,stroke=1)
            q=p(label,'cell');_,h=q.wrap(bw-18,32);q.drawOn(c,x+9,y+(34-h)/2)
            if i<len(self.labels)-1:
                cy=y-8;c.line(CW/2,y,CW/2,cy)
                c.line(CW/2-3,cy+3,CW/2,cy);c.line(CW/2+3,cy+3,CW/2,cy)

class Architecture(Flowable):
    def __init__(self):
        Flowable.__init__(self)
        self.width=CW;self.height=205
    def draw(self):
        c=self.canv
        def box(x,y,w,h,title,desc):
            c.setFillColor(PALE);c.setStrokeColor(DARK);c.setLineWidth(.7);c.roundRect(x,y,w,h,3,fill=1,stroke=1)
            q=p(title,'head');q=Paragraph(escape(title),ParagraphStyle('dt',parent=ST['head'],textColor=DARK))
            _,hh=q.wrap(w-16,h);q.drawOn(c,x+8,y+h-hh-8)
            q=p(desc,'cell');_,hh=q.wrap(w-16,h);q.drawOn(c,x+8,y+9)
        box(0,116,136,75,'Uçuş kontrolü','Pixhawk 6C\nMAVLink 2')
        box(164,116,136,75,'İHA görev yazılımı','Kamera ve Jetson\nAlgı / karar / yayın')
        box(328,116,125,75,'Yer istasyonu','Görüntü / telemetri\nHakem onayı')
        box(164,5,136,67,'İKA görev yazılımı','Rota alıcısı\nGezinim / sürücü')
        def arrow(x1,y1,x2,y2):
            c.setStrokeColor(DARK);c.line(x1,y1,x2,y2)
            if y1==y2:
                s=1 if x2>x1 else -1;c.line(x2-4*s,y2+3,x2,y2);c.line(x2-4*s,y2-3,x2,y2)
            else:c.line(x2-3,y2+4,x2,y2);c.line(x2+3,y2+4,x2,y2)
        arrow(136,155,164,155);arrow(300,155,328,155);arrow(232,116,232,72)
        c.setFont('C',9);c.setFillColor(DARK);c.drawString(238,89,'Rota + ACK')
        c.line(390,116,390,39);arrow(390,39,300,39)
        c.drawRightString(448,79,'İzin / komut')

def tab(head,rows,widths=None):
    if widths is None: widths=[1]*len(head)
    widths=[CW*v/sum(widths) for v in widths]
    a=[[p(x,'head') for x in head]]+[[p(str(x),'cell') for x in row] for row in rows]
    t=Table(a,colWidths=widths,repeatRows=1,hAlign='LEFT')
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),DARK),('VALIGN',(0,0),(-1,-1),'TOP'),
        ('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),
        ('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),
        ('GRID',(0,0),(-1,-1),.4,colors.HexColor('#A7B0B9')),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#F7F8F9')])]))
    return t

class Pages(canvas.Canvas):
    def __init__(self,*a,**kw):super().__init__(*a,**kw);self.states=[]
    def showPage(self):self.states.append(dict(self.__dict__));self._startPage()
    def save(self):
        total=len(self.states)
        for s in self.states:
            self.__dict__.update(s)
            self.setFillColor(colors.black);self.setFont('CB',10);self.drawCentredString(W/2,H-35,'TASNİF DIŞI')
            self.setFont('C',9);self.drawCentredString(W/2,31,f'TASNİF DIŞI - Sayfa {self._pageNumber} / {total}')
            self.setFont('C',8);self.drawString(M,18,'FDR_YZLM_003H');self.drawRightString(W-M,18,'14.09.2026')
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

def main():
    data=json.loads(DATA.read_text());story=[]
    for i,page in enumerate(data['pages']):
        if i:story.append(PageBreak())
        for b in page:
            kind=b['k']
            if kind in ST:story.append(p(b['s'],kind))
            elif kind=='t':story.extend([tab(b['head'],b['rows'],b.get('w')),Spacer(1,9)])
            elif kind=='chart':story.append(Chart(b['rows']))
            elif kind=='chain':story.append(Chain(b['labels']))
            elif kind=='architecture':story.append(Architecture())
            elif kind=='image':
                from PIL import Image as PI
                f=ROOT/b['path']; iw,ih=PI.open(f).size;ww=CW;hh=ww*ih/iw
                if hh>b.get('maxh',270):hh=b.get('maxh',270);ww=hh*iw/ih
                story.append(Image(str(f),width=ww,height=hh,hAlign='CENTER'))
            elif kind=='space':story.append(Spacer(1,b['h']))
    doc=SimpleDocTemplate(str(OUT),pagesize=A4,rightMargin=M,leftMargin=M,topMargin=70,bottomMargin=62,
      title='NAVITAS Final Değerlendirme Raporu Yazılım Bölümü',author='NAVITAS',subject='FDR yazılım mimarisi ve doğrulama sonuçları')
    doc.build(story,canvasmaker=Pages)
    reader=PdfReader(OUT)
    print(f'PDF: {len(reader.pages)} sayfa; hedef {len(data["pages"])}; {OUT.stat().st_size} bayt')
    if len(reader.pages)!=len(data['pages']):raise SystemExit('Sayfa taşması: QA ve yeniden dizgi gerekli')
if __name__=='__main__':main()
