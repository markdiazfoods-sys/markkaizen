from PIL import Image, ImageDraw, ImageFont, ImageFilter
import math
U='/root/.claude/uploads/9702cbc9-38ed-5b48-9399-2d43a78d96f1/'
base=Image.open(U+'fcb1227d-image.jpg').convert('RGBA')
cj=Image.open(U+'e55273ce-image.jpg').convert('RGB')
logo=Image.open('logo_florelima_extraido.png')
F='/usr/share/fonts/opentype/inter/InterDisplay-Black.otf'
FB='/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf'
GOLD=(255,214,102)
def text(img,xy,t,size,fill=(255,255,255),f=F,anchor='mm',stroke=0,sc=(90,30,20)):
    ft=ImageFont.truetype(f,size)
    sh=Image.new('RGBA',img.size,(0,0,0,0)); ImageDraw.Draw(sh).text((xy[0]+4,xy[1]+6),t,font=ft,fill=(0,0,0,170),anchor=anchor)
    sh=sh.filter(ImageFilter.GaussianBlur(6)); img.alpha_composite(sh)
    ImageDraw.Draw(img).text(xy,t,font=ft,fill=fill,anchor=anchor,stroke_width=stroke,stroke_fill=sc)
def grad(img,y0,y1,a0,a1,c=(30,5,25)):
    ov=Image.new('RGBA',img.size,(0,0,0,0)); d=ImageDraw.Draw(ov)
    for y in range(y0,y1): d.line([(0,y),(img.width,y)],fill=c+(int(a0+(a1-a0)*(y-y0)/(y1-y0)),))
    img.alpha_composite(ov)
def star(d,cx,cy,r,fill,outline):
    pts=[]
    for i in range(10):
        rr=r if i%2==0 else r*0.45; a=-math.pi/2+i*math.pi/5
        pts.append((cx+rr*math.cos(a),cy+rr*math.sin(a)))
    d.polygon(pts,fill=fill,outline=outline)
def stars(img,n,y=120):
    d=ImageDraw.Draw(img); r=62; gap=130; x0=540-2*gap
    for i in range(5):
        cx=x0+i*gap
        if i<n: star(d,cx,y,r,GOLD,(90,30,20)); star(d,cx,y,r,GOLD,(90,30,20))
        else: star(d,cx,y,r,None,(255,255,255,230))
def crop(box):
    w=box[2]-box[0]; return base.crop(box).resize((1080,int(1080*(box[3]-box[1])/w)),Image.LANCZOS)
def slide(i,bg,head,sub,full=False):
    s=bg.copy(); grad(s,0,330,150,0); grad(s,800,1350,0,200)
    stars(s,i)
    text(s,(540,980),head,70,GOLD,stroke=2)
    text(s,(540,1075),sub,44,(255,255,255),f=FB)
    s.alpha_composite(logo.resize((290,130)),(395,1190))
    s.convert('RGB').save(f'carrusel_{i}_de_5.png')
# fondo con logo original tapado: usar crops sin la zona del logo
full=base.copy()
box=(380,1150,710,1300); full.paste(full.crop(box).filter(ImageFilter.GaussianBlur(30)),box[:2])
slide(1,full,'NIVEL 1: se te olvidó','el detalle. Todavía estás a tiempo.')
slide(2,crop((250,150,890,950)),'NIVEL 2: ella ya','lo notó. Ya viene la mirada.')
slide(3,crop((480,280,1040,980)),'NIVEL 3: ya no contesta','tus mensajes. Las flores sí hablan.')
# slide 4: CJ + Big Smoke
C=Image.new('RGBA',(1080,1350)); g=ImageDraw.Draw(C)
for y in range(1350):
    t=y/1349; g.line([(0,y),(1080,y)],fill=(int(255-60*t),int(140-70*t),int(170-60*t),255))
pic=cj.resize((960,719),Image.LANCZOS).filter(ImageFilter.UnsharpMask(2,80,2)); C.paste(pic,(60,220))
ImageDraw.Draw(C).rectangle([56,216,1024,943],outline=(255,255,255,255),width=4)
sb=Image.new('RGBA',(960,100),(0,0,0,150)); C.alpha_composite(sb,(60,839))
text(C,(540,889),'“CJ, ¿y las flores?”',44,(255,255,255),f=FB)
slide(4,C,'NIVEL 4: hasta Big Smoke','te regaña. Pide las flores ya.')
# slide 5 CTA
s5=full.copy()
slide(5,s5,'NIVEL 5: solo flores te salvan','Pide tu ramo Florelima hoy',)
