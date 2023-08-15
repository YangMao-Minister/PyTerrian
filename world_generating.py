

from option import *
from base2 import *


WORLD_LAYER_EDGE = [-200, 320, 800, 1200]
WORLD_LAYER_BGM = "," \
                  "," \
                  "," \
                  "," \
                  "assets/bgm/Silencyde - AM.mp3," \
    .split(",")
WORLD_LAYER_BACKGROUND = "," \
                         "assets/textures/bgs/background.png," \
                         "assets/textures/bgs/skyland.png," \
                         "assets/textures/bgs/space.png," \
                         "assets/textures/bgs/outerspace.jpg," \
    .split(",")
WORLD_LAYER_NAME = []
temp = "地下 地表 天域 近地空间 外太空".split()
for ss in temp:
    WORLD_LAYER_NAME.append("—" + ss + "—")


class WorldGenerator:

    def __init__(self, seed):
        self.seed = seed
        # self._groundNS = NoiseSet(
        #     ValueNoise1D(seed=seed, frequency=500, loud=150),
        #     ValueNoise1D(seed=seed + 12, frequency=100, loud=50),
        #     ValueNoise1D(seed=seed + 23, frequency=12, loud=6)
        # )

        self._groundNS = NoiseSet(
            PerlinNoise2D(seed=seed, frequency=35, loud=50),
            PerlinNoise2D(seed=seed + 12, frequency=10, loud=25),
            PerlinNoise2D(seed=seed + 23, frequency=3, loud=13)
        )

        self._skyLandBottomNS = NoiseSet(
            ValueNoise1D(seed=seed + 25, frequency=500, loud=30),
            ValueNoise1D(seed=seed - 78, frequency=25, loud=6)
        )
        self._skyLandTopNS = NoiseSet(
            ValueNoise1D(seed=seed + 114514, frequency=350, loud=80),
            ValueNoise1D(seed=seed - 11442, frequency=100, loud=50),
            ValueNoise1D(seed=seed + 1212, frequency=12, loud=5)
        )

    def generateChunk(self, chunk):
        for line in chunk.blocks:
            y = line[0].y
            if -200 <= y < 320:
                wga = self._ground
            elif 320 <= y < 800:
                wga = self._skyLand
            else:
                wga = self._none
            for block in line:
                wga(block)

    def _none(self, block):
        pass

    def _ground(self, block):
        # 地表地形
        x, y = block.x, block.y
        random.seed(x)
        density = self.worldGenCurve(self._groundNS(x, y), y)
        bT = BlockID.air

        if 0 <= density < 20:
            bT = BlockID.dirt
        elif 20 <= density < 50:
            bT = BlockID.stone
        elif 50 <= density:
            bT = BlockID.stone

        block.blockType = bT

    def _skyLand(self, block):
        x, y = block.x, block.y
        bottom = round(self._skyLandBottomNS(x) + 340)
        top = round(self._skyLandTopNS(x) + 370)
        bT = BlockID.air
        if bottom <= y < top:
            bT = BlockID.cloud
        block.blockType = bT

    def worldGenCurve(self, nv, y):
        """定义域Z 值域R"""
        return nv - 3 * y


if __name__ == "__main__":
    import pygame

    cameraX = 0
    cameraY = 0

    pygame.init()
    window = pygame.display.set_mode((256, 256))

    pn1 = PerlinNoise2D(seed=0, frequency=50, loud=20)

    while True:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()

        for x in range(256):
            for y in reversed(range(256)):
                nv = min(max(pn1.getNoise(x, y)+10, 0), 255)
                pygame.draw.rect(
                    window,
                    (nv, nv, nv),
                    (x, y, 1, 1)
                )
        for x in range(256):
            for y in reversed(range(256)):
                if Vector2D(x, y) in pn1._cache:
                    pygame.draw.line(
                        window,
                        (255, 0, 0),
                        (x, y),
                        (x + pn1._cache[Vector2D(x, y)].x * 10, y + pn1._cache[Vector2D(x, y)].y * 10)
                    )

        pygame.display.flip()
