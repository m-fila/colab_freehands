"""Interactive canvases for Colab notebooks based on
https://gist.github.com/korakot/8409b3feec20f159d8a50b0a811d3bca"""

from base64 import b64decode
from io import BytesIO
from enum import Enum, auto
from PIL import Image
from scipy.ndimage import center_of_mass
from google.colab.output import eval_js
from IPython.display import HTML
import numpy as np


class Mode(Enum):
    """Canvas output mode

    Args:
        Enum (IMAGE): PIL.Image
        Enum (ARRAY): numpy.array
    """

    IMAGE = auto()
    ARRAY = auto()


class Canvas:
    """Interactive canvas for Colab

    Args:
        size (tuple, optional): Size of canvas. Defaults to (64, 64).
        line_width (int, optional): Width of painter. Defaults to 1.
    """

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
        """Save canvas content to png file

        Args:
            filename (string): output file
        """
        with open(filename, "wb") as file:
            file.write(self.raw)

    def to_image(self, size=(20, 20), margin=(4, 4), weighted=True):
        """Convert canvas content to PIL.Image

        Args:
            size (tuple, optional): Size of contents in output image. Defaults to (20, 20).
            margin (tuple, optional): Margins in output image. Defaults to (4, 4).
            weighted (bool, optional): If True center contents using center of mass,
            otherwise use geometrical center. Defaults to True.

        Returns:
            [type]: [description]
        """
        return self.__get(mode=Mode.IMAGE, size=size, margin=margin, weighted=weighted)

    def to_array(
        self, size=(20, 20), margin=(4, 4), weighted=True, flat=False, dtype=np.int32
    ):
        """Convert canvas content to numpy.array

        Args:
            size (tuple, optional): Size of contents in output image. Defaults to (20, 20).
            margin (tuple, optional): Margins in output image. Defaults to (4, 4).
            weighted (bool, optional): If True centers contents using center of mass,
            otherwise uses geometrical center. Defaults to True.
            flat (bool, optional): If True returns 1d array. Defaults to False.
            dtype ([type], optional): Type of output array. Defaults to np.int32.

        Returns:
            [type]: [description]
        """
        image = self.__get(mode="arrays", size=size, margin=margin, weighted=weighted)
        arr = np.array(image, dtype=dtype)
        if flat:
            return arr.reshape(-1)
        return arr

    def __get(self, mode=Mode.ARRAY, size=(20, 20), margin=(4, 4), weighted=True):
        if mode not in Mode:
            try:
                mode = Mode[mode.upper()]
            except:
                raise KeyError(mode)
        image = Image.open(BytesIO(self.raw))
        image = image.convert("LA").getchannel("A")
        image = image.crop(image.getbbox())
        image.thumbnail(size, Image.LANCZOS)
        background_size = tuple(s_i + 2 * m_i for s_i, m_i in zip(size, margin))
        background = Image.new("L", background_size)
        background_center = np.array((background.width, background.height)) / 2
        if weighted:
            im_center = center_of_mass(np.array(image))[::-1]
        else:
            im_center = np.array((image.width, image.height)) / 2
        background.paste(image, tuple((background_center - im_center).astype("int32")))
        return background
