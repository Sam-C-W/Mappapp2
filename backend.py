from layer_stack import LayerStack
from layer import Layer
from master_drawer import MasterDrawer
from drawer import Drawer
from ast import literal_eval as make_tuple
from PIL import Image
from time import perf_counter
from image_layer import ImageLayer
import base64
import copy
import io
import sys


class Backend:
    def __init__(self):
        self.working_dir = self.get_dir()
        self.layerlist = None
        self.active_tile_set = None
        self.grid_toggle = 0
        self.active_layer = 0
        self.active_tile_array = {}
        self.active_tile = (0, 0)
        self.active_tile_image = None
        self.active_tile_set_file = f"{self.working_dir}img_store/tilesets/{self.get_default_tileset()}"
        self.create_drawspace(1, 1)
        self.update_active_tileset()
        self.image_cache = None
        self.grid_cache = None
        self.fill_toggle = 0
        self.square_toggle = 0
        self.zoom_mod = 1
        self.undo_array = []
        self.undo_tracker = 0
        self.working_file = ""
        self.last_save = ""

    def get_default_tileset(self):
        config = open(f"{self.working_dir}mappapp_config",'r')
        for line in config:
            if "Default Tileset:" in line:
                return line.split(':')[1][0:-1]

    def create_drawspace(self, width, height, res=32, ):
        res = int(self.active_tile_set_file.split('/')[-1][0:2])
        self.layerlist = LayerStack(res)
        self.layerlist.new_layer(self.active_tile_set_file)
        self.active_layer = 1
        self.layerlist.resize((width, height))
        self.update_active_tileset()

    def zoom_map(self, image):
        if self.zoom_mod != 1:
            new_size = (int(val * self.zoom_mod) for val in image.size)
            return image.resize(new_size)
        else:
            return image

    def array_draw(self, touch):
        touch = self.coord_convert_map(touch)
        applied_array = {}
        for key in self.active_tile_array:
            new_key = key[0] + touch[0], key[1] + touch[1]
            if new_key in self.layerlist.get_layer(self.active_layer).grid:
                applied_array[new_key] = self.active_tile_array[key]
        self.layerlist.get_layer(self.active_layer).update_tiles(applied_array)
        return applied_array

    def square_select(self, start, end, type):
        self.active_tile_array = {}
        target_tiles, zero_key = self.get_box(start, end, type)
        for key in target_tiles.keys():
            keyx = key[0] - zero_key[0]
            keyy = key[1] - zero_key[1]
            temp_key = (keyx, keyy)
            if type != 'map':
                self.active_tile_array[temp_key] = key
            else:
                self.active_tile_array[temp_key] = self.layerlist.get_layer(self.active_layer).grid[key]

    def square_fill(self, start, end):
        target_tiles = self.get_box(start, end, 'map')[0]
        self.layerlist.get_layer(self.active_layer).update_tiles(target_tiles)
        return target_tiles

    def get_box(self, start, end, type="none"):
        if type == 'map':
            start = self.coord_convert_map(start)
            end = self.coord_convert_map(end)
        else:
            start = self.coord_convert_tileset(start)
            end = self.coord_convert_tileset(end)
        start, end = tuple(min(start[val], end[val]) for val in range(2)), tuple(
            max(start[val], end[val]) for val in range(2))
        target_tiles = {}
        for x in range(start[0], end[0] + 1):
            for y in range(start[1], end[1] + 1):
                target_tiles[(x, y)] = self.active_tile
        return target_tiles, start

    def fill_tool(self, touch):
        def is_adjacent(grid, cell, cell_list):
            cells_added = 0
            if cell in cell_list:
                return cells_added
            else:
                cellx, celly = cell[0], cell[1]
                north = (cellx, celly + 1)
                south = (cellx, celly - 1)
                east = (cellx + 1, celly)
                west = (cellx - 1, celly)
                for neibour in [north, south, east, west]:
                    if neibour in grid and neibour in cell_list and grid[cell] == tile_at_touch:
                        cell_list[cell] = grid[cell]
                        cells_added += 1
                        return cells_added
                else:
                    return cells_added

        touch_coords = self.coord_convert_map(touch)
        grid = self.layerlist.get_layer(self.active_layer).grid
        tile_at_touch = grid[touch_coords]
        target_cells = {}
        target_cells[touch_coords] = grid[touch_coords]
        checker = 2
        while checker > 0:
            counter = 0
            for cell in self.layerlist.get_layer(self.active_layer).grid:
                counter += is_adjacent(grid, cell, target_cells)
            counter = 0 if counter else -1
            checker += counter
        for cell in target_cells:
            target_cells[cell] = self.active_tile
        self.layerlist.get_layer(self.active_layer).update_tiles(target_cells)

    def get_dir(self):
        slash = "\\"
        full_path = sys.argv[0].split(slash)[0:-1]
        dir = ""
        for bit in full_path:
            dir += bit + "/"
        return dir

    def check_active_layer_type(self):
        if isinstance(self.layerlist.get_layer(self.active_layer), Layer):
            return True
        else:
            return False

    def update_target_tile(self, touch):
        touch_grid = self.coord_convert_map(touch)
        self.layerlist.get_layer(self.active_layer).update_tiles({touch_grid: self.active_tile})

    def draw_map(self, target=None, not_undoing=True):
        startt = perf_counter()
        artist = MasterDrawer(self.layerlist)
        if target:
            artist.layer_cache = self.image_cache
            map_img = artist.draw_subsection(self.active_layer, target)
            if self.grid_toggle:
                map_img = Image.alpha_composite(map_img, self.grid_cache)
        else:
            map_img = artist.draw_all()
            del self.image_cache
            self.image_cache = artist.layer_cache
            if self.grid_toggle:
                self.grid_cache = artist.draw_grid()
                map_img = Image.alpha_composite(map_img, self.grid_cache)
        del artist
        if not_undoing:
            if self.undo_tracker < len(self.undo_array):
                self.undo_array = self.undo_array[0:self.undo_tracker]
            if len(self.undo_array) < 10:
                self.undo_array.append(self.save_to_undo())
                self.undo_tracker += 1
            else:
                del self.undo_array[0]
                self.undo_array.append(self.save_to_undo())
        else:
            self.undo_tracker += -1
            self.undo_tracker = abs(self.undo_tracker)
            self.undo_tracker = 1 if self.undo_tracker < 1 else self.undo_tracker
        return self.zoom_map(map_img)

    def update_active_tileset(self):
        if self.active_tile_set:
            self.active_tile_set.close()
        self.active_tile_set = Image.open(self.active_tile_set_file)

    def get_active_tile_image(self):
        drawer = Drawer(self.layerlist.get_layer(self.active_layer))
        if self.active_tile_array:
            distances = {}
            for key in self.active_tile_array:
                distances[key[0] * 2 + key[1] * 2] = key
            start_d = min(distances.keys())
            end_d = max(distances.keys())
            start = distances[start_d]
            end = distances[end_d]
            width = end[0] + 1 - start[0]
            height = end[1] + 1 - start[1]
            image_size = (width * self.layerlist.get_grid_res(), height * self.layerlist.get_grid_res())
            base = Image.new('RGBA', image_size, color=(0, 0, 0, 0))
            self.active_tile_image = drawer.draw_tile_array(base, self.active_tile_array)
        else:
            self.active_tile_image = drawer.get_cell_image(self.active_tile)
        return self.active_tile_image

    def set_active_tile(self, touch):
        self.active_tile = self.coord_convert_tileset(touch)

    def coord_convert_tileset(self, touch):
        res = self.layerlist.get_grid_res()
        touchx = touch[0]
        touchy = abs(touch[1] - self.active_tile_set.size[1])
        gridx = int(touchx // res)
        gridy = int(touchy // res)
        return gridx, gridy

    def save_to_file(self, file):
        target = open(file, 'w')
        for layer in self.layerlist.stack:
            if isinstance(layer, Layer):
                line = layer.to_string() + "\n"
            else:
                line = str(layer.name) + "*" + layer.tileset + "*" + "(1, 1)" + "*" + str(layer.grid_res) + "*"
                output = io.BytesIO()
                layer.image.save(output, 'PNG')
                img_str = base64.b64encode(output.getvalue())
                byte_str = img_str.decode()
                line += byte_str + "\n"
            target.write(line)
        target.close()

    def load_from_file(self, file):
        source = open(file, 'r')
        loaded_layer_stack = LayerStack(32)
        loaded_layer_stack.del_layer(0)
        for line in source:
            layer_data = line.split("*")
            layer_name = layer_data[0]
            layer_tileset = layer_data[1]
            layer_size = make_tuple(layer_data[2])
            layer_res = int(layer_data[3])
            if layer_data[4][0] == "(":
                layer_grid_data = layer_data[4][0:-2].split("$")
                layer_grid = {}
                for cell in layer_grid_data:
                    kv_pair = cell.split(":")
                    layer_grid[make_tuple(kv_pair[0])] = make_tuple(kv_pair[1])
                loaded_layer = Layer("ts", (1, 1), 32, "seed")
                loaded_layer.grid = layer_grid
                loaded_layer.size = layer_size
                loaded_layer.tileset = layer_tileset
                loaded_layer.grid_res = layer_res
                loaded_layer.name = layer_name
                loaded_layer_stack.grid_resolution = layer_res
            else:
                byte_string = layer_data[4][0:]
                bytes64 = byte_string.encode()
                bytes = base64.b64decode(bytes64)
                fauxfile = io.BytesIO(bytes)
                layer_image = Image.open(fauxfile)
                loaded_layer = ImageLayer(layer_image, layer_tileset, layer_name, layer_res)
            loaded_layer_stack.stack.append(loaded_layer)
        self.layerlist = loaded_layer_stack
        self.active_layer = 1

    def save_to_undo(self):
        target = copy.deepcopy(self.layerlist)
        return target

    def load_from_undo(self, source):
        loaded_layer_stack = copy.deepcopy(source)
        self.layerlist = loaded_layer_stack
        self.active_layer = 1

    def redo(self):
        if self.undo_tracker < len(self.undo_array):
            layer_log = self.active_layer
            number_of_layers = len(self.layerlist.stack)
            self.load_from_undo(self.undo_array[max(self.undo_tracker, 0)])
            self.active_layer = layer_log if layer_log in range(len(self.layerlist.stack)) else len(
                self.layerlist.stack) - 1
            self.undo_tracker *= -1
            return 1

    def undo(self):
        if self.undo_tracker >= 0:
            layer_log = self.active_layer
            number_of_layers = len(self.layerlist.stack)
            self.load_from_undo(self.undo_array[max(self.undo_tracker - 2, 0)])
            self.active_layer = layer_log if layer_log in range(len(self.layerlist.stack)) else len(
                self.layerlist.stack) - 1
            return 1

    def export(self, file):
        img = self.draw_map()
        img.save(file)

    def import_img(self, file):
        img = Image.open(file)
        self.layerlist.add_image_layer(tileset=self.active_tile_set_file, image=img, position=self.active_layer + 1)
        self.active_layer += 1

    def coord_convert_map(self, touch):
        if self.layerlist.get_size()[1] - touch[1] < 1:
            touch = touch[0], touch[1] - 1
        if self.layerlist.get_size()[0] - touch[0] < 1:
            touch = touch[0] - 1, touch[1]
        if touch[1] == 0: touch = touch[0], 1
        if touch[0] == 0: touch = 1, touch[1]
        res = self.layerlist.get_grid_res()
        touch = tuple(val * (1 / self.zoom_mod) for val in touch)
        touchx = touch[0]
        touchy = abs(touch[1] - self.layerlist.get_size()[1] * res)
        gridx = int(touchx // res)
        gridy = int(touchy // res)
        return gridx, gridy
