class Layer:
    """
    Layer class consisting of a dictionary of co-ordinate tuples (x,y) as keys for tile target coordinate tuples
    """

    def __init__(self, tileset, size=(1, 1), resolution=32, name="layer"):
        self.tileset = tileset
        self.size = size
        self.grid_res = resolution
        self.grid = {}
        self.resize(size)
        self.name = name

    def resize(self, new_size: 'integer tuple'):
        """"
        Resize method, accepts an integer tuple of the new size and either adds or removes grid cells accordingly
        """
        x, y = new_size

        if x < 0 or y < 0:
            raise ValueError("Layer size cannot be less than 1 by 1")

        new_grid = {}
        for cell in self.grid:
            if cell[0] < x and cell[1] < y:
                new_grid[cell] = self.grid[cell]

        for i in range(x):
            for j in range(y):
                if (i, j) not in new_grid:
                    new_grid[(i, j)] = (0, 0)
        self.grid = new_grid
        self.size = new_size

    def update_tiles(self, target_dict: 'dict of tuple:tuple items'):
        """"
        method to update the targets of certain tiles in the grid. Accepts a subgrid dictionary consisting of the tiles
        to be modified and the new target for those tiles.
        """
        for k in target_dict:
            self.grid[k] = target_dict[k]

    def to_string(self):
        result = ""
        result += f"{self.name}*{self.tileset}*{self.size}*{self.grid_res}*"
        for i in self.grid:
            result += f"{i}:{self.grid[i]}$"
        return result
