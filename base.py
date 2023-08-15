import collections
import os
import json
import multiprocessing
import struct
import time

import pygame

from option import *
from world_generating import WorldGenerator


class ChunkError(Exception):
    """找区块时区块未加载时抛出"""


class Block:
    """
    方块类
    """
    # 储存每种方块纹理的字典
    blockTextureMap = {}

    __slots__ = ("x", "y", "blockType")

    def __init__(self, x, y, blockType=None):
        # 因为存在大量Block实例，为了节约内存，所以不用Vector2D类保存位置坐标。
        self.x = x
        self.y = y
        if blockType is None:
            self.blockType = BlockID.air
        else:
            self.blockType = blockType

    def __repr__(self):
        return f"Block {self.blockType} at ({self.x}, {self.y}), in chunk({self.x // CHUNK_SIZE}, {self.y // CHUNK_SIZE})"

    @classmethod
    def initBlockTextureMap(cls):
        for textureName, i in (k for k in BlockID.__dict__.items() if not k[0].startswith("_")):
            tPath = (os.getcwd() + "\\assets\\textures\\" + textureName + ".png")
            # print(textureName, i)
            try:
                cls.blockTextureMap[i] = pygame.image.load(tPath).convert_alpha()
            except FileNotFoundError:
                cls.blockTextureMap[i] = pygame.image.load(
                    os.getcwd() + "\\assets\\textures\\noFile.png").convert_alpha()
                # print(f"{tPath} 加载失败")


class Chunk:
    def __init__(self, x: int = None, y: int = None, fillBlock=None):
        self.x = x
        self.y = y
        self.blocks = None
        if fillBlock is not None:
            self.fillBlocksWith(fillBlock)

    def __repr__(self):
        return f"Chunk({self.x}, {self.y})"

    def __getitem__(self, item):
        return self.blocks[item]

    def fillBlocksWith(self, bt=None):
        self.blocks = [
            [Block(self.x * CHUNK_SIZE + i, self.y * CHUNK_SIZE + j, blockType=bt)
             for j in range(CHUNK_SIZE)]
            for i in range(CHUNK_SIZE)]

    def dump(self, path):
        with open(path, "wb") as f:
            f.write(struct.pack("i", self.x))
            f.write(struct.pack("i", self.y))
            for line in self:
                for block in line:
                    f.write(struct.pack("b", block.blockType))
        # print(f"{self} 已经卸载至磁盘。")

    @classmethod
    def load(cls, path):
        with open(path, "rb") as f:
            newChunk = cls()
            x = struct.unpack("i", f.read(4))[0]
            newChunk.x = x
            y = struct.unpack("i", f.read(4))[0]
            newChunk.y = y
            newChunk.fillBlocksWith(BlockID.air)
            for i in range(CHUNK_SIZE):
                for j in range(CHUNK_SIZE):
                    bt = struct.unpack("b", f.read(1))[0]
                    newChunk[i][j] = Block(x * CHUNK_SIZE + i, y * CHUNK_SIZE + j, blockType=bt)
        # print(f"{newChunk} 已经从磁盘中加载。")
        return newChunk


class World:
    def __init__(self, seed: int = DEFAULT_SEED, name: str = "New_World"):
        self.seed = seed
        self.name = name

        # 世界生成、加载相关
        self.totalChunks = set()
        self.loadedChunks = {}
        self.worldGenerator = WorldGenerator(seed=seed)
        self.worldLoadCenterOld = [0, 0]
        self.worldLoadCenterNew = [0, 0]

        self.savePath = os.getcwd() + f"/saves/{name}/"
        if not os.path.exists(self.savePath):
            os.mkdir(self.savePath)

    def __repr__(self):
        return f"World: \"{self.name}\" on seed \"{self.seed}\""

    def getBlock(self, x, y) -> Block:
        try:
            return self.loadedChunks[(x // CHUNK_SIZE, y // CHUNK_SIZE)][x % CHUNK_SIZE][y % CHUNK_SIZE]
        except KeyError:
            raise ChunkError(f"Chunk at ({x // CHUNK_SIZE}, {y // CHUNK_SIZE}) hasn't loaded!")
        except TypeError:
            raise ChunkError(f"Chunk at ({x // CHUNK_SIZE}, {y // CHUNK_SIZE}) hasn't initialized!")

    def updateLoadedChunks(self, forced=False):
        if self.worldLoadCenterNew == self.worldLoadCenterOld and not forced:
            # 世界加载中心没有变动
            return

        checkChunksSet = set()
        for y in range(self.worldLoadCenterNew[1] - LOAD_RANGE, self.worldLoadCenterNew[1] + LOAD_RANGE + 1):
            for x in range(self.worldLoadCenterNew[0] - LOAD_RANGE, self.worldLoadCenterNew[0] + LOAD_RANGE + 1):
                checkChunksSet.add((x, y))
                if (x, y) in self.loadedChunks:
                    # 这个区块已经在加载中了
                    continue
                try:
                    chunk = Chunk.load(self.savePath + f"Chunk({x}, {y}).bin")
                except FileNotFoundError:
                    # 区块还没有生成
                    chunk = Chunk(x, y, fillBlock=BlockID.air)
                    self.worldGenerator.generateChunk(chunk)
                    # print(f"{chunk} 已经被动态生成。")
                self.totalChunks.add((x, y))
                self.loadedChunks[(x, y)] = chunk

        for y in range(self.worldLoadCenterOld[1] - LOAD_RANGE, self.worldLoadCenterOld[1] + LOAD_RANGE + 1):
            for x in range(self.worldLoadCenterOld[0] - LOAD_RANGE, self.worldLoadCenterOld[0] + LOAD_RANGE + 1):
                if (x, y) not in checkChunksSet:
                    if (x, y) in self.loadedChunks:
                        self.loadedChunks[(x, y)].dump(self.savePath + f"Chunk({x}, {y}).bin")
                        del self.loadedChunks[(x, y)]

        self.worldLoadCenterOld = self.worldLoadCenterNew[:]

    @staticmethod
    def dumpWorld(world):
        path = (os.getcwd() + "/saves/" + world.name + "/")
        if not os.path.exists(path):
            os.mkdir(path)
        with open(path + "world.json", "w") as f:
            attrs = world.__dict__
            attrs["loadedChunks"] = tuple(world.loadedChunks.keys())
            json.dump(attrs, f, indent=4)

    @staticmethod
    def loadWorld(path):
        newWorld = World()
        newWorld.__dict__ = json.load(path + "world.json")
        return newWorld


class PromptBar:
    def __init__(self, font: pygame.font.Font, dest: pygame.Surface, maxLen, position=(0, 0), fadeTime=300):
        from collections import deque
        self._prompts = deque(maxlen=maxLen)
        self._font = font
        self._dest = dest
        self._defaultFadeTime = fadeTime
        self._x, self._y = position  # 左下角坐标

    def push(self, text, debug=False, *args, **kwargs):
        if not args:
            c = pygame.Color(0, 0, 0, 0)
            c.hsva = (12 * (round(time.time()) % 30), 100, 100, 100)
            args = (True, c)
        if debug:
            text = f"[{time.strftime('%H:%M:%S')}][调试信息] " + text
        textSurface = self._font.render(text, *args, **kwargs)
        self._prompts.appendleft([textSurface, self._defaultFadeTime])

    def biltMe(self):
        for i, (ts, ft) in enumerate(list(self._prompts)[:]):
            tsr = ts.get_rect()
            h = tsr.height
            tsr.topleft = (self._x, self._y - (i + 1) * h)
            ts.set_alpha(255 * (ft / self._defaultFadeTime))
            self._dest.blit(ts, tsr)
            if ft == 1:
                try:
                    del self._prompts[i]
                except IndexError:
                    pass
                continue
            self._prompts[i][1] -= 1


if __name__ == '__main__':
    a = 0
    for _ in range(10):
        t = time.time()
        for path in os.listdir(".\\saves\\New_World"):
            Chunk.load(os.getcwd() + "\\saves\\New_World\\" + path)
        b = time.time() - t
        print(b)
        a += b
    print(f"\n\t加载{len(os.listdir('./saves/New_World'))}区块平均用时{a / 10}s")
