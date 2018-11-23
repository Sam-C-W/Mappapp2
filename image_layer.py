from PIL import Image


class ImageLayer:
    """"
    class that describes a layer consisting of a singe image rather than a collection of tiles.
    """
    def __init__(self, image):
        self.image = image

    def resize(self, size: 'width,height tuple'):
        """"
        method that resizes the image layer according to the specified width and height tuple
        """

        self.image = self.image.crop((0,0,*size))

    def draw_on_image(self, brush, position):
        """"
        method that draws a sub image in place on the image layer.
        Accepts a brush image and a x:y pixel position tuple
        """
        canvas = Image.new('RGBA', self.image.size, color=(0, 0, 0, 0))
        canvas.paste(brush, position)
        self.image = Image.alpha_composite(self.image, canvas)
        canvas.close()


