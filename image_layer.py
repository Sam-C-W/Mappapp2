from PIL import Image


class ImageLayer:
    """"
    class that describes a layer consisting of a singe image rather than a collection of tiles.
    """

    def __init__(self, image, tileset, name="", grid_res=32):
        self.image = image
        self.tileset = tileset
        self.grid_res = grid_res
        self.name = name

    def resize(self, size: 'width,height tuple'):
        """"
        method that resizes the image layer according to the specified width and height tuple
        """
        size = size[0] * self.grid_res, size[1] * self.grid_res
        resized = Image.new('RGBA', size, color=(0, 0, 0, 0))
        resized.paste(self.image)
        self.image = resized

    def draw_on_image(self, brush, position):
        """"
        method that draws a sub image in place on the image layer.
        Accepts a brush image and a x:y pixel position tuple
        """
        canvas = Image.new('RGBA', self.image.size, color=(0, 0, 0, 0))
        canvas.paste(brush, position)
        self.image = Image.alpha_composite(self.image, canvas)
        canvas.close()
