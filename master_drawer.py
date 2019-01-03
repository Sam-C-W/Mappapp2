from drawer import Drawer
from PIL import Image, ImageDraw
from layer import Layer
from layer_stack import LayerStack


class MasterDrawer:
    """
    Class that controls drawing of mulitple layers to produce map images, takes a stack of layer objects as a paramenter
    and stores a cache of the drawn layer images.
    """

    def __init__(self, layerstack):
        self.layers = layerstack
        self.layer_cache = {}

    def draw_all(self):
        """
        Method that draws every cell in every layer in the stack and returns the complete map object
        """
        base = Drawer(self.layers.stack[0]).draw_full_layer()
        for i, layer in enumerate(self.layers.stack):
            if isinstance(layer, Layer):
                draw = Drawer(layer)
                layer_image = draw.draw_full_layer()
                base = Image.alpha_composite(base, layer_image)
                self.layer_cache[i] = layer_image
            else:
                layer_image = layer.image
                base = Image.alpha_composite(base, layer_image)
                self.layer_cache[i] = layer_image
        return base

    def draw_subsection(self, layer, target):
        """
        :param layer: the index of the layer to draw
        :param target: a dict of co-ordinate and tile target key-value pairs
        :return: an image with only the targeted selection of the targeted layer updated.
        """
        draw = Drawer(self.layers.get_layer(layer))
        self.layer_cache[layer] = draw.draw_sub_section(self.layer_cache[layer], target)
        return self.draw_cache()

    def draw_grid(self, color=(0, 0, 0, 150)):
        """
        method that draws a grid of a specified color and returns it on a transparent background
        :param image:
        :param color:
        :return:
        """
        gridres = self.layers.get_grid_res()
        grid_width = self.layers.get_size()[0]
        grid_height = self.layers.get_size()[1]
        grid = Image.new('RGBA', (grid_width * gridres, grid_height * gridres), (255, 0, 0, 0))
        artist = ImageDraw.Draw(grid)

        for i in range(grid_width):
            artist.line([(i * gridres, 0), (i * gridres, grid_height * gridres)], fill=color, width=1)
            if i > 0:
                artist.line([(i * gridres - 1, 0), (i * gridres - 1, grid_height * gridres)], fill=color, width=1)
        artist.line([(grid_width * gridres - 1, 0), (grid_width * gridres - 1, grid_height * gridres)],
                    fill=color, width=1)

        for i in range(grid_height):
            artist.line([(0, i * gridres), (grid_width * gridres, i * gridres)], fill=color, width=1)
            if i > 0:
                artist.line([(0, i * gridres - 1), (grid_width * gridres, i * gridres - 1)], fill=color, width=1)
        artist.line([0, (grid_height * gridres - 1), (grid_width * gridres, grid_height * gridres - 1)],
                    fill=color, width=1)

        del artist
        return grid

    def draw_cache(self):
        """
        Method that draws cached layer images sequentially.
        :return: The cached map image
        """
        cache_base = Drawer(self.layers.stack[0]).draw_full_layer()
        for i in self.layer_cache:
            cache_base = Image.alpha_composite(cache_base, self.layer_cache[i])
        return cache_base
