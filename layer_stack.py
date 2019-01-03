from layer import Layer
from PIL import Image
from image_layer import ImageLayer


class LayerStack:
    def __init__(self, grid_res):
        self.stack = []
        self.grid_resolution = grid_res
        self.stack.append(Layer("img_store/tilesets/0layertiles.png", resolution=grid_res))

    def new_layer(self, tileset, position=None):
        """
        method that adds a new layer to the top of the stack.
        """
        if position:
            self.stack.insert(position, Layer(tileset, self.stack[0].size, self.grid_resolution, name=len(self.stack)))
        else:
            self.stack.append(Layer(tileset, self.stack[0].size, self.grid_resolution, name=len(self.stack)))

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
        self.stack.insert(position, self.stack[position])

    def set_name(self, name, position):
        """
        updates the name of the specified layer
        :param position:
        :return:
        """
        self.get_layer(position).name = name

    def del_layer(self, position):
        """
        Method that deletes the layer at the targeted position
        """
        del self.stack[position]

    def add_image_layer(self, tileset, image=None, grid_res=None, position=None):
        """"
        Method that adds a new image layer to the stack, if an image is not specified a blank image is created
        """
        if not grid_res:
            grid_res = self.stack[0].grid_res
        if image:
            if image.size == (self.stack[0].size[0] * grid_res, self.stack[1].size[0] * grid_res):
                if position:
                    self.stack.insert(position, ImageLayer(image, tileset, grid_res=grid_res))
                else:
                    self.stack.append(ImageLayer(image, tileset, grid_res=grid_res))
            else:
                raise ValueError("The dimensions of the image much match those of the map.")
        else:
            new_image = Image.new('RGBA', tuple([num * self.get_grid_res() for num in self.stack[0].size]),
                                  color=(0, 0, 0, 0))
            if position:
                self.stack.insert(position, ImageLayer(new_image, tileset, grid_res=grid_res, name=len(self.stack)))
            else:
                self.stack.append(ImageLayer(new_image, tileset, grid_res=grid_res, name=len(self.stack)))

    def move_up(self, position):
        """
        Method that swaps a layer with the layer immediately above its current position
        """
        if position > 1:
            self.stack[position], self.stack[position - 1] = self.stack[position - 1], self.stack[position]
        else:
            raise ValueError("IDKman")

    def move_down(self, position):
        """
        Method that swaps a layer with the layer immediately below its current position
        """
        if position < len(self.stack) - 1:
            self.stack[position], self.stack[position + 1] = self.stack[position + 1], self.stack[position]
        else:
            raise ValueError("IDKman")

    def get_size(self):
        """
        Size getter
        :return: int, int tuple
        """
        return self.stack[0].size

    def get_layer(self, index):
        """
        returns the specified layer
        :param index:
        :return:
        """
        return self.stack[index]

    def get_layer_stack(self):
        """
        returns the layer array
        :return:
        """
        return self.stack

    def get_grid_res(self):
        """
         grid_res getter
         :return: int
         """
        return self.grid_resolution
