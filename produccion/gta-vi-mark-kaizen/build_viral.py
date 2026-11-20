#!/usr/bin/env python3
"""Teaser viral GTA VI · Mark Kaizen. 9:16, colores naturales, cortes al beat, audio sintetizado (sin copyright)."""
import subprocess, os, math, wave, struct, random
import numpy as np
U = "/root/.claude/uploads/02b330e5-cc3f-569b-af09-0be7409b6328"
SHEET, HERO = f"{U}/41ca21f7-image.png", f"{U}/6a09ca98-image.jpg"
HERE = os.path.dirname(os.path.abspath(__file__)); W = os.path.join(HERE, "_w"); os.makedirs(W, exist_ok=True)
FPS, CLIP = 30, 14            # 14 frames = 1 beat a ~128 BPM; 1 corte por beat
FONT = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
def run(*a): subprocess.run(a, check=True, stderr=subprocess.DEVNULL)

# paneles: nombre -> (x,y,w,h, centro horizontal del rostro 0..1)
P = {"main":(0,0,775,810,.58),"p1":(782,0,238,362,.5),"p2":(1026,0,228,362,.5),"p3":(782,366,238,444,.5),
     "p4":(1026,366,228,444,.5),"b1":(0,822,420,432,.5),"b2":(424,822,428,432,.55),"b3":(856,822,398,432,.55)}
for n,(x,y,w,h,_) in P.items(): run("ffmpeg","-y","-i",SHEET,"-vf",f"crop={w}:{h}:{x}:{y}",f"{W}/{n}.png")
run("ffmpeg","-y","-i",HERO,f"{W}/hero.png"); P["hero"]=(0,0,560,747,.5)

A = ["main","hero","p3","b1","p2","b2","p1","b3","p4","hero","main","b2","p3","b1","b3","main"]
ORDER = A + ["b2","p1","hero","b1","p4","main","p2","b3","hero","p3","b2","main","b1","p1","b3","main"]
# color natural: saturación leve, sin vignette fuerte
GRADE = "eq=saturation=1.04:contrast=1.05:brightness=0.01,colorbalance=rs=.03:bs=.05:rh=.03:bh=.03,unsharp=5:5:0.6"
for i,n in enumerate(ORDER):
    w,h,cx = P[n][2],P[n][3],P[n][4]
    # relleno 9:16 completo (sin bandas): escala a cubrir y recorta centrando el rostro
    cw = min(w, h*9/16); cxp = max(0, min(w-cw, cx*w-cw/2))
    punch = "1.16-0.16*min(1,on/6)+0.0012*on" if i%2==0 else "1.0+0.16*max(0,1-on/6)+0.0008*on"
    vf = (f"crop={cw:.1f}:{h}:{cxp:.1f}:0,scale=2160:3840:flags=lanczos,"
          f"zoompan=z='{punch}':d={CLIP}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps={FPS},{GRADE},format=yuv420p")
    run("ffmpeg","-y","-i",f"{W}/{n}.png","-vf",vf,"-frames:v",str(CLIP),"-r",str(FPS),f"{W}/c{i:02d}.mp4")
with open(f"{W}/list.txt","w") as f: f.write("".join(f"file 'c{i:02d}.mp4'\n" for i in range(len(ORDER))))
run("ffmpeg","-y","-f","concat","-i",f"{W}/list.txt","-c","copy",f"{W}/seq.mp4")
DUR = len(ORDER)*CLIP/FPS

# audio: kick en cada beat (7 frames), hat a contratiempo, clap en 2 y 4, bajo
SR=44100; beat=CLIP/FPS; n=int(SR*DUR); t=np.arange(n)/SR; out=np.zeros(n)
def add(sig,at):
    s=int(at*SR); e=min(n,s+len(sig)); 
    if s<n: out[s:e]+=sig[:e-s]
rng=np.random.default_rng(1)
k=np.arange(int(SR*.3))/SR; kick=np.sin(2*np.pi*(45*k+110*(1-np.exp(-k*28))/28))*np.exp(-k*11)*.9
hk=np.arange(int(SR*.05))/SR; hat=rng.standard_normal(len(hk))*np.exp(-hk*90)*.18
cl=np.arange(int(SR*.18))/SR; clap=rng.standard_normal(len(cl))*np.exp(-cl*28)*.35
b=0
while b*beat<DUR:
    add(kick,b*beat); add(hat,b*beat+beat/2)
    if b%2==1: add(clap,b*beat)
    b+=1
roots=[55,55,65.4,49]  # bajo por compás (4 beats)
for bar in range(int(DUR/(4*beat))+1):
    f0=roots[bar%4]; s=bar*4*beat; seg=np.arange(int(SR*4*beat))/SR
    sig=np.sin(2*np.pi*f0*seg)*.22*(0.6+0.4*np.sin(2*np.pi*(1/beat)*seg)**2); add(sig,s)
    pad=sum(np.sin(2*np.pi*f0*m*seg) for m in (4,5,6))*.03*np.minimum(1,seg*4); add(pad,s)
out=np.tanh(out*1.4); out/=max(1e-9,abs(out).max())/0.9
fade=np.minimum(1,(DUR-t)/0.5); out*=fade
with wave.open(f"{W}/beat.wav","wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((out*32767).astype("<i2").tobytes())

def txt(text,y,size,t0,t1,color="white",extra=""):
    return (f"drawtext=fontfile={FONT}:text='{text}':fontsize={size}:fontcolor={color}:borderw=7:bordercolor=black:"
            f"x=(w-tw)/2:y={y}:enable='between(t,{t0},{t1})'{extra}")
vf = ",".join([
  "drawbox=0:0:iw:120:color=black@0.30:t=fill",
  f"drawtext=fontfile={FONT}:text='MARK KAIZEN':fontsize=40:fontcolor=white:x=50:y=40:borderw=3:bordercolor=black",
  f"drawtext=fontfile={FONT}:text='\\$ 000,000,000':fontsize=36:fontcolor=0x7CFC8A:x=w-tw-50:y=42:borderw=3:bordercolor=black",
  txt("ASÍ SERÍA",760,120,0,1.9), txt("MARK KAIZEN",900,120,0,1.9,"0xFFD54A"), txt("EN GTA VI",1040,120,0,1.9),
  txt("MEJORA CONTINUA",1500,76,5.6,8.4,"0xFF6B00"),
  txt("VICE CITY",1500,90,9.3,11.5),
  txt("SÍGUEME",1380,130,12.9,"99"),txt("PARA MÁS",1530,80,12.9,"99","white"),
])
run("ffmpeg","-y","-i",f"{W}/seq.mp4","-i",f"{W}/beat.wav","-vf",vf,"-c:v","libx264","-crf","17","-pix_fmt","yuv420p",
    "-c:a","aac","-b:a","192k","-shortest",os.path.join(HERE,"mark_kaizen_gta-vi-viral_9x16.mp4"))
print("ok",DUR)
