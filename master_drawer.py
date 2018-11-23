from drawer import Drawer
from PIL import Image
from layer_stack import LayerStack

class MasterDrawer:
    def __init__(self, layerstack):
        self.layers = layerstack
        self.layer_cache = {}

    def draw_all(self):
        base = Drawer(self.layers.stack).draw_full_layer()
        for i, layer in enumerate(self.layers.stack):
            draw = Drawer(layer)
            layer_image = draw.draw_full_layer()
            base = Image.alpha_composite(base, layer_image)
            self.layer_cache[i] = base
        return base

    def draw_subsection(self, layer, target):
        draw = Drawer(self.layers.get_layer(layer))
        self.layer_cache[layer] = draw.draw_sub_section(self.layer_cache[layer],target)
        self.draw_cache()

    def draw_cache(self):
        cache_base = Drawer(self.layers.stack).draw_full_layer()
        for i in self.layer_cache:
            cache_base = Image.alpha_composite(cache_base, self.layer_cache[i])
        return cache_base

    def draw_grid(self):
        pass
