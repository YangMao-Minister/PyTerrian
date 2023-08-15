import math
import random
from collections import OrderedDict


class Vector2D:
    __slots__ = ("x", "y")

    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)

    def __neg__(self):
        return type(self)(-self.x, -self.y)

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

    def __add__(self, other):
        return type(self)(self.x + other.x, self.y + other.y)

    def __radd__(self, other):
        return other + self

    def __sub__(self, other):
        return type(self)(self.x - other.x, self.y - other.y)

    def __rsub__(self, other):
        return other - self

    def __abs__(self):
        """对向量取模"""
        return math.hypot(self.x, self.y)

    def __mul__(self, other):
        """向量数乘"""
        return type(self)(self.x * other, self.y * other)

    def __rmul__(self, other):
        return self * other

    def __truediv__(self, other):
        return self * (1 / other)

    def __matmul__(self, other):
        """向量点积，运算符为@"""
        return self.x * other.x + self.y + other.y

    def __repr__(self):
        return f'{type(self).__name__}({self.x},{self.y})'

    def __bool__(self):
        return self.x and self.y

    def __hash__(self):
        return hash((self.x, self.y))

    def normalize(self):
        """向量单位化"""
        if not self:
            return self
        return self * (1 / abs(self))

    def getCos(self, other):
        """获取向量之间的夹角余弦值"""
        return self @ other / (abs(self) * abs(other))

    def projective(self, other):
        """获取投影"""
        return self * other.normalize()

    def yMirror(self):
        """关于y轴镜像翻转"""
        return Vector2D(-self.x, self.y)

    def xMirror(self):
        """关于x轴镜像翻转"""
        return Vector2D(self.x, -self.y)

    def getTuple(self):
        """获取向量的元组形式"""
        return round(self.x, 3), round(self.y, 3)


class Noise:
    """实现噪声的类"""

    def __init__(self, seed, loud, frequency):
        self.seed = seed  # 噪声种子
        self.loud = loud  # 响度
        self.frequency = frequency  # 采样频率
        self._cache = OrderedDict()

    def __repr__(self):
        return f"{type(self).__name__}(seed={self.seed}, loud={self.loud}, frequency={self.frequency})"

    def getNoise(self, *args, **kwargs):
        pass


class ValueNoise1D(Noise):
    """实现一维值噪声的类"""

    @staticmethod
    def _fade(x: float):
        """平滑权重用函数"""
        return 6 * x ** 5 - 15 * x ** 4 + 10 * x ** 3

    def getNoise(self, position: float):
        lt = position - position % self.frequency
        lWeight = self._fade(1 - (position % self.frequency) / self.frequency)  # 左噪声权重
        if lt not in self._cache:
            random.seed(lt)
            lts = random.uniform(-self.loud, self.loud)  # 左噪音源
            self._cache[lt] = lts
        else:
            lts = self._cache[lt]

        rt = position - position % self.frequency + self.frequency
        rWeight = self._fade((position % self.frequency) / self.frequency)  # 右噪声权重
        if rt not in self._cache:
            random.seed(rt)
            rts = random.uniform(-self.loud, self.loud)  # 右噪音源
            self._cache[rt] = rts
        else:
            rts = self._cache[rt]

        # 更新缓存
        if len(self._cache) >= 32:
            self._cache.popitem()

        return lts * lWeight + rts * rWeight


class PerlinNoise2D(Noise):
    @staticmethod
    def _fade(x: float):
        """平滑权重用函数"""
        # return 6 * x ** 5 - 15 * x ** 4 + 10 * x ** 3
        # return 30 * x ** 4 - 60 * x ** 3 + 30 * x ** 2
        return x ** 2 * (3 - 2 * x)

        # return x **2
        # return x

    def getNoise(self, x, y):

        def getNS(v):
            if len(self._cache) >= 384:
                self._cache.popitem()
            if v not in self._cache:
                random.seed(v.getTuple())
                deg = random.uniform(0, 360)
                self._cache[v] = Vector2D(math.cos(deg), math.sin(deg))
            return self._cache[v]

        # 获取晶格四角坐标
        pos = Vector2D(x, y)

        ld = Vector2D(x // self.frequency, y // self.frequency)
        lu = ld + Vector2D(0, 1)
        rd = ld + Vector2D(1, 0)
        ru = ld + Vector2D(1, 1)

        ldv = (pos - ld * self.frequency) / self.frequency
        luv = (pos - lu * self.frequency) / self.frequency
        rdv = (pos - rd * self.frequency) / self.frequency
        ruv = (pos - ru * self.frequency) / self.frequency

        # 权重
        u = self._fade(ldv.x)
        v = self._fade(ldv.y)
        # print(ldv)
        # print(f"u:{u},v:{v}")

        # 计算噪音源
        ldn = getNS(ld * self.frequency)
        lun = getNS(lu * self.frequency)
        rdn = getNS(rd * self.frequency)
        run = getNS(ru * self.frequency)

        # 插值
        yuvn = (lun @ luv) * v + (ldn @ ldv) * (1 - v)
        ydvn = (run @ ruv) * v + (rdn @ rdv) * (1 - v)
        noiseValue = (ydvn * u + yuvn * (1 - u)) * self.loud

        return noiseValue


class NoiseSet:
    def __init__(self, *noises):
        self._noises = []
        if not noises:
            return
        if isinstance(noises[0], Noise):
            self.noiseType = type(noises[0])
        else:
            raise TypeError(f"There is at least one object in {noises} that is ont NOISE.")
        for n in noises:
            if not isinstance(n, self.noiseType):
                raise TypeError(f"The type of noise in {noises} is not unique.")
            else:
                self._noises.append(n)

    def __call__(self, *args, **kwargs):
        return sum(n.getNoise(*args, **kwargs) for n in self._noises)
