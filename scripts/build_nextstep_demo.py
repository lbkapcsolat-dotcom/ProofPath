from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import subprocess, json

ROOT = Path('dist/earth-evidence-demo')
ROOT.mkdir(parents=True, exist_ok=True)
OUT = Path('dist/Earth_Evidence_NextStep_Demo_V1.mp4')
W, H = 1280, 720
BG=(247,247,248); INK=(23,23,23); MUTED=(82,82,82); CARD=(255,255,255); LINE=(220,220,220)
REG='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
BOLD='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'

def F(path,size): return ImageFont.truetype(path,size)

def wrap(draw,text,font,maxw):
    words=text.split(); lines=[]; cur=''
    for w in words:
        t=(cur+' '+w).strip()
        if draw.textlength(t,font=font)<=maxw: cur=t
        else:
            if cur: lines.append(cur)
            cur=w
    if cur: lines.append(cur)
    return lines

def text_block(draw,x,y,text,font,fill,maxw,spacing=8):
    for line in wrap(draw,text,font,maxw):
        draw.text((x,y),line,font=font,fill=fill)
        y += font.size + spacing
    return y

def app_panel(im, claim='', evidence='', verdict='READY', category='Category: —', next_ev=''):
    d=ImageDraw.Draw(im)
    d.rounded_rectangle((665,35,1245,685),radius=22,fill=CARD,outline=LINE,width=2)
    d.text((700,65),'NextStep Earth Forward · offline ML',font=F(BOLD,15),fill=MUTED)
    d.text((700,100),'Earth Evidence',font=F(BOLD,38),fill=INK)
    d.text((700,155),'Environmental claim',font=F(BOLD,17),fill=INK)
    d.rounded_rectangle((700,185,1210,275),radius=12,fill=(252,252,252),outline=(200,200,200),width=1)
    text_block(d,715,200,claim or 'Planting one tree guarantees a city will never flood.',F(REG,17),INK,480,5)
    d.text((700,300),'Evidence',font=F(BOLD,17),fill=INK)
    d.rounded_rectangle((700,330,1210,420),radius=12,fill=(252,252,252),outline=(200,200,200),width=1)
    text_block(d,715,345,evidence or 'Trees may help reduce some stormwater runoff.',F(REG,17),INK,480,5)
    d.text((700,460),verdict,font=F(BOLD,31),fill=INK)
    d.text((700,505),category,font=F(BOLD,17),fill=INK)
    if next_ev:
        d.line((700,555,700,645),fill=INK,width=4)
        text_block(d,720,550,'Next evidence needed: '+next_ev,F(REG,15),INK,470,4)

def slide(name,title,body,app=None,footer=None):
    im=Image.new('RGB',(W,H),BG); d=ImageDraw.Draw(im)
    d.rounded_rectangle((35,35,625,685),radius=22,fill=CARD,outline=LINE,width=2)
    d.text((70,70),'NEXTSTEP HACKS 2026 · EARTH FORWARD',font=F(BOLD,16),fill=MUTED)
    y=text_block(d,70,115,title,F(BOLD,42),INK,510,5)+18
    text_block(d,70,y,body,F(REG,22),MUTED,510,9)
    if footer: text_block(d,70,615,footer,F(REG,14),MUTED,510,4)
    if app is not None: app_panel(im,**app)
    else:
        d.rounded_rectangle((665,60,1245,660),radius=22,fill=CARD,outline=LINE,width=2)
        d.text((710,105),'EARTH EVIDENCE V1',font=F(BOLD,24),fill=MUTED)
        bullets=['32 Earth-specific training pairs','10 untouched Earth holdout examples','Climate · Energy · Water · Waste','Biodiversity · Transport · General','Next-evidence guidance','No external AI API','No paid model or cloud inference']
        yy=170
        for b in bullets:
            d.ellipse((710,yy+7,720,yy+17),fill=INK)
            yy=text_block(d,740,yy,b,F(REG,21),INK,445,5)+18
    p=ROOT/name; im.save(p); return p

scenes=[
('Earth Evidence','A ProofPath-derived educational prototype for environmental evidence reasoning. It asks whether evidence supports a claim, contradicts it, or remains insufficient — and what evidence should come next.',{},'Claim ceiling: EDUCATIONAL_ENVIRONMENTAL_EVIDENCE_ASSESSMENT_ONLY'),
('What changed during NextStep?','The inherited ProofPath engine stays transparent and offline. This build adds a new Earth-specific corpus, environmental categories, a separate Earth holdout set, a redesigned interface, and a new next-evidence guidance step.',{},'Baseline disclosed separately from NextStep-specific work.'),
('The workflow','A learner enters an environmental claim and a piece of evidence. Earth Evidence returns SUPPORTED, CONTRADICTED, or INSUFFICIENT, identifies an Earth category, and converts the result into a concrete follow-up research question.',{},None),
('Demo 1 · SUPPORTED','The evidence directly states the same relationship as the claim. Earth Evidence accepts the support, then asks the learner to seek independent replication instead of treating one source as the end of the reasoning process.',{'claim':'Solar energy uses sunlight to generate electricity.','evidence':'Solar panels use sunlight to generate electricity.','verdict':'SUPPORTED','category':'Earth category: Energy','next_ev':'Seek an independent measurement or dataset across another place, time period, or sample.'},None),
('Demo 2 · CONTRADICTED','The claim says wind turbines burn coal. The evidence explicitly says they do not. The model places the pair in CONTRADICTED and asks the learner to verify the exact conflicting relationship and its source context.',{'claim':'Wind turbines burn coal to make electricity.','evidence':'Wind turbines do not burn coal; they use wind to generate electricity.','verdict':'CONTRADICTED','category':'Earth category: Energy','next_ev':'Verify the source, date, scale, and comparison baseline behind the conflict.'},None),
('Demo 3 · INSUFFICIENT','The evidence says trees can store carbon. That does not justify the much broader guarantee that one tree will stop global warming. Earth Evidence refuses to turn a partial observation into certainty.',{'claim':'Planting one tree guarantees global warming will stop.','evidence':'Trees can store carbon as they grow.','verdict':'INSUFFICIENT','category':'Earth category: Climate','next_ev':'Specify the missing scale, time window, baseline, measured outcome, and comparison.'},None),
('Why the extra step matters','Environmental debates often contain a real observation followed by a conclusion much larger than the evidence. The next-evidence prompt teaches what baseline, comparison, time window, measurement, or independent source is still missing.',{'claim':'One rainy day proves a drought is completely over.','evidence':'Rain may temporarily increase local water availability.','verdict':'INSUFFICIENT','category':'Earth category: Water','next_ev':'Define the drought baseline, duration, spatial scale, reservoir or soil metrics, and comparison period.'},None),
('Transparent technical scope','Everything runs in the browser. The current build uses the inherited three-class softmax/logistic-regression engine, 32 new Earth-specific training pairs, and 10 untouched Earth holdout examples.',None,'CI verification: Earth Evidence Tests = SUCCESS.'),
('Bounded, not overclaimed','A 10/10 result on a tiny curated holdout is only an implementation benchmark. Earth Evidence is not a climate model, scientific validator, policy recommendation engine, or automatic fact checker.',{},'The benchmark does not establish general-world accuracy.'),
('Earth Forward','The goal is simple: before a learner makes a stronger environmental conclusion, make the evidence boundary visible. Support what is supported, reject what is contradicted, and clearly name what is still missing.',{},'Live demo + public GitHub branch accompany the submission.')]

narrations=[
'Earth Evidence is a ProofPath-derived educational prototype built for the NextStep Earth Forward challenge. Its purpose is not to tell people what to believe about the environment. Instead, it teaches a disciplined evidence question: does the evidence actually support the claim, contradict it, or remain insufficient, and what evidence should come next?',
'The project starts from the previously submitted ProofPath baseline, and that inheritance is disclosed. During the NextStep build, I added a new Earth-specific training corpus, a separate Earth holdout set, environmental category detection, a redesigned Earth Forward interface, and a new next-evidence guidance step. The existing ProofPath classifier engine is reused rather than presented as brand-new work.',
'The workflow is intentionally simple. A learner enters an environmental claim and a piece of evidence. The browser-side model compares the pair and returns one of three outcomes: supported, contradicted, or insufficient. The interface also identifies a broad Earth category such as climate, energy, water, waste, biodiversity, or transport. Then the new feature asks what evidence would be needed next.',
'Here is a supported example. The claim says solar energy uses sunlight to generate electricity. The evidence says that solar panels use sunlight to generate electricity. The relationship is direct, so Earth Evidence places the pair in the supported class. It still does not stop there. The learner is asked to look for an independent measurement or dataset that tests the same energy claim in another place, time period, or sample.',
'Now a contradicted example. The claim says wind turbines burn coal to make electricity. The evidence explicitly says wind turbines do not burn coal and instead use wind to generate electricity. The conflict is visible in the wording, so the model places the pair in the contradicted class. The follow-up asks the learner to identify the exact conflict and verify the source, date, scale, and comparison baseline.',
'The insufficient class is especially important. This claim says that planting one tree guarantees global warming will stop. The evidence only states that trees can store carbon as they grow. That observation may be true, but it is nowhere near enough to justify the much broader guarantee. Earth Evidence keeps the conclusion conservative and asks for the missing scale, time window, baseline, measured outcome, and comparison.',
'That extra step is the main educational extension. Environmental discussions often contain a real observation followed by a conclusion that is much larger than the evidence. A rain event, one tree, one solar panel, or one wildlife sighting can be informative without proving a sweeping claim. Earth Evidence tries to make that boundary visible and convert uncertainty into a concrete research question.',
'Technically, the prototype is deliberately small and inspectable. It runs entirely in the browser. It uses the existing three-class softmax or logistic-regression engine, thirty-two Earth-specific training pairs, and ten untouched Earth holdout examples. No external AI API, paid model, account, CDN, model download, or cloud inference is required. The GitHub Actions verification for this branch completes successfully.',
'The claim ceiling matters. Ten out of ten on a tiny curated holdout does not mean general-world accuracy. Earth Evidence is not a climate model, scientific validator, policy recommendation engine, or automatic fact checker. It is an educational evidence-assessment prototype. The benchmark only shows that this bounded implementation behaves as designed on its fixed examples.',
'The Earth Forward goal is therefore straightforward: before a learner makes a stronger environmental conclusion, make the evidence boundary visible. Support what is supported, reject what is contradicted, and clearly name what is still missing. The live demo and public GitHub branch accompany this submission so the work, the inheritance, and the NextStep-specific changes can all be inspected.'
]

images=[]; audios=[]; durations=[]
for i,(title,body,app,footer) in enumerate(scenes,1):
    images.append(slide(f's{i}.png',title,body,app,footer))
    wav=ROOT/f'a{i}.wav'
    subprocess.run(['espeak','-v','en-us','-s','145','-w',str(wav),narrations[i-1]],check=True)
    audios.append(wav)
    dur=float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','default=nw=1:nk=1',str(wav)],text=True).strip())
    durations.append(dur)

(ROOT/'audio.txt').write_text('\n'.join([f"file '{p.resolve()}'" for p in audios]))
subprocess.run(['ffmpeg','-y','-f','concat','-safe','0','-i',str(ROOT/'audio.txt'),'-c:a','aac','-b:a','96k',str(ROOT/'narration.m4a')],check=True)
img_lines=[]
for p,dur in zip(images,durations):
    img_lines += [f"file '{p.resolve()}'",f'duration {dur:.3f}']
img_lines.append(f"file '{images[-1].resolve()}'")
(ROOT/'images.txt').write_text('\n'.join(img_lines))
subprocess.run(['ffmpeg','-y','-f','concat','-safe','0','-i',str(ROOT/'images.txt'),'-vf','fps=2,scale=1280:720,format=yuv420p','-c:v','libx264','-preset','veryfast','-crf','25',str(ROOT/'visual.mp4')],check=True)
subprocess.run(['ffmpeg','-y','-i',str(ROOT/'visual.mp4'),'-i',str(ROOT/'narration.m4a'),'-c:v','copy','-c:a','copy','-shortest',str(OUT)],check=True)
meta=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration,size','-of','json',str(OUT)],text=True))['format']
print(json.dumps({'output':str(OUT),'duration_seconds':float(meta['duration']),'bytes':int(meta['size'])},indent=2))
