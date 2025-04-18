import math
import sys
import threading
from base64 import b64encode, b64decode
from io import BytesIO

from PIL import Image, ImageFilter

import webview

BLUR_R = 0.035
WIDTH = 1920
HEIGHT = 1080
CHILDREN_SIZE = 0.6
DIM = 0.6

SHADER_ALPHA = 0.5
SHADER_POWER = 0.035

def rotate_point(x, y, θ, r) -> tuple[float, float]:
    xo = r * math.cos(math.radians(θ))
    yo = r * math.sin(math.radians(θ))
    return x + xo, y + yo

def compute_intersection(
    x0: float, y0: float,
    x1: float, y1: float,
    x2: float, y2: float,
    x3: float, y3: float
):
    a1 = y1 - y0
    b1 = x0 - x1
    c1 = x1 * y0 - x0 * y1
    a2 = y3 - y2
    b2 = x2 - x3
    c2 = x3 * y2 - x2 * y3
    return (b2 * c1 - b1 * c2) / (a1 * b2 - a2 * b1), (a1 * c2 - a2 * c1) / (a1 * b2 - a2 * b1)

def getDPower(width: float, height: float, deg: float):
    l1 = 0, 0, width, 0
    l2 = 0, height, *rotate_point(0, height, deg, (width ** 2 + height ** 2) ** 0.5)
    return compute_intersection(*l1, *l2)[0] / width

MAIN_JS = f"""\
const canvas = document.createElement("canvas");
const ctx = canvas.getContext("2d");
const img = new Image();
const blurimg = new Image();
const dpower = {getDPower(WIDTH, HEIGHT, 75)};
const children_size = {CHILDREN_SIZE};
const [w, h] = [{WIDTH}, {HEIGHT}];
var loaded = 0;
var result = null;

CanvasRenderingContext2D.prototype.diagonalRectangle = function(x0, y0, x1, y1, power) {{
    this.moveTo(x0 + (x1 - x0) * power, y0);
    this.lineTo(x1, y0);
    this.lineTo(x1 - (x1 - x0) * power, y1);
    this.lineTo(x0, y1);
    this.lineTo(x0 + (x1 - x0) * power, y0);
}}

CanvasRenderingContext2D.prototype.clipDiagonalRectangle = function(x0, y0, x1, y1, power) {{
    this.beginPath();
    this.diagonalRectangle(x0, y0, x1, y1, power);
    this.clip();
}}

CanvasRenderingContext2D.prototype.drawDiagonalRectangleClipImage = function(x0, y0, x1, y1, im, imx, imy, imw, imh, power, alpha) {{
    if (alpha == 0.0) return;
    this.save();
    this.globalAlpha *= alpha;
    this.beginPath();
    this.diagonalRectangle(x0, y0, x1, y1, power);
    this.clip();
    this.drawImage(im, x0 + imx, y0 + imy, imw, imh);
    this.restore();
}}
    
img.src = `data:image/png;base64,%INPUT_IMG%`;
blurimg.src = `data:image/png;base64,%INPUT_BLUR%`;

main = () => {{
    canvas.width = w;
    canvas.height = h;

    ctx.drawImage(blurimg, 0, 0, w, h);
    
    let x0 = w / 2 - w * children_size / 2, y0 = h / 2 - h * children_size / 2;
    let x1 = w / 2 + w * children_size / 2, y1 = h / 2 + h * children_size / 2;
    
    ctx.save();
    ctx.beginPath();
    ctx.fillStyle = "rgba(0, 0, 0, {1.0 - DIM})";
    ctx.rect(0, 0, w, h);
    ctx.fill();
    ctx.restore();
    
    ctx.save();
    ctx.beginPath();
    ctx.fillStyle = "rgba(0, 0, 0, {SHADER_ALPHA})";
    ctx.diagonalRectangle(x0, y0, x1, y1, dpower);
    ctx.shadowColor = "rgb(0, 0, 0)";
    ctx.shadowBlur = (w + h) * {SHADER_POWER};
    ctx.fill();
    ctx.restore();
    
    ctx.drawDiagonalRectangleClipImage(x0, y0, x1, y1, img, 0, 0, w * children_size, h * children_size, dpower, 1.0);
    
    result = canvas.toDataURL("image/png");
}}

img.onload = () => {{
    loaded++;
    if (loaded == 2) main();
}};

blurimg.onload = () => {{
    loaded++;
    if (loaded == 2) main();
}}
"""

def im2b64(im: Image.Image):
    io = BytesIO()
    im.save(io, format="png")
    return b64encode(io.getvalue()).decode()

def run(ipt: str, opt: str):
    im = Image.open(ipt)
    r = im.width / im.height
    
    if r > (WIDTH / HEIGHT):
        im = im.crop((
            (im.width - im.height * WIDTH / HEIGHT) / 2,
            0, 
            im.width - (im.width - im.height * WIDTH / HEIGHT) / 2,
            im.height
        ))
    else:
        im = im.crop((
            0,
            (im.height - im.width * HEIGHT / WIDTH) / 2,
            im.width,
            im.height - (im.height - im.width * HEIGHT / WIDTH) / 2
        ))
    
    imb64 = im2b64(im)
    blurim = im.filter(ImageFilter.GaussianBlur((im.width + im.height) * BLUR_R))
    blurb64 = im2b64(blurim)
    
    wv.evaluate_js("null;") # wait to load
    wv.evaluate_js(MAIN_JS.replace("%INPUT_IMG%", imb64).replace("%INPUT_BLUR%", blurb64))
    
    while True:
        result = wv.evaluate_js("result;")
        if result is not None: break
    
    with open(opt, "wb") as f:
        f.write(b64decode(result.split(",")[1]))

wv = webview.create_window("Auto_Image_TempWindow", hidden=True)

current_thread = threading.current_thread
def ban_threadtest_current_thread():
    obj = current_thread()
    obj.name = "MainThread"
    return obj
webview.threading.current_thread = ban_threadtest_current_thread

threading.Thread(target=lambda: webview.start(), daemon=True).start()

if __name__ == "__main__":
    run(sys.argv[1], sys.argv[2])
