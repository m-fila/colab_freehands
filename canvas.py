from IPython.display import HTML, Image
from google.colab.output import eval_js
from base64 import b64decode

from PIL import Image
from io import BytesIO
from scipy.ndimage import center_of_mass
from enum import Enum, auto
import numpy as np


class Mode(Enum):
    IMAGE = auto()
    ARRAY = auto()


class Canvas:

    html = """
  <canvas width=%d height=%d style="border: 1px solid black;"></canvas>
  <button>Finish</button>
  <script>
  var canvas = document.querySelector('canvas')
  var ctx = canvas.getContext('2d')
  ctx.lineWidth = %d
  var button = document.querySelector('button')
  var mouse = {x: 0, y: 0}
  canvas.addEventListener('mousemove', function(e) {
    mouse.x = e.pageX - this.offsetLeft
    mouse.y = e.pageY - this.offsetTop
  })
  canvas.onmousedown = ()=>{
    ctx.beginPath()
    ctx.moveTo(mouse.x, mouse.y)
    canvas.addEventListener('mousemove', onPaint)
  }
  canvas.onmouseup = ()=>{
    canvas.removeEventListener('mousemove', onPaint)
  }
  var onPaint = ()=>{
    ctx.lineTo(mouse.x, mouse.y)
    ctx.stroke()
  }
  var data = new Promise(resolve=>{
    button.onclick = ()=>{
      resolve(canvas.toDataURL('image/png'))
    }
  })
  </script>
  """

    def __init__(self, size=(64, 64), line_width=1):
        display(HTML(self.html % (size[0], size[1], line_width)))
        data = eval_js("data")
        self.raw = b64decode(data.split(",")[1])

    def save_png(self, filename):
        with open(filename, "wb") as file:
            file.write(self.binary)

    def to_image(self, size=(20, 20), margin=(4, 4), weighted=True):
        return self.__get(mode=Mode.IMAGE, size=size, margin=margin, weighted=weighted)

    def to_array(
        self, size=(20, 20), margin=(4, 4), weighted=True, flat=False, dtype=np.int32
    ):
        im = self.__get(mode=Mode.ARRAY, size=size, margin=margin, weighted=weighted)
        arr = np.array(im, dtype=dtype)
        if flat == True:
            return arr.reshape(-1)
        return arr

    def __get(self, mode=Mode.ARRAY, size=(20, 20), margin=(4, 4), weighted=True):
        if mode not in Mode:
            try:
                mode = Mode[mode.upper()]
            except:
                raise KeyError()
        im = Image.open(BytesIO(self.raw))
        im = im.convert("LA").getchannel("A")
        im = im.crop(im.getbbox())
        im.thumbnail(size, Image.LANCZOS)
        bg_size = tuple(s_i + 2 * m_i for s_i, m_i in zip(size, margin))
        bg = Image.new("L", bg_size)
        bg_center = np.array((bg.width, bg.height)) / 2
        if weighted:
            im_center = center_of_mass(np.array(im))[::-1]
        else:
            im_center = np.array((im.width, im.height)) / 2
        bg.paste(im, tuple((bg_center - im_center).astype("int32")))
        return bg
