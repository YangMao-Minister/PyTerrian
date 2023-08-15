WINDOW_WIDTH = 900
WINDOW_HEIGHT = 600
MAX_FPS = 60

CHUNK_SIZE = 16
BLOCK_SIZE = 16  # 单位:px
LOAD_RANGE = 5
DEFAULT_SEED = 0
LAYER_TIP_DISPLAY_TIME = 300


class BlockID:
    """专门存储方块id的类"""
    air = 0
    stone = 1
    grass = 2
    dirt = 3
    sand = 4
    water = 5
    cloud = 6
