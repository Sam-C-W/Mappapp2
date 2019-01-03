from PIL import Image
import numpy
from layer import Layer
from kivy.uix.widget import Widget
from kivy.uix.popup import Popup
from backend import Backend
from kivy.app import App
from kivy.uix.filechooser import FileChooserIconView
from kivy.uix.scrollview import ScrollView
from kivy.uix.image import Image as KvyImage
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.graphics.texture import Texture
from kivy.config import Config
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.core.window import Window
from kivy.uix.dropdown import DropDown
from kivy.uix.textinput import TextInput
from kivy.graphics import Color, Rectangle
from math import ceil
import os

Config.set('input', 'mouse', 'mouse,multitouch_on_demand')


class MapView(KvyImage):
    """
    class that controls mouse clicks on the map image
    """

    def __init__(self, backend=None, **kwargs):
        self.backend = backend
        super(MapView, self).__init__(**kwargs)

    def cursor_square(self, touch, start):
        if start == 'left':
            start = left_touch_start
        if start == 'right':
            start = right_touch_start
        try:
            print(f"right {right_touch_start} left: {left_touch_start}, target{start}")
        except :
            pass
        res = self.backend.layerlist.get_grid_res()*self.backend.zoom_mod
        touch1 = self.backend.coord_convert_map(start)
        touch2 = self.backend.coord_convert_map(touch.pos)
        starting_point = min(touch1[0], touch2[0]), min(touch1[1], touch2[1])
        ending_point = max(touch1[0], touch2[0]), max(touch1[1], touch2[1])
        size = (ending_point[0] + 1 - starting_point[0]) * res, (ending_point[1] + 1 - starting_point[1]) * res
        self.children[0].size = size
        self.children[0].pos = starting_point[0] * res, (
                self.backend.layerlist.get_size()[1] - ending_point[1] - 1) * res

    def on_touch_down(self, touch):
        """
        On touch down on map a tile is updated and the map is refreshed. On right-click the selected tile is set as the
        active tile.
        :param touch:
        :return:
        """
        if self.collide_point(*touch.pos):
            if touch.button == 'left':
                global left_touch_start
                left_touch_start = touch.pos
                if not self.backend.check_active_layer_type():
                    pos = tuple(val * (1 / self.backend.zoom_mod) for val in touch.pos)
                    touchx = pos[0]
                    touchy = abs(pos[1] - self.backend.layerlist.get_size()[1] * self.backend.layerlist.get_grid_res())
                    pos = (int(touchx - self.backend.active_tile_image.size[0] / 2),
                           int(touchy - self.backend.active_tile_image.size[0] / 2))

                    self.backend.layerlist.get_layer(self.backend.active_layer).draw_on_image(
                        self.backend.get_active_tile_image(), pos)
                    self.parent.parent.redraw_map()
                    return
                if self.backend.fill_toggle:
                    self.backend.fill_tool(touch.pos)
                    self.parent.parent.redraw_map()
                    return
                if self.backend.active_tile_array:
                    target = self.backend.array_draw(touch.pos)
                    self.parent.parent.redraw_map(target=target)
                    return
                if not self.backend.square_toggle:
                    self.backend.update_target_tile(touch.pos)
                    self.texture = self.parent.parent.get_texture \
                        (self.backend.draw_map({self.backend.coord_convert_map(touch.pos)}))
            elif touch.button == 'right' and self.backend.check_active_layer_type():
                self.backend.active_tile = self.backend.layerlist.get_layer(self.backend.active_layer).grid[
                    self.backend.coord_convert_map(touch.pos)]
                self.backend.active_tile_array = {}
                self.parent.parent.redraw_active_tile()
                global right_touch_start
                right_touch_start = touch.pos
                self.children[0].background_color = [0.9, 0.9, 0, 0.5]

    def on_touch_move(self, touch):
        """
        On touch move or drag tiles are updated along the drag path. Or if right-click or box mode is active it selects
        a sub-grid of titles to be updated.
        :param touch:
        :return:
        """
        if self.collide_point(*touch.pos) and self.backend.check_active_layer_type():
            if touch.button == 'left' and not self.backend.square_toggle:
                if self.backend.layerlist.get_layer(self.backend.active_layer).grid[
                    self.backend.coord_convert_map(touch.pos)] == self.backend.active_tile:
                    return
                self.backend.update_target_tile(touch.pos)
                self.texture = self.parent.parent.get_texture \
                    (self.backend.draw_map({self.backend.coord_convert_map(touch.pos)}))
            elif touch.button == 'left' and self.backend.square_toggle:
                self.cursor_square(touch, 'left')
            elif touch.button == 'right':
                self.children[0].background_color = [0.9, 0.9, 0, 0.5]
                self.cursor_square(touch, 'right')

    def on_touch_up(self, touch):
        """
        On Click release any box selections created by a moving touch are resolved.
        :param touch:
        :return:
        """
        if self.collide_point(*touch.pos) and self.backend.check_active_layer_type():
            if touch.button == 'right':
                self.backend.square_select(right_touch_start, touch.pos, "map")
                self.parent.parent.redraw_active_tile()
            if touch.button == 'left' and self.backend.square_toggle:
                target = self.backend.square_fill(left_touch_start, touch.pos)
                self.parent.parent.redraw_map(target=target)
                print(f"ending pos {touch.pos} start pos {left_touch_start}")


class TilesetView(KvyImage):
    """
    Class that controls mouse clicks on the tileset image.
    """

    def __init__(self, backend=None, **kwargs):
        self.backend = backend
        super(TilesetView, self).__init__(**kwargs)

    def cursor_square(self, touch, start):
        res = self.backend.layerlist.get_grid_res()
        touch1 = self.backend.coord_convert_tileset(start)
        touch2 = self.backend.coord_convert_tileset(touch.pos)
        starting_point = min(touch1[0], touch2[0]), min(touch1[1], touch2[1])
        ending_point = max(touch1[0], touch2[0]), max(touch1[1], touch2[1])
        size = (ending_point[0] + 1 - starting_point[0]) * res, (ending_point[1] + 1 - starting_point[1]) * res
        self.children[0].size = size
        self.children[0].pos = starting_point[0] * res, self.backend.active_tile_set.size[1] - (
                ending_point[1] + 1) * res

    def on_touch_down(self, touch):
        """
        On left touch down the selected tile is set for use as the active tile.
        :param touch:
        :return:
        """
        if self.collide_point(*touch.pos):
            if touch.button == 'left':
                self.backend.active_tile = self.backend.coord_convert_tileset(touch.pos)
                self.backend.active_tile_array = {}
                self.parent.parent.redraw_active_tile()
            elif touch.button == 'right':
                global right_touch_start
                right_touch_start = touch.pos
                self.backend.active_tile = self.backend.coord_convert_tileset(touch.pos)
                self.backend.active_tile_array = {}
                self.parent.parent.redraw_active_tile()

    def on_touch_move(self, touch):
        """
        On touch move a sub grid of tiles is selected for use as the active tile
        :param touch:
        :return:
        """
        if self.collide_point(*touch.pos):
            if touch.button == 'right':
                self.children[0].background_color = [0.9, 0.9, 0, 0.5]
                self.cursor_square(touch, right_touch_start)

    def on_touch_up(self, touch):
        """
        On touch up the selection described by the ón_touch_move method is resolved.
        :param touch:
        :return:
        """
        if self.collide_point(*touch.pos):
            if touch.button == 'right':
                self.backend.square_select(right_touch_start, touch.pos, "tile")
                self.parent.parent.redraw_active_tile()


class MainScreen(GridLayout):
    """
    This class describes the main GUI window
    """

    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)
        self.backend = Backend()
        self.initialize_keyboard()
        """---------------------A: this section of code controls the appearance of the main window-------------------"""

        self.cols = 3
        self.rows = 2
        self.padding = 20
        self.spacing = 10
        self.control_down = False

        def window_color_updater(instance, value):
            self.rect.pos = instance.pos
            self.rect.size = instance.size

        with self.canvas.before:
            Color(1, 1, 1, 0.2)
            self.rect = Rectangle(pos=self.pos, size=(200, 200))
            self.bind(size=window_color_updater, pos=window_color_updater)

        """------------B: This section of code creates the tileset control menue and active tile display------------"""

        def handle_tileset_select(instance):
            target_tileset = self.backend.working_dir + "img_store/tilesets/" + instance.text + ".png"
            if target_tileset != self.backend.active_tile_set_file:
                self.backend.active_tile_set_file = target_tileset
                self.backend.update_active_tileset()
                self.redraw_tileset()
                if self.backend.check_active_layer_type():
                    self.backend.layerlist.new_layer(self.backend.active_tile_set_file,
                                                     position=self.backend.active_layer + 1)
                    self.backend.active_layer += 1
                    self.populate_layer_list(layer_list)
                    self.backend.draw_map()
                    self.redraw_active_tile()
                current_set.text = self.backend.active_tile_set_file.split('/')[-1]
                tileset_dropdown.dismiss()
            else:
                tileset_dropdown.dismiss()

        def open_tile_set_dropdown(instance):
            tileset_dropdown.open(instance)

        tileset_menue = GridLayout(size_hint=(None, None), size=(300, 100), spacing=20, pos_hint=(None, 1), cols=3)
        tileset_select_shell = FloatLayout(size=(175, 100), size_hint=(None, None))
        tileset_dropdown = DropDown()
        available_sets = os.listdir(self.backend.working_dir + 'img_store/tilesets')

        for i in available_sets:
            set_name = i[:len(i) - 4]
            set_btn = Button(text=set_name, size_hint_y=None, height=44)
            set_btn.bind(on_press=handle_tileset_select)
            tileset_dropdown.add_widget(set_btn)
        tileset_dropdown_btn = Button(text="Select", size=(175, 27), size_hint=(None, None), pos_hint={'x': 0, 'y': .2})
        tileset_dropdown_btn.bind(on_release=open_tile_set_dropdown)
        current_set = Label(text=self.backend.active_tile_set_file.split('/')[-1], size=(175, 25),
                            size_hint=(None, None), pos_hint={'x': 0, 'y': .5})
        tileset_select_shell.add_widget(current_set)
        tileset_select_shell.add_widget(tileset_dropdown_btn)
        tileset_menue.add_widget(tileset_select_shell)

        tileset_menue.add_widget(Label(text="Active\nTile:", font_size='18sp'))
        active_tile_display = KvyImage()
        active_tile_display.texture = self.get_texture(self.backend.get_active_tile_image())
        tileset_menue.add_widget(active_tile_display)
        self.add_widget(tileset_menue)

        """-----------------------C: This section of code creates the map space control buttons----------------------"""
        map_control = GridLayout(cols=5, size=(100, 100), size_hint=(1, None), padding=20, spacing=5, rows=2)

        def alter_map(instance):
            if instance.text == "Resize":
                self.popup_constructor_size("Resize Map").open()
            else:
                self.popup_constructor_size("New Map: !!UNSAVED PROGRESS WILL BE LOST!!").open()

        def save_load_export(instance):
            if instance.text == "Save":
                self.popup_constructor_file("Save Map")
            if instance.text == "Load":
                self.popup_constructor_file("Load Map")
            if instance.text == "Export":
                self.popup_constructor_file("Export Map")

        resize_map_btn = Button(text="Resize")
        new_map_btn = Button(text="New")
        save_btn = Button(text="Save")
        load_btn = Button(text="Load")
        export_btn = Button(text="Export")
        resize_map_btn.bind(on_press=alter_map)
        new_map_btn.bind(on_press=alter_map)
        for button in [save_btn, load_btn, export_btn]:
            button.bind(on_press=save_load_export)
        for button in [new_map_btn, resize_map_btn, save_btn, load_btn, export_btn]:
            map_control.add_widget(button)

        def tool_logic(instance):
            if instance.text == "Grid":
                self.backend.grid_toggle = 1 if self.backend.grid_toggle == 0 else 0
                self.backend.undo_tracker += -1
                self.backend.undo_array = self.backend.undo_array[0:-1]
                self.redraw_map()
                if self.backend.grid_toggle:
                    tool_buttons[0].background_color = (0.5, 0.5, 0.5, 1.0)
                else:
                    tool_buttons[0].background_color = (1.0, 1.0, 1.0, 1.0)
            if instance.text == "Fill":
                self.backend.fill_toggle = 1 if self.backend.fill_toggle == 0 else 0
                self.backend.square_toggle = 0
                self.redraw_map()
                if self.backend.fill_toggle:
                    tool_buttons[1].background_color = (0.5, 0.5, 0.5, 1.0)
                    tool_buttons[2].background_color = (1.0, 1.0, 1.0, 1.0)
                else:
                    tool_buttons[1].background_color = (1.0, 1.0, 1.0, 1.0)
            if instance.text == "Sqr":
                self.backend.square_toggle = 1 if self.backend.square_toggle == 0 else 0
                self.backend.fill_toggle = 0
                if self.backend.square_toggle:
                    tool_buttons[2].background_color = (0.5, 0.5, 0.5, 1.0)
                    tool_buttons[1].background_color = (1.0, 1.0, 1.0, 1.0)
                else:
                    tool_buttons[2].background_color = (1.0, 1.0, 1.0, 1.0)
            if instance.text == "2x":
                self.backend.zoom_mod = 2 if self.backend.zoom_mod != 2 else 1
                self.backend.undo_tracker += -1
                self.backend.undo_array = self.backend.undo_array[0:-1]
                self.redraw_map()
                if self.backend.zoom_mod == 2:
                    tool_buttons[3].background_color = (0.5, 0.5, 0.5, 1.0)
                    tool_buttons[4].background_color = (1.0, 1.0, 1.0, 1.0)
                else:
                    tool_buttons[3].background_color = (1.0, 1.0, 1.0, 1.0)
            if instance.text == ".5x":
                self.backend.zoom_mod = 0.5 if self.backend.zoom_mod != 0.5 else 1
                self.backend.undo_tracker += -1
                self.backend.undo_array = self.backend.undo_array[0:-1]
                self.redraw_map()
                if self.backend.zoom_mod == 0.5:
                    tool_buttons[4].background_color = (0.5, 0.5, 0.5, 1.0)
                    tool_buttons[3].background_color = (1.0, 1.0, 1.0, 1.0)
                else:
                    tool_buttons[4].background_color = (1.0, 1.0, 1.0, 1.0)
            elif instance.text == "Img":
                self.popup_constructor_file('Import Image')

        tool_buttons = []
        for tool in ['Grid', 'Fill', 'Sqr', '2x', '.5x', 'Img', ]:
            tool_btn = Button(text=tool)
            tool_btn.bind(on_press=tool_logic)
            tool_buttons.append(tool_btn)

        for i in range(0, 6, 2):
            button_shell = GridLayout(cols=2, spacing=5)
            button_shell.add_widget(tool_buttons[i])
            button_shell.add_widget(tool_buttons[i + 1])
            map_control.add_widget(button_shell)
        self.add_widget(map_control)

        """-------------------------D: This section of code creates an important spacer label------------------------"""
        self.add_widget(Label(
            text="\n\n\n\n[b]Layer Menue[/b]",
            markup=True,
            text_size=(200, 100),
            font_size='20dp',
            size_hint=(None, None),
            size=(200, 100),
            pos_hint=(1, 0)))

        """---------------E: This section of code creates the scrollable viewers for the map and tileset-------------"""
        map_scroller = self.get_map_scroller()
        tile_scroller = self.get_tileset_scroller()
        tileset = TilesetView(backend=self.backend, size_hint=(None, None))
        map_image = MapView(backend=self.backend, size_hint=(None, None))
        map_scroller.add_widget(map_image)
        tile_scroller.add_widget(tileset)
        self.add_widget(tile_scroller)
        self.add_widget(map_scroller)
        tileset.texture = self.get_texture(self.backend.active_tile_set)
        map_image.texture = self.get_texture(self.backend.draw_map())
        tileset.size = tileset.texture.size
        map_image.size = map_image.texture.size

        cursor_size = (self.backend.layerlist.get_grid_res(), self.backend.layerlist.get_grid_res())
        cursor_size = tuple(val*self.backend.zoom_mod for val in cursor_size)
        map_cursor = Button(text="", size=cursor_size)
        tile_cursor = Button(text="", size=cursor_size)

        map_image.add_widget(map_cursor)

        tileset.add_widget(tile_cursor)

        def cursor_polling(instance, pos):

            res = self.backend.layerlist.get_grid_res()
            if map_scroller.collide_point(*pos):
                res = self.backend.layerlist.get_grid_res() * self.backend.zoom_mod
                pos = map_scroller.to_local(*pos)
                if map_image.collide_point(*pos):
                    tile_cursor.background_color = [0, 0, 0, 0]
                    map_cursor.background_color = [0, 0, 1, 0.3]
                    map_cursor.size = tuple(val*self.backend.zoom_mod for val in self.backend.active_tile_image.size)
                    if self.backend.check_active_layer_type():

                        pos = (pos[0] // res) * res, (pos[1] // res) * res - (
                                map_cursor.size[1] - res)
                    else:
                        pos = pos[0] - map_cursor.size[1] / 2, pos[1] - \
                             map_cursor.size[1] / 2
                    map_cursor.pos = pos
                else:
                    map_cursor.background_color = [0, 0, 0, 0]

            elif tile_scroller.collide_point(*pos):
                pos = tile_scroller.to_local(*pos)
                if tileset.collide_point(*pos):
                    tile_cursor.background_color = [0, 1, 0, 0.5]
                    map_cursor.background_color = [0, 0, 0, 0]
                    tile_cursor.size = cursor_size
                    pos = (pos[0] // res) * res, (pos[1] // res) * res
                    tile_cursor.pos = pos
                else:
                    tile_cursor.background_color = [0, 0, 0, 0]

        Window.bind(mouse_pos=cursor_polling)

        """-------------------------F: This section of code creates the layer control panel--------------------------"""
        layer_control_shell = GridLayout(rows=2, size_hint=(None, 1), size=(200, 200))
        layer_control_panel = GridLayout(rows=3, cols=3, size_hint=(None, None), size=(200, 40), pos=self.size,
                                         pos_hint=(None, None))
        layer_list = GridLayout(rows=1, cols=1, size=(200, 1), size_hint=(None, 1))

        def modify_layer_list(instance):
            """
            This method handles button presses on the layer control buttons.
            :param instance:
            :return:
            """
            if instance.text == "New":
                self.backend.layerlist.new_layer(self.backend.active_tile_set_file,
                                                 position=self.backend.active_layer + 1)
                self.backend.active_layer += 1
            elif instance.text == "Delete":
                self.backend.layerlist.del_layer(self.backend.active_layer)
                self.backend.active_layer += -1
                if self.backend.active_layer < 1:
                    if len(self.backend.layerlist.stack) <= 1:
                        self.backend.layerlist.new_layer(self.backend.active_tile_set_file)
                        self.backend.active_layer += 1
                    else:
                        self.backend.active_layer = 1
                self.backend.active_tile_set_file = self.backend.layerlist.get_layer(self.backend.active_layer).tileset
                self.backend.update_active_tileset()
                self.redraw_active_tile()
                self.redraw_tileset()
            elif instance.text == "Up":
                if self.backend.active_layer > 1:
                    self.backend.layerlist.move_up(self.backend.active_layer)
                    self.backend.active_layer += -1
            elif instance.text == "Down":
                if self.backend.active_layer < len(self.backend.layerlist.stack) - 1:
                    self.backend.layerlist.move_down(self.backend.active_layer)
                    self.backend.active_layer += 1
            elif instance.text == "Rename":
                self.popup_constructor_rename().open()
            else:
                self.backend.layerlist.add_image_layer(self.backend.active_tile_set_file,
                                                       position=self.backend.active_layer + 1)
                self.backend.active_layer += 1
            self.populate_layer_list(layer_list)
            self.redraw_map()

        new_layer_btn = Button(text="New")
        del_layer_btn = Button(text="Delete")
        new_layer_btn.bind(on_press=modify_layer_list)
        del_layer_btn.bind(on_press=modify_layer_list)
        up_btn = Button(text="Up")
        down_btn = Button(text="Down")
        rename_btn = Button(text="Rename")
        freedraw_btn = Button(text="Unsnap")
        for button in [rename_btn, new_layer_btn, up_btn, freedraw_btn, del_layer_btn, down_btn]:
            button.bind(on_press=modify_layer_list)
            layer_control_panel.add_widget(button)
        layer_control_shell.add_widget(layer_control_panel)
        self.populate_layer_list(layer_list)
        layer_control_shell.add_widget(layer_list)
        self.add_widget(layer_control_shell)

    def populate_layer_list(self, widget):
        """
        This layer populates the list of displayed layers, highlighting the active layer in white
        :param widget:
        :return:
        """

        def set_active_layer(instance):
            words = instance.text.split(" ")
            self.backend.active_layer = int(words[-1])
            self.populate_layer_list(widget)
            self.backend.active_tile_set_file = self.backend.layerlist.get_layer(self.backend.active_layer).tileset
            self.backend.update_active_tileset()
            self.redraw_active_tile()
            self.redraw_tileset()
            self.children[len(self.children) - 1].children[2].children[1]. \
                text = text = self.backend.active_tile_set_file.split('/')[-1]

        widget.clear_widgets()
        for i, layer in enumerate(self.backend.layerlist.stack[1:]):
            widget.rows += 1
            layer_button = Button(text=f"{layer.name} at position {i + 1}")
            layer_button.bind(on_press=set_active_layer)
            if not isinstance(layer, Layer):
                layer_button.color = [0.5, 0.5, 1, 1]
            if i + 1 == self.backend.active_layer:
                layer_button.background_normal = ""
                if not isinstance(layer, Layer):
                    layer_button.color = [0, 0.4, 0.9, 1]
                else:
                    layer_button.color = (0, 0, 0, 1)
            widget.add_widget(layer_button)

    def redraw_active_tile(self):
        self.children[5].children[0].texture = self.get_texture(self.backend.get_active_tile_image())
        self.children[5].children[0].size = self.children[5].children[0].texture.size

    def popup_constructor_rename(self):
        """
        this method creates a pop-up dialogue to rename a layer
        :return:
        """

        def resolve(instance):
            """
            This method resolves the rename popup
            :param instance:
            :return:
            """
            new_name = instance.text
            if new_name.isalnum():
                self.backend.layerlist.set_name(new_name, self.backend.active_layer)
                self.populate_layer_list(self.children[0].children[0])
            pop.dismiss()
            self.initialize_keyboard()

        name_input = TextInput(text="Layername")
        name_input.multiline = False
        name_input.bind(on_text_validate=resolve)
        pop = Popup(
            title="Rename Layer:",
            content=name_input,
            size_hint=(None, None),
            size=(500, 100),
            auto_dismiss=True
        )
        return pop

    def popup_constructor_file(self, title):
        """
        generalized popup constructor for save/load/export and import image commands
        :param title:
        :return:
        """
        changed_dir = False
        file_browser = FileChooserIconView()
        file_browser_text = TextInput(text="File.txt", multiline=False, size=(345, 30), size_hint=(None, None))
        file_browser.add_widget(file_browser_text)
        file_browser.path = self.backend.working_dir + 'Saved maps'
        file_browser_cancel_btn = Button(text="Cancel", size=(60, 30), size_hint=(None, None), pos=(415, 0))
        file_browser_confirm_btn = Button(text="blank", size=(60, 30), size_hint=(None, None), pos=(350, 0))
        if title == "Save Map":
            file_browser_text.text = file_browser.path + "/Untitled.text"
            file_browser_confirm_btn.text = "Save"
        elif title == "Load Map":
            file_browser_text.text = file_browser.path + "/Untitled.text"
            file_browser_confirm_btn.text = "Load"
        elif title == "Import Image":
            file_browser_text.text = file_browser.path + "/Untitled.png"
            file_browser_confirm_btn.text = "Import"
        else:
            file_browser_text.text = file_browser.path + "/Untitled.png"
            file_browser_confirm_btn.text = "Export"
        file_browser.add_widget(file_browser_cancel_btn)
        file_browser.add_widget(file_browser_confirm_btn)

        def resolve_dialogue(instance):
            try:
                if title == "Save Map":
                    if file_browser_text.text.split("\\")[-1] in [i.split("\\")[-1] for i in file_browser.files] or \
                            file_browser_text.text.split("/")[-1] in [i.split("\\")[-1] for i in file_browser.files]:
                        def overwrite_resolve(instance):
                            self.backend.save_to_file(file_browser_text.text)
                            pop2.dismiss()
                            pop.dismiss()
                            self.initialize_keyboard()

                        overwrite_okay.bind(on_press=overwrite_resolve)
                        nonlocal overwrite_msg
                        overwrite_msg = Label(text=f"The file: \n{file_browser_text.text}\nwill be Overwritten")
                        pop2.open()
                    else:
                        self.backend.save_to_file(file_browser_text.text)
                        pop.dismiss()
                        self.initialize_keyboard()
                elif title == "Load Map":
                    self.backend.load_from_file(file_browser_text.text)
                    self.redraw_map()
                    self.redraw_tileset()
                    self.redraw_active_tile()
                    self.populate_layer_list(self.children[0].children[0])
                    pop.dismiss()
                    self.initialize_keyboard()
                elif title == "Export Map":
                    if file_browser_text.text.split("\\")[-1] in [i.split("\\")[-1] for i in file_browser.files] or \
                            file_browser_text.text.split("/")[-1] in [i.split("\\")[-1] for i in file_browser.files]:
                        def overwrite_resolve(instance):
                            self.backend.export(file_browser_text.text)
                            pop2.dismiss()
                            pop.dismiss()
                            self.initialize_keyboard()

                        overwrite_okay.bind(on_press=overwrite_resolve)
                        overwrite_msg.text = f"!WARNING!: The file: \n{file_browser_text.text}\nwill be Overwritten"
                        pop2.open()
                    else:
                        self.backend.export(file_browser_text.text)
                        pop.dismiss()
                        self.initialize_keyboard()
                elif title == "Import Image":
                    self.backend.import_img(file_browser_text.text)
                    self.populate_layer_list(self.children[0].children[0])
                    self.redraw_map()
                    pop.dismiss()
                    self.initialize_keyboard()

            except Exception as e:
                error = Popup(
                    title=" An error Occured:",
                    content=(Label(text=e.__str__())),
                    size_hint=(None, None),
                    size=(400, 200),
                    auto_dismiss=True
                )
                error.open()

        def filecancel(instance):
            pop.dismiss()
            self.initialize_keyboard()

        def update_file_text(instance, path):
            changed_dir = True
            if title == "Save Map" or title == "Load Map":
                file_browser_text.text = file_browser.path + "/Untitled.text"
            else:
                file_browser_text.text = file_browser.path + "/Untitled.png"

        def update_file_text_select(instance, selection, touch):
            path = ""
            for i in selection:
                path = i
                file_browser_text.text = path
            if changed_dir == False:
                segments = path.split("\\")
                del segments[5]
                clean_path = "\\".join(segments)
                file_browser_text.text = clean_path

        file_browser.bind(on_submit=update_file_text_select, path=update_file_text)
        file_browser_cancel_btn.bind(on_press=filecancel)
        file_browser_confirm_btn.bind(on_press=resolve_dialogue)

        pop = Popup(
            title=title,
            content=file_browser,
            size_hint=(None, None),
            size=(500, 500),
            auto_dismiss=True
        )
        pop.open()

        overwrite = GridLayout(rows=2)
        overwrite_msg = Label(text=f"!WARNING!: The file: \n{file_browser_text.text}\nwill be Overwritten")
        overwrite_buttons = GridLayout(cols=2, size_hint=(1, None), size=(100, 40))
        overwrite_okay = Button(text="Overwrite", size_hint=(1, None), size=(100, 40))
        overwrite_cancel = Button(text="Cancel", size_hint=(1, None), size=(100, 40))
        overwrite_buttons.add_widget(overwrite_okay)
        overwrite_buttons.add_widget(overwrite_cancel)
        overwrite.add_widget(overwrite_msg)
        overwrite.add_widget(overwrite_buttons)
        overwrite_cancel.bind(on_press=lambda instance: pop2.dismiss())

        pop2 = Popup(
            title="Confirm File Overwrite",
            content=overwrite,
            size_hint=(None, None),
            size=(500, 300),
            auto_dismiss=True
        )

    def popup_constructor_size(self, title):
        """
        This popup creates a generic pop up with two text field inputs, used for height and width to update the size of
        the map, or create a new map of the specified size.
        :param title:
        :return:
        """
        grid_res = self.backend.layerlist.get_grid_res()
        self.map_width = self.backend.layerlist.get_size()[0]
        self.map_height = self.backend.layerlist.get_size()[1]

        def cancel_dialogue(instance):
            pop.dismiss()
            self.initialize_keyboard()

        def resolve_dialogue(instance):
            self.map_height = 1 if self.map_height < 2 else self.map_height
            self.map_width = 1 if self.map_height < 2 else self.map_width
            if title == "New Map: !!UNSAVED PROGRESS WILL BE LOST!!":
                self.backend.create_drawspace(1, 1)
                self.backend.layerlist.resize((self.map_width, self.map_height))
                self.redraw_map()
                self.populate_layer_list(self.children[0].children[0])
                pop.dismiss()
                self.initialize_keyboard()
            else:
                self.backend.layerlist.resize((self.map_width, self.map_height))
                self.redraw_map()
                pop.dismiss()
                self.initialize_keyboard()

        def store_width(instance, value):
            if instance.text != "":
                self.map_width = int(instance.text)

        def store_height(instance, value):
            if instance.text != "":
                self.map_height = int(instance.text)

        input_shell = GridLayout(rows=3, cols=2)
        input1 = TextInput(multiline=False, text=str(int(self.map_width)))
        input1.bind(text=store_width)
        input2 = TextInput(multiline=False, text=str(int(self.map_height)))
        input2.bind(text=store_height)
        input_shell.add_widget(Label(text="Grid Width"))
        input_shell.add_widget(Label(text="Grid Height"))
        input_shell.add_widget(input1)
        input_shell.add_widget(input2)
        okay_btn = Button(text="Okay")
        cancel_btn = Button(text="Cancel")
        okay_btn.bind(on_press=resolve_dialogue)
        cancel_btn.bind(on_press=cancel_dialogue)
        input_shell.add_widget(cancel_btn)
        input_shell.add_widget(okay_btn)
        pop = Popup(
            title=title,
            content=input_shell,
            size_hint=(None, None),
            size=(400, 200),
            auto_dismiss=True
        )
        return pop

    def redraw_map(self, target=None):
        """
        Simple method that redraws the full map and displays it on the gui.
        :return:
        """
        self.children[1].children[0].texture = self.get_texture(self.backend.draw_map(target))
        self.children[1].children[0].size = self.children[1].children[0].texture.size

    def redraw_tileset(self):
        """
        Simple method that redraws the tileset and displays it on the gui
        :return:
        """
        self.children[len(self.children) - 1].children[2].children[1].text = self.backend.active_tile_set_file.split('/')[-1]
        self.children[2].children[0].texture = self.get_texture(self.backend.active_tile_set)
        self.children[2].children[0].size = self.children[2].children[0].texture.size

    def get_map_scroller(self):
        """
        returns a scroll view object for viewing the map or drawspace
        :return:
        """
        returnable = ScrollView(
            size_hint=(1, 1),
            scroll_type=['bars'],
            bar_width=16
        )
        return returnable

    def get_tileset_scroller(self):
        """
        returns a scroll view object for viewing the tilset
        :return:
        """
        returnable = ScrollView(
            size_hint=(None, 1),
            size=(300, 300),
            scroll_type=['bars'],
            bar_width=16
        )
        return returnable

    def get_texture(self, image):
        """
        This method accepts a PIL image object and returns a kivy texture created from the image
        :param image:
        :return:
        """
        num_array = numpy.array(image)
        texture = Texture.create(size=image.size)
        texture.blit_buffer(num_array.tobytes(), bufferfmt="ubyte", colorfmt="rgba")
        texture.flip_vertical()
        return texture

    def run_undo(self):
        if self.backend.undo():
            self.children[1].children[0].texture = self.get_texture(self.backend.draw_map(not_undoing=False))
            self.children[1].children[0].size = self.children[1].children[0].texture.size
            self.backend.active_tile_set_file = self.backend.layerlist.get_layer(self.backend.active_layer).tileset
            self.backend.update_active_tileset()
            self.redraw_active_tile()
            self.redraw_tileset()
            self.populate_layer_list(self.children[0].children[0])

    def run_redo(self):
        if self.backend.redo():
            self.children[1].children[0].texture = self.get_texture(self.backend.draw_map(not_undoing=False))
            self.children[1].children[0].size = self.children[1].children[0].texture.size
            self.backend.active_tile_set_file = self.backend.layerlist.get_layer(self.backend.active_layer).tileset
            self.backend.update_active_tileset()
            self.redraw_active_tile()
            self.redraw_tileset()
            self.populate_layer_list(self.children[0].children[0])

    def initialize_keyboard(self):

        def _keyboard_closed():
            self._keyboard.unbind(on_key_down=on_keyboard_down)
            self._keyboard.unbind(on_key_up=on_keyboard_up)
            self._keyboard = None

        def on_keyboard_down(self, key, scancode, codepoint):
            if key == (305, 'lctrl'):
                self.control_down = True
            return True

        def on_keyboard_up(self, key):
            if key == (305, 'lctrl'):
                self.control_down = False
            if key == (122, 'z') and self.control_down:
                self.target.run_undo()
            elif key == (121, 'y') and self.control_down:
                self.target.run_redo()
            elif key == (115, 's') and self.control_down:
                print("ctrls")
            return True

        self._keyboard = Window.request_keyboard(_keyboard_closed, self)
        self._keyboard.bind(on_key_up=on_keyboard_up)
        self._keyboard.bind(on_key_down=on_keyboard_down)


class MappappApp(App):
    def build(self):
        return MainScreen()


MappappApp().run()
