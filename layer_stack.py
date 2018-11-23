from layer import Layer
from PIL import Image
from image_layer import ImageLayer


class LayerStack:
    def __init__(self, grid_res):
        self.stack = []
        self.grid_resolution = grid_res
        self.stack.append(Layer("0layertiles"))

    def new_layer(self, tileset):
        """
        method that adds a new layer to the top of the stack.
        """
        self.stack.append(Layer(tileset, self.stack[0].size, self.grid_resolution))

    def resize(self, size):
        """
        Method that resizes each layer in the stack to match the give size tuple
        """
        for i in self.stack:
            i.resize(size)

    def copy_layer(self, position):
        """
        Method that duplicates the layer at the target position
        """
        self.insert(position, self.stack[position])

    def del_layer(self,position):
        """
        Method that deletes the layer at the targeted position
        """
        del self.stack[position]

    def add_image_layer(self, image=None):
        """"
        Method that adds a new image layer to the stack, if an image is not specified a blank image is created
        """
        if image:
            if image.size == self.stack[0].size:
                self.stack.append(ImageLayer(image))
            else:
                raise ValueError("The dimensions of the image much match those of the map.")
        else:
            new_image = Image.new('RGBA', self.stack[0].size, color=(0, 0, 0, 0))
            self.stack.append(ImageLayer(new_image))

    def move_up(self, position):
        """
        Method that swaps a layer with the layer immediately above its current position
        """
        if position < len(self.stack)-1:
            self.stack[position], self.stack[position-1] = self.stack[position-1], self.stack[position]

    def move_down(self, position):
        """
        Method that swaps a layer with the layer immediately below its current position
        """
        if position > 1:
            self.stack[position], self.stack[position + 1] = self.stack[position + 1], self.stack[position]

    def get_size(self):
        return self.stack[0].size

    def get_grid_res(self):
        return self.grid_resolution
