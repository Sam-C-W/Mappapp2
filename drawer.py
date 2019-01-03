import layer
from PIL import Image


class Drawer:
    """
    Class that takes a layer object and draws a new image based on that layer's grid and target tileset
    """

    def __init__(self, layer):
        self.layer = layer
        self.tileset = Image.open(self.layer.tileset)

    def get_cell_image(self, target):
        """
        method that extracts a single tile image from the tileset as specified by a gris position tuple
        """
        x_start, y_start = self.grid_to_pixel(target)
        x_stop, y_stop = x_start + self.layer.grid_res, y_start + self.layer.grid_res
        return self.tileset.crop((x_start, y_start, x_stop, y_stop))

    def grid_to_pixel(self, cell):
        """
        method that converts a grid cell to a pixel co-ordinate indicating the top left corner of that cell
        """
        return tuple(i * self.layer.grid_res for i in cell)

    def draw_full_layer(self):
        """
        method that draws the entire grid of a layer and returns a PIL image object
        """
        image_size = tuple([i * self.layer.grid_res for i in self.layer.size])
        base = Image.new('RGBA', image_size, color=(0, 0, 0, 0))
        for key in self.layer.grid:
            tile = self.get_cell_image(self.layer.grid[key])
            base.paste(tile, self.grid_to_pixel(key))
            tile.close()
        return base

    def draw_sub_section(self, image, cells):
        """
        method that draws a sub-section of cells in a layer and then draws the resulting sub image onto a provided image
        - this should usually be an image representing the rest of the layer.
        """
        for key in cells:
            tile = self.get_cell_image(self.layer.grid[key])
            image.paste(tile, self.grid_to_pixel(key))
            tile.close()
        return image

    def draw_tile_array(self, image, cells):
        """
        method that draws a sub-section of cells in a layer and then draws the resulting sub image onto a provided image
        - this should usually be an image representing the rest of the layer.
        """
        for key in cells:
            tile = self.get_cell_image(cells[key])
            image.paste(tile, self.grid_to_pixel(key))
            tile.close()
        return image
