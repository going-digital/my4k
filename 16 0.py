import zlib

# Stage 1 is stored in UTF16 to maximise data efficiency. But each character of code costs 2 bytes.
stage1 = "\ufeff<script>(async()=>{z=0n;for(y of'{p}')z=z*63488n+BigInt(y.charCodeAt()^{x});a=[];while(z>>=8n)a.push(Number(z%256n));b=new Blob([new Uint8Array(a)]);a=await new Response(b.stream().pipeThrough(new DecompressionStream('deflate'))).blob();(1,eval)(await a.slice({pstart}).text())})()</script>"

# Stage 2 does initialisation and rendering
stage2 = """(async()=>{while(document.body===null)await new Promise(requestAnimationFrame);document.body.appendChild(b=document.createElement('button'));b.innerText="Precalc...";document.body.appendChild(c=document.createElement('canvas'));c.hidden=1;g=c.getContext('webgl');p=g.createProgram();s=g.createShader(g.VERTEX_SHADER);g.shaderSource(s,"attribute vec4 a;void main(){gl_Position=a;}");g.compileShader(s);g.attachShader(p,s);s=g.createShader(g.FRAGMENT_SHADER);g.shaderSource(s,`precision highp float;uniform vec3 u;
        void main(){
        vec2 p=vec2(2.*gl_FragCoord.xy-u.xy)/u.y;
        gl_FragColor=vec4(
            .5+.5*sin(p.xyx+u.z+vec3(0,2,4)),1
        );
}`);g.compileShader(s);g.attachShader(p,s);g.linkProgram(p);g.bindBuffer(g.ARRAY_BUFFER, g.createBuffer());g.bufferData(g.ARRAY_BUFFER,new Float32Array([-1,-1,-1,1,1,-1,1,1]),g.STATIC_DRAW);g.enableVertexAttribArray(g.getUniformLocation(p,'a'));g.vertexAttribPointer(0,2,g.FLOAT,false,0,0);var x,y,t=0;function render(){if(x!=document.body.clientWidth||y!=document.body.clientHeight){x=document.body.clientWidth;y=document.body.clientHeight;g.viewport(0,0,x,y);c.width=x;c.height=y;}g.clearColor(0,0,1,1);g.clear(g.COLOR_BUFFER_BIT);g.useProgram(p);g.uniform3fv(g.getUniformLocation(p,'u'),[x,y,t]);g.drawArrays(g.TRIANGLE_STRIP,0,4);t+=.033;window.requestAnimationFrame(render);}w=new Worker(URL.createObjectURL(new Blob(["self.onmessage=async e=>{a=(await WebAssembly.instantiateStreaming(fetch(e.data),{m:Math})).instance.exports;m=new Float32Array(a.m.buffer,a.s.value,a.l.value/4).map((v,i,d)=>d[i%(d.length/2)*2+~~(i/d.length)]);self.postMessage([m,a.l.value/8],[m.buffer])}"],{type:'application/javascript'})));w.onmessage=e=>{b.innerText="Play";b.onclick=(()=>{ac=new window.AudioContext;buffer=ac.createBuffer(2,e.data[1],44100);buffer.copyToChannel(e.data[0].slice(0,e.data[0].length/2), 0);buffer.copyToChannel(e.data[0].slice(e.data[0].length/2),1);src=ac.createBufferSource();src.buffer=buffer;src.connect(ac.destination);b.hidden=1;c.hidden=0;c.requestFullscreen();document.body.style.margin=document.body.style.padding=0;document.body.style.overflow='hidden';src.start();render();});};w.postMessage(window.URL.createObjectURL(a.slice({plstart},{plend},'application/wasm')));})()"""

for s in [
    # Replace WebGL literals with numeric value
    ('g.VERTEX_SHADER', '35633'),
    ('g.FRAGMENT_SHADER', '35632'),
    ('g.ARRAY_BUFFER', '34962'),
    ('g.STATIC_DRAW', '35044'),
    ('g.FLOAT', '5126'),
    ('g.COLOR_BUFFER_BIT', '16384'),
    ('g.TRIANGLE_STRIP', '5'),
]: stage2 = stage2.replace(*s)

# Link together pieces

# Big blob contains webassembly first
with open('16 wasm.wasm', 'rb') as fh:
    payload1 = fh.read()

# Then javascript (which needs to know length of webassembly)
payload2 = bytes(
    stage2
    .replace('{plstart}',str(0))
    .replace('{plend}',str(len(payload1))),
    encoding='utf-8'
)

# Compress the blob
compressor = zlib.compressobj(9)
payload = compressor.compress(payload1 + payload2) + compressor.flush()

# Encode the blob as base 63488
payload = bytes([0]) + payload # Add pad byte as first character ignored.
n=0
for c in payload[::-1]: n=n*256+c
ctrl_char = True
x=8191
while ctrl_char:
    ctrl_char=False
    x+=1
    if x>=0x27ff:
        raise("packing failed due to unavoidable control character")
    p=""
    n2=n;
    while n2:
        ch = (n2 % 63488) ^ x
        if (ch < 32) or (ch==ord("'")):
            ctrl_char=True
            break
        p = chr(ch) + p
        n2 //= 63488

# Build bootloader
result = stage1.replace('{p}',p).replace('{pstart}',str(len(payload1))).replace('{x}', str(x))
print("{} of 4096 bytes, {} bytes left".format(len(result)*2, 4096-len(result)*2))

with open('16 out.html', 'wb') as fh:
    fh.write(bytes(result, 'utf_16_le')) # utf_16_le
