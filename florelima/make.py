from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops
import numpy as np
U='/root/.claude/uploads/9702cbc9-38ed-5b48-9399-2d43a78d96f1/'
base=Image.open(U+'fcb1227d-image.jpg').convert('RGB')
cj=Image.open(U+'e55273ce-image.jpg').convert('RGB')
F='/usr/share/fonts/opentype/inter/InterDisplay-Black.otf'
FB='/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf'
font=lambda s,f=F: ImageFont.truetype(f,s)

# logo: white on transparent, from original piece
crop=np.array(base.crop((400,1160,690,1290))).astype(float)
a=np.clip((crop.min(axis=2)-115)/(205-115),0,1)
logo=Image.new('RGBA',(290,130),(255,255,255,0)); logo.putalpha(Image.fromarray((a*255).astype('uint8')))
logo.save('logo_florelima_extraido.png')

def text(img,xy,t,size,fill=(255,255,255),anchor='mm',f=F,stroke=0,shadow=True,sc=(0,0,0)):
    d=ImageDraw.Draw(img); ft=font(size,f)
    if shadow:
        sh=Image.new('RGBA',img.size,(0,0,0,0)); sd=ImageDraw.Draw(sh)
        sd.text((xy[0]+4,xy[1]+6),t,font=ft,fill=(0,0,0,170),anchor=anchor,stroke_width=stroke)
        sh=sh.filter(ImageFilter.GaussianBlur(6)); img.paste(sh,(0,0),sh)
    d.text(xy,t,font=ft,fill=fill,anchor=anchor,stroke_width=stroke,stroke_fill=sc)

def grad(img,y0,y1,top_a,bot_a,color=(0,0,0)):
    ov=Image.new('RGBA',img.size,(0,0,0,0)); px=ov.load()
    for y in range(max(0,y0),min(img.height,y1)):
        al=int(top_a+(bot_a-top_a)*(y-y0)/(y1-y0))
        for x in range(img.width): px[x,y]=color+(al,)
    img.alpha_composite(ov)

GOLD=(255,214,102); PINK=(255,120,170)

# A: misión especial (arriba)
A=base.convert('RGBA')
grad(A,0,330,120,0,(60,10,40))
text(A,(540,95),'MISIÓN ESPECIAL',112,GOLD,stroke=3,sc=(90,30,20))
text(A,(540,190),'Antes de GTA: compra flores',58,(255,255,255),f=FB)
A.convert('RGB').save('A_mision_especial_4x5.png')

# B: misión cumplida / respeto
B=base.convert('RGBA')
grad(B,820,1350,0,170,(30,5,25))
text(B,(540,985),'MISIÓN CUMPLIDA',104,GOLD,stroke=3,sc=(90,30,20))
text(B,(540,1068),'RESPETO +  · llegaste con flores',46,(255,255,255),f=FB)
B.alpha_composite(logo,(400,1160)); B.convert('RGB').save('B_mision_cumplida_4x5.png')

# C: escena CJ + Big Smoke
C=Image.new('RGBA',(1080,1350))
g=ImageDraw.Draw(C)
for y in range(1350):
    t=y/1349; g.line([(0,y),(1080,y)],fill=(int(255-60*t),int(140-70*t),int(170-60*t),255))
pic=cj.resize((960,int(194*960/259)),Image.LANCZOS).filter(ImageFilter.UnsharpMask(2,80,2))
C.paste(pic,(60,280))
ImageDraw.Draw(C).rectangle([56,276,1024,280+pic.height+4],outline=(255,255,255,255),width=4)
sub=Image.new('RGBA',(960,110),(0,0,0,150)); C.alpha_composite(sub,(60,280+pic.height-110))
text(C,(540,110),'MISIÓN ESPECIAL',112,GOLD,stroke=3,sc=(90,30,20))
text(C,(540,205),'Mañana sale GTA. Hoy toca esto:',46,(255,255,255),f=FB)
text(C,(540,280+pic.height-55),'“CJ, pasa por las flores primero.”',40,(255,255,255),f=FB,shadow=False)
text(C,(540,1062),'Primero las flores,',60,(255,255,255))
text(C,(540,1130),'después el GTA',60,(255,255,255))
lg=logo.resize((325,146),Image.LANCZOS); C.alpha_composite(lg,(377,1185))
C.convert('RGB').save('C_cj_bigsmoke_4x5.png')

# D: story 9:16
D=Image.new('RGBA',(1080,1920))
bg=base.resize((1536,1920),Image.LANCZOS).crop((228,0,1308,1920)).filter(ImageFilter.GaussianBlur(28))
D.paste(bg,(0,0)); grad(D,0,1920,70,70,(40,5,30))
D.alpha_composite(base.convert('RGBA'),(0,285))
text(D,(540,150),'MISIÓN ESPECIAL',112,GOLD,stroke=3,sc=(90,30,20))
text(D,(540,235),'Antes de GTA: compra flores',52,(255,255,255),f=FB)
text(D,(540,1760),'Pide tu ramo hoy 🌸'.replace(' 🌸',''),64,(255,255,255))
D.convert('RGB').save('D_story_9x16.png')
print('ok')
