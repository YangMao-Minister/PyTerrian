import multiprocessing
import sys
import bisect
import threading

import pygame.mixer

from base import *
from world_generating import *

# 模块参数初始化
pygame.init()


class Main:
    """负责交互,音效和渲染的类"""

    def __init__(self, window_: pygame.Surface, world=None):
        self.window = window_
        if not world:
            self.world = World()
        else:
            self.world = world

        self.clock = pygame.time.Clock()
        self.running = True
        self.fps = 0

        # 渲染部分
        self.screenCenterPosition = Vector2D(0, 0)
        self.screenCenterVelocity = Vector2D(0, 0)
        self.scale = 1.00
        self.centerPosition = Vector2D(WINDOW_WIDTH // 2, -WINDOW_HEIGHT // 2)
        self.backGroundDict = dict()
        self.backGroundRect = pygame.Rect(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT)

        # 音频部分
        self.volume = 0.25
        pygame.mixer.music.set_volume(self.volume)

        # 字体部分
        self.aaHhhFont16 = pygame.font.Font("./assets/fonts/Aa嘿嘿黑.ttf", 16)  # 宋体
        self.aahhhFont64 = pygame.font.Font("./assets/fonts/Aa嘿嘿黑.ttf", 64)

        # gui界面
        self.showInfo = False
        self.gui = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), flags=pygame.SRCALPHA)
        self.promptBar = PromptBar(font=self.aaHhhFont16, dest=self.window, maxLen=20, position=(0, WINDOW_HEIGHT),
                                   fadeTime=180)
        self.promptBar.push(
            f"[{time.strftime('%H:%M:%S')}][调试信息] 初始化已完成")

        # 其他变量
        # 区域提示计时器
        self.layerTipTimer = LAYER_TIP_DISPLAY_TIME
        # 区域名称
        # self.worldLayer = bisect.bisect(WORLD_LAYER_EDGE, self.screenCenterPosition.y)
        self.worldLayer = 0

    def run(self):
        while self.running:
            self.fps = self.clock.get_fps()

            self._updateFrame()
            self._renderFrame()
            self._checkEvents()

            # 限制最高帧率
            self.clock.tick(MAX_FPS)

        pygame.quit()
        sys.exit(0)

        # 多进程尝试
        # renderProcess = multiprocessing.Process(target=self._renderLoop)
        # renderProcess.start()
        # updateProcess = multiprocessing.Process(target=self._updateLoop)
        # updateProcess.start()

    def _renderLoop(self):
        while self.running:
            self.fps = self.clock.get_fps()

            self._renderFrame()

            self.clock.tick(MAX_FPS)

    def _updateLoop(self):
        self.world.updateLoadedChunks(forced=True)
        while self.running:
            self._updateFrame()
        pygame.quit()
        sys.exit()

    def _checkEvents(self):
        events = pygame.event.get()
        for e in events:
            if e.type == pygame.QUIT:
                self.running = False
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_COMMA:
                    self.volume = max(self.volume - 0.05, 0)
                    pygame.mixer.music.set_volume(self.volume)
                    self.promptBar.push(
                        "音量减小", debug=True
                    )
                elif e.key == pygame.K_PERIOD:
                    self.volume = min(self.volume + 0.05, 1)
                    pygame.mixer.music.set_volume(self.volume)
                    self.promptBar.push(
                        "音量增大", debug=True
                    )
                elif e.key == pygame.K_F3:
                    self.showInfo = not self.showInfo
                    self.promptBar.push(
                        f"已{'打开' if self.showInfo else '关闭'}调试信息界面", debug=True
                    )
                else:
                    pass

        pressedKeys = pygame.key.get_pressed()
        if pressedKeys[pygame.K_UP]:
            self.screenCenterVelocity.y += 0.5
        if pressedKeys[pygame.K_DOWN]:
            self.screenCenterVelocity.y -= 0.5
        if pressedKeys[pygame.K_LEFT]:
            self.screenCenterVelocity.x -= 0.5
        if pressedKeys[pygame.K_RIGHT]:
            self.screenCenterVelocity.x += 0.5
        if pressedKeys[pygame.K_SPACE]:
            self.screenCenterVelocity.x = 0.0
            self.screenCenterVelocity.y = 0.0
        if pressedKeys[pygame.K_LSHIFT]:
            self.screenCenterVelocity *= 0.5
        if pressedKeys[pygame.K_MINUS]:
            self.scale = max(self.scale - 0.05, 0.2)
        if pressedKeys[pygame.K_EQUALS]:
            self.scale = min(self.scale + 0.05, 5)

    def _renderFrame(self):
        # 清屏
        try:
            self.window.blit(self.backGroundDict[self.worldLayer], self.backGroundRect)
        except KeyError:
            pass
        self.gui.fill(color=(0, 0, 0, 0))
        # 渲染方块
        self._renderBlocks()
        # gui界面
        self._renderGUI()
        # 渲染提示栏
        self.promptBar.biltMe()
        # 刷新屏幕
        pygame.display.flip()

    def _renderGUI(self):
        # 屏幕中间炫酷吊炸天的提示！！！
        if self.worldLayer != bisect.bisect(WORLD_LAYER_EDGE, self.screenCenterPosition.y):
            self.layerTipTimer = LAYER_TIP_DISPLAY_TIME
        if self.layerTipTimer:
            layerTip = self.aahhhFont64.render(WORLD_LAYER_NAME[self.worldLayer], True, "#99c9fd")
            layerTipRect = layerTip.get_rect()
            layerTipRect.center = (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 4)
            layerTip.set_alpha(self.layerTipTimer * (256 // 120))
            self.layerTipTimer -= 1
            self.gui.blit(layerTip, layerTipRect)
        self.worldLayer = bisect.bisect(WORLD_LAYER_EDGE, self.screenCenterPosition.y)

        if self.showInfo:
            information = (
                f"当前帧率：{round(self.fps)}\n",
                f"相机位置：{self.screenCenterPosition.getTuple()}\n",
                f"相机速度：{self.screenCenterVelocity.getTuple()}\n",
                f"世界名称：{self.world.name}\n",
                f"当前加载区块数：{len(self.world.loadedChunks)}\n",
                f"世界总区块数：{len(self.world.totalChunks)}\n",
                f"当前区域： {WORLD_LAYER_NAME[self.worldLayer]}",
                f"当前缩放倍率： {round(self.scale, 2)}",
                f"背景音乐：{WORLD_LAYER_BGM[bisect.bisect(WORLD_LAYER_EDGE, self.screenCenterPosition.y)].split('/')[-1]}",
                f"当前音量： {round(self.volume * 100)}%"
            )
            for i, info in enumerate(information):
                infoSurface = self.aaHhhFont16.render(info, True, "#ffffff")
                info2 = infoSurface.copy()
                info2.fill("#000000")
                infoRenderRect = infoSurface.get_rect()
                info2.set_alpha(128)
                infoRenderRect.topleft = (0, i * infoRenderRect.height)
                self.gui.blit(info2, infoRenderRect)
                self.gui.blit(infoSurface, infoRenderRect)

        self.window.blit(self.gui, self.backGroundRect)

    def _renderBlocks(self):
        widthBlockCount = int(WINDOW_WIDTH // (2 * (BLOCK_SIZE * self.scale)) + 4)
        heightBlockCount = int(WINDOW_HEIGHT // (2 * (BLOCK_SIZE * self.scale)) + 4)

        for y in range(round(self.screenCenterPosition.y - heightBlockCount - 2),
                       round(self.screenCenterPosition.y + heightBlockCount + 2)):
            for x in range(round(self.screenCenterPosition.x - widthBlockCount - 2),
                           round(self.screenCenterPosition.x + widthBlockCount + 2)):
                try:
                    tBlock = self.world.getBlock(x, y)
                except ChunkError:
                    continue
                if tBlock.blockType == BlockID.air:
                    continue
                self._renderBlock(tBlock)

    def _renderBlock(self, block: Block):
        blockTexture = pygame.transform.scale(Block.blockTextureMap[block.blockType],
                                              (BLOCK_SIZE * self.scale + 1,
                                               BLOCK_SIZE * self.scale + 1))  # 这是一个Surface对象
        blockPos = Vector2D(block.x, block.y)
        # 因为上面的计算都是以世界坐标（x轴以右为正方向，y轴以上为正方向）进行运算的，
        # 而屏幕是以左上角为原点、x以下为正方向、y以右为正方向，所以需要翻转y坐标。
        displayPos = (
                (BLOCK_SIZE * (blockPos - self.screenCenterPosition)) * self.scale + self.centerPosition).xMirror()
        if displayPos.x > WINDOW_WIDTH or displayPos.y > WINDOW_HEIGHT:
            return
        displayRect = blockTexture.get_rect()

        displayRect.topleft = displayPos.getTuple()

        self.window.blit(blockTexture, displayRect)

    def _updateFrame(self):
        # 更改标题
        # pygame.display.set_caption(f"{''.join(chr(random.randint(1, 32767)) for _ in range(16))}")

        # 更新相机位置
        self.screenCenterPosition += self.screenCenterVelocity * (20 / (self.fps + 1))
        self.screenCenterVelocity *= 0.9

        # 更新加载区块
        self.world.updateLoadedChunks()
        self.world.worldLoadCenterNew[0] = int(self.screenCenterPosition.x // CHUNK_SIZE)
        self.world.worldLoadCenterNew[1] = int(self.screenCenterPosition.y // CHUNK_SIZE)

        # 更新bgm
        i = bisect.bisect(WORLD_LAYER_EDGE, self.screenCenterPosition.y)
        if self.worldLayer != i:
            pygame.mixer.music.unload()
            try:
                pygame.mixer.music.load(WORLD_LAYER_BGM[i])
                pygame.mixer.music.play(-1)
            except pygame.error:
                pass

        # 加载背景
        if self.worldLayer != i:
            try:
                backg = pygame.transform.scale(pygame.image.load(WORLD_LAYER_BACKGROUND[i]).convert_alpha(),
                                               (WINDOW_WIDTH, WINDOW_HEIGHT))
                self.backGroundDict[i] = backg
            except FileNotFoundError:
                backg = pygame.transform.scale(pygame.image.load("./assets/textures/bgs/noBG.png").convert_alpha(),
                                               (WINDOW_WIDTH, WINDOW_HEIGHT))
                self.backGroundDict[i] = backg


# 运行前及类初始化
window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), flags=pygame.HWSURFACE)
Block.initBlockTextureMap()
pygame.display.set_icon(Block.blockTextureMap[2])

# 标题整活
pygame.display.set_caption(f"{''.join(chr(random.randint(0, 32767)) for _ in range(16))}")

if __name__ == "__main__":
    os.system(f"del {os.getcwd()}\\saves\\New_World /F /Q")
    Main(window, world=None).run()
