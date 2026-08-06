"""
Stardust Devourer_v1 (星尘吞噬者) —— 16 关闯关版
==========================================
霓虹风格吞噬成长游戏，16 关循序渐进、顺序解锁（通过一关才能玩下一关）。
吞噬小星体成长；比刺球大时可吞噬刺球（高双倍分）。
敌方刺球拥有生命值，光枪/光刃/黑洞等非吞噬攻击削减其生命，归零方毁灭。
12 种道具（含光枪/光刃武器自动攻击）。敌方有多种种族（尖刺/病毒/三球/双球）。
每关独特背景氛围，后期移动背景干扰；难度越高恐怖音效越强。
9 种特色皮肤（各具专属技能与霸气外观/拖尾）。金币商店、闯关积累。
支持单人（鼠标/手势/方向键）与双人模式。

操作（请在大写锁定下输入字母键）：
  单人：
    鼠标移动 / 手势(食指) / 方向键 —— 控制星球
    鼠标左键 / 伸掌 / V             —— 加速冲刺
    鼠标右键 / 握拳 / B             —— 触发皮肤专有技能
    H —— 循环切换 鼠标 → 手势 → 方向键（非手势模式关闭摄像头）
  双人：
    P1: WASD 移动 + V 加速 + B 皮肤技能
    P2: ↑↓←→ 移动 + M 加速 + ] 皮肤技能
  ← → —— 地图切换（仅可进入已解锁关卡）
  T   —— 切换单人 / 双人模式（地图界面）
  ?/F1—— 游戏说明（地图界面）
  空格/回车/点击 —— 开始 / 下一关
  P —— 暂停    Q —— 暂停/结束时返回地图
  F3—— 静音    R —— 重开当前关
  F11—— 全屏 / 窗口切换
  ESC —— 返回地图 / 暂停 / 退出
"""
import sys
import os
import math
import random
import json
import threading
import pygame
import numpy as np
import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# ================ 配置 ================
WIDTH, HEIGHT = 960, 720
FPS = 60

CAM_W, CAM_H = 320, 240
PREVIEW_W, PREVIEW_H = 240, 180
MODEL_PATH = "hand_landmarker.task"
SR = 44100

NEON_CYAN   = (0, 240, 255)
NEON_PINK   = (255, 70, 170)
NEON_PURPLE = (170, 90, 255)
NEON_GREEN  = (90, 255, 170)
NEON_YELLOW = (255, 215, 90)
NEON_ORANGE = (255, 140, 60)
NEON_RED    = (255, 60, 90)
WHITE       = (235, 240, 255)
DIM         = (130, 140, 175)
HAND_GREEN  = (0, 255, 0)

STAR_COLORS = [NEON_CYAN, NEON_GREEN, NEON_YELLOW, NEON_PINK, NEON_PURPLE, NEON_ORANGE]
STAGE_COLORS = [NEON_CYAN, NEON_GREEN, NEON_PURPLE, NEON_PINK,
                NEON_YELLOW, NEON_ORANGE, NEON_RED, (180, 255, 255)]

# ---- 道具 ----
POWERUP_COLORS = {
    "SHIELD": NEON_CYAN, "MAGNET": NEON_PURPLE, "TIME": NEON_YELLOW,
    "BOMB": NEON_ORANGE, "SHRINK": NEON_GREEN, "SCORE": NEON_PINK,
    "LIFE": NEON_GREEN, "PHANTOM": (180, 220, 255), "BLACKHOLE": NEON_PURPLE, "DOUBLE": NEON_ORANGE,
    "GUN": (255, 220, 80), "SWORD": (90, 255, 220),
}
POWERUP_LETTER = {
    "SHIELD": "S", "MAGNET": "M", "TIME": "T", "BOMB": "B", "SHRINK": "↓", "SCORE": "$",
    "LIFE": "+", "PHANTOM": "φ", "BLACKHOLE": "◎", "DOUBLE": "×", "GUN": "枪", "SWORD": "刀",
}
POWERUP_NAME = {
    "SHIELD": "护盾", "MAGNET": "磁吸", "TIME": "时停", "BOMB": "炸弹", "SHRINK": "缩小",
    "SCORE": "加分", "LIFE": "加命", "PHANTOM": "幻影", "BLACKHOLE": "黑洞", "DOUBLE": "双倍",
    "GUN": "光枪", "SWORD": "光刃",
}
POWERUP_DURATION = {"SHIELD": 6.0, "MAGNET": 7.0, "TIME": 5.0, "DOUBLE": 8.0,
                    "GUN": 9.0, "SWORD": 9.0, "PHANTOM": 4.5}

# ---- 皮肤系统 ----
# id: (名称, 价格, 主色, 能力描述)
# SKINS 元组格式：(名字, 价格, 颜色, 描述)
# 价格类型：int(金币) 或 tuple("diamond", int钻石数量)
# 商店排序：钻石皮肤排序在金币皮肤之后，按钻石升序
SKINS = {
    "tri":     ("三色灵球", 50,  (255, 70, 90),    "右键切红/黄/蓝三态：红吐炸弹、黄护盾、蓝加速"),
    "moon":    ("月华之球", 80,  (220, 230, 255),  "右键缩小30%更易躲避+分裂特效，再按还原"),
    "sun":     ("烈阳之球", 120, (255, 180, 60),   "左键发光排斥敌球+加速；右键全局光波击退"),
    "rainbow": ("虹光七彩", 150, (255, 120, 200),  "左键用对应色道具(时长30%)；右键切色耗能"),
    "frost":   ("霜冻冰魄", 300, (120, 200, 255),  "左键冰粒冻结；右键消耗能量冻结全场"),
    "thunder": ("雷霆战神", 500, (255, 240, 100),  "左键自动电球(伤害+击退)；右键周围雷电"),
    "void":    ("深渊黑洞", 700, (150, 70, 220),   "左键螺旋黑洞(3s)；右键6向黑洞清屏"),
    "inferno": ("炼狱炎魂", 200, (255, 90, 30),    "左键发射火球；右键变大灼烧环5s"),
    "chaos":   ("混沌魔神", 900, (200, 80, 255),   "左键钩吸血(消耗30)；右键六剑10s(消耗80)"),
    # ===== 第二页：钻石级霸气皮肤 =====
    # 天罚之眼 - 最基础钻石皮
    "judge":   ("天罚之眼", ("diamond", 5),  (255, 240, 200),
                "左键发射审判光弹穿透；右键展开天眼激光横扫全场"),
    # 真龙帝皇 - 雷电+火焰
    "dragon":  ("真龙帝皇", ("diamond", 10), (255, 180, 80),
                "左键帝皇火球·龙焰追踪；右键咆哮龙卷·全屏击飞敌人"),
    # 九幽魔君 - 毒雾+死亡
    "demon":   ("九幽魔君", ("diamond", 15), (120, 60, 200),
                "左键魔焰弹·毒雾腐蚀；右键九幽之门·召唤骷髅群吸血"),
    # 星海主宰 - 星辰+陨石
    "stellar": ("星海主宰", ("diamond", 25), (150, 220, 255),
                "左键星轨弹·持续切割；右键召唤陨石雨·大面积暴击"),
    # 六道轮回 - 轮回+时间
    "samsara": ("六道轮回", ("diamond", 40), (200, 160, 255),
                "左键·六首子球：消耗50%能量分裂6首子球追踪爆炸；右键·360度球弹：全围球弹自动追踪爆炸"),
    # 寂灭神皇 - 湮灭+创造
    "寂灭":     ("寂灭神皇", ("diamond", 60), (255, 200, 255),
                 "左键寂灭射线·瞬间湮灭小半径敌人；右键毁灭火莲·3秒后大范围爆炸(自身无影响)"),
    # 鸿蒙之始 - 混沌最高
    "primal":  ("鸿蒙之始", ("diamond", 90), (220, 255, 200),
                "左键鸿蒙一炁·吸万物于一点；右键两仪生灭·生成阴阳极双黑洞"),
    # 太上无极 - 太极+万物
    "taiji":   ("太上无极", ("diamond", 130),(240, 240, 220),
                "左键两仪剑·青红双剑自动连击；右键太极阵·反弹+减速12秒阵法"),
    # 大道涅槃 - 最高级不灭
    "nirvana": ("大道涅槃", ("diamond", 200),(255, 220, 120),
                "左键·灼烧凤凰：发射灼烧凤凰弹；右键·凤凰护体：凤凰环绕+2秒无敌(耗尽100%能量)"),
    # ===== 第三页：至高霸气混合支付皮肤（金币+钻石一起买）9 个 =====
    # 价格类型：("mix", 金币, 钻石)；全部四字中文称号（全部重命名为更霸气的称号，技能全面增强）
    # 1.
    "titan":   ("裂空雷将", ("mix", 500, 10),  (120, 180, 255),
                "左键·双雷锁敌：射出两枚追踪雷弹(低能耗)；右键·六雷震世：全屏六颗全局雷弹爆发+击退"),
    # 2.
    "qinglong":("沧溟潮君", ("mix", 600, 15),  (60, 220, 160),
                "左键·高压水柱：喷射长矩形单水柱(长按连射至边缘)；右键·沧海横流：六道潮卷环绕护体+全屏潮涌"),
    # 3.
    "baihu":   ("碎雪巡使", ("mix", 700, 20),  (240, 240, 240),
                "左键·月牙刃：发射弧形月牙刃；右键·圆环刃：360度逐渐扩大的圆环刃"),
    # 4.
    "zhuque":  ("燎原武侯", ("mix", 900, 30),  (255, 120, 60),
                "左键·燎原连珠：高射速穿透天火连射；右键·火龙卷风：向前发射龙卷风卷敌前进"),
    # 5.
    "xuanwu":  ("玄冰卫圣", ("mix", 1200, 40), (80, 140, 220),
                "左键·玄冰锥：召唤单支巨冰锥(单点爆炸+冻结)；右键·寒冰裂渊：开洞召唤冰锥雨(单点不穿透,密集高伤)"),
    # 6.
    "stargod": ("星陨领主", ("mix", 1500, 55), (255, 230, 120),
                "左键·星裂陨：大陨石砸落后爆裂成4颗小陨石；右键·八曜护世：8颗恒星自转,敌人来袭自动吸附攻击"),
    # 7.
    "chrono":  ("时空猎手", ("mix", 2000, 70), (180, 120, 255),
                "左键·裂空闪：向前快闪一大步；右键·巨爪裂空：发射巨大爪子击退敌人"),
    # 8.
    "buddha":  ("不灭尊者", ("mix", 2800, 90), (255, 200, 80),
                "左键·舍利子球：最多加6颗子球贪吃蛇叠加巡游,敌碰球爆炸连锁,碰我则球挡伤害减数量；右键·万佛降世：9座金佛环绕+超华丽净化光波"),
    # 9.
    "god":     ("极律虚皇", ("mix", 4000, 150),(255, 255, 200),
                "左键·虚皇圣律：蓝色光柱穿透+击退；右键·万法归一：消耗100%所有能量,全屏爆伤+时空停止+圣光护罩"),
    # ===== 第四页：终极至强皮肤（金币+钻石混合 · 3 个） =====
    # 1. 生命起源 - 创世之力
    "origin":  ("生命起源", ("mix", 5000, 200), (100, 255, 180),
                "左键·元素循环：发射12种元素球(火灼烧/冰冻结/电连锁/磁吸引/铁击退/暗吸血/黑洞吞噬/光穿透/毒减速/雷范围/风扩散/土眩晕)自动循环；右键·万物复苏：召唤12元素球环绕护体8秒+HP加到5"),
    # 2. 逆悖突进 - 时空悖论
    "paradox": ("逆悖突进", ("mix", 8000, 350), (200, 100, 255),
                "左键·悖论炮循环：发射4种圆柱炮(灭磁吸引/毒素减速/极冻冻结/毁灭爆炸)自动循环；右键·六光柱：展开6根光柱360°旋转击退6秒+HP加到5"),
    # 3. 终焉 - 最终毁灭
    "finality":("终焉", ("mix", 15000, 600), (255, 50, 50),
                "左键·终焉之枪：投掷必中灭世长枪(穿透全屏+即死非Boss+Boss500伤害)+镰刀360°旋转击退爆炸；右键·无敌破坏死光：3秒大范围血红黑激光+无敌+HP加到5"),
}
# 全皮肤统一顺序：第一页金币9 → 第二页钻石9 → 第三页混合9 → 第四页终极3
# （供暂停换皮面板、商店排序、帮助页皮肤列表等共享使用）
ALL_SKIN_ORDER = (
    # 第一页 金币9 （按价格升序）
    "tri", "moon", "sun", "rainbow", "inferno", "frost", "thunder", "void", "chaos",
    # 第二页 钻石9 （按钻石数升序）
    "judge", "dragon", "demon", "stellar", "samsara", "寂灭", "primal", "taiji", "nirvana",
    # 第三页 混合9 （按金币+钻石总价值升序）
    "titan", "qinglong", "baihu", "zhuque", "xuanwu", "stargod", "chrono", "buddha", "god",
    # 第四页 终极3 （最强皮肤）
    "origin", "paradox", "finality",
)
RAINBOW_COLORS = [
    (255, 70, 70),    # 红 -> 护盾
    (255, 140, 50),   # 橙 -> 磁吸
    (255, 220, 80),   # 黄 -> 时停
    (90, 255, 130),   # 绿 -> 幻影
    (90, 220, 255),   # 青 -> 加分
    (90, 130, 255),   # 蓝 -> 缩小
    (180, 90, 255),   # 紫 -> 黑洞
]
RAINBOW_EFFECTS = ["SHIELD", "MAGNET", "TIME", "PHANTOM", "SCORE", "SHRINK", "BLACKHOLE"]
RAINBOW_NAMES = ["红·护盾", "橙·磁吸", "黄·时停", "绿·幻影", "青·加分", "蓝·缩小", "紫·黑洞"]
SAVE_PATH = "stardust_save.json"

# ---- 16 关数据 ----
# speed: 星体速度倍率; danger: 刺球概率; pu: 道具刷新倍率; goal: 通关吞噬数
# theme: 背景氛围主题; node: 地图节点颜色; horror: 恐怖氛围强度(0~1)
# chaos: 星体随机变向概率(0~1); interfere: 后期移动背景干扰强度(0~1)
LEVELS = [
    {"name": "起源星云", "bg": (8, 8, 24),     "node": (120, 160, 255), "theme": "nebula",
     "speed": 0.85, "danger": 0.15, "pu": 1.2, "goal": 15, "horror": 0.0,  "chaos": 0.0,    "interfere": 0.0,
     "desc": "入门关，熟悉操作"},
    {"name": "冰晶带",   "bg": (10, 18, 36),   "node": (150, 220, 255), "theme": "ice",
     "speed": 0.9,  "danger": 0.16, "pu": 1.2, "goal": 22, "horror": 0.0,  "chaos": 0.0,    "interfere": 0.0,
     "desc": "星体较慢，道具略多"},
    {"name": "翡翠林",   "bg": (8, 24, 18),    "node": (90, 255, 170),  "theme": "sparkle",
     "speed": 0.95, "danger": 0.18, "pu": 1.1, "goal": 30, "horror": 0.0,  "chaos": 0.0,    "interfere": 0.0,
     "desc": "翠绿星海，宁静生长"},
    {"name": "火焰星云", "bg": (30, 12, 16),   "node": (255, 130, 60),  "theme": "fire",
     "speed": 1.05, "danger": 0.22, "pu": 1.0, "goal": 40, "horror": 0.2,  "chaos": 0.005,  "interfere": 0.0,
     "desc": "星体更快，刺球增多"},
    {"name": "风暴域",   "bg": (14, 16, 26),   "node": (170, 190, 230), "theme": "storm",
     "speed": 1.1,  "danger": 0.24, "pu": 1.0, "goal": 52, "horror": 0.25, "chaos": 0.008,  "interfere": 0.0,
     "desc": "风暴裹挟，方向难测"},
    {"name": "黑暗深渊", "bg": (3, 3, 10),     "node": (120, 90, 160),  "theme": "dark",
     "speed": 1.1,  "danger": 0.24, "pu": 0.9, "goal": 65, "horror": 0.55, "chaos": 0.006,  "interfere": 0.0,
     "desc": "视野受限，暗角笼罩"},
    {"name": "混沌带",   "bg": (22, 8, 30),    "node": (210, 100, 230), "theme": "chaos",
     "speed": 1.2,  "danger": 0.28, "pu": 1.0, "goal": 80, "horror": 0.35, "chaos": 0.020,  "interfere": 0.0,
     "desc": "星体乱飞，难以预判"},
    {"name": "道具天堂", "bg": (8, 22, 26),    "node": (90, 255, 170),  "theme": "sparkle",
     "speed": 1.15, "danger": 0.24, "pu": 2.4, "goal": 95, "horror": 0.0,  "chaos": 0.005,  "interfere": 0.0,
     "desc": "道具刷新极快"},
    {"name": "水晶洞",   "bg": (10, 20, 30),   "node": (140, 210, 240), "theme": "crystal",
     "speed": 1.25, "danger": 0.30, "pu": 1.0, "goal": 115, "horror": 0.2,  "chaos": 0.010,  "interfere": 0.0,
     "desc": "晶莹剔透，暗藏杀机"},
    {"name": "熔岩海",   "bg": (28, 8, 8),     "node": (255, 110, 40),  "theme": "magma",
     "speed": 1.3,  "danger": 0.34, "pu": 1.0, "goal": 140, "horror": 0.4,  "chaos": 0.012,  "interfere": 0.0,
     "desc": "熔岩翻涌，灼热逼人"},
    {"name": "极光带",   "bg": (6, 18, 26),    "node": (120, 255, 200), "theme": "aurora",
     "speed": 1.3,  "danger": 0.32, "pu": 1.1, "goal": 170, "horror": 0.2,  "chaos": 0.015,  "interfere": 0.0,
     "desc": "绚丽极光掩杀机"},
    {"name": "刺球地狱", "bg": (32, 6, 10),    "node": (255, 70, 70),   "theme": "hell",
     "speed": 1.35, "danger": 0.50, "pu": 1.1, "goal": 200, "horror": 0.75, "chaos": 0.018,  "interfere": 0.2,
     "desc": "几乎全是刺球"},
    {"name": "虚空裂隙", "bg": (26, 4, 30),    "node": (180, 100, 255), "theme": "void",
     "speed": 1.45, "danger": 0.40, "pu": 1.0, "goal": 240, "horror": 0.6,  "chaos": 0.055,  "interfere": 0.4,
     "desc": "虚空吞噬，光影扭曲"},
    {"name": "时空乱流", "bg": (18, 10, 30),   "node": (200, 140, 255), "theme": "vortex",
     "speed": 1.5,  "danger": 0.45, "pu": 1.0, "goal": 285, "horror": 0.7,  "chaos": 0.085,  "interfere": 0.6,
     "desc": "时空错乱，背景狂舞"},
    {"name": "终焉废墟", "bg": (24, 14, 12),   "node": (255, 170, 90),  "theme": "ruin",
     "speed": 1.6,  "danger": 0.50, "pu": 1.1, "goal": 340, "horror": 0.85, "chaos": 0.11,   "interfere": 0.8,
     "desc": "末日废墟，群敌环伺"},
    {"name": "奇点",     "bg": (20, 4, 28),    "node": (230, 120, 255), "theme": "singularity",
     "speed": 1.8,  "danger": 0.55, "pu": 1.2, "goal": 400, "horror": 1.0,  "chaos": 0.16,   "interfere": 1.0,
     "desc": "终极奇点，万物崩塌"},
]


# ---- 16 关副本（更难，通关奖励钻石） ----
# difficulty: 额外难度倍率（星体数/危险度）
# diamond_reward: 通关获得的钻石
# snake_ratio: 蛇形敌人占比（越多蛇越长）
DUNGEON_LEVELS = [
    {"name": "蚀星·始源",   "bg": (20, 8, 20),      "node": (255, 90, 200),  "theme": "chaos",
     "speed": 1.25, "danger": 0.50, "pu": 0.8, "goal": 60,  "horror": 0.6, "chaos": 0.04, "interfere": 0.3,
     "desc": "试炼第一重，小钻石奖赏", "difficulty": 1.15, "diamond_reward": 1, "snake_ratio": 0.10},
    {"name": "寒渊·冰锁",   "bg": (8, 20, 48),      "node": (140, 200, 255),  "theme": "ice",
     "speed": 1.30, "danger": 0.52, "pu": 0.8, "goal": 80,  "horror": 0.6, "chaos": 0.05, "interfere": 0.3,
     "desc": "冰锁长蛇盘踞深渊", "difficulty": 1.25, "diamond_reward": 1, "snake_ratio": 0.15},
    {"name": "翠灭·藤林",   "bg": (8, 38, 24),      "node": (90, 255, 170),   "theme": "sparkle",
     "speed": 1.35, "danger": 0.54, "pu": 0.75, "goal": 100, "horror": 0.7, "chaos": 0.06, "interfere": 0.4,
     "desc": "翠林吞噬者，长蛇无数", "difficulty": 1.35, "diamond_reward": 2, "snake_ratio": 0.22},
    {"name": "火噬·狱焰",   "bg": (40, 12, 16),     "node": (255, 110, 50),   "theme": "fire",
     "speed": 1.45, "danger": 0.56, "pu": 0.75, "goal": 125, "horror": 0.7, "chaos": 0.07, "interfere": 0.4,
     "desc": "狱焰焚烧，刺球如蝗", "difficulty": 1.45, "diamond_reward": 2, "snake_ratio": 0.25},
    {"name": "怒涡·风暴",   "bg": (20, 26, 48),     "node": (170, 200, 255),  "theme": "storm",
     "speed": 1.50, "danger": 0.58, "pu": 0.7,  "goal": 150, "horror": 0.8, "chaos": 0.09, "interfere": 0.5,
     "desc": "风暴乱流，方向全乱", "difficulty": 1.55, "diamond_reward": 3, "snake_ratio": 0.30},
    {"name": "无明·黑洞",   "bg": (4, 2, 16),       "node": (120, 80, 180),   "theme": "dark",
     "speed": 1.55, "danger": 0.60, "pu": 0.7,  "goal": 175, "horror": 0.9, "chaos": 0.10, "interfere": 0.5,
     "desc": "视野几近全黑，危机四伏", "difficulty": 1.65, "diamond_reward": 3, "snake_ratio": 0.32},
    {"name": "乱序·混沌",   "bg": (38, 12, 50),     "node": (210, 100, 240),  "theme": "chaos",
     "speed": 1.60, "danger": 0.62, "pu": 0.65, "goal": 200, "horror": 0.8, "chaos": 0.15, "interfere": 0.6,
     "desc": "宇宙秩序彻底崩解", "difficulty": 1.75, "diamond_reward": 4, "snake_ratio": 0.38},
    {"name": "宝藏·幻境",   "bg": (10, 34, 40),     "node": (90, 255, 180),   "theme": "crystal",
     "speed": 1.60, "danger": 0.60, "pu": 1.6,  "goal": 225, "horror": 0.5, "chaos": 0.12, "interfere": 0.5,
     "desc": "幻境宝藏，道具与危机共存", "difficulty": 1.75, "diamond_reward": 4, "snake_ratio": 0.30},
    {"name": "碎晶·矿脉",   "bg": (12, 30, 54),     "node": (140, 210, 250),  "theme": "crystal",
     "speed": 1.65, "danger": 0.65, "pu": 0.65, "goal": 250, "horror": 0.85, "chaos": 0.14, "interfere": 0.7,
     "desc": "碎晶之间，长蛇穿梭", "difficulty": 1.90, "diamond_reward": 5, "snake_ratio": 0.40},
    {"name": "焦海·熔岩",   "bg": (44, 10, 8),      "node": (255, 100, 40),   "theme": "magma",
     "speed": 1.70, "danger": 0.68, "pu": 0.65, "goal": 280, "horror": 0.9,  "chaos": 0.15, "interfere": 0.7,
     "desc": "焦海熔岩，万物成灰", "difficulty": 2.00, "diamond_reward": 5, "snake_ratio": 0.42},
    {"name": "流光·极地",   "bg": (8, 28, 44),      "node": (120, 255, 200),  "theme": "aurora",
     "speed": 1.75, "danger": 0.70, "pu": 0.6,  "goal": 315, "horror": 0.85, "chaos": 0.18, "interfere": 0.8,
     "desc": "极光之下，杀机翻涌", "difficulty": 2.10, "diamond_reward": 6, "snake_ratio": 0.45},
    {"name": "刺冢·葬场",   "bg": (50, 8, 10),      "node": (255, 60, 60),    "theme": "hell",
     "speed": 1.80, "danger": 0.82, "pu": 0.6,  "goal": 350, "horror": 1.0,  "chaos": 0.20, "interfere": 0.85,
     "desc": "刺球坟场，触之即亡", "difficulty": 2.25, "diamond_reward": 7, "snake_ratio": 0.48},
    {"name": "虚渊·吞噬",   "bg": (44, 6, 54),      "node": (180, 100, 255),  "theme": "void",
     "speed": 1.85, "danger": 0.74, "pu": 0.55, "goal": 390, "horror": 1.0,  "chaos": 0.28, "interfere": 0.9,
     "desc": "虚空吞星，光影尽碎", "difficulty": 2.40, "diamond_reward": 8, "snake_ratio": 0.50},
    {"name": "裂时·乱序",   "bg": (32, 16, 50),     "node": (200, 140, 255),  "theme": "vortex",
     "speed": 1.90, "danger": 0.76, "pu": 0.55, "goal": 435, "horror": 1.0,  "chaos": 0.34, "interfere": 0.95,
     "desc": "时间碎裂，空间崩坏", "difficulty": 2.55, "diamond_reward": 9, "snake_ratio": 0.55},
    {"name": "终殁·废墟",   "bg": (40, 20, 18),     "node": (255, 160, 90),   "theme": "ruin",
     "speed": 1.95, "danger": 0.80, "pu": 0.55, "goal": 480, "horror": 1.0,  "chaos": 0.40, "interfere": 1.0,
     "desc": "废墟尽头，终极守关", "difficulty": 2.70, "diamond_reward": 10, "snake_ratio": 0.58},
    {"name": "禁域·真源",   "bg": (40, 8, 60),      "node": (255, 130, 255),  "theme": "singularity",
     "speed": 2.05, "danger": 0.88, "pu": 0.55, "goal": 540, "horror": 1.0,  "chaos": 0.50, "interfere": 1.0,
     "desc": "宇宙本源，禁域之门", "difficulty": 3.0, "diamond_reward": 15, "snake_ratio": 0.65},
]


# ================ 工具 ================
def clamp(v, lo, hi):
    return lo if v < lo else hi if v > hi else v


def lerp(a, b, t):
    return a + (b - a) * t


_font_cache = {}
_FONT_REGULAR = (r"C:\Windows\Fonts\msyh.ttc", r"C:\Windows\Fonts\msyh.tt",
                 r"C:\Windows\Fonts\simhei.ttf", r"C:\Windows\Fonts\simsun.ttc")
_FONT_BOLD = (r"C:\Windows\Fonts\msyhbd.ttc", r"C:\Windows\Fonts\msyhbd.tt",
              r"C:\Windows\Fonts\simhei.ttf")


def _load_font_file(candidates, size):
    for p in candidates:
        if os.path.isfile(p):
            try:
                return pygame.font.Font(p, size)
            except Exception:
                continue
    return None


def get_font(size, bold=False):
    key = (size, bold)
    if key not in _font_cache:
        f = _load_font_file(_FONT_BOLD if bold else _FONT_REGULAR, size)
        if f is None:
            f = _load_font_file(_FONT_REGULAR, size)
        if f is None:
            # 硬编码字体路径都不可用时，使用 SysFont 按名字查找系统中文黑体/雅黑，保证中文不呈 □
            try:
                # 多候选逗号分隔，按系统字体匹配优先级：微软雅黑 > 黑体 > 宋体 > Arial
                f = pygame.font.SysFont("microsoftyahei,simhei,simsun,arial",
                                        size, bold=bold)
            except Exception:
                try:
                    f = pygame.font.SysFont("microsoft yahei", size, bold=bold)
                except Exception:
                    try:
                        f = pygame.font.SysFont("simhei", size, bold=bold)
                    except Exception:
                        f = pygame.font.Font(None, size)
        # set_bold 对已有的中文字体文件也能追加加粗效果；若 f 已是加粗字体不影响
        try:
            f.set_bold(bold)
        except Exception:
            pass
        _font_cache[key] = f
    return _font_cache[key]


def make_glow(radius, color, alpha=190):
    radius = max(1, int(radius))
    size = radius * 2
    y, x = np.ogrid[:size, :size]
    dist = np.sqrt((x - radius + 0.5) ** 2 + (y - radius + 0.5) ** 2)
    t = np.clip(1.0 - dist / radius, 0.0, 1.0)
    inten = t ** 2.4
    k = alpha / 255.0
    rgba = np.zeros((size, size, 4), dtype=np.uint8)
    rgba[..., 0] = (color[0] * inten * k).astype(np.uint8)
    rgba[..., 1] = (color[1] * inten * k).astype(np.uint8)
    rgba[..., 2] = (color[2] * inten * k).astype(np.uint8)
    rgba[..., 3] = (inten * 255).astype(np.uint8)
    surf = pygame.image.frombuffer(rgba.tobytes(), (size, size), 'RGBA')
    return surf.convert_alpha()


_glow_cache = {}
def get_glow(radius, color, alpha=190):
    qr = max(2, round(radius / 2) * 2)
    key = (qr, color, alpha)
    if key not in _glow_cache:
        _glow_cache[key] = make_glow(qr, color, alpha)
    return _glow_cache[key]


def draw_entity(surf, x, y, radius, color, glow_alpha=150):
    px, py = int(x), int(y)
    r = max(1, int(radius))
    glow = get_glow(radius * 1.9, color, alpha=glow_alpha)
    surf.blit(glow, glow.get_rect(center=(px, py)), special_flags=pygame.BLEND_RGB_ADD)
    pygame.draw.circle(surf, color, (px, py), r)
    hl = (min(255, color[0] + 90), min(255, color[1] + 90), min(255, color[2] + 90))
    pygame.draw.circle(surf, hl,
                       (px - int(r * 0.32), py - int(r * 0.32)),
                       max(1, int(r * 0.34)))


# ================ 粒子 ================
class Particle:
    __slots__ = ("x", "y", "vx", "vy", "life", "max_life", "color", "size")

    def __init__(self, x, y, vx, vy, life, color, size):
        self.x = x; self.y = y
        self.vx = vx; self.vy = vy
        self.life = life; self.max_life = life
        self.color = color; self.size = size

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        damp = math.pow(0.12, dt)
        self.vx *= damp
        self.vy *= damp
        self.life -= dt

    @property
    def alive(self):
        return self.life > 0

    def draw(self, surf, ox, oy):
        t = clamp(self.life / self.max_life, 0, 1)
        r = max(1.0, self.size * (0.4 + 0.6 * t))
        g = get_glow(r * 3.2, self.color, alpha=int(220 * t))
        rect = g.get_rect(center=(int(self.x + ox), int(self.y + oy)))
        surf.blit(g, rect, special_flags=pygame.BLEND_RGB_ADD)


# ================ 星体 ================
class Star:
    __slots__ = ("x", "y", "vx", "vy", "r", "color", "danger", "spin", "phase", "_dead",
                 "tier", "kind", "hp", "max_hp", "hit_flash", "sub_phase", "blade_cd",
                 "segments", "worm_target", "worm_orbit",
                 "snake_chain", "snake_head_flag", "snake_prev",
                 "frozen_timer",  # 霜冻：被冰冻结的剩余时间（>0 时减速+冻结视觉）
                 "chase_player",  # 0/1/2：不追踪/轻度/强追踪
                 "chase_id",      # 强追踪锁定的玩家索引
                 "horror_split_count",  # 死亡分裂次数（牛魔/幽灵/蜘蛛/恐怖种）
                 # 六道轮回：被轮回印标记（死亡后返还标记者能量）
                 "_samsara_mark", "_samsara_owner",
                 # 寂灭神皇：命中过玩家的寂灭射线（防止重复扣血等防御标记，留空即可）
                 # 太上无极：太极阵反弹命中的敌人标记，避免一帧多次反弹
                 "_taiji_hit_phase",
                 # 大道涅槃：涅槃光环命中敌人的冷却相位
                 "_nirvana_hit_cd",
                 # 玄冰玄武：玄冰命中冻结标记
                 "_frost_hit_cd",
                 # 预留若干扩展位，避免后续皮肤新增属性又 __slots__ AttributeError
                 "_ext1", "_ext2", "_ext3",
                 # Q3：BOSS模式/无尽Boss标记
                 "is_boss", "boss_level", "_endless_boss")

    def __init__(self, x, y, vx, vy, r, color, danger, tier=0, kind="spike"):
        self.x = x; self.y = y
        self.vx = vx; self.vy = vy
        self.r = r
        self.color = color
        self.danger = danger
        self.tier = tier  # 敌方强度等级 0~3（仅 danger 时有意义）
        # t7：新增 6 个种族：spider/centipede/ghost/turtle/oxdemon/fangshe（毒升级版蛇）
        self.kind = kind  # 敌方种族："spike"/"virus"/"tri"/"dual"/"worm"/"snake"/"spider"/"centipede"/"ghost"/"turtle"/"oxdemon"/"fangshe"
        self.spin = random.uniform(-2.0, 2.0)
        self.phase = random.uniform(0, math.tau)
        self._dead = False
        # 生命值：非吞噬攻击削减，归零才消失
        # c10/t7：整体敌人加强 × 1.25；复合种族再额外加强
        if danger:
            base = [2, 3, 4, 6][tier]
            kind_mul = {"spike": 1, "virus": 2.4, "tri": 3.6, "dual": 2.4,
                        "worm": 4.8, "snake": 2.4, "horror": 3.2,
                        "spider": 2.0, "centipede": 4.2, "ghost": 3.0,
                        "turtle": 5.2, "oxdemon": 4.0, "fangshe": 2.8}.get(kind, 1)
            global_mul = 1.25
            self.max_hp = int(round(base * kind_mul * global_mul))
            self.hp = self.max_hp
        else:
            self.max_hp = 1
            self.hp = 1
        self.hit_flash = 0.0   # 受击闪白
        self.frozen_timer = 0.0  # 霜冻冻结剩余秒数
        self.sub_phase = random.uniform(0, math.tau)  # 多球体旋转相位
        self.blade_cd = 0.0   # 光刃命中冷却（避免每帧多次扣血）
        # 虫子类/蜈蚣类专属：长条身段 + 包围行为
        self.segments = []  # [(x,y), ...] 虫身节点（worm/centipede 用）
        self.worm_target = None  # 当前包围目标玩家
        self.worm_orbit = 0.0   # 包围角度
        if kind == "worm":
            # 初始化 8 段虫身
            for i in range(8):
                self.segments.append((x - (i + 1) * r * 1.4, y))
        if kind == "centipede":
            # 蜈蚣 12 段更长更恐怖
            for i in range(12):
                self.segments.append((x - (i + 1) * r * 1.1, y))
        # 长蛇多球节/毒蛇专属：snake_chain = [头, 节1, 节2, ...]，所有节共享同一个链
        self.snake_chain = None   # list[Star]，蛇头持有这个链；其他节引用同一条链
        self.snake_head_flag = False  # 是否为蛇头
        self.snake_prev = None    # 前一节（用于牵引跟随 & 断节拆链）
        # c7/c10/t7：主动追踪玩家
        # chase_player: 0=不追踪，1=轻度，2=强追踪（恐怖种/牛魔/幽灵/蜘蛛升级）
        chase_map = {"horror": 2, "oxdemon": 2, "ghost": 2,
                     "spider": 1, "centipede": 1, "fangshe": 1, "turtle": 0}
        self.chase_player = chase_map.get(kind, 0)
        self.chase_id = None      # 强追踪时锁定的玩家索引 0/1
        split_map = {"horror": 2, "oxdemon": 2, "spider": 1, "ghost": 0}
        self.horror_split_count = split_map.get(kind, 0)
        # Q3：BOSS/无尽Boss标记默认值（避免读取未初始化属性）
        self.is_boss = False
        self.boss_level = 0
        self._endless_boss = False

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.phase += self.spin * dt
        self.sub_phase += dt * 2.4
        if self.hit_flash > 0:
            self.hit_flash -= dt
        if self.blade_cd > 0:
            self.blade_cd -= dt
        if self.frozen_timer > 0:
            self.frozen_timer -= dt
            # 冻结期：速度被极强衰减（每帧乘 0.1^dt ≈ -80%/秒）
            k = math.pow(0.08, dt)
            self.vx *= k
            self.vy *= k

    @property
    def offscreen(self):
        m = self.r + 80
        return (self.x < -m or self.x > WIDTH + m or
                self.y < -m or self.y > HEIGHT + m)


# ================ 道具 ================
class PowerUp:
    __slots__ = ("x", "y", "vx", "vy", "r", "ptype", "phase", "life", "max_life", "_dead")

    def __init__(self, x, y, vx, vy, ptype):
        self.x = x; self.y = y
        self.vx = vx; self.vy = vy
        self.r = 15
        self.ptype = ptype
        self.phase = 0.0
        self.life = 14.0
        self.max_life = 14.0
        self._dead = False

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.phase += dt * 3.5
        self.life -= dt

    @property
    def offscreen(self):
        m = 60
        return (self.x < -m or self.x > WIDTH + m or
                self.y < -m or self.y > HEIGHT + m)


# ================ 子弹（光枪） ================
class Bullet:
    __slots__ = ("x", "y", "vx", "vy", "life", "_dead", "owner")

    def __init__(self, x, y, vx, vy, owner=None):
        self.x = x; self.y = y
        self.vx = vx; self.vy = vy
        self.life = 1.6
        self._dead = False
        self.owner = owner

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.life -= dt
        if self.life <= 0:
            self._dead = True


# ================ 玩家 ================
class Player:
    def __init__(self, x=WIDTH / 2, y=HEIGHT / 2, color=NEON_CYAN, pid=1):
        self.x = x
        self.y = y
        self.prev_x = self.x
        self.prev_y = self.y
        self.r = 18.0
        self.energy = 100.0
        self.invuln = 0.0
        self.flash = 0.0
        self.shield_timer = 0.0
        self.magnet_timer = 0.0
        self.phantom_timer = 0.0   # 幻影：穿透无敌
        self.trail_timer = 0.0
        self.color = color
        self.pid = pid
        self.alive = True
        self.spawn_flash = 0.0
        self.weapon_timer = 0.0
        self.weapon_type = None  # "GUN" / "SWORD"
        self.weapon_cd = 0.0
        self.weapon_ang = 0.0    # 当前武器朝向（用于绘制）
        self.dash_glow = 0.0     # 加速发光渐变（0~1）
        self._is_sub = False     # 是否为分裂子细胞
        # 皮肤状态
        self.tri_mode = 0        # 三色灵球：0=红 1=黄 2=蓝
        self.moon_shrunk = False # 月华：是否处于缩小态
        self._energy_depleted = False  # 能量是否刚耗尽（用于减速回复）
        self._tri_boost_timer = 0.0  # 三色蓝球加速剩余时间
        self._inferno_ring_timer = 0.0  # 炼狱灼烧环剩余时间
        self._inferno_base_r = 0.0      # 炼狱环开启前的本体半径（还原用）
        self._sun_glow_timer = 0.0      # 烈阳左键发光排斥剩余时间
        # 混沌皮肤：钩子+六剑
        self._chaos_hook = None         # {"x","y","vx","vy","target","drain_timer"}
        self._chaos_sword_timer = 0.0   # 六剑剩余时间
        self._chaos_hp = 1              # 混沌生命值（1~5格）
        # 深渊黑洞：螺旋黑洞
        # 雷霆：周围雷电
        # 霜冻：无需新加字段
        # ===== 钻石皮肤专属状态 =====
        self._samsara_timer = 0.0     # 六道轮回：回溯期剩余时间
        self._samsara_snap = None     # 六道轮回：状态快照
        self._taiji_timer = 0.0       # 太上无极：太极阵剩余时间
        self._nirvana_timer = 0.0     # 大道涅槃：不灭金身剩余时间
        self._nirvana_revive = False  # 大道涅槃：本关是否可复活一次
        self._judge_bullets_cd = 0.0  # 天罚之眼：左键审判弹冷却
        self._dragon_cd = 0.0         # 真龙帝皇：左键龙焰追踪弹冷却
        self._demon_cd = 0.0          # 九幽魔君：左键魔焰毒雾弹冷却
        self._stellar_cd = 0.0        # 星海主宰：左键星轨切割弹冷却
        self._寂灭_cd = 0.0          # 寂灭神皇：左键寂灭射线冷却
        self._primal_cd = 0.0         # 鸿蒙之始：左键鸿蒙一炁吸附冷却
        self._taiji_cd = 0.0          # 太上无极：左键两仪连击冷却
        self._nirvana_click_cd = 0.0  # 大道涅槃：左键涅槃火冷却
        # ===== 第三页 至高霸气皮肤专属状态 =====
        self._titan_domain = 0.0        # 雷神泰坦：雷霆领域剩余时间
        self._titan_next_lightning = 0.0  # 泰坦：下一次雷击的累计
        self._titan_cd = 0.0            # 泰坦左键冷却
        self._qinglong_timer = 0.0      # 青龙帝君：6龙护体剩余
        self._qinglong_cd = 0.0         # 青龙左键冷却
        self._zhuque_revive = False     # 朱雀圣皇：本次是否可复活一次
        self._zhuque_timer = 0.0        # 朱雀涅槃印记剩余时间
        self._zhuque_cd = 0.0           # 朱雀左键天火冷却
        self._xuanwu_timer = 0.0        # 玄武：帝尊守护剩余时间
        self._xuanwu_cd = 0.0           # 玄武左键玄冰锥形冷却
        self._stargod_timer = 0.0       # 星辰古神：8恒星护体剩余
        self._stargod_phase = [0.0]*8   # 恒星轨道相位
        self._stargod_cd = 0.0          # 星辰古神左键陨石冷却
        self._chrono_cd = 0.0           # 时空帝主左键时之刃冷却
        self._buddha_timer = 0.0        # 万佛之祖：9佛环绕剩余
        self._buddha_cd = 0.0           # 万佛左键佛手冷却
        self._god_timer = 0.0           # 至高神皇：15秒全开状态剩余
        self._god_cd = 0.0              # 神皇左键神罚9道光柱冷却
        # ===== 终极皮肤状态 =====
        # 生命起源：12元素球循环
        self._origin_elem_idx = 0       # 当前元素索引(0-11)
        self._origin_cd = 0.0           # 左键冷却
        self._origin_orbs = []          # 右键召唤的12元素环绕球
        self._origin_orb_timer = 0.0    # 环绕球剩余时间
        # 逆悖突进：4种圆柱炮循环
        self._paradox_cannon_idx = 0    # 当前炮类型(0-3)
        self._paradox_cd = 0.0          # 左键冷却
        self._paradox_pillars = []      # 右键6根光柱
        self._paradox_pillar_timer = 0.0
        # 终焉
        self._finality_cd = 0.0         # 左键冷却
        self._finality_scythe_timer = 0.0  # 镰刀旋转剩余
        self._finality_laser_timer = 0.0   # 破坏死光剩余
        # 动态弹道：天罚审判弹（持续伤害穿透）
        if not hasattr(type(self), "_dummy"):
            pass

    def _clamp(self):
        self.x = clamp(self.x, self.r, WIDTH - self.r)
        self.y = clamp(self.y, self.r, HEIGHT - self.r)

    def move_to(self, tx, ty, dt, dashing):
        god_bonus = 2.0 if getattr(self, "_god_timer", 0) > 0 else 1.0
        follow = (13.0 if dashing else 6.0) * god_bonus
        t = 1.0 - math.exp(-follow * dt)
        self.x = lerp(self.x, tx, t)
        self.y = lerp(self.y, ty, t)
        self._clamp()

    def move_by(self, vx, vy, dt, dashing):
        god_bonus = 2.0 if getattr(self, "_god_timer", 0) > 0 else 1.0
        mul = (2.2 if dashing else 1.0) * god_bonus
        self.x += vx * dt * mul
        self.y += vy * dt * mul
        self._clamp()

    def update_timers(self, dt, dashing):
        if dashing:
            self.energy = max(0.0, self.energy - 55 * dt)
            self.dash_glow = min(1.0, self.dash_glow + dt * 3.5)
            if self.energy <= 0:
                self._energy_depleted = True
        else:
            # 能量耗尽后回复速度减慢 50%
            rate = 16.0 if self._energy_depleted else 32.0
            self.energy = min(100.0, self.energy + rate * dt)
            if self.energy >= 100.0:
                self._energy_depleted = False
            self.dash_glow = max(0.0, self.dash_glow - dt * 2.5)
        if self.invuln > 0:
            self.invuln -= dt
        if self.flash > 0:
            self.flash -= dt
        if self.shield_timer > 0:
            self.shield_timer -= dt
        if self.magnet_timer > 0:
            self.magnet_timer -= dt
        if self.phantom_timer > 0:
            self.phantom_timer -= dt
        if self.spawn_flash > 0:
            self.spawn_flash -= dt
        if self.weapon_timer > 0:
            self.weapon_timer -= dt
            if self.weapon_timer <= 0:
                self.weapon_type = None
        if self.weapon_cd > 0:
            self.weapon_cd -= dt
        if self._tri_boost_timer > 0:
            self._tri_boost_timer -= dt
        if self._sun_glow_timer > 0:
            self._sun_glow_timer -= dt
        if self._inferno_ring_timer > 0:
            self._inferno_ring_timer -= dt
            if self._inferno_ring_timer <= 0:
                # 还原本体大小
                if self._inferno_base_r > 0:
                    self.r = self._inferno_base_r
                    self._inferno_base_r = 0.0
        if self._samsara_timer > 0:
            self._samsara_timer -= dt
        if self._taiji_timer > 0:
            self._taiji_timer -= dt
        if self._nirvana_timer > 0:
            self._nirvana_timer -= dt
        if self._judge_bullets_cd > 0:
            self._judge_bullets_cd -= dt
        if self._dragon_cd > 0:
            self._dragon_cd -= dt
        if self._demon_cd > 0:
            self._demon_cd -= dt
        if self._stellar_cd > 0:
            self._stellar_cd -= dt
        if self._寂灭_cd > 0:
            self._寂灭_cd -= dt
        if self._primal_cd > 0:
            self._primal_cd -= dt
        if self._taiji_cd > 0:
            self._taiji_cd -= dt
        if self._nirvana_click_cd > 0:
            self._nirvana_click_cd -= dt
        # ===== 第三页 至高霸气 timer 递减 =====
        if self._titan_domain > 0:
            self._titan_domain -= dt
        if self._titan_cd > 0:
            self._titan_cd -= dt
        if self._qinglong_timer > 0:
            self._qinglong_timer -= dt
        if self._qinglong_cd > 0:
            self._qinglong_cd -= dt
        if self._zhuque_timer > 0:
            self._zhuque_timer -= dt
            if self._zhuque_timer <= 0:
                self._zhuque_revive = False
        if self._zhuque_cd > 0:
            self._zhuque_cd -= dt
        if self._xuanwu_timer > 0:
            self._xuanwu_timer -= dt
        if self._xuanwu_cd > 0:
            self._xuanwu_cd -= dt
        if self._stargod_timer > 0:
            self._stargod_timer -= dt
        if self._stargod_cd > 0:
            self._stargod_cd -= dt
        if self._chrono_cd > 0:
            self._chrono_cd -= dt
        if self._buddha_timer > 0:
            self._buddha_timer -= dt
        if self._buddha_cd > 0:
            self._buddha_cd -= dt
        if self._god_timer > 0:
            self._god_timer -= dt
            # 神皇期间无限护盾（不断刷新 shield_timer）
            self.shield_timer = max(self.shield_timer, 1.0)
        if self._god_cd > 0:
            self._god_cd -= dt
        # ===== 终极皮肤冷却更新 =====
        if getattr(self, "_origin_cd", 0) > 0:
            self._origin_cd -= dt
        if getattr(self, "_origin_orb_timer", 0) > 0:
            self._origin_orb_timer -= dt
        if getattr(self, "_paradox_cd", 0) > 0:
            self._paradox_cd -= dt
        if getattr(self, "_paradox_pillar_timer", 0) > 0:
            self._paradox_pillar_timer -= dt
        if getattr(self, "_finality_cd", 0) > 0:
            self._finality_cd -= dt
        if getattr(self, "_finality_scythe_timer", 0) > 0:
            self._finality_scythe_timer -= dt
        if getattr(self, "_finality_laser_timer", 0) > 0:
            self._finality_laser_timer -= dt

    @property
    def invulnerable(self):
        extra = (self._taiji_timer > 0 or self._nirvana_timer > 0
                 or self._xuanwu_timer > 0)
        return self.invuln > 0 or self.shield_timer > 0 or self.phantom_timer > 0 or extra

    @invulnerable.setter
    def invulnerable(self, val):
        """设置 invulnerable 时实际修改 invuln 计时器。"""
        if val > 0:
            self.invuln = max(self.invuln, float(val))
        else:
            self.invuln = 0.0


# ================ 手势追踪（独立线程，可暂停释放摄像头） ================
class HandTracker:
    def __init__(self, model_path):
        self.model_path = model_path
        self.result = None
        self.frame = None
        self.lock = threading.Lock()
        self.running = False
        self.available = False
        self.timestamp = 0
        self._thread = None
        self.cap = None
        self.detector = None
        self._setup()

    def _setup(self):
        try:
            if not os.path.isfile(self.model_path):
                print(f"[HandTracker] 未找到模型文件: {self.model_path}")
                return
            BaseOptions = python.BaseOptions
            HandLandmarkerOptions = vision.HandLandmarkerOptions
            VisionRunningMode = vision.RunningMode

            def cb(result, output_image, timestamp_ms):
                with self.lock:
                    self.result = result

            options = HandLandmarkerOptions(
                base_options=BaseOptions(model_asset_path=self.model_path),
                running_mode=VisionRunningMode.LIVE_STREAM,
                num_hands=1,
                result_callback=cb)
            self.detector = vision.HandLandmarker.create_from_options(options)
            # 仅验证摄像头可用，随后释放（鼠标模式不占用摄像头）
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                raise RuntimeError("摄像头无法打开")
            cap.release()
            self.available = True
        except Exception as e:
            print(f"[HandTracker] 初始化失败（手势模式不可用）: {e}")
            self.available = False

    def resume(self):
        """打开摄像头并启动采集线程。"""
        if self.running or not self.available:
            return
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAM_W)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAM_H)
        if not self.cap.isOpened():
            self.available = False
            return
        self.running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def pause(self):
        """停止采集并释放摄像头。"""
        self.running = False
        if self._thread is not None:
            self._thread.join(timeout=1.0)
            self._thread = None
        if self.cap is not None:
            try:
                self.cap.release()
            except Exception:
                pass
            self.cap = None
        with self.lock:
            self.frame = None
            self.result = None

    def _loop(self):
        while self.running:
            ok, img = self.cap.read()
            if not ok:
                continue
            img = cv2.flip(img, 1)  # 镜像，画面正向
            with self.lock:
                self.frame = img
            try:
                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=img)
                self.timestamp += 1
                self.detector.detect_async(mp_image, self.timestamp)
            except Exception:
                pass

    def get(self):
        with self.lock:
            frame = self.frame
            result = self.result
        lms = None
        if result and result.hand_landmarks:
            lms = result.hand_landmarks[0]
        return frame, lms

    def stop(self):
        self.pause()


# ================ 手势判定 ================
def fingers_extended(lms):
    ext = []
    for i in (8, 12, 16, 20):
        ext.append(lms[i].y < lms[i - 2].y)
    ext.append(lms[4].x < lms[3].x)
    return ext


def is_open_palm(lms):
    """伸掌（四指伸直）= 加速。"""
    idx, mid, ring, pinky, _ = fingers_extended(lms)
    return idx and mid and ring and pinky


def is_fist(lms):
    """握拳（四指均弯曲）= 皮肤专有技能。"""
    idx, mid, ring, pinky, _ = fingers_extended(lms)
    return (not idx) and (not mid) and (not ring) and (not pinky)


# ================ 音效合成 ================
def _snd_sweep(f0, f1, dur, decay=6.0, vol=0.4):
    n = int(SR * dur)
    t = np.arange(n) / SR
    env = np.exp(-t * decay)
    freq = np.linspace(f0, f1, n)
    phase = 2 * np.pi * np.cumsum(freq) / SR
    wave = vol * env * np.sin(phase)
    s = (wave * 32767).astype(np.int16)
    return np.ascontiguousarray(np.column_stack([s, s]))


def _snd_tone(freqs, dur, decay=5.0, vol=0.35):
    n = int(SR * dur)
    t = np.arange(n) / SR
    env = np.exp(-t * decay)
    wave = np.zeros(n)
    for f in freqs:
        wave += np.sin(2 * np.pi * f * t)
    wave /= max(1, len(freqs))
    s = (vol * env * wave * 32767).astype(np.int16)
    return np.ascontiguousarray(np.column_stack([s, s]))


def _snd_hit(dur=0.28, vol=0.5):
    n = int(SR * dur)
    t = np.arange(n) / SR
    env = np.exp(-t * 7)
    noise = np.random.uniform(-1, 1, n)
    freq = np.linspace(160, 55, n)
    low = np.sin(2 * np.pi * np.cumsum(freq) / SR)
    wave = 0.55 * noise + 0.6 * low
    s = (vol * env * wave * 32767).astype(np.int16)
    return np.ascontiguousarray(np.column_stack([s, s]))


def _snd_boom(dur=0.5, vol=0.55):
    n = int(SR * dur)
    t = np.arange(n) / SR
    env = np.exp(-t * 4)
    noise = np.random.uniform(-1, 1, n)
    freq = np.linspace(120, 30, n)
    low = np.sin(2 * np.pi * np.cumsum(freq) / SR)
    wave = 0.7 * noise + 0.8 * low
    s = (vol * env * wave * 32767).astype(np.int16)
    return np.ascontiguousarray(np.column_stack([s, s]))


def _snd_drum(dur=0.35, vol=0.5):
    """低沉鼓声（心跳/危险）。"""
    n = int(SR * dur)
    t = np.arange(n) / SR
    env = np.exp(-t * 9)
    freq = np.linspace(110, 45, n)
    low = np.sin(2 * np.pi * np.cumsum(freq) / SR)
    click = np.exp(-t * 60) * np.random.uniform(-1, 1, n) * 0.4
    wave = 0.9 * low + click
    s = (vol * env * wave * 32767).astype(np.int16)
    return np.ascontiguousarray(np.column_stack([s, s]))


def _snd_stinger(dur=0.7, vol=0.4):
    """不协和刺耳音（恐怖突袭）。"""
    n = int(SR * dur)
    t = np.arange(n) / SR
    env = np.exp(-t * 3.5)
    # 微音程造成不安感
    wave = (np.sin(2 * np.pi * 220 * t) +
            np.sin(2 * np.pi * 233 * t) +
            np.sin(2 * np.pi * 466 * t)) / 3
    noise = np.random.uniform(-1, 1, n) * 0.3
    wave = wave * 0.7 + noise * 0.3
    s = (vol * env * wave * 32767).astype(np.int16)
    return np.ascontiguousarray(np.column_stack([s, s]))


def _snd_drone(dur=2.4, vol=0.22):
    """可循环的低频幽暗环境音。"""
    n = int(SR * dur)
    t = np.arange(n) / SR
    # 缓慢起伏的低频叠加
    lfo = 0.5 + 0.5 * np.sin(2 * np.pi * 0.4 * t)
    wave = (np.sin(2 * np.pi * 55 * t) +
            np.sin(2 * np.pi * 58 * t) * 0.6 +
            np.sin(2 * np.pi * 82 * t) * 0.3) / 1.9
    noise = np.random.uniform(-1, 1, n) * 0.18
    wave = wave * (0.7 + 0.3 * lfo) + noise
    # 首尾淡入淡出以无缝循环
    fade = int(n * 0.08)
    env = np.ones(n)
    env[:fade] = np.linspace(0, 1, fade)
    env[-fade:] = np.linspace(1, 0, fade)
    s = (vol * env * wave * 32767).astype(np.int16)
    return np.ascontiguousarray(np.column_stack([s, s]))


def _snd_whoosh(dur=0.22, vol=0.32):
    """加速冲刺嗖声。"""
    n = int(SR * dur)
    t = np.arange(n) / SR
    env = np.sin(np.pi * t / dur) ** 1.5
    noise = np.random.uniform(-1, 1, n)
    # 带通感：用随时间变化的低频塑形
    freq = np.linspace(800, 200, n)
    tone = np.sin(2 * np.pi * np.cumsum(freq) / SR)
    wave = 0.65 * noise + 0.5 * tone
    s = (vol * env * wave * 32767).astype(np.int16)
    return np.ascontiguousarray(np.column_stack([s, s]))


def _snd_tick(dur=0.05, vol=0.25):
    n = int(SR * dur)
    t = np.arange(n) / SR
    env = np.exp(-t * 80)
    wave = np.sin(2 * np.pi * 1400 * t)
    s = (vol * env * wave * 32767).astype(np.int16)
    return np.ascontiguousarray(np.column_stack([s, s]))


def _snd_select(dur=0.16, vol=0.3):
    n = int(SR * dur)
    t = np.arange(n) / SR
    env = np.exp(-t * 7)
    wave = (np.sin(2 * np.pi * 880 * t) + np.sin(2 * np.pi * 1320 * t) * 0.5) / 1.5
    s = (vol * env * wave * 32767).astype(np.int16)
    return np.ascontiguousarray(np.column_stack([s, s]))


def _snd_ghost(dur=0.9, vol=0.25):
    """飘渺低语（深渊/虚空）。"""
    n = int(SR * dur)
    t = np.arange(n) / SR
    env = np.exp(-t * 2.2) * (1 - np.exp(-t * 8))
    freq = np.linspace(300, 120, n) + 20 * np.sin(2 * np.pi * 5 * t)
    wave = np.sin(2 * np.pi * np.cumsum(freq) / SR)
    wave += 0.4 * np.sin(2 * np.pi * np.cumsum(freq * 1.5) / SR)
    s = (vol * env * wave * 32767).astype(np.int16)
    return np.ascontiguousarray(np.column_stack([s, s]))


def _snd_shoot(dur=0.12, vol=0.22):
    """光枪射击：高频脆响。"""
    n = int(SR * dur)
    t = np.arange(n) / SR
    env = np.exp(-t * 22)
    freq = np.linspace(1800, 600, n)
    wave = np.sin(2 * np.pi * np.cumsum(freq) / SR) * 0.7
    wave += np.random.uniform(-1, 1, n) * 0.3
    s = (vol * env * wave * 32767).astype(np.int16)
    return np.ascontiguousarray(np.column_stack([s, s]))


def _snd_slash(dur=0.22, vol=0.28):
    """光刃挥砍：扫频嗖响。"""
    n = int(SR * dur)
    t = np.arange(n) / SR
    env = np.sin(np.pi * t / dur) ** 1.2
    noise = np.random.uniform(-1, 1, n)
    freq = np.linspace(1200, 300, n)
    tone = np.sin(2 * np.pi * np.cumsum(freq) / SR)
    wave = 0.6 * noise + 0.6 * tone
    s = (vol * env * wave * 32767).astype(np.int16)
    return np.ascontiguousarray(np.column_stack([s, s]))


def _snd_pop(dur=0.16, vol=0.3):
    """敌方被击毁：清脆爆裂。"""
    n = int(SR * dur)
    t = np.arange(n) / SR
    env = np.exp(-t * 14)
    freq = np.linspace(900, 200, n)
    wave = np.sin(2 * np.pi * np.cumsum(freq) / SR) * 0.7
    wave += np.exp(-t * 30) * np.random.uniform(-1, 1, n) * 0.5
    s = (vol * env * wave * 32767).astype(np.int16)
    return np.ascontiguousarray(np.column_stack([s, s]))


def _snd_warn(dur=0.3, vol=0.3):
    """强敌出现警示（两声升调）。"""
    n = int(SR * dur)
    t = np.arange(n) / SR
    env = np.exp(-t * 5)
    f = np.where(t < dur / 2, 440, 660)
    wave = np.sin(2 * np.pi * f * t)
    s = (vol * env * wave * 32767).astype(np.int16)
    return np.ascontiguousarray(np.column_stack([s, s]))


def _snd_shield_break(dur=0.35, vol=0.45):
    """护盾破裂：玻璃碎裂感。"""
    n = int(SR * dur)
    t = np.arange(n) / SR
    env = np.exp(-t * 7)
    noise = np.random.uniform(-1, 1, n) * 0.8
    freq = np.linspace(2400, 400, n)
    tone = np.sin(2 * np.pi * np.cumsum(freq) / SR) * 0.5
    wave = 0.6 * noise + 0.6 * tone
    s = (vol * env * wave * 32767).astype(np.int16)
    return np.ascontiguousarray(np.column_stack([s, s]))


def _snd_wind(dur=4.0, vol=0.18):
    """可循环北风呼啸（带随机起伏）。"""
    n = int(SR * dur)
    t = np.arange(n) / SR
    # 多层低频带通噪声模拟风声
    noise = np.random.uniform(-1, 1, n)
    # 随时间变化的"风强"
    gust = 0.5 + 0.5 * (np.sin(2 * np.pi * 0.13 * t) +
                        0.6 * np.sin(2 * np.pi * 0.27 * t + 1.3))
    # 简易低通：累加平均
    kernel = 64
    if n > kernel:
        csum = np.cumsum(np.insert(noise, 0, 0))
        low = (csum[kernel:] - csum[:-kernel]) / kernel
        # 右侧补 kernel-1 个，恰好凑成 n 个样本（原 n+1-kernel + (kernel-1) = n）
        low = np.pad(low, (0, kernel - 1), mode="edge")
    else:
        low = noise
    wave = low * gust
    # 首尾淡入淡出无缝循环
    fade = int(n * 0.06)
    env = np.ones(n)
    env[:fade] = np.linspace(0, 1, fade)
    env[-fade:] = np.linspace(1, 0, fade)
    s = (vol * env * wave * 32767).astype(np.int16)
    s = np.clip(s, -32767, 32767)
    # 强制长度为 n（防御性：最后裁剪）
    if s.shape[0] != n:
        s = s[:n]
    return np.ascontiguousarray(np.column_stack([s, s]))


def _snd_drone_dark(dur=3.0, vol=0.20):
    """深渊低频幽暗环境（可循环，更压抑）。"""
    n = int(SR * dur)
    t = np.arange(n) / SR
    lfo = 0.5 + 0.5 * np.sin(2 * np.pi * 0.25 * t)
    wave = (np.sin(2 * np.pi * 42 * t) +
            np.sin(2 * np.pi * 47 * t) * 0.7 +
            np.sin(2 * np.pi * 63 * t) * 0.4) / 2.1
    noise = np.random.uniform(-1, 1, n) * 0.22
    wave = wave * (0.7 + 0.3 * lfo) + noise
    fade = int(n * 0.08)
    env = np.ones(n)
    env[:fade] = np.linspace(0, 1, fade)
    env[-fade:] = np.linspace(1, 0, fade)
    s = (vol * env * wave * 32767).astype(np.int16)
    return np.ascontiguousarray(np.column_stack([s, s]))


def _snd_coin(dur=0.22, vol=0.3):
    """金币拾取：清脆叮声。"""
    n = int(SR * dur)
    t = np.arange(n) / SR
    env = np.exp(-t * 9)
    wave = (np.sin(2 * np.pi * 1318 * t) + np.sin(2 * np.pi * 1760 * t) * 0.6) / 1.6
    s = (vol * env * wave * 32767).astype(np.int16)
    return np.ascontiguousarray(np.column_stack([s, s]))


def _snd_buy(dur=0.4, vol=0.32):
    """购买成功：上行琶音。"""
    n = int(SR * dur)
    t = np.arange(n) / SR
    env = np.exp(-t * 4)
    wave = np.zeros(n)
    for i, f in enumerate([523, 659, 784, 1047]):
        seg = (t >= i * dur / 4) & (t < (i + 1) * dur / 4)
        wave += seg * np.sin(2 * np.pi * f * t)
    s = (vol * env * wave * 32767 / 4).astype(np.int16)
    return np.ascontiguousarray(np.column_stack([s, s]))


def _snd_shockwave(dur=0.5, vol=0.4):
    """光波冲击：低频爆裂扫频。"""
    n = int(SR * dur)
    t = np.arange(n) / SR
    env = np.exp(-t * 3.5)
    freq = np.linspace(800, 60, n)
    tone = np.sin(2 * np.pi * np.cumsum(freq) / SR)
    noise = np.random.uniform(-1, 1, n) * 0.4
    wave = 0.7 * tone + 0.5 * noise
    s = (vol * env * wave * 32767).astype(np.int16)
    return np.ascontiguousarray(np.column_stack([s, s]))


def _snd_ehit(dur=0.10, vol=0.28):
    """敌球受击：短促金属脆响。"""
    n = int(SR * dur)
    t = np.arange(n) / SR
    env = np.exp(-t * 28)
    wave = (np.sin(2 * np.pi * 880 * t) + np.random.uniform(-1, 1, n) * 0.5) * 0.6
    s = (vol * env * wave * 32767).astype(np.int16)
    return np.ascontiguousarray(np.column_stack([s, s]))


def _snd_edie(dur=0.28, vol=0.4):
    """敌球毁灭：闷爆 + 下行扫频。"""
    n = int(SR * dur)
    t = np.arange(n) / SR
    env = np.exp(-t * 7)
    freq = np.linspace(420, 70, n)
    tone = np.sin(2 * np.pi * np.cumsum(freq) / SR)
    noise = np.random.uniform(-1, 1, n) * 0.6
    wave = 0.6 * tone + 0.6 * noise
    s = (vol * env * wave * 32767).astype(np.int16)
    return np.ascontiguousarray(np.column_stack([s, s]))


def _snd_freeze(dur=0.6, vol=0.35):
    """冻结：上行冰晶碎裂。"""
    n = int(SR * dur)
    t = np.arange(n) / SR
    env = np.exp(-t * 3)
    freq = np.linspace(300, 1800, n)
    tone = np.sin(2 * np.pi * np.cumsum(freq) / SR) * 0.6
    shimmer = np.sin(2 * np.pi * 3200 * t) * 0.3 * np.exp(-t * 5)
    s = (vol * env * (tone + shimmer) * 32767 / 1.5).astype(np.int16)
    return np.ascontiguousarray(np.column_stack([s, s]))


def _snd_thunder(dur=0.35, vol=0.38):
    """闪电：白噪爆裂 + 高频滋滋。"""
    n = int(SR * dur)
    t = np.arange(n) / SR
    env = np.exp(-t * 8)
    noise = np.random.uniform(-1, 1, n)
    zap = np.sin(2 * np.pi * 2400 * t) * 0.4
    wave = 0.7 * noise + 0.5 * zap
    s = (vol * env * wave * 32767).astype(np.int16)
    return np.ascontiguousarray(np.column_stack([s, s]))


def _snd_phantom(dur=0.45, vol=0.32):
    """幻影：空灵飘忽上滑。"""
    n = int(SR * dur)
    t = np.arange(n) / SR
    env = np.exp(-t * 3.5)
    freq = np.linspace(200, 1200, n)
    wave = np.sin(2 * np.pi * np.cumsum(freq) / SR) * 0.5
    wave += np.sin(2 * np.pi * (freq * 1.5) * t) * 0.25
    s = (vol * env * wave * 32767 / 1.5).astype(np.int16)
    return np.ascontiguousarray(np.column_stack([s, s]))


class SoundBank:
    # 每种氛围音对应一个可循环 track
    AMBIENT_KEYS = ("wind", "drone", "drone_dark")

    def __init__(self):
        self.sounds = {}
        self.ok = False
        self._ambient_chan = None
        self._ambient_key = None
        if not pygame.mixer.get_init():
            print("[SoundBank] mixer 未初始化，跳过音效")
            return
        try:
            pygame.mixer.set_num_channels(32)
        except Exception:
            pass
        # 每个音效单独 try/except：单个失败不影响整体
        _build = [
            ("eat", lambda: pygame.sndarray.make_sound(_snd_sweep(520, 1100, 0.12, 10, 0.30))),
            ("big", lambda: pygame.sndarray.make_sound(_snd_sweep(300, 900, 0.2, 7, 0.38))),
            ("levelup", lambda: pygame.sndarray.make_sound(_snd_tone([523, 659, 784, 1047], 0.45, 3, 0.30))),
            ("hit", lambda: pygame.sndarray.make_sound(_snd_hit(0.28, 0.5))),
            ("death", lambda: pygame.sndarray.make_sound(_snd_sweep(520, 70, 0.7, 2.5, 0.45))),
            ("start", lambda: pygame.sndarray.make_sound(_snd_sweep(320, 820, 0.2, 6, 0.30))),
            ("powerup", lambda: pygame.sndarray.make_sound(_snd_sweep(600, 1400, 0.25, 4, 0.32))),
            ("bomb", lambda: pygame.sndarray.make_sound(_snd_boom(0.5, 0.55))),
            ("win", lambda: pygame.sndarray.make_sound(_snd_tone([523, 659, 784, 1047, 1319], 0.6, 2, 0.35))),
            ("drum", lambda: pygame.sndarray.make_sound(_snd_drum(0.35, 0.5))),
            ("stinger", lambda: pygame.sndarray.make_sound(_snd_stinger(0.7, 0.4))),
            ("drone", lambda: pygame.sndarray.make_sound(_snd_drone(2.4, 0.22))),
            ("whoosh", lambda: pygame.sndarray.make_sound(_snd_whoosh(0.22, 0.32))),
            ("tick", lambda: pygame.sndarray.make_sound(_snd_tick(0.05, 0.25))),
            ("select", lambda: pygame.sndarray.make_sound(_snd_select(0.16, 0.3))),
            ("ghost", lambda: pygame.sndarray.make_sound(_snd_ghost(0.9, 0.25))),
            ("shoot", lambda: pygame.sndarray.make_sound(_snd_shoot(0.12, 0.22))),
            ("slash", lambda: pygame.sndarray.make_sound(_snd_slash(0.22, 0.28))),
            ("pop", lambda: pygame.sndarray.make_sound(_snd_pop(0.16, 0.3))),
            ("warn", lambda: pygame.sndarray.make_sound(_snd_warn(0.3, 0.3))),
            ("shield_break", lambda: pygame.sndarray.make_sound(_snd_shield_break(0.35, 0.45))),
            ("wind", lambda: pygame.sndarray.make_sound(_snd_wind(4.0, 0.18))),
            ("drone_dark", lambda: pygame.sndarray.make_sound(_snd_drone_dark(3.0, 0.20))),
            ("coin", lambda: pygame.sndarray.make_sound(_snd_coin(0.22, 0.3))),
            ("buy", lambda: pygame.sndarray.make_sound(_snd_buy(0.4, 0.32))),
            ("shockwave", lambda: pygame.sndarray.make_sound(_snd_shockwave(0.5, 0.4))),
            ("ehit", lambda: pygame.sndarray.make_sound(_snd_ehit(0.10, 0.28))),
            ("edie", lambda: pygame.sndarray.make_sound(_snd_edie(0.28, 0.4))),
            ("freeze", lambda: pygame.sndarray.make_sound(_snd_freeze(0.6, 0.35))),
            ("thunder", lambda: pygame.sndarray.make_sound(_snd_thunder(0.35, 0.38))),
            ("phantom", lambda: pygame.sndarray.make_sound(_snd_phantom(0.45, 0.32))),
        ]
        for name, fn in _build:
            try:
                self.sounds[name] = fn()
            except Exception as e:
                print(f"[SoundBank] 音效 {name} 加载失败：{type(e).__name__}: {e}")
        if self.sounds:
            self.ok = True
        else:
            print("[SoundBank] 全部音效加载失败（静音运行）")

    def play(self, name):
        s = self.sounds.get(name)
        if not s:
            return
        # 通道不足时：先找空闲 channel 再 fallback 到 play()（pygame 会自动抢占最低优先级）
        ch = None
        try:
            ch = s.play()
        except Exception:
            ch = None
        if ch is None:
            try:
                # 清理可能卡住的通道后重试
                pygame.mixer.stop()
                ch = s.play()
            except Exception:
                pass

    def start_ambient(self, key, vol=0.5):
        """开始循环播放指定氛围音（wind / drone / drone_dark）。"""
        if not self.ok or key not in self.sounds:
            return
        if self._ambient_key == key and self._ambient_chan is not None:
            try:
                self.sounds[key].set_volume(vol)
            except Exception:
                pass
            return
        self.stop_ambient()
        try:
            s = self.sounds[key]
            s.set_volume(vol)
            self._ambient_chan = s.play(loops=-1)
            self._ambient_key = key
        except Exception:
            self._ambient_chan = None
            self._ambient_key = None

    def stop_ambient(self):
        if self._ambient_chan is not None:
            try:
                self._ambient_chan.stop()
            except Exception:
                pass
            self._ambient_chan = None
        self._ambient_key = None

    def rebuild_all(self):
        """卸载所有已加载 Sound 并清空。"""
        for s in list(self.sounds.values()):
            try:
                s.stop()
            except Exception:
                pass
        self.sounds.clear()
        self.stop_ambient()
        self.ok = False

    # 旧接口兼容
    def start_drone(self, vol=0.7):
        self.start_ambient("drone", vol)

    def stop_drone(self):
        self.stop_ambient()


# ================ 游戏 ================
class Game:
    MAP = "map"
    PLAYING = "playing"
    PAUSED = "paused"
    LEVEL_COMPLETE = "level_complete"
    VICTORY = "victory"
    OVER = "over"

    def __init__(self):
        pygame.mixer.pre_init(SR, -16, 2, 512)
        pygame.init()
        pygame.display.set_caption("星尘吞噬者  Stardust Devourer")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.SCALED, vsync=1)
        self.clock = pygame.time.Clock()
        self.sounds = SoundBank()
        self.muted = False
        self.fullscreen = False
        self._flash_msg = ""
        self._flash_timer = 0.0
        # ===== 通用弹窗（导出/导入/兑换码 结果提示等）=====
        self._modal = None          # {title, body_lines, ok_rect?, close_rect?, input?:"" , input_title?}
        self._modal_clipboard = ""  # 复制到剪贴板缓存
        # ===== 抽奖每日刷新 & 钻石抽奖页 =====
        self._lottery_day = None
        self._diamond_lottery = False  # True=钻石抽奖页，False=金币抽奖页
        # ===== 游戏内皮肤切换：暂停后空格键确认 =====
        self._pending_skin = None
        self.tracker = HandTracker(MODEL_PATH)
        # 单人控制循环：鼠标 -> 手势 -> 方向键 -> 鼠标
        self.control_mode = "mouse"  # 初始鼠标模式，摄像头关闭
        self.hand_vel = (0.0, 0.0)
        self.hand_dash = False
        self._cam_frame = None
        self._last_lms = None
        # 方向键速度（单人方向键模式 / 双人 P2）
        self.arrow_vel = (0.0, 0.0)
        self.wasd_vel = (0.0, 0.0)
        self.p1_dash_key = False
        self.p2_dash_key = False
        self.bg_stars = self._make_bg_stars()
        self.vignette = self._make_vignette()
        # 关卡进度（顺序解锁：通过一关才解锁下一关）
        self.current_level = 0
        self.unlocked = 1  # 主线解锁数
        self.dungeon_unlocked = 0  # 副本解锁数（0 表示未开通）
        self.map_cursor = 0
        self.score = 0
        self.best = 0
        self.state = self.MAP
        self.shake = 0.0
        self.bg_color = LEVELS[0]["bg"]
        # 副本 vs 主线切换
        self.is_dungeon = False  # False=主线  True=副本
        self.DUNGEON_LEVELS = DUNGEON_LEVELS
        # 模式：1P / 2P
        self.num_players = 1
        # 氛围 / 恐怖
        self.ambient = []          # 每关氛围粒子
        self.ambient_timer = 0.0
        self.heartbeat_timer = 0.0
        self.drone_on = False
        self.lightning_timer = 0.0
        self.lightning_alpha = 0.0
        self.show_help = False
        self._last_text_tick = -1000
        # 金币 / 钻石 / 皮肤 / 商店
        self.coins = 0
        self.diamonds = 0              # 钻石（仅从副本关卡获得，用于购买第二页皮肤）
        self.owned_skins = set()       # 已拥有的皮肤 id
        self.active_skin = None        # 当前装备的皮肤 id（P1）
        self.active_skin_p2 = None     # P2 当前装备的皮肤 id（None 表示跟随 P1）
        self.show_shop = False         # True=P1 商店；"p2"=P2 商店
        self.shop_cursor = 0
        self.shop_page = 0             # 皮肤商店当前页：0=第一页（金币），1=第二页（钻石）
        self.show_lottery = False
        # Q6/Q7/Q8：新功能状态
        self.show_achievements = False
        self.show_settings = False
        self._ach_page = 0
        self._endless_mode = False
        self._endless_wave = 0
        self._endless_score = 0
        self._boss_mode = False  # Q9：BOSS模式
        self._boss_level = 0
        self._endless_high_score = 0
        self._endless_high_wave = 0
        self._lang = "zh"  # "zh" or "en"
        self._sound_on = True
        # 成就统计计数（用于成就检测）
        self._achievements_list = None     # 懒加载，首次打开成就时构建
        self._achievements_unlocked = set()
        self._ach_toasts = []  # 成就解锁提示队列 [{"name", "timer"}]
        self._total_kills = 0
        self._max_combo = 0
        self._max_eaten = 0
        self._games_played = 0
        # 右键分裂
        self.split_cells = []          # 分裂出的子细胞（Player 列表）
        self.split_angle = 0.0
        # 金币实体
        self.coin_pickups = []
        self.coin_spawn_timer = 4.0
        # ===== 所有皮肤技能所需的实体列表 & 计时器，统一预初始化，避免进入关卡后 AttributeError =====
        self.dragon_fire = []
        self.demon_clouds = []
        self.stellar_orbs = []
        self.taiji_blades = []
        self.baihu_shadows = []
        self.baihu_blades = []
        self.titan_hammers = []
        self.qinglong_dragons = []
        self.zhuque_fire = []
        self.xuanwu_ices = []
        self.stargod_meteors = []
        self.chrono_blades = []
        self.chrono_hooks = []
        self.buddha_hands = []
        self.god_pillars = []
        self.meteors = []
        self.fireballs = []
        # 时空帝主：全场冻结计时（必须先在这初始化，不能靠 update 后面的 hasattr，否则第一帧崩）
        self.time_freeze_timer = 0.0
        # 抽奖/帮助面板相关的属性
        if not hasattr(self, "_lottery_revealed"):
            self._lottery_revealed = {}
        if not hasattr(self, "_lottery_anim"):
            self._lottery_anim = {}
        if not hasattr(self, "_help_page"):
            self._help_page = 0
        # ESC 退出确认弹窗（MAP 状态下按 ESC：默认不直接退出，弹窗确认）
        self._confirm_exit = False
        # 崩溃：显示异常信息到屏幕上 + 停留几秒再退出，避免闪一下就没
        self._crash_info = None   # (msg_short, tb_text) 或 None
        self._crash_wait = 0.0    # 崩溃后剩余停留秒数
        self.reset_level()

    # ---- 背景星空 ----
    def _make_bg_stars(self):
        layers = []
        for _, count, speed in ((0.25, 90, 6), (0.5, 50, 14), (1.0, 25, 30)):
            stars = []
            for _ in range(count):
                stars.append([random.uniform(0, WIDTH),
                              random.uniform(0, HEIGHT),
                              random.uniform(0.6, 1.6)])
            layers.append((stars, speed))
        return layers

    def _make_vignette(self):
        cx, cy = WIDTH / 2, HEIGHT / 2
        maxd = math.hypot(cx, cy)
        y, x = np.ogrid[:HEIGHT, :WIDTH]
        d = np.sqrt((x - cx) ** 2 + (y - cy) ** 2)
        a = np.clip((d / maxd * 1.5 - 0.55) * 255, 0, 210).astype(np.uint8)
        rgba = np.zeros((HEIGHT, WIDTH, 4), dtype=np.uint8)
        rgba[..., 3] = a
        surf = pygame.image.frombuffer(rgba.tobytes(), (WIDTH, HEIGHT), 'RGBA')
        return surf.convert_alpha()

    def _update_bg(self, dt, px, py):
        for stars, speed in self.bg_stars:
            for s in stars:
                s[1] += speed * dt * 0.15
                if s[1] > HEIGHT:
                    s[1] = 0
                    s[0] = random.uniform(0, WIDTH)

    # ---- 每关氛围粒子 ----
    def _init_ambient(self, theme):
        self.ambient_theme = theme
        cfg = {
            "nebula":  ("drift", 60, [(90, 60, 160), (60, 120, 200), (160, 80, 180)]),
            "ice":     ("fall",   80, [(180, 220, 255), (220, 240, 255)]),
            "fire":    ("rise",   70, [(255, 120, 40), (255, 70, 30), (255, 200, 80)]),
            "dark":    ("drift",  40, [(60, 50, 90), (40, 40, 80)]),
            "chaos":   ("swirl",  70, [(200, 90, 220), (90, 200, 220), (220, 200, 90)]),
            "sparkle": ("twinkle",90, [(120, 255, 180), (180, 255, 220), (255, 240, 150)]),
            "hell":    ("rise",   60, [(255, 60, 40), (200, 30, 20), (255, 120, 60)]),
            "void":    ("drift",  50, [(150, 80, 220), (90, 60, 160)]),
            "storm":   ("rise",   70, [(150, 170, 210), (110, 130, 180), (200, 210, 240)]),
            "crystal": ("twinkle",80, [(140, 220, 255), (200, 240, 255), (120, 200, 230)]),
            "magma":   ("rise",   70, [(255, 90, 30), (255, 150, 50), (200, 40, 20)]),
            "aurora":  ("drift",  70, [(90, 255, 200), (120, 200, 255), (180, 255, 220)]),
            "vortex":  ("swirl",  90, [(200, 120, 255), (120, 160, 255), (220, 180, 255)]),
            "ruin":    ("drift",  55, [(200, 150, 90), (160, 120, 80), (220, 170, 110)]),
            "singularity": ("swirl", 100, [(230, 120, 255), (180, 80, 220), (120, 60, 180)]),
        }.get(theme, ("drift", 40, [(120, 120, 160)]))
        self._ambient_kind, self._ambient_count, self._ambient_cols = cfg
        self.ambient = [self._spawn_ambient() for _ in range(self._ambient_count)]

    def _spawn_ambient(self):
        kind = self._ambient_kind
        col = random.choice(self._ambient_cols)
        a = {
            "x": random.uniform(0, WIDTH),
            "y": random.uniform(0, HEIGHT),
            "vx": random.uniform(-10, 10),
            "vy": random.uniform(-10, 10),
            "r": random.uniform(1.5, 4.0),
            "col": col,
            "ph": random.uniform(0, math.tau),
            "sp": random.uniform(0.5, 2.0),
            "life": random.uniform(2.0, 5.0),
        }
        if kind == "fall":
            a["y"] = random.uniform(-40, HEIGHT)
            a["vy"] = random.uniform(20, 55)
            a["vx"] = random.uniform(-8, 8)
        elif kind == "rise":
            a["y"] = random.uniform(0, HEIGHT + 40)
            a["vy"] = -random.uniform(20, 60)
            a["vx"] = random.uniform(-12, 12)
        elif kind == "swirl":
            a["cx"] = random.uniform(WIDTH * 0.2, WIDTH * 0.8)
            a["cy"] = random.uniform(HEIGHT * 0.2, HEIGHT * 0.8)
            a["rad"] = random.uniform(60, 260)
            a["ang"] = random.uniform(0, math.tau)
        return a

    def _update_ambient(self, dt):
        kind = self._ambient_kind
        for a in self.ambient:
            a["ph"] += dt * a["sp"]
            if kind == "fall":
                a["x"] += a["vx"] * dt
                a["y"] += a["vy"] * dt
                if a["y"] > HEIGHT + 10:
                    a["y"] = -10
                    a["x"] = random.uniform(0, WIDTH)
            elif kind == "rise":
                a["x"] += a["vx"] * dt
                a["y"] += a["vy"] * dt
                if a["y"] < -10:
                    a["y"] = HEIGHT + 10
                    a["x"] = random.uniform(0, WIDTH)
            elif kind == "swirl":
                a["ang"] += dt * a["sp"]
                a["x"] = a["cx"] + math.cos(a["ang"]) * a["rad"]
                a["y"] = a["cy"] + math.sin(a["ang"]) * a["rad"]
            else:  # drift / twinkle
                a["x"] += a["vx"] * dt
                a["y"] += a["vy"] * dt
                if a["x"] < -20: a["x"] = WIDTH + 20
                if a["x"] > WIDTH + 20: a["x"] = -20
                if a["y"] < -20: a["y"] = HEIGHT + 20
                if a["y"] > HEIGHT + 20: a["y"] = -20

    def _draw_ambient(self, ox, oy):
        kind = self._ambient_kind
        for a in self.ambient:
            col = a["col"]
            if kind == "twinkle":
                tw = 0.4 + 0.6 * (0.5 + 0.5 * math.sin(a["ph"]))
                g = get_glow(a["r"] * 4, col, alpha=int(160 * tw))
            elif kind in ("fire", "hell", "rise"):
                g = get_glow(a["r"] * 3.5, col, alpha=130)
            else:
                g = get_glow(a["r"] * 3.2, col, alpha=110)
            self.screen.blit(g, g.get_rect(center=(int(a["x"] + ox), int(a["y"] + oy))),
                             special_flags=pygame.BLEND_RGB_ADD)

    # ---- 恐怖氛围：心跳鼓 / 低频环境音 / 闪电 / 鬼低语 ----
    # 每个主题对应一种长播放氛围音
    THEME_AMBIENT = {
        "nebula": ("wind", 0.30), "ice": ("wind", 0.42), "sparkle": ("wind", 0.22),
        "fire": ("drone", 0.32), "storm": ("wind", 0.50), "dark": ("drone_dark", 0.55),
        "chaos": ("drone_dark", 0.40), "crystal": ("wind", 0.30), "magma": ("drone", 0.45),
        "aurora": ("wind", 0.32), "hell": ("drone", 0.55), "void": ("drone_dark", 0.50),
        "vortex": ("drone_dark", 0.55), "ruin": ("drone", 0.45), "singularity": ("drone_dark", 0.65),
    }

    def _ambient_for_level(self, idx=None):
        if idx is None:
            idx = self.current_level
        theme = LEVELS[idx]["theme"]
        return self.THEME_AMBIENT.get(theme, ("wind", 0.30))

    def _update_horror(self):
        lv = self._get_levels()[self.current_level]
        h = lv.get("horror", 0.0)
        self._horror = h
        # 长播放氛围音：仅游戏中播放
        if self.state != self.PLAYING or self.muted:
            if self.drone_on:
                self.sounds.stop_ambient()
                self.drone_on = False
            return
        key, base_vol = self._ambient_for_level()
        vol = base_vol + h * 0.25
        self.sounds.start_ambient(key, vol)
        self.drone_on = True

    def _tick_horror(self, dt):
        h = getattr(self, "_horror", 0.0)
        if h <= 0:
            return
        # 心跳：随恐怖度加快
        self.heartbeat_timer -= dt
        if self.heartbeat_timer <= 0:
            self._play("drum")
            self.heartbeat_timer = lerp(1.3, 0.45, h) + random.uniform(-0.05, 0.05)
            if h >= 0.7 and random.random() < 0.25:
                self._play("stinger")
        # 闪电（虚空/地狱）
        theme = self._get_levels()[self.current_level]["theme"]
        if theme in ("void", "hell", "dark"):
            self.lightning_timer -= dt
            if self.lightning_timer <= 0:
                self.lightning_alpha = 1.0
                self.lightning_timer = random.uniform(4.0, 9.0) - h * 2.0
                if theme == "void" and random.random() < 0.4:
                    self._play("ghost")
            self.lightning_alpha = max(0.0, self.lightning_alpha - dt * 3.5)
        # 偶发鬼低语
        if h >= 0.55 and random.random() < 0.04 * dt:
            self._play("ghost")

    def _draw_horror_overlay(self):
        theme = self._get_levels()[self.current_level]["theme"]
        # 闪电
        if self.lightning_alpha > 0:
            a = int(self.lightning_alpha * 90)
            ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            ov.fill((200, 200, 255, a))
            self.screen.blit(ov, (0, 0))
        # 黑暗深渊 / 虚空：更重暗角
        if theme == "dark":
            self.screen.blit(self.vignette, (0, 0))
            ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            ov.fill((0, 0, 0, 60))
            self.screen.blit(ov, (0, 0))
        elif theme == "void":
            self.screen.blit(self.vignette, (0, 0))
        # 地狱：底部红色火光
        if theme == "hell":
            g = get_glow(380, (255, 60, 30), alpha=70)
            self.screen.blit(g, g.get_rect(center=(WIDTH // 2, HEIGHT + 120)),
                             special_flags=pygame.BLEND_RGB_ADD)

    # ---- 后期移动背景干扰（视觉迷惑，错乱感，不影响判定） ----
    def _draw_interfere(self):
        interfere = self._get_levels()[self.current_level].get("interfere", 0.0)
        if interfere <= 0:
            return
        t = pygame.time.get_ticks() * 0.001
        ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        # 1) 横向滚动光带（多方向）
        n_bands = int(3 + interfere * 5)
        for i in range(n_bands):
            spd = (50 + i * 28) * (0.6 + interfere)
            y = ((t * spd + i * 137) % (HEIGHT + 200)) - 100
            h = 22 + int(24 * math.sin(t * 1.5 + i))
            col = (255, 255, 255, int(16 + 38 * interfere))
            pygame.draw.rect(ov, col, (0, int(y), WIDTH, h))
        # 2) 斜向错位条纹（错乱感核心）
        if interfere >= 0.3:
            n_stripes = int(6 + interfere * 10)
            for i in range(n_stripes):
                spd = (90 + i * 18) * (0.5 + interfere)
                x = ((t * spd + i * 211) % (WIDTH + 300)) - 150
                skew = math.sin(t * 0.7 + i) * 60 * interfere
                col = (180, 80, 200, int(10 + 26 * interfere))
                pygame.draw.polygon(ov, col, [
                    (x, 0), (x + 40 + skew, 0),
                    (x + 20 - skew, HEIGHT), (x - 20, HEIGHT)])
        # 3) 旋转斜纹扇形 + 漂移光团
        if interfere >= 0.5:
            cx, cy = WIDTH // 2, HEIGHT // 2
            for i in range(8):
                ang = t * (0.6 + interfere) + i * (math.tau / 8)
                rad = 180 + 60 * math.sin(t * 0.9 + i)
                x = cx + math.cos(ang) * rad
                y = cy + math.sin(ang) * rad
                g = get_glow(110, (200, 80, 220), alpha=int(40 * interfere))
                ov.blit(g, g.get_rect(center=(int(x), int(y))),
                        special_flags=pygame.BLEND_RGB_ADD)
        # 4) 高强度：全屏色偏闪烁（极强错乱）
        if interfere >= 0.7:
            flick = (math.sin(t * 8) * 0.5 + 0.5) * interfere
            col = (120, 0, 40, int(24 * flick))
            pygame.draw.rect(ov, col, (0, 0, WIDTH, HEIGHT))
        self.screen.blit(ov, (0, 0))

    def _draw_bg(self, ox, oy):
        self.screen.fill(self.bg_color)
        for i, (stars, speed) in enumerate(self.bg_stars):
            bright = 60 + i * 50
            col = (bright, bright, min(255, bright + 30))
            for s in stars:
                px = s[0] + ox * (0.2 + i * 0.15)
                py = s[1] + oy * (0.2 + i * 0.15)
                self.screen.fill(col, (int(px), int(py), max(1, int(s[2])), max(1, int(s[2]))))
        # Q1：副本模式 - 主题专属背景景物（与主线形成明显差异）
        if getattr(self, "_dungeon_mode", False) or getattr(self, "_boss_mode", False):
            self._draw_dungeon_scenery(ox, oy)

    # ---- Q1：副本主题背景景物 ----
    def _draw_dungeon_scenery(self, ox, oy):
        lv = self._get_levels()[self.current_level]
        theme = lv.get("theme", "")
        t = pygame.time.get_ticks() * 0.001
        dun_lv = getattr(self, "_dungeon_level", 1)
        # 强度随副本层数递增（视觉密度/亮度）
        intensity = 0.55 + min(0.45, dun_lv * 0.03)

        if theme == "chaos":
            # 混沌带：紫红螺旋星云 + 漂浮能量裂缝
            cx, cy = WIDTH * 0.5, HEIGHT * 0.5
            for i in range(5):
                r = 80 + i * 70
                ang = t * (0.25 - i * 0.04) + i * 1.3
                col = (180 - i * 18, 60 + i * 10, 220 - i * 14)
                pts = []
                for k in range(28):
                    a = ang + k * (math.tau / 28)
                    rr = r + math.sin(k * 0.6 + t) * 22
                    pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr * 0.62))
                if len(pts) > 2:
                    surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                    pygame.draw.polygon(surf, (*col, int(40 * intensity)), pts)
                    self.screen.blit(surf, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
            # 能量裂缝
            for i in range(6):
                x = (i * 197 + t * 30) % WIDTH
                y = HEIGHT * 0.2 + (i * 53) % (HEIGHT * 0.6)
                g = get_glow(60, (220, 100, 240), alpha=int(80 * intensity))
                self.screen.blit(g, g.get_rect(center=(int(x), int(y))),
                                 special_flags=pygame.BLEND_RGB_ADD)

        elif theme == "ice":
            # 冰晶带：远处冰山轮廓 + 冰晶柱 + 寒雾
            # 冰山轮廓
            ice_col = (60, 110, 160)
            for layer in range(3):
                base_y = HEIGHT - 40 - layer * 50
                pts = [(0, HEIGHT)]
                step = 80 + layer * 30
                x = -step
                while x <= WIDTH + step:
                    h = 80 + (math.sin(x * 0.013 + layer * 1.7) * 0.5 + 0.5) * 120 * (1 - layer * 0.25)
                    pts.append((x, base_y - h))
                    x += step
                pts.append((WIDTH, HEIGHT))
                c = tuple(max(0, v - layer * 20) for v in ice_col)
                pygame.draw.polygon(self.screen, c, pts)
            # 冰晶柱
            for i in range(7):
                x = (i * 173 + 80) % WIDTH
                h = 60 + (i * 23) % 80
                base_y = HEIGHT - 40
                pygame.draw.polygon(self.screen, (180, 220, 255),
                                    [(x, base_y), (x - 18, base_y - h), (x, base_y - h - 14), (x + 18, base_y - h)])
                pygame.draw.polygon(self.screen, (220, 240, 255),
                                    [(x, base_y), (x - 8, base_y - h * 0.7), (x, base_y - h - 14)])
            # 寒雾
            for i in range(4):
                y = HEIGHT * 0.3 + i * 90
                g = get_glow(220, (140, 180, 220), alpha=int(28 * intensity))
                self.screen.blit(g, g.get_rect(center=(int(WIDTH * (0.2 + i * 0.25) + math.sin(t + i) * 30), int(y))),
                                 special_flags=pygame.BLEND_RGB_ADD)

        elif theme == "sparkle":
            # 翠灭藤林：远树轮廓 + 漂浮光球 + 林间光斑
            # 远树
            for layer in range(3):
                base_y = HEIGHT - 30 - layer * 35
                col = (max(0, 20 - layer * 5), max(0, 60 - layer * 12), max(0, 40 - layer * 8))
                x = -50
                while x <= WIDTH + 50:
                    h = 50 + (math.sin(x * 0.02 + layer * 2.1) * 0.5 + 0.5) * 90 * (1 - layer * 0.2)
                    pygame.draw.polygon(self.screen, col,
                                        [(x, base_y), (x + 25, base_y - h * 0.5),
                                         (x + 12, base_y - h), (x + 40, base_y - h * 0.6),
                                         (x + 50, base_y)])
                    x += 90 + layer * 20
            # 漂浮光球（萤火）
            for i in range(14):
                x = (i * 137 + t * 18) % WIDTH
                y = (i * 89 + math.sin(t * 0.7 + i) * 60) % HEIGHT
                tw = 0.4 + 0.6 * (0.5 + 0.5 * math.sin(t * 2 + i))
                g = get_glow(14, (160, 255, 180), alpha=int(160 * tw * intensity))
                self.screen.blit(g, g.get_rect(center=(int(x), int(y))),
                                 special_flags=pygame.BLEND_RGB_ADD)

        elif theme == "fire":
            # 火焰星云：远处火山 + 火焰柱 + 灰烬
            # 火山轮廓
            for i in range(3):
                cx = WIDTH * (0.2 + i * 0.3)
                base_y = HEIGHT - 30
                h = 130 - i * 25
                pygame.draw.polygon(self.screen, (60, 18, 14),
                                    [(cx - 110, base_y), (cx - 35, base_y - h),
                                     (cx, base_y - h - 18), (cx + 40, base_y - h + 8),
                                     (cx + 110, base_y)])
                # 火山口火光
                g = get_glow(70, (255, 100, 40), alpha=int(150 * intensity))
                self.screen.blit(g, g.get_rect(center=(int(cx), int(base_y - h - 8))),
                                 special_flags=pygame.BLEND_RGB_ADD)
            # 火焰柱
            for i in range(5):
                x = (i * 167 + 90) % WIDTH
                fh = 50 + (i * 19) % 60
                for k in range(3):
                    fy = HEIGHT - 30 - k * 18
                    fw = max(4, 14 - k * 3)
                    col = (255, max(60, 200 - k * 50), 40)
                    pygame.draw.polygon(self.screen, col,
                                        [(x, fy), (x - fw, fy - fh + k * 10),
                                         (x, fy - fh + k * 10 - 6), (x + fw, fy - fh + k * 10)])
            # 漂浮灰烬
            for i in range(12):
                x = (i * 113 + t * 25) % WIDTH
                y = (HEIGHT - t * 40 - i * 47) % HEIGHT
                g = get_glow(6, (255, 140, 60), alpha=int(120 * intensity))
                self.screen.blit(g, g.get_rect(center=(int(x), int(y))),
                                 special_flags=pygame.BLEND_RGB_ADD)

        elif theme == "storm":
            # 风暴域：乌云层 + 闪电 + 雨幕
            # 乌云
            for i in range(5):
                cx = (i * 211 + t * 35) % (WIDTH + 200) - 100
                cy = 60 + (i % 2) * 50
                for k in range(4):
                    g = get_glow(80 + k * 20, (60, 70, 100), alpha=int(60 * intensity))
                    self.screen.blit(g, g.get_rect(center=(int(cx + k * 30), int(cy))),
                                     special_flags=pygame.BLEND_RGB_ADD)
            # 闪电（偶发）
            if int(t * 2) % 7 == 0:
                flash = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                flash.fill((180, 200, 255, int(60 * intensity)))
                self.screen.blit(flash, (0, 0))
                # 闪电线
                sx = (int(t * 80) % WIDTH)
                pts = [(sx, 0)]
                yy = 0
                while yy < HEIGHT * 0.6:
                    yy += 30
                    sx += random.randint(-25, 25)
                    pts.append((sx, yy))
                pygame.draw.lines(self.screen, (220, 230, 255), False, pts, 2)
            # 雨幕
            for i in range(60):
                x = (i * 47 + t * 200) % WIDTH
                y = (i * 89 + t * 600) % HEIGHT
                pygame.draw.line(self.screen, (140, 170, 210),
                                 (int(x), int(y)), (int(x - 4), int(y + 14)), 1)

        elif theme == "dark":
            # 黑暗深渊：远处黑洞 + 稀疏星辰 + 深邃阴影
            # 远处黑洞
            cx, cy = WIDTH * 0.7, HEIGHT * 0.35
            for r in range(140, 30, -20):
                a = int(40 * intensity * (1 - r / 140))
                g = get_glow(r, (60, 30, 90), alpha=a)
                self.screen.blit(g, g.get_rect(center=(int(cx), int(cy))),
                                 special_flags=pygame.BLEND_RGB_ADD)
            pygame.draw.circle(self.screen, (0, 0, 0), (int(cx), int(cy)), 36)
            # 吸积盘
            for k in range(3):
                rr = 50 + k * 18
                pts = []
                for a in range(0, 360, 18):
                    ar = math.radians(a + t * (30 - k * 8))
                    pts.append((cx + math.cos(ar) * rr, cy + math.sin(ar) * rr * 0.35))
                if len(pts) > 2:
                    pygame.draw.polygon(self.screen, (80 + k * 20, 40, 120),
                                        pts, 1)
            # 稀疏远景星辰
            for i in range(20):
                x = (i * 311) % WIDTH
                y = (i * 197) % HEIGHT
                if (i * 7) % 5 == 0:
                    tw = 0.4 + 0.6 * (0.5 + 0.5 * math.sin(t * 1.5 + i))
                    pygame.draw.circle(self.screen, (200, 200, 240),
                                       (int(x), int(y)), 1)

        elif theme == "crystal":
            # 水晶洞：水晶柱 + 矿脉反光 + 晶簇
            # 远处水晶柱
            for i in range(8):
                x = (i * 137 + 60) % WIDTH
                h = 70 + (i * 31) % 90
                base_y = HEIGHT - 30
                col = (120 + (i * 20) % 60, 180 + (i * 13) % 50, 230)
                pygame.draw.polygon(self.screen, col,
                                    [(x, base_y), (x - 22, base_y - h * 0.6),
                                     (x - 8, base_y - h), (x + 8, base_y - h),
                                     (x + 22, base_y - h * 0.6)])
                # 高光
                pygame.draw.polygon(self.screen, (220, 240, 255),
                                    [(x, base_y), (x - 6, base_y - h * 0.6), (x, base_y - h)])
            # 晶簇光斑
            for i in range(10):
                x = (i * 173 + t * 12) % WIDTH
                y = HEIGHT * 0.4 + (i * 67) % (HEIGHT * 0.4)
                tw = 0.5 + 0.5 * math.sin(t * 2 + i)
                g = get_glow(18, (200, 230, 255), alpha=int(140 * tw * intensity))
                self.screen.blit(g, g.get_rect(center=(int(x), int(y))),
                                 special_flags=pygame.BLEND_RGB_ADD)

        elif theme == "magma":
            # 熔岩海：熔岩流 + 喷发 + 火山岩
            # 底部熔岩海
            lava_y = HEIGHT - 80
            pygame.draw.rect(self.screen, (90, 20, 10), (0, lava_y, WIDTH, 80))
            # 熔岩表面波纹
            for i in range(3):
                pts = [(0, lava_y + i * 20)]
                for x in range(0, WIDTH + 40, 40):
                    pts.append((x, lava_y + i * 20 + math.sin(x * 0.03 + t * 2 + i) * 6))
                pts.append((WIDTH, lava_y + i * 20 + 30))
                pts.append((0, lava_y + i * 20 + 30))
                col = (200 + i * 20, 60 + i * 30, 20)
                pygame.draw.polygon(self.screen, col, pts)
            # 熔岩光斑
            for i in range(15):
                x = (i * 113 + t * 18) % WIDTH
                y = lava_y + (i * 7) % 60
                g = get_glow(20, (255, 150, 50), alpha=int(180 * intensity))
                self.screen.blit(g, g.get_rect(center=(int(x), int(y))),
                                 special_flags=pygame.BLEND_RGB_ADD)
            # 喷发火球
            for i in range(4):
                x = (i * 263 + 130) % WIDTH
                phase = (t * 1.3 + i * 0.7) % 2.5
                if phase < 1.5:
                    y = lava_y - phase * 120
                    r = max(4, 16 - int(phase * 6))
                    g = get_glow(r * 2, (255, 100, 40), alpha=int(200 * intensity))
                    self.screen.blit(g, g.get_rect(center=(int(x), int(y))),
                                     special_flags=pygame.BLEND_RGB_ADD)
            # 漂浮火山岩
            for i in range(8):
                x = (i * 191 + t * 10) % WIDTH
                y = lava_y - 30 - (i * 23) % 100
                pygame.draw.circle(self.screen, (50, 30, 25), (int(x), int(y)), 8)
                pygame.draw.circle(self.screen, (90, 50, 40), (int(x), int(y)), 8, 1)

        elif theme == "aurora":
            # 极光带：流动极光 + 星空 + 冰原
            # 流动极光（多带）
            for band in range(3):
                pts_top = []
                pts_bot = []
                col = [(90, 255, 200), (120, 200, 255), (180, 255, 220)][band]
                for x in range(0, WIDTH + 20, 20):
                    base_y = HEIGHT * 0.18 + band * 50
                    wave = math.sin(x * 0.008 + t * (0.8 + band * 0.3)) * 40
                    wave2 = math.sin(x * 0.02 + t * 1.5 + band) * 18
                    pts_top.append((x, base_y + wave + wave2))
                    pts_bot.append((x, base_y + wave + wave2 + 60 + band * 10))
                pts = pts_top + list(reversed(pts_bot))
                surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                pygame.draw.polygon(surf, (*col, int(50 * intensity)), pts)
                self.screen.blit(surf, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
            # 冰原
            pygame.draw.rect(self.screen, (20, 50, 70), (0, HEIGHT - 60, WIDTH, 60))
            pygame.draw.line(self.screen, (140, 200, 240), (0, HEIGHT - 60), (WIDTH, HEIGHT - 60), 2)
            # 星空
            for i in range(40):
                x = (i * 137) % WIDTH
                y = (i * 89) % (HEIGHT * 0.5)
                tw = 0.4 + 0.6 * (0.5 + 0.5 * math.sin(t * 1.2 + i))
                pygame.draw.circle(self.screen, (220, 230, 255),
                                   (int(x), int(y)), 1 if tw < 0.7 else 2)

        elif theme == "hell":
            # 刺球地狱：地面火焰 + 骷髅堆 + 血雾
            # 地面火焰
            for x in range(0, WIDTH, 30):
                fh = 30 + math.sin(x * 0.05 + t * 4) * 12 + math.sin(x * 0.13 + t * 7) * 8
                col = (255, 80 + int(math.sin(x * 0.1 + t * 3) * 40), 30)
                pygame.draw.polygon(self.screen, col,
                                    [(x, HEIGHT), (x + 6, HEIGHT - fh - 8),
                                     (x + 15, HEIGHT - fh), (x + 24, HEIGHT - fh - 6),
                                     (x + 30, HEIGHT)])
            # 地面火光
            g = get_glow(380, (255, 80, 30), alpha=int(80 * intensity))
            self.screen.blit(g, g.get_rect(center=(WIDTH // 2, HEIGHT + 100)),
                             special_flags=pygame.BLEND_RGB_ADD)
            # 骷髅堆
            for i in range(6):
                x = (i * 197 + 80) % WIDTH
                y = HEIGHT - 35
                pygame.draw.circle(self.screen, (180, 180, 170), (int(x), int(y)), 12)
                pygame.draw.circle(self.screen, (40, 20, 20), (int(x - 4), int(y - 2)), 3)
                pygame.draw.circle(self.screen, (40, 20, 20), (int(x + 4), int(y - 2)), 3)
                pygame.draw.rect(self.screen, (180, 180, 170), (int(x - 8), int(y + 6), 16, 8))
            # 血雾
            for i in range(8):
                x = (i * 167 + t * 14) % WIDTH
                y = HEIGHT * 0.4 + (i * 53) % (HEIGHT * 0.4)
                g = get_glow(80, (180, 30, 30), alpha=int(40 * intensity))
                self.screen.blit(g, g.get_rect(center=(int(x), int(y))),
                                 special_flags=pygame.BLEND_RGB_ADD)

        elif theme == "void":
            # 虚渊吞噬：虚空裂缝 + 紫光 + 空间扭曲
            # 多条虚空裂缝
            for i in range(5):
                cx = (i * 251 + t * 18) % WIDTH
                cy = (i * 137 + 60) % HEIGHT
                length = 80 + (i * 23) % 60
                ang = t * 0.5 + i * 1.2
                ex = cx + math.cos(ang) * length
                ey = cy + math.sin(ang) * length
                # 裂缝主体
                for k in range(3):
                    w = 6 - k * 2
                    col = (180 + k * 20, 80 + k * 30, 220)
                    pygame.draw.line(self.screen, col, (int(cx), int(cy)), (int(ex), int(ey)), w)
                # 裂缝光晕
                g = get_glow(40, (180, 80, 220), alpha=int(120 * intensity))
                self.screen.blit(g, g.get_rect(center=(int((cx + ex) / 2), int((cy + ey) / 2))),
                                 special_flags=pygame.BLEND_RGB_ADD)
            # 空间扭曲环
            for i in range(3):
                cx = WIDTH * (0.3 + i * 0.2)
                cy = HEIGHT * 0.5 + math.sin(t + i) * 50
                rr = 40 + i * 30 + math.sin(t * 2 + i) * 10
                pygame.draw.circle(self.screen, (140, 80, 200),
                                   (int(cx), int(cy)), int(rr), 1)

        elif theme == "vortex":
            # 裂时乱序：时间漩涡 + 空间环 + 时间碎片
            cx, cy = WIDTH * 0.5, HEIGHT * 0.5
            # 时间漩涡（多层）
            for layer in range(6):
                rr = 60 + layer * 50
                ang = t * (0.4 - layer * 0.05) + layer * 0.5
                col = (180 + layer * 10, 100 + layer * 20, 240 - layer * 14)
                pts = []
                for k in range(36):
                    a = ang + k * (math.tau / 36)
                    wave = math.sin(k * 0.5 + t * 2 + layer) * 15
                    pts.append((cx + math.cos(a) * (rr + wave),
                                cy + math.sin(a) * (rr + wave) * 0.6))
                if len(pts) > 2:
                    surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                    pygame.draw.polygon(surf, (*col, int(30 * intensity)), pts, 1)
                    self.screen.blit(surf, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
            # 时间碎片（漂浮菱形）
            for i in range(12):
                x = (i * 167 + t * 25) % WIDTH
                y = (i * 89 + math.sin(t + i) * 80) % HEIGHT
                ang = t * 1.5 + i
                size = 6 + (i % 3) * 3
                pts = [(x + math.cos(ang) * size, y + math.sin(ang) * size),
                       (x + math.cos(ang + 1.57) * size, y + math.sin(ang + 1.57) * size),
                       (x + math.cos(ang + 3.14) * size, y + math.sin(ang + 3.14) * size),
                       (x + math.cos(ang + 4.71) * size, y + math.sin(ang + 4.71) * size)]
                pygame.draw.polygon(self.screen, (220, 180, 255), pts)
                pygame.draw.polygon(self.screen, (255, 220, 255), pts, 1)

        elif theme == "ruin":
            # 终殁废墟：废墟石柱 + 断壁残垣 + 火焰残烬
            # 远处废墟石柱
            for i in range(7):
                x = (i * 167 + 50) % WIDTH
                h = 80 + (i * 29) % 100
                base_y = HEIGHT - 30
                # 主柱
                pygame.draw.rect(self.screen, (80, 60, 50),
                                 (int(x - 14), int(base_y - h), 28, h))
                # 顶部断茬
                pygame.draw.polygon(self.screen, (80, 60, 50),
                                    [(x - 14, base_y - h), (x - 8, base_y - h - 14),
                                     (x + 2, base_y - h - 6), (x + 14, base_y - h - 12),
                                     (x + 14, base_y - h)])
                # 裂纹
                pygame.draw.line(self.screen, (40, 30, 25),
                                 (int(x), int(base_y - h * 0.7)),
                                 (int(x + 6), int(base_y - h * 0.3)), 1)
            # 断壁
            for i in range(4):
                x = (i * 263 + 100) % WIDTH
                y = HEIGHT - 60
                w = 50 + (i * 23) % 40
                pygame.draw.rect(self.screen, (60, 45, 38), (int(x), int(y), w, 30))
                pygame.draw.polygon(self.screen, (60, 45, 38),
                                    [(x, y), (x + w * 0.3, y - 12),
                                     (x + w * 0.7, y - 6), (x + w, y)])
            # 火焰残烬
            for i in range(10):
                x = (i * 137 + t * 18) % WIDTH
                y = (HEIGHT - t * 30 - i * 67) % HEIGHT
                g = get_glow(8, (255, 130, 60), alpha=int(140 * intensity))
                self.screen.blit(g, g.get_rect(center=(int(x), int(y))),
                                 special_flags=pygame.BLEND_RGB_ADD)
            # 远处废墟剪影
            pts = [(0, HEIGHT - 30)]
            for x in range(0, WIDTH + 40, 30):
                h = 20 + (math.sin(x * 0.04) * 0.5 + 0.5) * 60
                pts.append((x, HEIGHT - 30 - h))
            pts.append((WIDTH, HEIGHT - 30))
            pts.append((WIDTH, HEIGHT))
            pts.append((0, HEIGHT))
            pygame.draw.polygon(self.screen, (30, 22, 18), pts)

        elif theme == "singularity":
            # 禁域真源：奇点光芒 + 能量环 + 宇宙本源
            cx, cy = WIDTH * 0.5, HEIGHT * 0.5
            # 奇点核心光芒
            for r in range(180, 30, -15):
                a = int(40 * intensity * (1 - r / 180))
                col = (230, 120, 255) if r > 90 else (255, 180, 255)
                g = get_glow(r, col, alpha=a)
                self.screen.blit(g, g.get_rect(center=(int(cx), int(cy))),
                                 special_flags=pygame.BLEND_RGB_ADD)
            # 奇点核心
            pygame.draw.circle(self.screen, (255, 230, 255), (int(cx), int(cy)), 14)
            pygame.draw.circle(self.screen, (255, 255, 255), (int(cx), int(cy)), 6)
            # 能量环（多层旋转）
            for layer in range(5):
                rr = 60 + layer * 35
                ang = t * (0.6 - layer * 0.08) + layer * 0.7
                col = (230 - layer * 14, 120 + layer * 18, 255 - layer * 10)
                pts = []
                for k in range(30):
                    a = ang + k * (math.tau / 30)
                    rr_w = rr + math.sin(k * 0.7 + t * 3 + layer) * 12
                    pts.append((cx + math.cos(a) * rr_w,
                                cy + math.sin(a) * rr_w * 0.55))
                if len(pts) > 2:
                    pygame.draw.polygon(self.screen, col, pts, 2)
            # 漂浮能量粒子
            for i in range(16):
                ang = t * 0.5 + i * (math.tau / 16)
                rad = 200 + math.sin(t * 1.5 + i) * 50
                x = cx + math.cos(ang) * rad
                y = cy + math.sin(ang) * rad * 0.6
                g = get_glow(10, (255, 200, 255), alpha=int(180 * intensity))
                self.screen.blit(g, g.get_rect(center=(int(x), int(y))),
                                 special_flags=pygame.BLEND_RGB_ADD)

    # ---- 关卡重置 ----
    def reset_level(self):
        # 无尽模式：用合成关卡配置，不读取主线/副本关卡表
        if getattr(self, "_endless_mode", False):
            wv = getattr(self, "_endless_wave", 1)
            lv = {"name": f"无尽·波次{wv}", "bg": (8, 4, 18),
                  "theme": "void", "speed": 1.0, "danger": 0.55, "pu": 1.4,
                  "goal": 99999, "node": NEON_PURPLE, "desc": "无尽模式·永无止境",
                  "difficulty": 1.0 + wv * 0.08, "chaos": 0.0}
        elif getattr(self, "_boss_mode", False):
            # Q9：BOSS模式 - 使用恐怖背景
            bl = getattr(self, "_boss_level", 1)
            lv = {"name": f"BOSS·第{bl}关", "bg": (30, 6, 10),
                  "theme": "hell", "speed": 1.0 + bl * 0.03, "danger": 0.6,
                  "pu": 1.0, "goal": 1, "node": (255, 60, 60),
                  "desc": f"BOSS挑战 第{bl}关", "difficulty": 1.5 + bl * 0.1,
                  "chaos": 0.1 + bl * 0.02, "horror": 0.8}
        else:
            lv = self._get_levels()[self.current_level]
        # 进入关卡时清除退出确认状态，避免 MAP 下残留的 _confirm_exit 导致 ESC 第一次不暂停
        self._confirm_exit = False
        # 非无尽模式：累计游玩局数（用于成就统计）
        if not getattr(self, "_endless_mode", False):
            self._games_played = getattr(self, "_games_played", 0) + 1
        # 玩家：1P 居中；2P 左右分置
        if self.num_players == 2:
            self.player = Player(WIDTH * 0.35, HEIGHT / 2, NEON_CYAN, pid=1)
            self.player2 = Player(WIDTH * 0.65, HEIGHT / 2, NEON_PINK, pid=2)
            self.players = [self.player, self.player2]
        else:
            self.player = Player(WIDTH / 2, HEIGHT / 2, self._player_color(), pid=1)
            self.player2 = None
            self.players = [self.player]
        # 附上各自皮肤（通过 p.skin 属性，优先于 self.active_skin）
        if self.active_skin and self.active_skin in self.owned_skins:
            self.player.skin = self.active_skin
        if self.num_players == 2:
            # P2：如果已单独选皮肤则用其皮肤，否则跟随 P1
            p2_sk = self.active_skin_p2 if (self.active_skin_p2 and self.active_skin_p2 in self.owned_skins) else getattr(self.player, "skin", None)
            if p2_sk and p2_sk in self.owned_skins:
                self.player2.skin = p2_sk
        for p in self.players:
            p.spawn_flash = 1.0
        self.stars = []
        self.powerups = []
        self.particles = []
        self.bullets = []
        self.sweeps = []  # 光刃挥砍特效 {"x","y","ang","r","life","max"}
        self.blade_spins = []  # 光刃 360° 旋刃 {"owner","angle","life","max","r"}
        self.tri_bombs = []  # 三色红球炸弹 {"x","y","vx","vy","timer","max","owner","_dead"}
        self.frost_pellets = []  # 霜冻冰粒 {"x","y","vx","vy","timer","r","owner","_dead"}
        self.thunder_balls = []  # 雷霆电球 {"x","y","vx","vy","timer","r","owner","_dead"}
        self.void_holes = []  # 螺旋/多向黑洞 {"x","y","vx","vy","timer","max","r","owner","_dead"}
        self.thunder_field_timer = 0.0  # 雷霆右键雷电场剩余时间
        self.blackhole = None
        self.split_cells = []
        self.split_angle = 0.0
        self.coin_pickups = []
        self.coin_spawn_timer = 4.0
        self.skin_tick = 0.0  # 皮肤技能周期计时
        self.combo = 0
        self.combo_timer = 0.0
        self.combo_peak = 0
        self.level_eaten = 0
        self.level = self.current_level + 1
        # Q9：每局皮肤切换无限制
        self._pending_skin = None
        self.spawn_timer = 0.0
        diff = float(lv.get("difficulty", 1.0))
        self.spawn_interval = max(0.25, 0.9 / (0.7 + 0.4 * diff))
        self._max_stars = int(140 * (0.8 + 0.35 * diff))
        self.powerup_timer = 7.0
        self.powerup_interval = 11.0 / lv["pu"]
        # 无尽模式：波次生成跟踪 + 更频繁的道具
        if getattr(self, "_endless_mode", False):
            self._endless_spawned = 0
            self._endless_killed = 0
            self._endless_wave_target = 3 + int(getattr(self, "_endless_wave", 1) * 1.2)
            self.powerup_interval = max(4.0, self.powerup_interval * 0.6)
            self.powerup_timer = 4.0
        self.time_slow_timer = 0.0
        self.double_timer = 0.0
        self.lives = 3
        self.shake = 0.0
        self.over_timer = 0.0
        self.lc_timer = 0.0
        self.time_alive = 0.0
        self.bg_color = lv["bg"]
        # 氛围粒子与恐怖参数
        self.ambient = []
        self.ambient_timer = 0.0
        self.heartbeat_timer = 1.2
        self.lightning_timer = random.uniform(3.0, 6.0)
        self.lightning_alpha = 0.0
        self._init_ambient(lv["theme"])
        self._update_horror()
        # Q9：BOSS模式 - 生成Boss和小怪
        if getattr(self, "_boss_mode", False):
            self._boss_spawn()
            self._boss_spawning = False  # 标记Boss已生成

    # ---- 生成星体 ----
    def spawn_star(self):
        # 超过星体上限就不生成了（每关上限被副本难度扩容）
        max_stars = getattr(self, "_max_stars", 140)
        if len(self.stars) >= max_stars:
            return
        lv = self._get_levels()[self.current_level]
        side = random.randint(0, 3)
        if side == 0:
            x, y = random.uniform(0, WIDTH), -40
        elif side == 1:
            x, y = random.uniform(0, WIDTH), HEIGHT + 40
        elif side == 2:
            x, y = -40, random.uniform(0, HEIGHT)
        else:
            x, y = WIDTH + 40, random.uniform(0, HEIGHT)
        tx = random.uniform(WIDTH * 0.2, WIDTH * 0.8)
        ty = random.uniform(HEIGHT * 0.2, HEIGHT * 0.8)
        ang = math.atan2(ty - y, tx - x)
        diff = float(lv.get("difficulty", 1.0))
        speed = (random.uniform(60, 120) + self.level * 6) * lv["speed"] * math.sqrt(diff)
        vx = math.cos(ang) * speed
        vy = math.sin(ang) * speed

        pr = max((p.r for p in self.players if p.alive), default=18.0)
        danger_chance = clamp((lv["danger"] + self.level * 0.02) * (0.85 + 0.15 * diff), 0.1, 0.85)
        if random.random() < danger_chance:
            if random.random() < 0.55:
                r = (random.uniform(pr * 1.15, pr * 1.9) + 4) * (0.9 + 0.1 * diff)
            else:
                r = random.uniform(max(6, pr * 0.45), pr * 0.95) * (0.9 + 0.1 * diff)
            # 按相对强度划分 4 个敌方等级（凶恶邪恶配色）
            ratio = r / max(pr, 8.0)
            if ratio >= 1.6:
                tier, col = 3, (90, 10, 25)        # 深渊血魔：暗红黑
            elif ratio >= 1.1:
                tier, col = 2, (120, 40, 160)      # 邪紫恶灵
            elif ratio >= 0.7:
                tier, col = 1, (180, 60, 30)       # 锈血刺魔
            else:
                tier, col = 0, (200, 50, 70)       # 猩红小鬼
            # 种族：尖刺/病毒/三球/双球/虫群/长蛇/恐怖（等级越高越易出现复合体）
            kind_roll = random.random()
            # 副本可额外配置 snake_ratio 作为长蛇概率（否则默认按关卡）
            override_snake = lv.get("snake_ratio", None)
            # c7/t7：恐怖/新种出现概率（主线 >=6 或副本 >=1：开启；深渊副本更高）
            is_dungeon = getattr(self, "_dungeon_mode", False)
            dungeon_lv = getattr(self, "_dungeon_level", 0)
            horror_chance = 0.0
            # t7：新种概率（幽灵/牛魔王/玄武龟/蜈蚣/蜘蛛/毒蛇）
            oxdemon_chance = 0.0
            ghost_chance = 0.0
            turtle_chance = 0.0
            spider_chance = 0.0
            centipede_chance = 0.0
            fangshe_chance = 0.0
            if is_dungeon and dungeon_lv >= 1:
                horror_chance = min(0.22, 0.07 + dungeon_lv * 0.015)
                oxdemon_chance = min(0.12, 0.04 + dungeon_lv * 0.012)
                ghost_chance = min(0.15, 0.05 + dungeon_lv * 0.012)
                turtle_chance = min(0.10, 0.03 + dungeon_lv * 0.008)
                spider_chance = min(0.20, 0.08 + dungeon_lv * 0.012)
                centipede_chance = min(0.12, 0.04 + dungeon_lv * 0.009)
                fangshe_chance = min(0.10, 0.03 + dungeon_lv * 0.008)
            else:
                if self.current_level >= 6:
                    horror_chance = min(0.14, 0.04 + (self.current_level - 6) * 0.01)
                if self.current_level >= 5:
                    oxdemon_chance = min(0.08, 0.015 + (self.current_level - 5) * 0.008)
                    ghost_chance = min(0.09, 0.02 + (self.current_level - 5) * 0.008)
                    turtle_chance = min(0.06, 0.01 + (self.current_level - 5) * 0.006)
                    fangshe_chance = min(0.07, 0.015 + (self.current_level - 5) * 0.007)
                if self.current_level >= 4:
                    spider_chance = min(0.12, 0.03 + (self.current_level - 4) * 0.009)
                    centipede_chance = min(0.08, 0.015 + (self.current_level - 4) * 0.007)
            if override_snake is not None:
                snake_chance = override_snake
                worm_chance = max(0.0, override_snake * 0.85)
            else:
                # 虫群出现概率：随关卡升高（5 关后开始出现，最高 18%）
                worm_chance = 0.0
                snake_chance = 0.0
                if self.current_level >= 4:
                    worm_chance = min(0.18, 0.05 + (self.current_level - 4) * 0.012)
                if self.current_level >= 5:
                    # 长蛇出现概率：随关卡升高（比虫群略稀有，约为虫群的 60%）
                    snake_chance = min(0.11, 0.03 + (self.current_level - 5) * 0.009)
            roll_special = random.random()
            spawned_snake = False
            # 特殊：snake / worm / horror / oxdemon / ghost / turtle / spider / centipede / fangshe / normal
            snake_end = snake_chance
            worm_end = snake_end + worm_chance
            horror_end = worm_end + horror_chance
            oxdemon_end = horror_end + oxdemon_chance
            ghost_end = oxdemon_end + ghost_chance
            turtle_end = ghost_end + turtle_chance
            spider_end = turtle_end + spider_chance
            cent_end = spider_end + centipede_chance
            fang_end = cent_end + fangshe_chance
            if roll_special < snake_end:
                # ---- 直接生成整条多球节长蛇，返回蛇头；每节都是独立 Star 加入 self.stars ----
                head = self._spawn_snake(x, y, vx, vy, r, tier=tier)
                if head is not None:
                    spawned_snake = True
                    if tier >= 3:
                        self._play("warn")
            elif roll_special < worm_end:
                kind = "worm"
                col = (100, 220, 90)  # 虫群嫩绿
                # 虫子体型偏长条
                r = max(r, pr * 0.7)
                self.stars.append(Star(x, y, vx, vy, r, col, True, tier=tier, kind=kind))
            elif roll_special < horror_end:
                # c7：恐怖外形敌人（血红骷髅头 + 双牛角 + 嘴部尖牙 + 黑紫气息）
                kind = "horror"
                col = (150, 10, 30)
                r = max(r, pr * 0.85)
                s = Star(x, y, vx, vy, r, col, True, tier=tier, kind=kind)
                self.stars.append(s)
                if tier >= 2:
                    self._play("warn")
            elif roll_special < oxdemon_end:
                # t7：牛魔王球体 - 双巨大牛角+鼻环+厚皮+红鬃
                kind = "oxdemon"
                col = (150, 60, 30)
                r = max(r, pr * 1.05)
                s = Star(x, y, vx, vy, r, col, True, tier=tier, kind=kind)
                self.stars.append(s)
                if tier >= 2:
                    self._play("warn")
            elif roll_special < ghost_end:
                # t7：幽灵球 - 半透明飘动感+鬼脸+寒气+穿墙追玩家
                kind = "ghost"
                col = (200, 220, 255)
                r = max(r, pr * 0.95)
                s = Star(x, y, vx, vy, r, col, True, tier=tier, kind=kind)
                self.stars.append(s)
                if tier >= 2:
                    self._play("warn")
            elif roll_special < turtle_end:
                # t7：玄武龟球 - 六边形甲壳+头尾四爪+慢但高血量
                kind = "turtle"
                col = (40, 110, 70)
                r = max(r, pr * 1.2)
                s = Star(x, y, vx, vy, r, col, True, tier=tier, kind=kind)
                # 龟天生慢一点
                s.vx *= 0.55; s.vy *= 0.55
                self.stars.append(s)
                if tier >= 2:
                    self._play("warn")
            elif roll_special < spider_end:
                # t7：蜘蛛球 - 8 条长腿+红眼+黑紫身体+腹部斑纹
                kind = "spider"
                col = (60, 10, 30)
                r = max(r, pr * 0.85)
                s = Star(x, y, vx, vy, r, col, True, tier=tier, kind=kind)
                self.stars.append(s)
            elif roll_special < cent_end:
                # t7：蜈蚣球 - 12节黑紫长身+每节双毒腿+头部毒牙
                kind = "centipede"
                col = (150, 20, 170)
                r = max(r, pr * 0.7)
                s = Star(x, y, vx, vy, r, col, True, tier=tier, kind=kind)
                self.stars.append(s)
            elif roll_special < fang_end:
                # t7：毒蛇 fangshe - 单球版毒蛇（周围毒雾+毒牙+血瞳）
                kind = "fangshe"
                col = (160, 220, 30)
                r = max(r, pr * 0.8)
                s = Star(x, y, vx, vy, r, col, True, tier=tier, kind=kind)
                self.stars.append(s)
            else:
                # t7：normal 分支里也加入新种（spider/fangshe/turtle/oxdemon/ghost）
                if tier >= 3:
                    if kind_roll < 0.28:
                        kind = "tri"
                    elif kind_roll < 0.48:
                        kind = "dual"
                    elif kind_roll < 0.62:
                        kind = "oxdemon"
                    elif kind_roll < 0.78:
                        kind = "ghost"
                    elif kind_roll < 0.9:
                        kind = "turtle"
                    else:
                        kind = "virus"
                elif tier == 2:
                    if kind_roll < 0.28:
                        kind = "dual"
                    elif kind_roll < 0.48:
                        kind = "tri"
                    elif kind_roll < 0.62:
                        kind = "turtle"
                    elif kind_roll < 0.8:
                        kind = "fangshe"
                    else:
                        kind = "virus"
                elif tier == 1:
                    if kind_roll < 0.3:
                        kind = "virus"
                    elif kind_roll < 0.5:
                        kind = "dual"
                    elif kind_roll < 0.72:
                        kind = "spider"
                    elif kind_roll < 0.86:
                        kind = "fangshe"
                    else:
                        kind = "spike"
                else:
                    if kind_roll < 0.55:
                        kind = "spike"
                    elif kind_roll < 0.78:
                        kind = "virus"
                    elif kind_roll < 0.92:
                        kind = "spider"
                    else:
                        kind = "fangshe"
                # 种族主色微调
                if kind == "virus":
                    col = (60, 180, 80)        # 病毒绿
                elif kind == "tri":
                    col = (140, 50, 200)       # 三球邪紫
                elif kind == "dual":
                    col = (200, 120, 40)       # 双球锈橙
                elif kind == "worm":
                    col = (100, 220, 90)       # 虫群嫩绿
                elif kind == "spider":
                    col = (60, 10, 30)         # 蜘蛛暗黑
                elif kind == "centipede":
                    col = (150, 20, 170)       # 蜈蚣紫黑
                elif kind == "ghost":
                    col = (200, 220, 255)      # 幽灵白蓝
                elif kind == "turtle":
                    col = (40, 110, 70)        # 玄武龟墨绿
                elif kind == "oxdemon":
                    col = (150, 60, 30)        # 牛魔王棕红
                elif kind == "fangshe":
                    col = (160, 220, 30)       # 毒蛇绿
                ns = Star(x, y, vx, vy, r, col, True, tier=tier, kind=kind)
                # c10：Tier>=2 危险敌人 35% 概率轻度追踪玩家（新 kind 已在 chase_map 默认配置）
                if tier >= 2 and ns.chase_player == 0 and random.random() < 0.35:
                    ns.chase_player = 1
                # 龟天生慢
                if kind == "turtle":
                    ns.vx *= 0.55; ns.vy *= 0.55
                self.stars.append(ns)
            if not spawned_snake and tier >= 3:
                self._play("warn")
        else:
            r = random.uniform(max(5, pr * 0.25), pr * 0.92)
            color = random.choice(STAR_COLORS)
            self.stars.append(Star(x, y, vx, vy, r, color, False))
        # Q8：副本模式敌方球体生命值加厚（×2.0，随副本层数递增）
        if getattr(self, "_dungeon_mode", False) and self.stars:
            last = self.stars[-1]
            if last.danger:
                dun_lv = getattr(self, "_dungeon_level", 1)
                mul = 2.0 + min(1.5, dun_lv * 0.12)
                last.max_hp = int(last.max_hp * mul)
                last.hp = last.max_hp

    # ---- 生成道具 ----
    def spawn_powerup(self):
        types = ["SHIELD", "MAGNET", "TIME", "BOMB", "SHRINK", "SCORE",
                 "LIFE", "PHANTOM", "BLACKHOLE", "DOUBLE", "GUN", "SWORD"]
        # LIFE 从 1 权重提升到 4（约提升到 ~15%+ 出现率，更容易捡到命）
        weights = [2, 2, 2, 1, 1, 2, 4, 2, 1, 2, 2, 2]
        ptype = random.choices(types, weights=weights)[0]
        side = random.randint(0, 3)
        if side == 0:
            x, y = random.uniform(WIDTH * 0.2, WIDTH * 0.8), -30
        elif side == 1:
            x, y = random.uniform(WIDTH * 0.2, WIDTH * 0.8), HEIGHT + 30
        elif side == 2:
            x, y = -30, random.uniform(HEIGHT * 0.2, HEIGHT * 0.8)
        else:
            x, y = WIDTH + 30, random.uniform(HEIGHT * 0.2, HEIGHT * 0.8)
        tx = random.uniform(WIDTH * 0.3, WIDTH * 0.7)
        ty = random.uniform(HEIGHT * 0.3, HEIGHT * 0.7)
        ang = math.atan2(ty - y, tx - x)
        sp = random.uniform(40, 70)
        self.powerups.append(PowerUp(x, y, math.cos(ang) * sp, math.sin(ang) * sp, ptype))

    # ---- 生成金币 ----
    def _spawn_coin(self):
        x = random.uniform(WIDTH * 0.15, WIDTH * 0.85)
        y = random.uniform(HEIGHT * 0.18, HEIGHT * 0.82)
        self.coin_pickups.append({"x": x, "y": y, "phase": random.uniform(0, math.tau),
                                  "life": 12.0, "_dead": False})

    # ---- 粒子 ----
    def burst(self, x, y, color, count, speed, size=3.0, life=0.5):
        for _ in range(count):
            a = random.uniform(0, math.tau)
            s = random.uniform(speed * 0.3, speed)
            self.particles.append(Particle(
                x, y, math.cos(a) * s, math.sin(a) * s,
                random.uniform(life * 0.6, life), color,
                random.uniform(size * 0.6, size * 1.4)))

    # ---- 音效 ----
    _MISSING_WARNED = set()

    def _play(self, name):
        if self.muted:
            return
        if not self.sounds.ok:
            # 首次发现音频失效时尝试重建一次
            if not getattr(self, "_rebuilt_once", False):
                self._rebuilt_once = True
                try:
                    self._rebuild_sound()
                except Exception:
                    return
                if not self.sounds.ok:
                    return
            else:
                return
        if name not in self.sounds.sounds:
            if name not in Game._MISSING_WARNED:
                Game._MISSING_WARNED.add(name)
                print(f"[_play] 音效未注册: {name}")
            return
        self.sounds.play(name)

    # ---- 手势输入（食指控制，中心偏右，相对速度） ----
    def _update_hand_input(self):
        if not self.tracker.available or not self.tracker.running:
            self._cam_frame = None
            self._last_lms = None
            self.hand_vel = (0.0, 0.0)
            self.hand_dash = False
            return
        frame, lms = self.tracker.get()
        self._cam_frame = frame
        if lms:
            # 食指尖(8) 相对画面中心(0.5, 0.5) 的偏移 = 速度向量
            dx = lms[8].x - 0.5
            dy = lms[8].y - 0.5
            mag = math.hypot(dx, dy)
            dead = 0.06  # 小死区，手原地即可居中
            if mag > dead:
                scale = ((mag - dead) / (1.0 - dead)) ** 1.2
                nx, ny = dx / mag, dy / mag
                speed = 820 * scale
                self.hand_vel = (nx * speed, ny * speed)
            else:
                self.hand_vel = (0.0, 0.0)
            self.hand_dash = is_open_palm(lms)  # 伸掌 = 加速
            # 握拳 = 皮肤专有技能（边缘触发，避免长按连续触发）
            fist_now = is_fist(lms)
            if fist_now and not getattr(self, "_fist_prev", False):
                # 在手势模式下：朝玩家位置释放技能
                if self.state == self.PLAYING and self.player.alive:
                    p = self.player
                    self._skin_skill_at(p, p.x, p.y, who="p1")
            self._fist_prev = fist_now
            self._last_lms = lms
        else:
            self.hand_vel = (0.0, 0.0)
            self.hand_dash = False
            self._last_lms = None

    def _toggle_control(self):
        # 单人模式循环：鼠标 -> 手势 -> 方向键 -> 鼠标
        if self.num_players != 1:
            return
        order = ["mouse", "hand", "arrow"]
        # 手势不可用时跳过
        if not self.tracker.available and "hand" in order:
            order = ["mouse", "arrow"]
        try:
            i = order.index(self.control_mode)
        except ValueError:
            i = -1
        nxt = order[(i + 1) % len(order)]
        # 离开手势模式时关闭摄像头
        if self.control_mode == "hand" and nxt != "hand":
            self.tracker.pause()
        if nxt == "hand":
            self.tracker.resume()
        self.control_mode = nxt
        self._play("tick")

    # ---- 主循环 ----
    def run(self):
        running = True
        import traceback as _tb
        def _make_tb_str(exc_type, exc, tb):
            import io
            buf = io.StringIO()
            _tb.print_exception(exc_type, exc, tb, file=buf)
            return buf.getvalue()
        def _write_crash(exc_type, exc, tb):
            tb_text = _make_tb_str(exc_type, exc, tb)
            try:
                with open("_exception.log", "w", encoding="utf-8") as f:
                    f.write(tb_text)
                    f.write("\n--- coins=%s state=%s level=%s sk=%s sk2=%s\n" %
                            (getattr(self, "coins", None),
                             getattr(self, "state", None),
                             getattr(self, "current_level", None),
                             getattr(self, "active_skin", None),
                             getattr(self, "active_skin_p2", None)))
            except Exception:
                pass
            return tb_text
        sys.excepthook = lambda et, e, tb: _write_crash(et, e, tb)
        while running:
            try:
                dt = min(self.clock.tick(FPS) / 1000.0, 1 / 30)
                mx, my = pygame.mouse.get_pos()

                # ---- 崩溃停留倒计时（崩溃后还能继续渲染几帧显示异常信息）----
                if self._crash_wait > 0:
                    self._crash_wait -= dt
                    if self._crash_wait <= 0:
                        running = False
                        break

                for e in pygame.event.get():
                    if e.type == pygame.QUIT:
                        running = False
                    elif e.type == pygame.KEYDOWN:
                        # 模态弹窗优先处理键盘（兑换码/导入码输入框）
                        consumed = False
                        if getattr(self, "_modal", None) is not None:
                            consumed = self._modal_key_input(e)
                        if not consumed:
                            running = self._handle_key(e.key) and running
                    elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                        # 模态弹窗优先处理点击
                        mconsumed = False
                        if getattr(self, "_modal", None) is not None:
                            mconsumed = self._modal_click(mx, my)
                        if not mconsumed:
                            self._handle_click(mx, my)
                    elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 3:
                        # 模态弹窗打开时屏蔽右键（避免皮肤技能干扰）
                        if getattr(self, "_modal", None) is None:
                            self._handle_right_click(mx, my)

                # 只有非崩溃时才 update 正常游戏逻辑
                if self._crash_info is None:
                    self._update_hand_input()
                    self._read_keyboard()

                    if self.state == self.PLAYING:
                        self.update(dt, mx, my)
                    elif self.state == self.OVER:
                        self.over_timer += dt
                        arr = self.particles
                        for i in range(len(arr)):
                            it = arr[i]
                            if isinstance(it, tuple) and len(it) == 7:
                                arr[i] = Particle(it[0], it[1], it[2], it[3], it[4], it[5], it[6])
                        for p in self.particles:
                            p.update(dt)
                        self.particles = [p for p in self.particles if p.alive]
                        self._tick_horror(dt)
                    elif self.state == self.LEVEL_COMPLETE:
                        self.lc_timer += dt
                        arr = self.particles
                        for i in range(len(arr)):
                            it = arr[i]
                            if isinstance(it, tuple) and len(it) == 7:
                                arr[i] = Particle(it[0], it[1], it[2], it[3], it[4], it[5], it[6])
                        for p in self.particles:
                            p.update(dt)
                        self.particles = [p for p in self.particles if p.alive]

                    if self._flash_timer > 0:
                        self._flash_timer -= dt
                    # Q7：成就解锁提示倒计时
                    if self._ach_toasts:
                        for t in self._ach_toasts:
                            t["timer"] -= dt
                        self._ach_toasts = [t for t in self._ach_toasts if t["timer"] > 0]

                self.draw(mx, my)
                pygame.display.flip()
            except BaseException as _e:
                tb_text = _write_crash(type(_e), _e, _e.__traceback__)
                short = f"{type(_e).__name__}: {_e}"
                # 尝试保存存档避免丢失进度
                try: self._save_game()
                except Exception: pass
                # 把异常信息装进 _crash_info，主循环会继续渲染显示 5 秒再退出
                try:
                    self._crash_info = (short, tb_text)
                    self._crash_wait = 5.0
                    # 停掉氛围音，避免崩溃后音乐一直响
                    try:
                        if getattr(self, "drone_on", False):
                            self.sounds.stop_drone()
                            self.drone_on = False
                    except Exception:
                        pass
                except Exception:
                    running = False
                    break
        try:
            self.tracker.stop()
        except Exception:
            pass
        try:
            if self.drone_on:
                self.sounds.stop_drone()
        except Exception:
            pass
        try:
            pygame.quit()
        except Exception:
            pass
        sys.exit()

    # ---- 读取键盘速度（方向键 / WASD / 加速键） ----
    def _read_keyboard(self):
        keys = pygame.key.get_pressed()
        sp = 360.0
        # P2：方向键（双人模式）/ 单人方向键模式
        ax = (keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]) * sp
        ay = (keys[pygame.K_DOWN] - keys[pygame.K_UP]) * sp
        self.arrow_vel = (ax, ay)
        # P1：WASD（双人模式）
        wx = (keys[pygame.K_d] - keys[pygame.K_a]) * sp
        wy = (keys[pygame.K_s] - keys[pygame.K_w]) * sp
        self.wasd_vel = (wx, wy)
        # 加速键：P1=V，P2=[（按住生效）— Q2：V 无需大写锁定
        self.p1_dash_key = keys[pygame.K_v]
        self.p2_dash_key = keys[pygame.K_LEFTBRACKET]

    def _handle_key(self, key):
        # ---- 崩溃后：任意键立即退出（用户不想等 5 秒就点任意键/按任意键跳过） ----
        if getattr(self, "_crash_wait", 0) > 0:
            return False
        # ---- ESC 退出确认：MAP 下不再直接退出，弹确认窗 ----
        if key == pygame.K_ESCAPE:
            if self._confirm_exit:
                # 已开确认窗：再按 ESC = 取消退出
                self._confirm_exit = False
                self._play("tick")
                return True
            if self.show_shop:
                self.show_shop = False
                return True
            if self.show_lottery:
                self.show_lottery = False
                self._lottery_revealed = {}
                self._lottery_anim = {}
                return True
            if self.show_help:
                self.show_help = False
                return True
            if getattr(self, "show_settings", False):
                self.show_settings = False
                self._play("tick")
                return True
            if getattr(self, "show_achievements", False):
                self.show_achievements = False
                self._play("tick")
                return True
            if self.state == self.PLAYING:
                self.state = self.PAUSED
            elif self.state == self.PAUSED:
                self.state = self.PLAYING
            elif self.state in (self.OVER, self.LEVEL_COMPLETE, self.VICTORY):
                self._goto_map()
            elif self.state == self.MAP:
                # 不再直接 return False（退出），而是弹确认窗
                self._confirm_exit = True
                self._play("tick")
                return True
            return True
        # ---- 退出确认窗：Y 才退出，N 取消 ----
        if self._confirm_exit:
            # 支持大小写 y/Y
            if key in (pygame.K_y,):
                return False  # running = False
            if key in (pygame.K_n, pygame.K_RETURN, pygame.K_SPACE):
                self._confirm_exit = False
                self._play("tick")
                return True
            # 其他键：忽略
            return True
        if key == pygame.K_F11:
            self._toggle_fullscreen()
            return True
        if key == pygame.K_F3:
            # t6：F3 不再做静音切换，只负责取消 F2 作弊（统一"撤销作弊"功能）
            if getattr(self, "_f2_enabled", False):
                setattr(self, "_infinite_coins", False)
                setattr(self, "_infinite_diamonds", False)
                setattr(self, "_lottery_unlocked", False)
                setattr(self, "_f2_enabled", False)
                # 把金币/钻石从作弊数值降到合理正常的保存值（不剥夺保留的皮肤和关卡解锁）
                if self.coins > 10000:
                    self.coins = 2000
                if self.diamonds > 500:
                    self.diamonds = 50
                self._save_game()
                self._flash_msg = "F3：已取消 F2 全部作弊（无静音）"
                self._flash_timer = 2.4
            else:
                self._flash_msg = "F3：撤销 F2 作弊（未开启 F2）"
                self._flash_timer = 1.5
            return True
        if key == pygame.K_F2:
            # Q4：还原 F2 单键解锁全功能作弊（金币/钻石无限 + 全关卡/皮肤/抽奖解锁）
            self.unlocked = len(LEVELS)
            # 解锁主线+副本
            self.dungeon_unlocked = len(getattr(self, "DUNGEON_LEVELS", LEVELS))
            for sid in SKINS:
                self.owned_skins.add(sid)
            self.coins = 99999  # 金币无限
            self.diamonds = 99999  # 钻石无限
            setattr(self, "_infinite_coins", True)
            setattr(self, "_infinite_diamonds", True)  # 无限钻石
            setattr(self, "_lottery_unlocked", True)
            # 开启 F2 标记：用于 F3 可统一取消
            setattr(self, "_f2_enabled", True)
            self._save_game()
            self._play("buy")
            self._flash_msg = "F2：金币/钻石无限 + 全解锁 + 抽奖全开（F3取消）"
            self._flash_timer = 2.6
            self._check_achievements()
            return True
        if key in (pygame.K_F1, pygame.K_SLASH, pygame.K_QUESTION):
            # 帮助：MAP 和 暂停（PLAYING/PAUSED） 均可开/关
            if self.state in (self.MAP, self.PAUSED, self.PLAYING):
                self.show_help = not self.show_help
                self._play("tick")
            return True
        # 暂停态 按 B / S：打开 皮肤商店（此时切换皮肤不扣血，玩家可以自由买换）
        if self.state == self.PAUSED:
            if key in (pygame.K_b, pygame.K_s):
                # 区分大小写：小写也识别（避免必须大写才开商店，体验不好）
                if self.show_shop:
                    self.show_shop = False
                else:
                    self.show_shop = True
                self._play("tick")
                return True
        # 暂停 / 进行中：数字键 1-9 快速切换已拥有皮肤
        if self.state in (self.PAUSED, self.PLAYING):
            if pygame.K_1 <= key <= pygame.K_9:
                owned = [sid for sid in ALL_SKIN_ORDER if sid in self.owned_skins]
                if owned:
                    idx = (key - pygame.K_1) % len(owned)
                    target = owned[idx]
                    if self.state == self.PAUSED:
                        # 暂停时直接切换皮肤（无需空格确认）
                        self.active_skin = target
                        self._pending_skin = None
                        self._sync_skin_to_player()
                        self._save_game()
                        self._play("buy")
                        nm = SKINS[target][0] if target in SKINS else "默认星辰"
                        self._flash_msg = f"已切换为皮肤：{nm}"
                        self._flash_timer = 1.5
                    else:
                        # 游戏中仅预览（不打断游戏）
                        self._pending_skin = target
                        self._play("select")
                return True
        # 暂停态：数字键 0（pygame.K_0）切换 P2 皮肤（如果是双人且P2有皮肤）
        if self.state == self.PAUSED and key == pygame.K_0 and self.num_players == 2:
            owned = [sid for sid in ALL_SKIN_ORDER if sid in self.owned_skins]
            if owned:
                p2_now = self.active_skin_p2
                if p2_now in owned:
                    nxt = (owned.index(p2_now) + 1) % len(owned)
                else:
                    nxt = 0
                self.active_skin_p2 = owned[nxt]
                self._sync_skin_to_player()
                self._play("select")
            return True
        # 字母键（统一基于 KEYDOWN）
        mods = pygame.key.get_mods()
        upper = bool(mods & (pygame.KMOD_CAPS | pygame.KMOD_SHIFT))
        if key in (pygame.K_h, pygame.K_q, pygame.K_p, pygame.K_t, pygame.K_r):
            if not upper:
                return True  # 小写状态忽略
            self._dispatch_letter(chr(key).lower())
        elif key == pygame.K_b:
            # Q2：B 右键技能（无需大写锁定，直接生效）
            self._handle_skill_key(chr(key))
        elif key == pygame.K_v:
            # Q2：V 左键（无需大写锁定，直接生效）
            mx, my = pygame.mouse.get_pos()
            self._handle_click(mx, my)
            return True
        elif key == pygame.K_RIGHTBRACKET:
            # ] 非字母键，无需大写检查
            self._handle_skill_key(chr(key))
        elif key == pygame.K_SPACE:
            # Q1：游戏中按空格暂停，再按一次空格继续（与ESC行为一致）
            if self.state == self.PLAYING:
                self.state = self.PAUSED
                self._play("tick")
            elif self.state == self.PAUSED:
                self.state = self.PLAYING
                self._play("tick")
            else:
                self._handle_confirm()
        elif key == pygame.K_RETURN:
            self._handle_confirm()
        elif key == pygame.K_LEFT:
            if self.show_help:
                self._help_page = max(0, getattr(self, "_help_page", 0) - 1)
                self._play("tick")
            elif self.state == self.MAP:
                self.map_cursor = max(0, self.map_cursor - 1)
                self._play("tick")
            elif self.state == self.PAUSED:
                # Q2：暂停时左键 = 切换到上一个已拥有皮肤（直接生效）
                owned = [sid for sid in ALL_SKIN_ORDER if sid in self.owned_skins]
                if owned:
                    cur = self.active_skin
                    try:
                        ci = owned.index(cur)
                    except ValueError:
                        ci = 0
                    nxt = owned[(ci - 1) % len(owned)]
                    self.active_skin = nxt
                    self._pending_skin = None
                    self._sync_skin_to_player()
                    self._save_game()
                    self._play("buy")
                    nm = SKINS[nxt][0] if nxt in SKINS else "默认星辰"
                    self._flash_msg = f"已切换为皮肤：{nm}"
                    self._flash_timer = 1.5
        elif key == pygame.K_RIGHT:
            if self.show_help:
                self._help_page = min(6, getattr(self, "_help_page", 0) + 1)
                self._play("tick")
            elif self.state == self.MAP:
                unlock = self._get_unlocked()
                self.map_cursor = min(max(0, unlock - 1), self.map_cursor + 1)
                self._play("tick")
            elif self.state == self.PAUSED:
                # Q2：暂停时右键 = 切换到下一个已拥有皮肤（直接生效）
                owned = [sid for sid in ALL_SKIN_ORDER if sid in self.owned_skins]
                if owned:
                    cur = self.active_skin
                    try:
                        ci = owned.index(cur)
                    except ValueError:
                        ci = -1
                    nxt = owned[(ci + 1) % len(owned)]
                    self.active_skin = nxt
                    self._pending_skin = None
                    self._sync_skin_to_player()
                    self._save_game()
                    self._play("buy")
                    nm = SKINS[nxt][0] if nxt in SKINS else "默认星辰"
                    self._flash_msg = f"已切换为皮肤：{nm}"
                    self._flash_timer = 1.5
        return True

    def _handle_skill_key(self, ch):
        """皮肤专有技能触发键：B（玩家1）/ ]（玩家2）。
        单人模式鼠标右键也会调用此方法（ch='right'）。
        """
        if self.state != self.PLAYING:
            return
        if ch == "B":
            # P1 皮肤技能：朝鼠标方向
            mx, my = pygame.mouse.get_pos()
            self._skin_skill_at(self.player, mx, my, who="p1")
        elif ch == "]":
            # P2 皮肤技能：朝 P2 自身位置附近释放
            if self.num_players == 2 and len(self.players) >= 2:
                p2 = self.players[1]
                self._skin_skill_at(p2, p2.x, p2.y, who="p2")

    def _skin_skill(self, p, who):
        """旧入口：触发皮肤技能（无鼠标方向信息）。"""
        self._skin_skill_at(p, p.x, p.y, who=who)

    def _skin_skill_at(self, p, mx, my, who="p1"):
        """触发玩家 p 当前皮肤专有技能，目标点 (mx, my)。"""
        if not p or not p.alive:
            return
        sk = getattr(p, "skin", None) or self.active_skin
        if not sk or sk == "default":
            # 默认皮肤无专有技能：给个提示但不报错
            self._flash_msg = "默认皮肤无专有技能（商店可购买）"
            self._flash_timer = 1.0
            return
        # 调用统一的皮肤单击能力
        saved = self.active_skin
        saved_p = self.player
        try:
            # _skin_on_click 内部使用 self.active_skin 与 self.player，
            # 这里临时切换以适配对应玩家
            if who == "p2":
                self.player = p
                self.active_skin = sk
            handled = self._skin_on_click(mx, my)
        finally:
            if who == "p2":
                self.player = saved_p
                self.active_skin = saved
        if not handled:
            self._flash_msg = f"皮肤 {sk} 暂无主动技能"
            self._flash_timer = 1.0

    def _dispatch_letter(self, ch):
        if ch == "h":
            self._toggle_control()
        elif ch == "q":
            if self.state in (self.PAUSED, self.OVER, self.LEVEL_COMPLETE, self.VICTORY):
                self._goto_map()
        elif ch == "p":
            if self.state == self.PLAYING:
                self.state = self.PAUSED
            elif self.state == self.PAUSED:
                self.state = self.PLAYING
        elif ch == "t":
            if self.state == self.MAP:
                self.num_players = 2 if self.num_players == 1 else 1
                if self.control_mode == "hand":
                    self.tracker.pause()
                self.control_mode = "mouse"
                self._play("select")
        elif ch == "r":
            if self.state in (self.OVER, self.PAUSED):
                self.reset_level()
                self.state = self.PLAYING
                self._play("start")
            elif self.state == self.VICTORY:
                self._goto_map()

    def _toggle_muted(self):
        self.muted = not self.muted
        if self.muted:
            if self.drone_on:
                self.sounds.stop_drone()
                self.drone_on = False
            try:
                pygame.mixer.pause()
            except Exception:
                pass
            self._flash_msg = "已静音（F3 恢复）"
            self._flash_timer = 1.6
        else:
            try:
                pygame.mixer.unpause()
            except Exception:
                pass
            self._flash_msg = "已恢复音量"
            self._flash_timer = 1.2
            if self.state == self.PLAYING:
                self._update_horror()

    def _rebuild_sound(self):
        """切换显示/全屏模式后，重建 mixer 与 SoundBank，避免 SDL 音频掉线。"""
        try:
            pygame.mixer.stop()
        except Exception:
            pass
        # 先停掉氛围音再重建
        if getattr(self.sounds, "stop_ambient", None):
            try:
                self.sounds.stop_ambient()
            except Exception:
                pass
        if getattr(self.sounds, "rebuild_all", None):
            try:
                self.sounds.rebuild_all()
            except Exception:
                pass
        init_ok = False
        for (freq, fmt, chan, buf) in [(SR, -16, 2, 512), (SR, -16, 2, 1024),
                                       (22050, -16, 2, 512), (44100, -8, 1, 1024)]:
            try:
                try:
                    pygame.mixer.quit()
                except Exception:
                    pass
                try:
                    pygame.mixer.pre_init(freq, fmt, chan, buf)
                except Exception:
                    pass
                pygame.mixer.init(freq, fmt, chan, buf)
                if pygame.mixer.get_init():
                    init_ok = True
                    break
            except Exception:
                continue
        if not init_ok:
            try:
                pygame.mixer.init()
                init_ok = bool(pygame.mixer.get_init())
            except Exception:
                pass
        if init_ok:
            try:
                pygame.mixer.set_num_channels(32)
            except Exception:
                pass
            self.sounds = SoundBank()
            # 重新开启氛围音（若处于游戏中）
            if self.state == self.PLAYING and not self.muted:
                self.drone_on = False
                self._update_horror()
        elif not init_ok:
            print("[rebuild_sound] mixer 无法重启，继续静音运行")

    def _goto_map(self):
        self.state = self.MAP
        if self.drone_on:
            self.sounds.stop_drone()
            self.drone_on = False
        if self.control_mode == "hand":
            self.tracker.pause()
            self.control_mode = "mouse"
        # 无尽模式中途返回地图：结束无尽并保存高分
        if getattr(self, "_endless_mode", False):
            if getattr(self, "_endless_score", 0) > getattr(self, "_endless_high_score", 0):
                self._endless_high_score = self._endless_score
            self._endless_high_wave = max(getattr(self, "_endless_high_wave", 0),
                                          getattr(self, "_endless_wave", 0))
            self._endless_mode = False
        # Q9：BOSS模式中途返回地图
        if getattr(self, "_boss_mode", False):
            self._boss_mode = False
            self._save_game()
        # 返回地图时检测一次成就（覆盖购买皮肤、通关、死亡等场景）
        self._check_achievements()

    def _sync_skin_to_player(self):
        """切换皮肤后立即同步：更新玩家颜色，清除旧皮肤的专属状态。"""
        sk = self.active_skin
        col = NEON_CYAN
        if sk is not None and sk in SKINS:
            col = SKINS[sk][2]
        # P1
        if self.player and self.player.alive:
            self.player.color = col
            self.player.tri_mode = 0
            self.player.moon_shrunk = False
            self.player._tri_boost_timer = 0.0
            self.player._inferno_ring_timer = 0.0
            if self.player._inferno_base_r > 0:
                self.player.r = self.player._inferno_base_r
                self.player._inferno_base_r = 0.0
            self.player._sun_glow_timer = 0.0
            self.player._chaos_hook = None
            self.player._chaos_sword_timer = 0.0
            self.player._samsara_timer = 0.0
            self.player._taiji_timer = 0.0
            self.player._nirvana_timer = 0.0
        # P2
        sk2 = self.active_skin_p2
        col2 = NEON_PINK
        if sk2 is not None and sk2 in SKINS:
            col2 = SKINS[sk2][2]
        if self.player2 and self.player2.alive:
            self.player2.color = col2

    def _toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        flags = pygame.SCALED
        if self.fullscreen:
            flags |= pygame.FULLSCREEN
        try:
            self.screen = pygame.display.set_mode((WIDTH, HEIGHT), flags, vsync=1)
        except Exception as e:
            print(f"[全屏] 切换失败: {e}")
            self.fullscreen = False
            self.screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.SCALED, vsync=1)
        # Windows 上 SCALED + FULLSCREEN 切换可能导致 SDL 音频设备掉线，重建 mixer
        try:
            self._rebuild_sound()
        except Exception as e2:
            print(f"[全屏] 重建音频失败: {e2}")
        self._play("tick")

    def _handle_confirm(self):
        if self.state == self.MAP:
            self.current_level = self.map_cursor
            self.reset_level()
            self.state = self.PLAYING
            self._play("start")
        elif self.state == self.LEVEL_COMPLETE:
            self.next_level()
        elif self.state == self.VICTORY:
            self._goto_map()
        elif self.state == self.PAUSED:
            # Q2：暂停时空格已改为切换皮肤（在按键事件中处理），
            # 这里是回车键或其它确认键 → 继续游戏
            pending = getattr(self, "_pending_skin", None)
            if pending is not None and pending != self.active_skin:
                self.active_skin = pending
                self._pending_skin = None
                self._sync_skin_to_player()
                self._save_game()
                self._play("buy")
            self.state = self.PLAYING
            self._play("tick")

    def _handle_click(self, mx, my):
        if self.state == self.PLAYING:
            sk = self.active_skin
            # 三色灵球左键技能
            if sk == "tri":
                self._tri_left_click(mx, my)
                return
            # 月华左键 = 正常加速（不触发技能）
            if sk == "moon":
                return
            # 烈阳左键 = 发光排斥+加速
            if sk == "sun":
                self._sun_left_click(mx, my)
                return
            # 虹光左键 = 使用对应色道具（30%时长）
            if sk == "rainbow":
                self._rainbow_left_click(mx, my)
                return
            # 炼狱左键 = 发射火球
            if sk == "inferno":
                self._inferno_left_click(mx, my)
                return
            # 霜冻左键 = 发射冰粒冻结
            if sk == "frost":
                self._frost_left_click(mx, my)
                return
            # 雷霆左键 = 发射自动电球
            if sk == "thunder":
                self._thunder_left_click(mx, my)
                return
            # 深渊左键 = 发射螺旋黑洞
            if sk == "void":
                self._void_left_click(mx, my)
                return
            # 混沌左键 = 发射钩子
            if sk == "chaos":
                self._chaos_left_click(mx, my)
                return
            # ===== 钻石皮肤左键 =====
            # 天罚之眼左键：审判光弹穿透
            if sk == "judge":
                self._judge_left_click(mx, my)
                return
            if sk == "dragon":
                self._dragon_left_click(mx, my)
                return
            if sk == "demon":
                self._demon_left_click(mx, my)
                return
            if sk == "stellar":
                self._stellar_left_click(mx, my)
                return
            if sk == "samsara":
                # 轮回印左键：标记敌人死亡返还能量（右键时回轮）
                self._samsara_left_click(mx, my)
                return
            if sk == "寂灭":
                self._寂灭_left_click(mx, my)
                return
            if sk == "primal":
                self._primal_left_click(mx, my)
                return
            if sk == "taiji":
                self._taiji_left_click(mx, my)
                return
            if sk == "nirvana":
                self._nirvana_left_click(mx, my)
                return
            # ===== 第三页 至高霸气皮肤左键 =====
            if sk == "titan":
                self._titan_left_click(mx, my)
                return
            if sk == "qinglong":
                self._qinglong_left_click(mx, my)
                return
            if sk == "baihu":
                self._baihu_left_click(mx, my)
                return
            if sk == "zhuque":
                self._zhuque_left_click(mx, my)
                return
            if sk == "xuanwu":
                self._xuanwu_left_click(mx, my)
                return
            if sk == "stargod":
                self._stargod_left_click(mx, my)
                return
            if sk == "chrono":
                self._chrono_left_click(mx, my)
                return
            if sk == "buddha":
                self._buddha_left_click(mx, my)
                return
            if sk == "god":
                self._god_left_click(mx, my)
                return
            if sk == "origin":
                self._origin_left_click(mx, my)
                return
            if sk == "paradox":
                self._paradox_left_click(mx, my)
                return
            if sk == "finality":
                self._finality_left_click(mx, my)
                return
            # 其他皮肤单击能力
            self._skin_on_click(mx, my)
            return
        if self.state == self.PAUSED:
            # 返回地图按钮
            btn_back = pygame.Rect(WIDTH // 2 - 130, HEIGHT // 2 + 150, 260, 52)
            if btn_back.collidepoint(mx, my):
                self._goto_map()
                return
            # ===== Q2：皮肤切换：暂停时直接切换（无需空格确认） =====
            prev_btn = pygame.Rect(WIDTH // 2 - 210, HEIGHT // 2 + 20, 80, 48)
            next_btn = pygame.Rect(WIDTH // 2 + 130, HEIGHT // 2 + 20, 80, 48)
            # 收集 P1 已拥有的皮肤（只能切换已拥有）
            owned = [sid for sid in ALL_SKIN_ORDER if sid in self.owned_skins]
            if not owned:
                owned = [None]
            cur_sid = self.active_skin
            try:
                cur_idx = owned.index(cur_sid)
            except ValueError:
                cur_idx = 0
            if prev_btn.collidepoint(mx, my):
                if owned and owned[0] is not None:
                    new_idx = (cur_idx - 1) % len(owned)
                    target = owned[new_idx]
                    self.active_skin = target
                    self._pending_skin = None
                    self._sync_skin_to_player()
                    self._save_game()
                    self._play("buy")
                    nm = SKINS[target][0] if target in SKINS else "默认星辰"
                    self._flash_msg = f"已切换为皮肤：{nm}"
                    self._flash_timer = 1.5
                return
            if next_btn.collidepoint(mx, my):
                if owned and owned[0] is not None:
                    new_idx = (cur_idx + 1) % len(owned)
                    target = owned[new_idx]
                    self.active_skin = target
                    self._pending_skin = None
                    self._sync_skin_to_player()
                    self._save_game()
                    self._play("buy")
                    nm = SKINS[target][0] if target in SKINS else "默认星辰"
                    self._flash_msg = f"已切换为皮肤：{nm}"
                    self._flash_timer = 1.5
                return
            return
        if self.state == self.MAP:
            # ===== Q8：签到按钮（左上角，兑换码上方）=====
            if self._sign_in_button_rect().collidepoint(mx, my):
                self._do_sign_in()
                return
            # ===== Q5：兑换码按钮（初始界面左上角）=====
            if self._redeem_code_button_rect().collidepoint(mx, my):
                self._open_redeem_modal()
                self._play("tick")
                return
            # 商店按钮（打开 P1 商店）
            if self._shop_button_rect().collidepoint(mx, my):
                if self.show_shop == True:
                    self.show_shop = False
                else:
                    self.show_shop = True
                self._play("tick")
                return
            # P2 皮肤按钮：双人模式打开 P2 商店
            if self._p2skin_button_rect().collidepoint(mx, my):
                if self.num_players == 2:
                    if self.show_shop == "p2":
                        self.show_shop = False
                    else:
                        self.show_shop = "p2"
                    self._play("tick")
                else:
                    self._flash_msg = "先切换为双人模式（按 T 或点击模式按钮）"
                    self._flash_timer = 1.4
                return
            # 商店打开时处理商店内点击
            if self.show_shop:
                self._handle_shop_click(mx, my)
                return
            # 抽奖按钮
            if self._lottery_button_rect().collidepoint(mx, my):
                self.show_lottery = not self.show_lottery
                self._lottery_revealed = {}
                self._lottery_anim = {}
                if self.show_lottery:
                    # 每次打开随机重置 12 个箱子的奖项
                    self._reshuffle_lottery()
                self._play("tick")
                return
            # 抽奖面板打开时处理抽奖点击
            if self.show_lottery:
                self._lottery_click(mx, my)
                return
            # 说明按钮
            if self._help_button_rect().collidepoint(mx, my):
                self.show_help = not self.show_help
                self._help_page = 0
                self._play("tick")
                return
            # 说明面板打开时处理按钮
            if self.show_help:
                if self._help_close_rect().collidepoint(mx, my):
                    self.show_help = False
                    self._play("tick")
                    return
                if self._help_prev_rect().collidepoint(mx, my):
                    if not hasattr(self, "_help_page"):
                        self._help_page = 0
                    if self._help_page > 0:
                        self._help_page -= 1
                        self._play("tick")
                    return
                if self._help_next_rect().collidepoint(mx, my):
                    if not hasattr(self, "_help_page"):
                        self._help_page = 0
                    total = 7
                    if self._help_page < total - 1:
                        self._help_page += 1
                        self._play("tick")
                    return
                return
            # Q8：设置面板打开时处理点击
            if getattr(self, "show_settings", False):
                self._handle_settings_click(mx, my)
                return
            # Q6：成就面板打开时处理点击
            if getattr(self, "show_achievements", False):
                self._handle_achievements_click(mx, my)
                return
            # 模式切换按钮
            if self._mode_button_rect().collidepoint(mx, my):
                self.num_players = 2 if self.num_players == 1 else 1
                if self.control_mode == "hand":
                    self.tracker.pause()
                self.control_mode = "mouse"
                self._play("select")
                return
            # 副本/主线 切换按钮
            db = self._dungeon_button_rect()
            if db.collidepoint(mx, my):
                if self.is_dungeon:
                    self.is_dungeon = False
                    self.map_cursor = min(self.map_cursor, len(LEVELS) - 1)
                    self.current_level = 0
                else:
                    if self.unlocked >= len(LEVELS):
                        self.is_dungeon = True
                        self.map_cursor = 0
                        self.current_level = 0
                        # 首次进入副本默认解锁第1关
                        if self.dungeon_unlocked <= 0:
                            self.dungeon_unlocked = 1
                            self._save_game()
                    else:
                        self._flash_msg = f"主线 1-{len(LEVELS)} 关全部通关后才可进入副本"
                        self._flash_timer = 1.8
                self._play("tick")
                return
            # 进度导出/导入按钮
            if self._export_button_rect().collidepoint(mx, my):
                self._export_progress()
                return
            if self._import_button_rect().collidepoint(mx, my):
                self._import_progress()
                return
            # Q6/Q7/Q8：新功能按钮
            if self._achievement_button_rect().collidepoint(mx, my):
                self.show_achievements = True
                self._ach_page = 0
                self._play("tick")
                return
            if self._endless_button_rect().collidepoint(mx, my):
                self._start_endless()
                return
            # Q9：BOSS模式按钮
            if self._boss_mode_button_rect().collidepoint(mx, my):
                self._start_boss_mode()
                return
            if self._settings_button_rect().collidepoint(mx, my):
                self.show_settings = True
                self._play("tick")
                return
            # 检测点击哪个关卡节点
            unlock = self._get_unlocked()
            for i, (nx, ny) in enumerate(self._map_positions()):
                if math.hypot(mx - nx, my - ny) < 40 and i < unlock:
                    self.map_cursor = i
                    self.current_level = i
                    self.reset_level()
                    self.state = self.PLAYING
                    self._play("start")
                    return
        elif self.state == self.LEVEL_COMPLETE and self.lc_timer > 0.4:
            self.next_level()
        elif self.state == self.VICTORY:
            self._goto_map()
        elif self.state == self.OVER and self.over_timer > 0.6:
            self.reset_level()
            self.state = self.PLAYING
            self._play("start")

    def next_level(self):
        levels = self._get_levels()
        if self.current_level >= len(levels) - 1:
            self.state = self.VICTORY
            self._play("win")
            if self.drone_on:
                self.sounds.stop_drone()
                self.drone_on = False
            self.burst(WIDTH / 2, HEIGHT / 2, NEON_YELLOW, 80, 380, size=4.0, life=1.2)
            # 副本全部通关：额外送钻石 + 提示
            if self.is_dungeon:
                total_bonus = 50
                if getattr(self, "_infinite_diamonds", False):
                    self.diamonds = max(self.diamonds, 99999)
                else:
                    self.diamonds += total_bonus
                self._flash_msg = f"全部副本通关！额外奖励钻石 +{total_bonus}"
                self._flash_timer = 3.0
                self._save_game()
        else:
            self.current_level += 1
            self._set_unlocked(max(self._get_unlocked(), self.current_level + 1))
            self.map_cursor = self.current_level
            self._save_game()  # 持久化解锁进度
            self.reset_level()
            self.state = self.PLAYING
            self._play("start")

    # ---- 更新 ----
    def update(self, dt, tx, ty):
        self.time_alive += dt
        self._update_horror()  # 确保氛围音随状态切换
        lv = self._get_levels()[self.current_level]

        # 决定每个玩家的输入
        inputs = self._resolve_inputs()
        # 玩家移动 + 计时 + 拖尾
        for p, (vel, dash) in zip(self.players, inputs):
            if not p.alive:
                continue
            p.prev_x, p.prev_y = p.x, p.y
            dashing = dash and p.energy > 0
            # 加速启动音
            if dashing and not getattr(p, "_was_dashing", False):
                self._play("whoosh")
            p._was_dashing = dashing
            smul = self._skin_move_mul(p)
            if vel is not None:
                p.move_by(vel[0] * smul, vel[1] * smul, dt, dashing)
            else:
                # 鼠标模式：tri 加速时提高跟随速度
                follow = (13.0 if dashing else 6.0) * (1.0 + 0.5 * (smul - 1.0))
                t = 1.0 - math.exp(-follow * dt)
                p.x = lerp(p.x, tx, t)
                p.y = lerp(p.y, ty, t)
                p._clamp()
            p.update_timers(dt, dashing)

            # 拖尾：所有皮肤均带长霸气拖尾（加速时更长更密）
            p.trail_timer -= dt
            trail_rate = 0.006 if dashing else 0.016
            if p.trail_timer <= 0:
                p.trail_timer = trail_rate
                skin_col = self._skin_color(p)
                tc = NEON_PINK if dashing else skin_col
                # 皮肤特化拖尾色
                sk = self.active_skin
                if sk == "inferno":
                    tc = (255, 120, 40) if not dashing else (255, 200, 80)
                elif sk == "frost":
                    tc = (150, 220, 255) if not dashing else NEON_PINK
                elif sk == "thunder":
                    tc = (255, 240, 120) if not dashing else NEON_PINK
                elif sk == "void":
                    tc = (180, 90, 255) if not dashing else NEON_PINK
                elif sk == "chaos":
                    palette = [(200, 80, 255), (255, 90, 30), (90, 200, 255)]
                    tc = palette[int(pygame.time.get_ticks() * 0.005) % 3]
                # 长拖尾：多个粒子沿反速度方向延伸
                pdx = p.x - p.prev_x
                pdy = p.y - p.prev_y
                spd = math.hypot(pdx, pdy)
                trail_len = 5 if dashing else 3
                for ti in range(trail_len):
                    off = ti * 3.0
                    if spd > 0.5:
                        ux, uy = pdx / spd, pdy / spd
                        tx2 = p.x - ux * (p.r * 0.6 + off)
                        ty2 = p.y - uy * (p.r * 0.6 + off)
                    else:
                        tx2 = p.x + random.uniform(-3, 3)
                        ty2 = p.y + random.uniform(-3, 3)
                    life = 0.5 + ti * 0.15 if dashing else 0.35 + ti * 0.1
                    size = max(1.5, 5.0 - ti * 0.8) if dashing else max(1.5, 4.0 - ti * 0.6)
                    self.particles.append(Particle(
                        tx2 + random.uniform(-1.5, 1.5), ty2 + random.uniform(-1.5, 1.5),
                        random.uniform(-8, 8), random.uniform(-8, 8),
                        life, tc, size))

        # 分裂子细胞：双球围绕鼠标旋转
        if self.split_cells and self.player.alive:
            self.split_angle += dt * 2.6
            orbit_r = 56 + self.player.r * 0.4
            mxp, myp = tx, ty
            self.player.prev_x, self.player.prev_y = self.player.x, self.player.y
            self.player.x = mxp + math.cos(self.split_angle) * orbit_r
            self.player.y = myp + math.sin(self.split_angle) * orbit_r
            self.player._clamp()
            dash1 = inputs[0][1] and self.player.energy > 0
            self.player.update_timers(dt, dash1)
            for i, c in enumerate(self.split_cells):
                if not c.alive:
                    continue
                ang = self.split_angle + math.pi * (i + 1)
                c.prev_x, c.prev_y = c.x, c.y
                c.x = mxp + math.cos(ang) * orbit_r
                c.y = myp + math.sin(ang) * orbit_r
                c._clamp()
                c.update_timers(dt, dash1)
                c.trail_timer -= dt
                if c.trail_timer <= 0:
                    c.trail_timer = 0.03
                    self.particles.append(Particle(
                        c.x, c.y, 0, 0, 0.4, c.color, 3.0))
            # 移除已死亡子细胞（独立存活：主球不受影响）
            self.split_cells = [c for c in self.split_cells if c.alive]

        # 光刃旋刃：360° 旋转持续 4s，碰到敌方削减生命（带命中冷却）
        for bl in self.blade_spins:
            owner = bl["owner"]
            if not owner.alive:
                bl["life"] = 0
                continue
            bl["life"] -= dt
            bl["angle"] += dt * math.tau * 1.6  # 快速旋转
            reach = bl["r"]
            for s in self.stars:
                if not s.danger or s._dead:
                    continue
                if math.hypot(s.x - owner.x, s.y - owner.y) < reach + s.r:
                    if s.blade_cd <= 0:
                        s.blade_cd = 0.22  # 每个敌球 0.22s 受一次刃击
                        self._damage_enemy(s, 1, owner)
        self.blade_spins = [bl for bl in self.blade_spins if bl["life"] > 0]

        # 皮肤周期能力
        self._skin_update(dt)
        self._skin_frame(dt)

        # 金币生成与拾取
        MAG_RANGE = 200
        MAG_FORCE = 9200
        MAG_MIN = 55.0  # 最小拉力下限，确保范围内路过的球都能被吸到
        self.coin_spawn_timer -= dt
        if self.coin_spawn_timer <= 0:
            self._spawn_coin()
            self.coin_spawn_timer = random.uniform(5.0, 9.0)
        for c in self.coin_pickups:
            c["life"] -= dt
            c["phase"] += dt * 4.0
            c["y"] += math.sin(c["phase"]) * 12 * dt
            # Q7：磁吸道具专门吸金币（拉向玩家），强度比普通吸星略大
            if "vx" not in c:
                c["vx"] = 0.0
            if "vy" not in c:
                c["vy"] = 0.0
            for p in self.players:
                if p.alive and p.magnet_timer > 0:
                    dx = p.x - c["x"]; dy = p.y - c["y"]
                    d = math.hypot(dx, dy)
                    if 0 < d < MAG_RANGE * 1.2:
                        f = max(MAG_FORCE * 1.3 / max(d, 12), MAG_MIN * 1.6)
                        c["vx"] += dx / d * f * dt
                        c["vy"] += dy / d * f * dt
            # 应用金币自己的速度
            c["x"] += c["vx"] * dt
            c["y"] += c["vy"] * dt
            c["vx"] *= math.pow(0.06, dt)
            c["vy"] *= math.pow(0.06, dt)
        for c in self.coin_pickups:
            for p in self._all_player_cells():
                if p.alive and math.hypot(c["x"] - p.x, c["y"] - p.y) < p.r + 14:
                    c["_dead"] = True
                    self.coins += 1
                    self._save_game()
                    self.burst(c["x"], c["y"], NEON_YELLOW, 18, 240, size=2.6, life=0.45)
                    self._play("coin")
                    break
        self.coin_pickups = [c for c in self.coin_pickups if not c.get("_dead")
                             and c["life"] > 0]
        # 时空帝主：全场冻结（time_freeze_timer > 0 时，所有敌人 frozen_timer 保底延长并静止）
        if self.time_freeze_timer > 0:
            self.time_freeze_timer -= dt
            # 给每个危险敌人延长 frozen_timer（至少覆盖到 freeze 结束 + 少许）
            for s in self.stars:
                if s.danger and not s._dead:
                    s.frozen_timer = max(s.frozen_timer, self.time_freeze_timer + 0.4)
                    s.vx *= math.pow(0.02, dt)
                    s.vy *= math.pow(0.02, dt)

        # 全局计时（仅一次）
        if self.double_timer > 0:
            self.double_timer -= dt
        if self.combo > 0:
            self.combo_timer -= dt
            if self.combo_timer <= 0:
                self.combo = 0

        slow = self.time_slow_timer > 0
        if slow:
            self.time_slow_timer -= dt
        star_dt = dt * (0.25 if slow else 1.0)

        # 氛围 / 恐怖
        self._update_ambient(dt)
        self._tick_horror(dt)

        # 星体随机变向（按关卡 chaos 值，后期极强随机）
        chaos = lv.get("chaos", 0.0)
        if chaos > 0:
            # 后期 chaos 值越大，变向概率与冲量都显著增强
            for s in self.stars:
                # 每帧多次判定（chaos 高时几乎乱飞）
                trials = 1 + int(chaos * 6)
                for _ in range(trials):
                    if random.random() < chaos:
                        a = random.uniform(0, math.tau)
                        sp = random.uniform(60, 200) * (0.6 + chaos * 4)
                        s.vx += math.cos(a) * sp
                        s.vy += math.sin(a) * sp

        # 生成
        self.spawn_timer -= dt
        if self.spawn_timer <= 0:
            if getattr(self, "_endless_mode", False):
                # 无尽模式：本波次限量生成，并按波次强化敌人
                if getattr(self, "_endless_spawned", 0) < getattr(self, "_endless_wave_target", 0):
                    self.spawn_star()
                    self._endless_spawned = getattr(self, "_endless_spawned", 0) + 1
                    if self.stars:
                        last = self.stars[-1]
                        hp_scale = 1.0 + self._endless_wave * 0.15
                        sp_scale = 1.0 + self._endless_wave * 0.05
                        last.hp = max(1, int(last.hp * hp_scale))
                        last.max_hp = max(1, int(last.max_hp * hp_scale))
                        last.vx *= sp_scale
                        last.vy *= sp_scale
                    self.spawn_timer = max(0.3, self.spawn_interval * random.uniform(0.7, 1.2))
                else:
                    self.spawn_timer = 0.5
            else:
                # Q7：BOSS模式不进行常规刷新 —— 敌人持续存在直至被击败
                if getattr(self, "_boss_mode", False):
                    self.spawn_timer = 1.0
                else:
                    self.spawn_star()
                    self.spawn_timer = self.spawn_interval * random.uniform(0.7, 1.2)
        self.powerup_timer -= dt
        if self.powerup_timer <= 0:
            self.spawn_powerup()
            self.powerup_timer = self.powerup_interval + random.uniform(-3, 3)

        # 黑洞
        if self.blackhole is not None:
            bh = self.blackhole
            bh["life"] -= dt
            bh["r"] = 150 + math.sin(pygame.time.get_ticks() * 0.01) * 10
            if bh["life"] <= 0:
                self.blackhole = None
            else:
                # 强力吸引；进入 2/3 半径即被吞噬
                devour_r = bh["r"] * (2.0 / 3.0)
                pull_r = bh["r"] * 2.4
                for s in self.stars:
                    ddx = bh["x"] - s.x
                    ddy = bh["y"] - s.y
                    d = math.hypot(ddx, ddy)
                    if d < devour_r:
                        self.burst(s.x, s.y, s.color, 14, 280, size=2.6, life=0.45)
                        gain = int(s.r * 5 * (2 if self.double_timer > 0 else 1))
                        self.score += gain
                        self.level_eaten += 0 if s.danger else 1
                        s._dead = True
                    elif d < pull_r and d > 0:
                        # 远强于以往的引力
                        f = 4200 / max(d, 18)
                        s.vx += ddx / d * f * dt
                        s.vy += ddy / d * f * dt
                        # 黑洞潮汐：对敌方刺球持续削减生命（非吞噬性攻击）
                        if s.danger:
                            self._damage_enemy(s, 2.0 * dt)
                self.stars = [s for s in self.stars if not s._dead]

        # 星体更新 + 磁吸 + 碰撞（对每个玩家判定）
        MAG_RANGE = 200
        MAG_FORCE = 9200
        MAG_MIN = 55.0  # 最小拉力下限，确保范围内路过的球都能被吸到
        for s in self.stars:
            # 长蛇的节不要在 s.update 里移动位置（snake head 才在 _update_snakes 里主动移动，
            # 其它节的位置由 _update_snakes 中的跟随算法控制），但仍然更新 phase/hit_flash
            if s.kind == "snake" and not s.snake_head_flag:
                # 非蛇头节：跳过 update 的 x += vx*dt 部分，但更新 phase/hit_flash
                s.phase += s.spin * star_dt
                s.sub_phase += star_dt * 2.4
                if s.hit_flash > 0:
                    s.hit_flash -= star_dt
                if s.blade_cd > 0:
                    s.blade_cd -= star_dt
            else:
                s.update(star_dt)
            # 虫群/蜈蚣 AI：长条身体跟随 + 一定概率包围玩家
            if s.kind in ("worm", "centipede") and s.danger and not s._dead:
                self._update_worm(s, dt)
            # c7/c10：主动追踪玩家（轻度追踪 Tier>=2 / 强追踪 horror）
            if s.danger and not s._dead and s.chase_player > 0:
                # 选择距离最近的存活玩家为目标（强追踪锁定一次）
                alive_players = [p for p in self.players if p.alive]
                if alive_players:
                    tgt = None
                    if s.chase_player == 2 and s.chase_id is not None:
                        cand = self.players[s.chase_id]
                        if cand.alive:
                            tgt = cand
                    if tgt is None:
                        best_d = None
                        best_p = None
                        for p in alive_players:
                            d_ = math.hypot(p.x - s.x, p.y - s.y)
                            if best_d is None or d_ < best_d:
                                best_d = d_; best_p = p
                        tgt = best_p
                        if s.chase_player == 2:
                            s.chase_id = self.players.index(tgt) if tgt in self.players else 0
                    if tgt is not None and getattr(s, "frozen_timer", 0) <= 0:
                        ddx_ = tgt.x - s.x
                        ddy_ = tgt.y - s.y
                        d_ = math.hypot(ddx_, ddy_)
                        if d_ > 1:
                            # 恐怖种强追踪：强力加速度；轻度追踪：柔和加速度
                            if s.chase_player == 2:
                                acc = 260.0
                                sp_cap = 260.0 + s.tier * 35
                            else:
                                acc = 110.0
                                sp_cap = 200.0 + s.tier * 20
                            s.vx += (ddx_ / d_) * acc * dt
                            s.vy += (ddy_ / d_) * acc * dt
                            # 速度上限（避免无限提速）
                            sp = math.hypot(s.vx, s.vy)
                            if sp > sp_cap:
                                s.vx = s.vx / sp * sp_cap
                                s.vy = s.vy / sp * sp_cap
        # 长蛇整体 AI + 断节拆分（放在 for s in stars 后面，避免节和链的交叉修改）
        self._update_snakes(dt)
        # 第二轮遍历 stars：碰撞（长蛇节单独移动也需参与碰撞）
        for s in self.stars:
            # Q7：磁吸道具不再吸无害小球；磁吸专门吸金币（见 coin_pickups 的处理，这里仅保留道具磁吸（道具在 powerups 段处理）
            # 碰撞：依次对每个玩家判定（含分裂子细胞）
            for p in self._all_player_cells():
                if not p.alive:
                    continue
                dx = s.x - p.x
                dy = s.y - p.y
                dist = math.hypot(dx, dy)
                if s.danger:
                    eatable = p.r > s.r * 1.05
                    if eatable and dist < p.r - s.r * 0.2:
                        self._eat(s, p, getattr(p, "_was_dashing", False), big=True)
                        s._dead = True
                        break
                    elif p.shield_timer > 0 and dist < p.r + s.r:
                        # 护盾：碰一次即破裂，毁掉敌人
                        self.burst(s.x, s.y, NEON_CYAN, 24, 320, size=3.0, life=0.55)
                        self.burst(p.x, p.y, NEON_CYAN, 30, 260, size=3.2, life=0.5)
                        p.shield_timer = 0.0
                        self.shake = max(self.shake, 0.35)
                        self._play("shield_break")
                        s._dead = True
                        break
                    elif (not p.invulnerable and dist < p.r + s.r - max(p.r, s.r) * 0.3
                          and s.r > p.r * 0.9):
                        # ===== 不灭尊者：舍利卫星挡伤（优先于真正扣血）=====
                        sats = getattr(p, "_buddha_satellites", None)
                        if sats and len(sats) > 0 and not getattr(p, "_is_sub", False):
                            # 去掉尾部最后一颗卫星（最外面那一颗先挡）
                            sat = sats.pop()
                            R = sat.get("explode_r", 150)
                            for s2 in list(self.stars):
                                if s2.danger and not s2._dead:
                                    dd2 = math.hypot(s2.x - sat["x"], s2.y - sat["y"])
                                    if dd2 < R:
                                        f2 = 1 - dd2 / R
                                        self._damage_enemy(s2, sat.get("explode_dmg", 5.5) * f2 + 2.0, p)
                            self.burst(sat["x"], sat["y"], (255, 220, 120), 70, 460,
                                       size=5.0, life=0.95)
                            # 短暂无敌+击退敌人 s（不真正扣血）
                            p.invulnerable = max(p.invulnerable, 0.6)
                            dxu = s.x - p.x; dyu = s.y - p.y; d0 = math.hypot(dxu, dyu) or 1
                            s.vx += dxu / d0 * 540
                            s.vy += dyu / d0 * 540
                            self.shake = max(self.shake, 0.3)
                            self._play("shield_break")
                            s._dead = True
                            break
                        if getattr(p, "_is_sub", False):
                            # 子细胞独立死亡，不影响主球生命
                            p.alive = False
                            self.burst(p.x, p.y, p.color, 30, 320, size=3.0, life=0.6)
                            self._play("hit")
                        else:
                            self._hit(s, p, getattr(p, "_was_dashing", False))
                        s._dead = True
                        break
                else:
                    if p.r > s.r and dist < p.r - s.r * 0.25:
                        self._eat(s, p, getattr(p, "_was_dashing", False), big=False)
                        s._dead = True
                        break
        # Q2：无尽模式中，飞出屏幕的敌人不视为击败 —— 重新投放到屏幕内
        # 这样玩家必须真正吞噬/打败所有敌人才能推进波次
        # Q7：BOSS模式同理 —— 敌人持续存在直至被击败
        if getattr(self, "_endless_mode", False) or getattr(self, "_boss_mode", False):
            for s in self.stars:
                if not s._dead and s.offscreen:
                    # 重新从屏幕边缘投放，朝向屏幕中心
                    side = random.randint(0, 3)
                    if side == 0:
                        s.x, s.y = random.uniform(0, WIDTH), -s.r - 20
                    elif side == 1:
                        s.x, s.y = random.uniform(0, WIDTH), HEIGHT + s.r + 20
                    elif side == 2:
                        s.x, s.y = -s.r - 20, random.uniform(0, HEIGHT)
                    else:
                        s.x, s.y = WIDTH + s.r + 20, random.uniform(0, HEIGHT)
                    tx = random.uniform(WIDTH * 0.2, WIDTH * 0.8)
                    ty = random.uniform(HEIGHT * 0.2, HEIGHT * 0.8)
                    ang = math.atan2(ty - s.y, tx - s.x)
                    spd = math.hypot(s.vx, s.vy) or 80.0
                    s.vx = math.cos(ang) * spd
                    s.vy = math.sin(ang) * spd
        self.stars = [s for s in self.stars if not s._dead and not s.offscreen]

        # 道具（磁吸也吸附道具）
        for pu in self.powerups:
            pu.update(star_dt)
            # 磁吸吸附
            for p in self.players:
                if p.alive and p.magnet_timer > 0:
                    ddx = p.x - pu.x
                    ddy = p.y - pu.y
                    d = math.hypot(ddx, ddy)
                    if 0 < d < MAG_RANGE:
                        f = max(MAG_FORCE * 0.9 / max(d, 18), MAG_MIN)
                        pu.vx += ddx / d * f * dt
                        pu.vy += ddy / d * f * dt
            eaten = False
            for p in self.players:
                if p.alive and math.hypot(pu.x - p.x, pu.y - p.y) < p.r + pu.r:
                    self.apply_powerup(pu.ptype, p)
                    pu._dead = True
                    eaten = True
                    break
            if not eaten and (pu.life <= 0 or pu.offscreen):
                pu._dead = True
        self.powerups = [pu for pu in self.powerups if not pu._dead]

        # 武器（光枪/光刃）自动攻击
        self._update_weapons(dt)
        # 三色红球炸弹
        self._update_tri_bombs(dt)
        # 霜冻冰粒
        self._update_frost_pellets(dt)
        # 雷霆电球 + 雷电场
        self._update_thunder(dt)
        # 深渊黑洞
        self._update_void_holes(dt)
        # 混沌钩子
        self._update_chaos(dt)
        # 钻石皮肤特效子弹
        if not hasattr(self, "dragon_fire"):
            self.dragon_fire = []
        if not hasattr(self, "demon_clouds"):
            self.demon_clouds = []
        if not hasattr(self, "stellar_orbs"):
            self.stellar_orbs = []
        if not hasattr(self, "taiji_blades"):
            self.taiji_blades = []
        if not hasattr(self, "samsara_blades"):
            self.samsara_blades = []
        if not hasattr(self, "寂灭_lotus"):
            self.寂灭_lotus = []
        self._update_diamond_projectiles(dt)
        # 六道轮回刃群 + 寂灭创世莲 + 六道领域 + 寂灭脉冲 + 太极自动两仪剑
        self._update_advanced_diamond_effects(dt)
        # ===== 第三页 至高霸气专属容器 & 更新 =====
        if not hasattr(self, "baihu_shadows"):
            self.baihu_shadows = []
        if not hasattr(self, "titan_hammers"):
            self.titan_hammers = []
        if not hasattr(self, "qinglong_dragons"):
            self.qinglong_dragons = []
        if not hasattr(self, "zhuque_fire"):
            self.zhuque_fire = []
        if not hasattr(self, "xuanwu_ices"):
            self.xuanwu_ices = []
        if not hasattr(self, "stargod_meteors"):
            self.stargod_meteors = []
        if not hasattr(self, "chrono_blades"):
            self.chrono_blades = []
        if not hasattr(self, "buddha_hands"):
            self.buddha_hands = []
        if not hasattr(self, "god_pillars"):
            self.god_pillars = []
        if not hasattr(self, "time_freeze_timer"):
            self.time_freeze_timer = 0.0
        self._update_page3_skills(dt)

        # 粒子（历史代码有的直接塞 tuple，这里统一归一化为 Particle 实例避免 AttributeError）
        arr = self.particles
        for i in range(len(arr)):
            it = arr[i]
            if isinstance(it, tuple) and len(it) == 7:
                arr[i] = Particle(it[0], it[1], it[2], it[3], it[4], it[5], it[6])
        for pp in self.particles:
            pp.update(dt)
        self.particles = [pp for pp in self.particles if pp.alive]
        if len(self.particles) > 600:
            self.particles = self.particles[-600:]

        if self.shake > 0:
            self.shake = max(0, self.shake - dt * 18)

        # 背景跟随主玩家
        ref = self.player if self.player.alive else self.players[-1]
        self._update_bg(dt, ref.x, ref.y)

        # 无尽模式：本波次敌人全部击败（吞噬小怪/打败大怪）才推进下一波
        if getattr(self, "_endless_mode", False) and self.state == self.PLAYING:
            if (getattr(self, "_endless_killed", 0) >= getattr(self, "_endless_wave_target", 0)
                    and len(self.stars) == 0):
                self._endless_advance_wave()

        # Q9：BOSS模式 - 所有敌人清除（Boss被击败）则通关
        if getattr(self, "_boss_mode", False) and self.state == self.PLAYING:
            if len(self.stars) == 0 and not getattr(self, "_boss_spawning", False):
                # Boss被击败，通关
                self._boss_advance_level()

        # 通关检测（无尽/BOSS模式不走普通通关逻辑）
        if (not getattr(self, "_endless_mode", False)
                and not getattr(self, "_boss_mode", False)
                and self.level_eaten >= self._get_levels()[self.current_level]["goal"]
                and self.state == self.PLAYING):
            self.state = self.LEVEL_COMPLETE
            self.lc_timer = 0.0
            self._play("win")
            # 副本通关：发放钻石奖励（每关 diamond_reward）
            if self.is_dungeon:
                lv = self._get_levels()[self.current_level]
                dr = int(lv.get("diamond_reward", 0))
                if dr > 0:
                    if getattr(self, "_infinite_diamonds", False):
                        self.diamonds = max(self.diamonds, 99999)
                    else:
                        self.diamonds += dr
                    self._flash_msg = f"副本 {lv['name']} 通关！获得钻石 +{dr}"
                    self._flash_timer = 2.4
                self._save_game()
            for p in self.players:
                if p.alive:
                    self.burst(p.x, p.y, NEON_YELLOW, 40, 340, size=3.5, life=0.9)
            self._check_achievements()

    # ---- 解析各玩家输入 -> [(vel, dash), ...] ----
    def _resolve_inputs(self):
        results = []
        if self.num_players == 1:
            p = self.player
            mode = self.control_mode
            if mode == "hand" and self.tracker.available and self.tracker.running:
                results.append((self.hand_vel, self.hand_dash))
            elif mode == "arrow":
                results.append((self.arrow_vel, self.p1_dash_key))
            else:  # mouse
                results.append((None, pygame.mouse.get_pressed()[0]))
        else:
            # 2P：P1 WASD+LSHIFT，P2 方向键+RSHIFT
            results.append((self.wasd_vel, self.p1_dash_key))
            results.append((self.arrow_vel, self.p2_dash_key))
        return results

    def _player_color(self):
        stage = min(len(STAGE_COLORS) - 1, self.current_level // 2)
        return STAGE_COLORS[stage]

    def _all_player_cells(self):
        """主玩家 + 分裂子细胞（用于碰撞/吞噬判定）。"""
        cells = []
        for p in self.players:
            if p.alive:
                cells.append(p)
        for c in self.split_cells:
            if c.alive:
                cells.append(c)
        return cells

    def _handle_right_click(self, mx, my):
        """右键：皮肤专有技能（替代旧的分裂操作）。
        单人模式：触发 P1 皮肤技能（指向鼠标位置）；
        双人模式：触发 P1 皮肤技能（P2 用 ] 键触发）。
        """
        if self.state != self.PLAYING:
            return
        if not self.player.alive:
            return
        # 右键专供 P1（含单人）
        self._skin_skill_at(self.player, mx, my, who="p1")

    # ---- 存档 / 读档 ----
    def _load_save(self):
        try:
            if os.path.isfile(SAVE_PATH):
                with open(SAVE_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.coins = int(data.get("coins", 0))
                self.diamonds = int(data.get("diamonds", 0))
                self.owned_skins = set(data.get("skins", []))
                self.active_skin = data.get("active") or None
                if self.active_skin and self.active_skin not in self.owned_skins:
                    self.active_skin = None
                # P2 皮肤
                self.active_skin_p2 = data.get("active_p2") or None
                if self.active_skin_p2 and self.active_skin_p2 not in self.owned_skins:
                    self.active_skin_p2 = None
                # 关卡进度持久化（顺序解锁）
                sv_unlock = int(data.get("unlocked", 1))
                self.unlocked = max(1, min(len(LEVELS), sv_unlock))
                self.map_cursor = min(self.map_cursor, self.unlocked - 1)
                # 副本解锁进度（0 表示没解锁过；默认主线通关后才给1）
                du = int(data.get("dungeon_unlocked", 0))
                # 主线16关全通关时默认至少解锁副本1关
                main_full = (self.unlocked >= len(LEVELS))
                if main_full and du == 0:
                    du = 1
                self.dungeon_unlocked = max(0, du) if du > 0 else (1 if main_full else 0)
                # 已使用的兑换码（避免重启游戏后重复兑换）
                self._redeem_used = set(data.get("redeem_used", []))
                # Q6/Q7：成就解锁记录 + 无尽高分 + 统计计数
                self._achievements_unlocked = set(int(x) for x in data.get("achievements", []))
                self._endless_high_score = int(data.get("endless_high_score", 0))
                self._endless_high_wave = int(data.get("endless_high_wave", 0))
                self._total_kills = int(data.get("total_kills", 0))
                self._max_combo = int(data.get("max_combo", 0))
                self._max_eaten = int(data.get("max_eaten", 0))
                self._games_played = int(data.get("games_played", 0))
                self._sign_in_date = data.get("sign_in_date", None)
                self._sign_in_streak = int(data.get("sign_in_streak", 0))
        except Exception as e:
            print(f"[存档] 读取失败: {e}")

    def _save_game(self):
        try:
            if not hasattr(self, "_redeem_used"):
                self._redeem_used = set()
            data = {"coins": self.coins,
                    "diamonds": self.diamonds,
                    "skins": list(self.owned_skins),
                    "active": self.active_skin,
                    "active_p2": self.active_skin_p2,
                    "unlocked": self.unlocked,
                    "dungeon_unlocked": getattr(self, "dungeon_unlocked", 0),
                    "redeem_used": list(self._redeem_used),
                    "achievements": sorted(self._achievements_unlocked),
                    "endless_high_score": getattr(self, "_endless_high_score", 0),
                    "endless_high_wave": getattr(self, "_endless_high_wave", 0),
                    "total_kills": getattr(self, "_total_kills", 0),
                    "max_combo": getattr(self, "_max_combo", 0),
                    "max_eaten": getattr(self, "_max_eaten", 0),
                    "games_played": getattr(self, "_games_played", 0),
                    "sign_in_date": getattr(self, "_sign_in_date", None),
                    "sign_in_streak": getattr(self, "_sign_in_streak", 0)}
            with open(SAVE_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)
        except Exception as e:
            print(f"[存档] 写入失败: {e}")

    # ---- 皮肤 ----
    def _skin_color(self, p):
        """返回当前皮肤主色（彩虹/三色会循环）。优先取玩家专属 skin。"""
        sk = getattr(p, "skin", None) or self.active_skin
        if not sk:
            return p.color
        t = pygame.time.get_ticks() * 0.001
        if sk == "rainbow":
            idx = getattr(p, "_rb_idx", 0)
            return RAINBOW_COLORS[idx % 7]
        if sk == "tri":
            # 三色灵球：根据当前形态显示主色
            cols = [(255, 70, 90), (255, 220, 80), (90, 130, 255)]  # 红/黄/蓝
            return cols[p.tri_mode % 3]
        if sk == "moon":
            return (220, 230, 255)
        if sk == "sun":
            return (255, 180, 60)
        if sk == "void":
            return (150, 70, 220)
        if sk == "inferno":
            return (255, 90 + int(40 * math.sin(t * 6)), 30)
        if sk == "frost":
            return (120, 200, 255)
        if sk == "thunder":
            return (255, 240, 100)
        if sk == "chaos":
            # 混沌：随时间循环多色
            palette = [(200, 80, 255), (255, 90, 30), (90, 200, 255), (255, 240, 100)]
            return palette[int(t * 1.2) % len(palette)]
        return p.color

    def _skin_update(self, dt):
        """皮肤周期能力（每 6s）。"""
        sk = self.active_skin
        if not sk or self.state != self.PLAYING:
            return
        p = self.player
        if not p.alive:
            return
        self.skin_tick += dt
        if self.skin_tick >= 6.0:
            self.skin_tick = 0.0
            if sk == "frost":
                # 冻结全场敌球 2s
                self._freeze_timer = 2.0
                for s in self.stars:
                    if s.danger and not s._dead:
                        s.vx *= 0.05
                        s.vy *= 0.05
                self.burst(p.x, p.y, (120, 200, 255), 40, 280, size=3.2, life=0.7)
                self._play("freeze")
            elif sk == "chaos":
                # 混沌新星：范围伤害 + 移速 buff + 灼烧
                self._do_shockwave(p)
                self._skin_buff_timer = 3.0
                self._chaos_burn = 3.0
        # 混沌 buff 计时
        if hasattr(self, "_skin_buff_timer") and self._skin_buff_timer > 0:
            self._skin_buff_timer -= dt
        # 冻结/灼烧计时
        if getattr(self, "_freeze_timer", 0) > 0:
            self._freeze_timer -= dt
        if getattr(self, "_chaos_burn", 0) > 0:
            self._chaos_burn -= dt

    def _skin_frame(self, dt):
        """皮肤每帧被动效果（炼狱灼烧 / 雷霆连锁 / 霜冻维持 / 混沌灼烧）。"""
        sk = self.active_skin
        if not sk or self.state != self.PLAYING:
            return
        p = self.player
        if not p.alive:
            return
        if sk == "inferno":
            # 灼烧光环：靠近的敌球持续掉血
            aura = p.r + 70
            # 右键灼烧环激活时，外环更大并持续灼烧
            ring_active = p._inferno_ring_timer > 0
            ring_r = p._inferno_base_r * 3 if ring_active else 0
            for s in self.stars:
                if s.danger and not s._dead:
                    if math.hypot(s.x - p.x, s.y - p.y) < aura + s.r:
                        self._damage_enemy(s, 1.5 * dt)
                    # 灼烧环：卡在外环内的敌球持续灼烧
                    if ring_active and ring_r > 0:
                        dist = math.hypot(s.x - p.x, s.y - p.y)
                        if p.r < dist < ring_r:
                            self._damage_enemy(s, 4.0 * dt)
            # 视觉：偶尔火星
            if random.random() < 0.5:
                a = random.uniform(0, math.tau)
                self.particles.append(Particle(
                    p.x + math.cos(a) * p.r, p.y + math.sin(a) * p.r,
                    math.cos(a) * 40, math.sin(a) * 40 - 30,
                    0.5, (255, 120, 40), 2.6))
            # 灼烧环视觉：外圈火焰
            if ring_active:
                for _ in range(3):
                    a = random.uniform(0, math.tau)
                    rr = random.uniform(p.r + 5, ring_r)
                    self.particles.append(Particle(
                        p.x + math.cos(a) * rr, p.y + math.sin(a) * rr,
                        math.cos(a) * 30, math.sin(a) * 30 - 20,
                        0.4, (255, 80, 20), 3.2))
        if sk == "sun" and p._sun_glow_timer > 0:
            # 烈阳发光：排斥所有靠近的敌球（含大球）
            repel_r = 200
            for s in self.stars:
                if not s._dead:
                    dx = s.x - p.x
                    dy = s.y - p.y
                    d = math.hypot(dx, dy) or 1
                    if d < repel_r:
                        # 排斥力：越近越强
                        force = (1 - d / repel_r) * 400
                        s.vx += (dx / d) * force * dt
                        s.vy += (dy / d) * force * dt
            # 发光视觉
            if random.random() < 0.8:
                a = random.uniform(0, math.tau)
                self.particles.append(Particle(
                    p.x + math.cos(a) * p.r, p.y + math.sin(a) * p.r,
                    math.cos(a) * 80, math.sin(a) * 80,
                    0.3, (255, 220, 100), 3.0))
        elif sk == "thunder":
            # 自动连锁闪电（带冷却）
            now = pygame.time.get_ticks()
            if now - getattr(self, "_thunder_cd", -9999) > 1100:
                targets = []
                for s in self.stars:
                    if s.danger and not s._dead:
                        if math.hypot(s.x - p.x, s.y - p.y) < 260:
                            targets.append(s)
                    if len(targets) >= 3:
                        break
                if targets:
                    self._thunder_cd = now
                    self._play("thunder")
                    prev = (p.x, p.y)
                    for s in targets:
                        self._chain_bolt(prev, (s.x, s.y))
                        self._damage_enemy(s, 1, p)
                        prev = (s.x, s.y)
                    self._chain_bolt(prev, (p.x, p.y))
        elif sk == "frost":
            # 维持冻结：敌球速度被压制（仅冻结计时内强压制）
            if getattr(self, "_freeze_timer", 0) > 0:
                for s in self.stars:
                    if s.danger and not s._dead:
                        s.vx *= 0.92
                        s.vy *= 0.92
        elif sk == "chaos":
            # 混沌灼烧光环（继承炼狱）
            if getattr(self, "_chaos_burn", 0) > 0:
                aura = p.r + 80
                for s in self.stars:
                    if s.danger and not s._dead:
                        if math.hypot(s.x - p.x, s.y - p.y) < aura + s.r:
                            self._damage_enemy(s, 2.0 * dt)

    def _chain_bolt(self, a, b):
        """绘制一道折线闪电特效（短暂粒子）。"""
        steps = 5
        for i in range(steps):
            t1 = i / steps
            t2 = (i + 1) / steps
            x1 = a[0] + (b[0] - a[0]) * t1 + random.uniform(-8, 8)
            y1 = a[1] + (b[1] - a[1]) * t1 + random.uniform(-8, 8)
            x2 = a[0] + (b[0] - a[0]) * t2 + random.uniform(-8, 8)
            y2 = a[1] + (b[1] - a[1]) * t2 + random.uniform(-8, 8)
            self.particles.append(Particle(
                (x1 + x2) / 2, (y1 + y2) / 2, 0, 0, 0.18,
                (255, 240, 150), 3.0))
        self.burst(b[0], b[1], (255, 240, 150), 8, 220, size=2.4, life=0.3)

    def _skin_on_click(self, mx, my):
        """单击触发的皮肤能力（鼠标右键 / B / ] 触发）。
        返回 True 表示该皮肤有主动技能。
        """
        sk = self.active_skin
        if not sk or self.state != self.PLAYING:
            return False
        p = self.player
        if not p.alive:
            return False
        # 通用冷却（避免刷屏）
        now = pygame.time.get_ticks()
        cd_attr = f"_skill_cd_{sk}"
        cd_map = {"inferno": 800, "frost": 1500, "thunder": 600,
                  "chaos": 1200, "rainbow": 350, "void": 1500,
                  "sun": 1200, "tri": 1500, "moon": 1500,
                  "judge": 1800, "dragon": 2200, "demon": 2000,
                  "stellar": 2400, "samsara": 3000, "寂灭": 2800,
                  "primal": 3200, "taiji": 2600, "nirvana": 3500}
        cd = cd_map.get(sk, 800)
        if now - getattr(self, cd_attr, -99999) < cd:
            return True
        setattr(self, cd_attr, now)

        # 皮肤右键技能耗能配置（合理化，不再全部100）
        if sk == "rainbow":
            # 虹光：右键切换颜色（消耗100%所有能量，且切换后立即持续施放该色道具5秒）
            if p.energy < 30.0:
                self._flash_msg = "能量不足(需30)，无法切换虹光"
                self._flash_timer = 1.0
                return True
            idx = (getattr(p, "_rb_idx", 0) + 1) % 7
            p._rb_idx = idx
            # 消耗全部能量（100%）
            p._energy_depleted = True
            p.energy = 0.0
            eff = RAINBOW_EFFECTS[idx]
            col = RAINBOW_COLORS[idx]
            # 切色后立即用时长倍率 ×5 激活对应色道具（可玩性增强）
            old_durations = dict(POWERUP_DURATION)
            for k in POWERUP_DURATION:
                POWERUP_DURATION[k] = POWERUP_DURATION[k] * 5.0
            self.apply_powerup(eff, p)
            POWERUP_DURATION.update(old_durations)
            self.burst(p.x, p.y, col, 64, 460, size=4.5, life=0.95)
            self._flash_msg = f"虹光爆发·{RAINBOW_NAMES[idx]} 已激活！"
            self._flash_timer = 1.4
            self._play("powerup")
            return True
        if sk == "inferno":
            # 炼狱：右键变大灼烧环3.5s（消耗70能）
            if p.energy < 70.0:
                self._flash_msg = "能量不足(需70)，无法释放灼烧环"
                self._flash_timer = 1.0
                return True
            p._inferno_ring_timer = 3.5
            p._inferno_base_r = p.r
            p.r = max(12.0, p.r * 0.5)
            p.energy = max(0.0, p.energy - 70.0)
            if p.energy <= 0:
                p._energy_depleted = True
            self._inferno_burn = 3.5
            self.burst(p.x, p.y, (255, 90, 30), 40, 300, size=3.5, life=0.7)
            self._flash_msg = "炼狱灼烧环！3.5s"
            self._flash_timer = 1.6
            self._play("powerup")
            return True
        if sk == "frost":
            # 霜冻：消耗能量冻结全场（消耗40能起，不足按比例缩短）
            if p.energy < 20.0:
                self._flash_msg = "能量不足(需20+)，无法冻结全场"
                self._flash_timer = 1.0
                return True
            cost = min(70.0, p.energy)
            freeze_sec = 0.8 + (cost / 70.0) * 2.5
            p.energy = max(0.0, p.energy - cost)
            if p.energy <= 0:
                p._energy_depleted = True
            self._freeze_timer = freeze_sec
            for s in self.stars:
                if s.danger and not s._dead:
                    s.frozen_timer = max(s.frozen_timer, freeze_sec)
                    s.vx *= 0.03; s.vy *= 0.03
                    s.hit_flash = 0.2
                    for zz in range(10):
                        a = zz * (math.tau / 10)
                        self.particles.append(
                            (s.x + math.cos(a) * s.r,
                             s.y + math.sin(a) * s.r,
                             math.cos(a) * 120, math.sin(a) * 120,
                             0.9, (220, 240, 255), 2.8))
            self.burst(p.x, p.y, (120, 200, 255), 60, 340, size=3.8, life=0.9)
            self._flash_msg = f"全场冰冻 {freeze_sec:.1f}s！"
            self._flash_timer = 1.4
            self._play("freeze")
            return True
        if sk == "thunder":
            # 雷霆：右键球周围放出雷电（持续2.5s，消耗50能）
            if p.energy < 50.0:
                self._flash_msg = "能量不足(需50)，无法释放雷电场"
                self._flash_timer = 1.0
                return True
            p.energy = max(0.0, p.energy - 50.0)
            if p.energy <= 0:
                p._energy_depleted = True
            self.thunder_field_timer = 2.5
            self._flash_msg = "雷电场！2.5s"
            self._flash_timer = 1.4
            self._play("thunder")
            return True
        if sk == "void":
            # 深渊：右键朝着6个方向发射黑洞（消耗80能）
            if p.energy < 80.0:
                self._flash_msg = "能量不足(需80)，无法释放六向黑洞"
                self._flash_timer = 1.0
                return True
            p.energy = max(0.0, p.energy - 80.0)
            if p.energy <= 0:
                p._energy_depleted = True
            for i in range(6):
                a = i * (math.tau / 6)
                self.void_holes.append({
                    "x": p.x, "y": p.y,
                    "vx": math.cos(a) * 280, "vy": math.sin(a) * 280,
                    "timer": 2.5, "max": 2.5, "r": 80, "owner": p,
                    "_dead": False, "spiral": False
                })
            self._flash_msg = "六向黑洞清屏！"
            self._flash_timer = 1.4
            self._play("powerup")
            return True
        if sk == "chaos":
            # 混沌：右键 → 消耗100%所有能量，六剑模式持续 14 秒 + 立即引爆周围敌人一次爆炸
            if p.energy < 20.0:
                self._flash_msg = "能量不足(需20+)，混沌魔神六剑无法启动"
                self._flash_timer = 1.0
                return True
            p._chaos_sword_timer = 14.0
            # 消耗全部能量（100%）
            p._energy_depleted = True
            p.energy = 0.0
            # 立即对大范围内敌人造成爆炸伤害+粒子（霸气视觉）
            for s in list(self.stars):
                if s.danger and not s._dead:
                    d = math.hypot(s.x - p.x, s.y - p.y)
                    if d < 260:
                        s.hp -= 5.0
                        s.hit_flash = 0.25
                        # 击退
                        dx_ = (s.x - p.x); dy_ = (s.y - p.y); d_ = d or 1
                        s.vx += dx_ / d_ * 380
                        s.vy += dy_ / d_ * 380
                        if s.hp <= 0:
                            s._dead = True
                            self.burst(s.x, s.y, s.color, 18, 240, size=3.2, life=0.6)
            self.burst(p.x, p.y, (200, 80, 255), 90, 520, size=5.2, life=1.1)
            self._flash_msg = "混沌魔神·万剑归宗！14s + 领域爆发！"
            self._flash_timer = 1.9
            self._play("shockwave")
            return True
        if sk == "sun":
            # 烈阳：右键释放全局光波击退所有敌球（消耗70能）
            if p.energy < 70.0:
                self._flash_msg = "能量不足(需70)，无法释放全局光波"
                self._flash_timer = 1.0
                return True
            p.energy = max(0.0, p.energy - 70.0)
            if p.energy <= 0:
                p._energy_depleted = True
            self._sun_global_blast(p)
            return True
        if sk == "tri":
            # 三色灵球：右键切换红/黄/蓝三态（消耗25能）
            if p.energy < 25.0:
                self._flash_msg = "能量不足(需25)，无法切换三色形态"
                self._flash_timer = 1.0
                return True
            names = ["红球·吐炸弹", "黄球·护盾", "蓝球·加速"]
            colors = [(255, 70, 90), (255, 220, 80), (90, 130, 255)]
            p.tri_mode = (p.tri_mode + 1) % 3
            p.energy = max(0.0, p.energy - 25.0)
            if p.energy <= 0:
                p._energy_depleted = True
            c = colors[p.tri_mode]
            self.burst(p.x, p.y, c, 30, 260, size=3.0, life=0.6)
            self._flash_msg = f"切换为 {names[p.tri_mode]}"
            self._flash_timer = 1.6
            self._play("powerup")
            return True
        if sk == "moon":
            # 月华之球：右键切换缩小/还原（消耗35能）
            if p.energy < 35.0:
                self._flash_msg = "能量不足(需35)，无法使用月华技能"
                self._flash_timer = 1.0
                return True
            p.energy = max(0.0, p.energy - 35.0)
            if p.energy <= 0:
                p._energy_depleted = True
            if p.moon_shrunk:
                # 还原
                p.r = p.r / 0.7
                p.moon_shrunk = False
                self._flash_msg = "月华：还原大小"
            else:
                # 缩小 30% + 分裂特效
                p.r = max(12.0, p.r * 0.7)
                p.moon_shrunk = True
                self._flash_msg = "月华：缩小30% 更易躲避"
                # 分裂视觉特效
                for i in range(12):
                    a = i * (math.tau / 12)
                    self.particles.append(Particle(
                        p.x, p.y,
                        math.cos(a) * 120, math.sin(a) * 120,
                        0.6, (220, 230, 255), 4.0))
            self.burst(p.x, p.y, (220, 230, 255), 24, 220, size=2.8, life=0.55)
            self._play("powerup")
            return True
        # =============== 钻石皮肤右键 ===============
        if sk == "judge":
            # 天罚之眼：天眼激光横扫（朝鼠标方向）
            if p.energy < 60:
                self._flash_msg = "能量不足(需60)"
                self._flash_timer = 1.0
                return True
            p.energy -= 60
            if p.energy <= 0: p._energy_depleted = True
            dx = mx - p.x; dy = my - p.y
            ang_base = math.atan2(dy, dx)
            # 生成 13 道横扫激光（覆盖 ±45°）
            for i in range(-6, 7):
                ang = ang_base + i * 0.09
                for t in range(1, 22):
                    bx = p.x + math.cos(ang) * t * 38
                    by = p.y + math.sin(ang) * t * 38
                    for s in self.stars:
                        if s.danger and not s._dead:
                            if math.hypot(s.x - bx, s.y - by) < s.r + 28:
                                self._damage_enemy(s, 2.2, p)
                    self.particles.append((bx, by, random.uniform(-6,6), random.uniform(-6,6),
                                           0.22, (255, 245, 220), 3.0))
            self.burst(p.x, p.y, (255, 240, 200), 40, 400, size=3.2, life=0.5)
            self._flash_msg = "天罚·天眼激光横扫！"
            self._flash_timer = 1.2
            self._play("thunder")
            return True
        if sk == "dragon":
            # 真龙帝皇：咆哮龙卷·消耗100%所有能量，全屏敌人击退+大量伤害+龙息爆炸粒子
            if p.energy < 40:
                self._flash_msg = "能量不足(需40+)，真龙帝皇咆哮无法启动"
                self._flash_timer = 1.0
                return True
            # 消耗全部能量（100%）——先保存当前能量用于伤害计算
            p._energy_depleted = True
            all_energy = max(40.0, float(p.energy))
            p.energy = 0.0
            # 伤害按消耗能量放大（能量越多越霸气）
            dmg = 4.0 + all_energy * 0.05
            force = 1200 + all_energy * 6
            # 从玩家扩散到屏幕四角 4 条龙形轨迹
            for s in list(self.stars):
                if s.danger and not s._dead:
                    dx = s.x - p.x
                    dy = s.y - p.y
                    d = math.hypot(dx, dy) or 1
                    s.vx += dx / d * force
                    s.vy += dy / d * force
                    self._damage_enemy(s, dmg, p)
                    s.hit_flash = 0.3
            # 龙息爆炸：3 层同心粒子
            for rr, cnt, col in ((30, 70, (255, 120, 40)),
                                 (80, 90, (255, 200, 80)),
                                 (180, 60, (255, 240, 160))):
                for i in range(cnt):
                    a = i * (math.tau / cnt)
                    self.particles.append(
                        (p.x + math.cos(a) * rr * 0.15, p.y + math.sin(a) * rr * 0.15,
                         math.cos(a) * (360 + rr), math.sin(a) * (360 + rr),
                         0.9, col, 4.4))
            self.burst(p.x, p.y, (255, 180, 80), 120, 640, size=5.6, life=1.2)
            self._flash_msg = "真龙帝皇·咆哮龙卷！全屏弹飞+爆伤！"
            self._flash_timer = 1.8
            self._play("warn")
            return True
        if sk == "demon":
            # 九幽魔君：召唤骷髅群吸血
            if p.energy < 85:
                self._flash_msg = "能量不足(需85)"
                self._flash_timer = 1.0
                return True
            p.energy -= 85
            if p.energy <= 0: p._energy_depleted = True
            skel_num = 10
            for i in range(skel_num):
                a = i * (math.tau / skel_num) + random.uniform(-0.2, 0.2)
                sx = p.x + math.cos(a) * 80
                sy = p.y + math.sin(a) * 80
                tgt = None
                tgt_d = 1e9
                for s in self.stars:
                    if s.danger and not s._dead:
                        dd = math.hypot(s.x - sx, s.y - sy)
                        if dd < tgt_d:
                            tgt_d = dd; tgt = s
                if tgt is None:
                    continue
                ddx = tgt.x - sx; ddy = tgt.y - sy
                dd = math.hypot(ddx, ddy) or 1
                spd = 340
                vx = ddx / dd * spd
                vy = ddy / dd * spd
                # 骷髅 = 高速追踪目标的小投射物（放入 demon_clouds 统一处理）
                self.demon_clouds.append({
                    "x": sx, "y": sy, "vx": vx, "vy": vy,
                    "life": 2.0, "r": 12, "owner": p, "_dead": False
                })
            self.burst(p.x, p.y, (180, 60, 255), 30, 280, size=3.2, life=0.7)
            self._flash_msg = "九幽之门·召唤骷髅吸血！"
            self._flash_timer = 1.4
            self._play("powerup")
            return True
        if sk == "stellar":
            # 星海主宰：召唤陨石雨（+ 星轨环绕 3 秒，有视觉冲突特效）
            if p.energy < 90:
                self._flash_msg = "能量不足(需90)"
                self._flash_timer = 1.0
                return True
            p.energy -= 90
            if p.energy <= 0: p._energy_depleted = True
            # 32 颗大陨石从上方坠落 → 目标围绕玩家 + 鼠标周围
            for i in range(32):
                tx_ = p.x + random.uniform(-340, 340)
                ty_ = p.y + random.uniform(-240, 240)
                sx_ = tx_ + random.uniform(-200, 200)
                sy_ = -40 - random.randint(0, 600)
                ang_ = math.atan2(ty_ - sy_, tx_ - sx_)
                spd_ = 540 + random.uniform(-60, 120)
                self.stargod_meteors.append({
                    "x": sx_, "y": sy_,
                    "vx": math.cos(ang_) * spd_,
                    "vy": math.sin(ang_) * spd_,
                    "r": random.uniform(32, 56),
                    "life": 4.5, "max": 4.5,
                    "owner": p, "_dead": False
                })
            # 额外：在玩家身边散出一圈星轨粒子（环绕感）
            for i in range(90):
                a_ = i * (math.tau / 90)
                rr_ = 70 + random.uniform(-8, 18)
                self.particles.append((
                    p.x + math.cos(a_) * rr_,
                    p.y + math.sin(a_) * rr_,
                    math.cos(a_) * 260 + random.uniform(-40, 40),
                    math.sin(a_) * 260 + random.uniform(-40, 40),
                    0.85, (190, 230, 255), 4.2
                ))
            self.burst(p.x, p.y, (150, 220, 255), 80, 520, size=5.0, life=1.0)
            self.shake = max(self.shake, 0.55)
            self._flash_msg = "星海主宰·星辰陨石雨·宇宙降临！"
            self._flash_timer = 1.7
            self._play("warn")
            return True
        if sk == "samsara":
            # Q3：六道轮回右键：全球360度外围长满球弹，自动瞄准追踪并造成爆炸和弹开敌人
            if p.energy < 60:
                self._flash_msg = "能量不足(需60)"
                self._flash_timer = 1.0
                return True
            p.energy -= 60
            if p.energy <= 0: p._energy_depleted = True
            samsara_blades = getattr(self, "samsara_blades", None)
            if samsara_blades is None:
                self.samsara_blades = []
                samsara_blades = self.samsara_blades
            # 360度外围生成 20 颗球弹，自动追踪最近敌人
            num = 20
            for i in range(num):
                a = i * (math.tau / num)
                rr = 80  # 外围半径
                sx = p.x + math.cos(a) * rr
                sy = p.y + math.sin(a) * rr
                samsara_blades.append({
                    "x": sx, "y": sy,
                    "vx": math.cos(a) * 340, "vy": math.sin(a) * 340,
                    "life": 4.0, "r": 14, "owner": p, "_dead": False,
                    "pierced": set(),
                    "track": True,
                    "explode": True,
                    "explode_r": 140,
                    "explode_dmg": 5.0,
                    "hit_cd": {}
                })
            # 360度爆发粒子
            for ring, col in ((60, (200, 160, 255)), (120, (230, 210, 255)), (200, (180, 120, 255))):
                for i in range(60):
                    a = i * (math.tau / 60)
                    self.particles.append((
                        p.x + math.cos(a) * ring * 0.12,
                        p.y + math.sin(a) * ring * 0.12,
                        math.cos(a) * (260 + ring),
                        math.sin(a) * (260 + ring),
                        0.85, col, 3.6
                    ))
            self.burst(p.x, p.y, (200, 160, 255), 80, 560, size=5.2, life=1.0)
            self.shake = max(self.shake, 0.5)
            self._flash_msg = "六道轮回·360度球弹轰炸！自动追踪爆炸！"
            self._flash_timer = 1.8
            self._play("powerup")
            return True
        if sk == "寂灭":
            # Q4：寂灭神皇右键：自身留下毁灭火莲，一闪一闪的，3s后造成大范围爆炸伤害，自身无影响
            if p.energy < 70:
                self._flash_msg = "能量不足(需70)"
                self._flash_timer = 1.0
                return True
            p.energy -= 70
            if p.energy <= 0: p._energy_depleted = True
            if not hasattr(self, "寂灭_lotus"):
                self.寂灭_lotus = []
            # 在自身位置留下一朵毁灭火莲（固定位置，不跟随）
            self.寂灭_lotus.append({
                "x": p.x, "y": p.y,
                "vx": 0.0, "vy": 0.0,
                "r": 30, "life": 3.0, "owner": p, "_dead": False,
                "phase": 0.0,
                "fire_lotus": True,      # Q4：毁灭火莲类型
                "timer": 3.0,            # 3秒倒计时
                "explode_r": 320,        # 大范围爆炸
                "explode_dmg": 9.0,
                "no_self_damage": True   # 自身无影响
            })
            # 留下火莲时的粒子
            for i in range(30):
                a = random.uniform(0, math.tau)
                rr = random.uniform(10, 50)
                self.particles.append((
                    p.x + math.cos(a) * rr * 0.1,
                    p.y + math.sin(a) * rr * 0.1,
                    math.cos(a) * (80 + rr),
                    math.sin(a) * (80 + rr),
                    0.6,
                    random.choice([(255, 100, 30), (255, 160, 60), (255, 60, 20)]),
                    3.4
                ))
            self._flash_msg = "寂灭神皇·毁灭火莲！3秒后大范围爆炸！"
            self._flash_timer = 1.8
            self._play("warn")
            return True
        if sk == "primal":
            # 鸿蒙之始：两仪生灭 - 蓝圆(排斥) + 红圆(吸入)
            if p.energy < 100:
                self._flash_msg = "能量不足(需100)"
                self._flash_timer = 1.0
                return True
            p.energy -= 100
            if p.energy <= 0: p._energy_depleted = True
            dx = mx - p.x; dy = my - p.y
            d = math.hypot(dx, dy) or 1
            offs = 140
            a0 = math.atan2(dy, dx)
            for sgn, bh_type in ((-1, "repel"), (1, "attract")):
                a = a0 + sgn * 0.6
                sx = p.x + math.cos(a) * offs
                sy = p.y + math.sin(a) * offs
                bh_vx = math.cos(a) * 180
                bh_vy = math.sin(a) * 180
                self.void_holes.append({
                    "x": sx, "y": sy, "vx": bh_vx, "vy": bh_vy,
                    "_orig_vx": bh_vx, "_orig_vy": bh_vy,
                    "timer": 3.5, "max": 3.5, "r": 130, "owner": p, "_dead": False,
                    "spiral": True, "spiral_phase": 0.0,
                    "spiral_center": (sx, sy),
                    "bh_type": bh_type  # "repel"=蓝排斥, "attract"=红吸入
                })
            # 蓝色排斥爆发 + 红色吸入爆发
            for col, off in (((80, 160, 255), -0.6), ((255, 80, 80), 0.6)):
                bx = p.x + math.cos(a0 + off) * offs
                by = p.y + math.sin(a0 + off) * offs
                self.burst(bx, by, col, 30, 300, size=3.8, life=0.7)
            self._flash_msg = "两仪生灭 - 蓝圆排斥 + 红圆吸入！"
            self._flash_timer = 1.4
            self._play("powerup")
            return True
        if sk == "taiji":
            # 太上无极：太极阵·反弹+减速14秒 + 启动瞬间爆发伤害 + 阵内周期发射两仪剑
            if p.energy < 80:
                self._flash_msg = "能量不足(需80)"
                self._flash_timer = 1.0
                return True
            p.energy -= 80
            if p.energy <= 0: p._energy_depleted = True
            p._taiji_timer = 14.0
            # 启动瞬间大范围爆炸+击退
            R_ = 320
            for s in list(self.stars):
                if s.danger and not s._dead:
                    dd = math.hypot(s.x - p.x, s.y - p.y)
                    if dd < R_:
                        self._damage_enemy(s, 4.5, p)
                        s.hit_flash = 0.25
                        # 反弹
                        dx_ = s.x - p.x; dy_ = s.y - p.y; L_ = dd or 1
                        s.vx += dx_ / L_ * 680
                        s.vy += dy_ / L_ * 680
            # 太极爆发：青、红双色巨型粒子
            for ring, col in ((60, (90, 220, 255)), (140, (255, 90, 90)), (260, (240, 240, 220))):
                for i in range(70):
                    a = i * (math.tau / 70)
                    self.particles.append((
                        p.x + math.cos(a) * ring * 0.12,
                        p.y + math.sin(a) * ring * 0.12,
                        math.cos(a) * (420 + ring),
                        math.sin(a) * (420 + ring),
                        0.9, col, 4.4
                    ))
            # 周期自动发射两仪剑的相位
            p._taiji_blade_phase = 0.0
            self.shake = max(self.shake, 0.6)
            self.burst(p.x, p.y, (240, 240, 220), 80, 520, size=5.4, life=1.1)
            self._flash_msg = "太上无极·太极阵14秒！爆发+反弹+自动双剑！"
            self._flash_timer = 1.7
            self._play("warn")
            return True
        if sk == "nirvana":
            # 大道涅槃：凤凰护体·灼烧凤凰环绕360°+2秒无敌（耗尽100%能量）
            if p.energy < 40:
                self._flash_msg = "能量不足(需40)"
                self._flash_timer = 1.0
                return True
            # 耗尽 100% 能量
            p.energy = 0.0
            p._energy_depleted = True
            # 环绕凤凰 2 秒 + 2 秒无敌
            p._nirvana_orbit = 2.0
            p._nirvana_orbit_phase = 0.0
            p._nirvana_orbit_tick = 0.0
            p.invulnerable = max(p.invulnerable, 2.0)
            # 启动瞬间金色爆炸视觉
            self.burst(p.x, p.y, (255, 220, 120), 80, 480, size=5.2, life=1.0)
            for i in range(40):
                a = random.uniform(0, math.tau)
                self.particles.append((
                    p.x, p.y,
                    math.cos(a) * random.uniform(120, 380),
                    math.sin(a) * random.uniform(120, 380),
                    0.7,
                    random.choice([(255, 200, 80), (255, 120, 40), (255, 240, 140)]),
                    4.0
                ))
            self.shake = max(self.shake, 0.6)
            self._flash_msg = "大道涅槃·凤凰护体！2秒无敌！"
            self._flash_timer = 1.6
            self._play("shockwave")
            return True
        # ===== 第三页 至高霸气皮肤右键（全面重制，更霸气+多种技能组合） =====
        if sk == "titan":
            # 裂空雷将：六雷震世·全屏6颗全局雷弹爆炸+击退（至强技能）
            if p.energy < 70:
                self._flash_msg = "能量不足(需70)"
                self._flash_timer = 1.0
                return True
            p.energy -= 70
            if p.energy <= 0: p._energy_depleted = True
            # 全屏 6 颗雷弹：玩家6方向+屏幕内随机4位置（总共6个）+ 每颗落地 260 半径爆炸
            spawns = []
            for i in range(6):
                a = i * (math.tau / 6) + 0.25
                spawns.append((p.x + math.cos(a) * 260,
                               p.y + math.sin(a) * 260))
            for i, (sx, sy) in enumerate(spawns):
                # 把雷弹放进 titan_hammers：立即落地爆炸
                self.titan_hammers.append({
                    "x": p.x, "y": p.y,
                    "vx": (sx - p.x), "vy": (sy - p.y),
                    "r": 24, "life": 1.2, "max": 1.2, "hit_cd": {},
                    "owner": p, "_dead": False,
                    "global_bomb": True,
                    "land_x": sx, "land_y": sy,
                    "spark_phase": 0.0
                })
                # 即时 6 处爆炸（全局雷弹落地位置立即炸）
                self.burst(sx, sy, (120, 180, 255), 55, 480, size=5.2, life=1.0)
                for s in list(self.stars):
                    if s.danger and not s._dead:
                        dd = math.hypot(s.x - sx, s.y - sy)
                        if dd < 260:
                            f = 1 - dd / 260
                            self._damage_enemy(s, 4.0 * f + 3.0, owner=p)
                            dx_ = (s.x - sx) / (dd or 1)
                            dy_ = (s.y - sy) / (dd or 1)
                            s.vx += dx_ * 620
                            s.vy += dy_ * 620
            self.shake = max(self.shake, 0.6)
            self._flash_msg = "裂空雷将·六雷震世！全屏爆炸！"
            self._flash_timer = 1.8
            self._play("thunder")
            return True
        if sk == "qinglong":
            # 沧溟潮君：沧海横流·六道潮卷环绕护体+全屏潮涌冲击波（至强技能）
            if p.energy < 80:
                self._flash_msg = "能量不足(需80)"
                self._flash_timer = 1.0
                return True
            p.energy -= 80
            if p.energy <= 0: p._energy_depleted = True
            p._qinglong_timer = 12.0
            # 全屏潮涌冲击波：所有敌人被海浪推离
            for s in self.stars:
                if s.danger and not s._dead:
                    dd = math.hypot(s.x - p.x, s.y - p.y) or 1
                    f = 1 - min(1.0, dd / 1200)
                    dx_ = (s.x - p.x) / dd
                    dy_ = (s.y - p.y) / dd
                    self._damage_enemy(s, 4.0 * f + 2.5, owner=p)
                    s.vx += dx_ * 900 * f
                    s.vy += dy_ * 900 * f
            # 6 道潮卷护体（放在 qinglong_dragons kind="tornado"）
            for i in range(6):
                a = i * (math.tau / 6)
                self.qinglong_dragons.append({
                    "kind": "tornado",
                    "x": p.x + math.cos(a) * 70,
                    "y": p.y + math.sin(a) * 70,
                    "phase": a, "r": 26,
                    "life": 12.0, "max": 12.0,
                    "owner": p, "_dead": False,
                    "explode_dmg": 5.0, "explode_r": 160
                })
            self.shake = max(self.shake, 0.55)
            self._flash_msg = "沧溟潮君·沧海横流·六道潮卷护体！"
            self._flash_timer = 1.9
            self._play("warn")
            return True
        if sk == "baihu":
            # 碎雪巡使：圆环刃·360度逐渐扩大的圆环刃（能耗65）
            if p.energy < 65:
                self._flash_msg = "能量不足(需65)"
                self._flash_timer = 1.0
                return True
            p.energy -= 65
            if p.energy <= 0: p._energy_depleted = True
            if not hasattr(self, "baihu_rings"):
                self.baihu_rings = []
            # 圆环刃：从玩家位置以 20 半径开始向外扩张到 400
            self.baihu_rings.append({
                "x": p.x, "y": p.y,
                "r": 20, "max_r": 400, "life": 1.5, "max": 1.5,
                "owner": p, "_dead": False, "hit": set(),
                "dmg": 5.0, "expand_speed": 280
            })
            # 雪花+白风暴粒子（3 层）
            for ring, col in ((80, (240, 250, 255)), (160, (255, 255, 255)), (260, (210, 230, 255))):
                for k in range(60):
                    a = random.uniform(0, math.tau)
                    self.particles.append(Particle(
                        p.x, p.y,
                        math.cos(a) * (300 + ring),
                        math.sin(a) * (300 + ring),
                        0.9, col, 3.4
                    ))
            self.burst(p.x, p.y, (240, 240, 240), 90, 520, size=5.4, life=1.1)
            self.shake = max(self.shake, 0.5)
            self._flash_msg = "碎雪巡使·圆环刃！360度扩张切割！"
            self._flash_timer = 1.8
            self._play("thunder")
            return True
        if sk == "zhuque":
            # 燎原武侯：火龙卷风·向前发射龙卷风卷敌前进（能耗85）
            if p.energy < 85:
                self._flash_msg = "能量不足(需85)"
                self._flash_timer = 1.0
                return True
            p.energy -= 85
            if p.energy <= 0: p._energy_depleted = True
            if not hasattr(self, "zhuque_tornados"):
                self.zhuque_tornados = []
            dx_ = mx - p.x; dy_ = my - p.y; d_ = math.hypot(dx_, dy_) or 1
            self.zhuque_tornados.append({
                "x": p.x + dx_ / d_ * (p.r + 20),
                "y": p.y + dy_ / d_ * (p.r + 20),
                "vx": dx_ / d_ * 200, "vy": dy_ / d_ * 200,
                "r": 80, "life": 3.0, "max": 3.0,
                "owner": p, "_dead": False, "hit_cd": {},
                "spin_phase": 0.0
            })
            # 火凤爆发粒子（发射瞬间）
            for ring, col, cnt in ((100, (255, 120, 60), 80),
                                   (200, (255, 200, 80), 100),
                                   (320, (255, 240, 160), 90)):
                for k in range(cnt):
                    a = random.uniform(0, math.tau)
                    self.particles.append(Particle(
                        p.x, p.y,
                        math.cos(a) * (360 + ring),
                        math.sin(a) * (360 + ring),
                        0.9, col, 3.6
                    ))
            self.burst(p.x, p.y, (255, 120, 60), 100, 560, size=5.8, life=1.2)
            self.shake = max(self.shake, 0.55)
            self._flash_msg = "燎原武侯·火龙卷风！卷敌前进！"
            self._flash_timer = 1.9
            self._play("powerup")
            return True
        if sk == "xuanwu":
            # 玄冰卫圣：寒冰裂渊·开洞召唤冰锥雨（单点不穿透，密集高伤）
            if p.energy < 85:
                self._flash_msg = "能量不足(需85)"
                self._flash_timer = 1.0
                return True
            p.energy -= 85
            if p.energy <= 0: p._energy_depleted = True
            # 开洞：鼠标位置为中心，在屏幕上方落下 36 根冰锥（单点爆炸不穿透）
            if not hasattr(self, "xuanwu_ices"):
                self.xuanwu_ices = []
            for i in range(36):
                # 落点：鼠标为中心，随机 220 半径内
                off_a = random.uniform(0, math.tau)
                off_r = random.uniform(10, 220)
                land_x = mx + math.cos(off_a) * off_r
                land_y = my + math.sin(off_a) * off_r
                # 从上方飞下
                start_x = land_x + random.uniform(-40, 40)
                start_y = land_y - HEIGHT * 0.6 - random.uniform(0, 200)
                ang_ = math.atan2(land_y - start_y, land_x - start_x)
                self.xuanwu_ices.append({
                    "x": start_x, "y": start_y,
                    "vx": math.cos(ang_) * 560, "vy": math.sin(ang_) * 560,
                    "r": 16, "life": 4.0, "max": 4.0,
                    "owner": p, "_dead": False,
                    "rain_spike": True,  # 冰锥雨：单点不穿透，碰到就爆
                    "pierced": False,
                    "freeze": True
                })
            # 开洞特效：屏幕上方落下冰雾 + 鼠标位置 3 层爆炸
            for ring, col in ((70, (160, 220, 255)), (150, (200, 240, 255)), (260, (140, 200, 255))):
                for k in range(70):
                    a = random.uniform(0, math.tau)
                    self.particles.append(Particle(
                        mx, my,
                        math.cos(a) * (260 + ring),
                        math.sin(a) * (260 + ring) - 60,
                        0.9, col, 3.6
                    ))
            self.burst(mx, my, (80, 140, 220), 90, 520, size=5.4, life=1.1)
            self.shake = max(self.shake, 0.5)
            self._flash_msg = "玄冰卫圣·寒冰裂渊！冰锥雨降临！"
            self._flash_timer = 1.9
            self._play("warn")
            return True
        if sk == "stargod":
            # 星陨领主：八曜护世·8颗恒星护体自转碰一个爆一个+击退（至强护体）
            if p.energy < 80:
                self._flash_msg = "能量不足(需80)"
                self._flash_timer = 1.0
                return True
            p.energy -= 80
            if p.energy <= 0: p._energy_depleted = True
            p._stargod_timer = 14.0
            p._stargod_phase = [i * math.tau / 8 for i in range(8)]
            # 八曜护体每颗属性（碰撞后该颗立即爆炸消失，下一颗接上来）
            p._stargod_sun_hp = [2 for _ in range(8)]  # 每颗 2 点碰撞次数
            self.burst(p.x, p.y, (255, 230, 120), 80, 480, size=5.0, life=1.0)
            self.shake = max(self.shake, 0.4)
            self._flash_msg = "星陨领主·八曜护世·恒星护体14秒！"
            self._flash_timer = 1.8
            self._play("powerup")
            return True
        if sk == "chrono":
            # Q4：时空猎手右键·巨爪裂空·发射巨大爪子（击退+伤害，能耗40）
            if p.energy < 40:
                self._flash_msg = "能量不足(需40)"
                self._flash_timer = 1.0
                return True
            p.energy -= 40
            if p.energy <= 0: p._energy_depleted = True
            if not hasattr(self, "chrono_hooks"):
                self.chrono_hooks = []
            dx_ = mx - p.x; dy_ = my - p.y; d_ = math.hypot(dx_, dy_) or 1
            a0 = math.atan2(dy_, dx_)
            # 巨爪：大体积飞行物，碰到的敌人被击退+伤害
            self.chrono_hooks.append({
                "kind": "giant_claw",
                "x": p.x + dx_ / d_ * (p.r + 12),
                "y": p.y + dy_ / d_ * (p.r + 12),
                "vx": dx_ / d_ * 620, "vy": dy_ / d_ * 620,
                "angle": a0,
                "life": 0.9, "r": 42, "owner": p, "_dead": False,
                "hit": set(), "dmg": 6.0, "knockback": 520
            })
            # 紫色发射粒子
            for k in range(20):
                a = a0 + random.uniform(-0.5, 0.5)
                self.particles.append(Particle(
                    p.x, p.y,
                    math.cos(a) * (280 + random.uniform(-50, 70)),
                    math.sin(a) * (280 + random.uniform(-50, 70)),
                    0.45, (180, 120, 255), 3.0
                ))
            self._flash_msg = "时空猎手·巨爪裂空！"
            self._flash_timer = 1.2
            self._play("shoot")
            return True
        if sk == "buddha":
            # 不灭尊者：万佛降世·9座金佛环绕+超华丽净化光波（特效更明显！多层扩环+卍字爆+金身护盾）
            if p.energy < 90:
                self._flash_msg = "能量不足(需90)"
                self._flash_timer = 1.0
                return True
            p.energy -= 90
            if p.energy <= 0: p._energy_depleted = True
            p._buddha_timer = 9.0
            # ===== 主动瞬间：超大范围净化光波 =====
            # （净化半径加大到 900，伤害更高，更强击退）
            for s in list(self.stars):
                if s.danger and not s._dead:
                    dd = math.hypot(s.x - p.x, s.y - p.y)
                    if dd < 1100:
                        f = 1 - dd / 1100
                        self._damage_enemy(s, 8.0 * f + 5.0, owner=p)
                        ddx = s.x - p.x; ddy = s.y - p.y; d0 = dd or 1
                        s.vx += ddx / d0 * 860 * f
                        s.vy += ddy / d0 * 860 * f
            # ===== 超华丽 5 层金佛粒子（金/白金/橙金/赤金/紫金）— Q15 加强 =====
            for ring, col, cnt in ((80,  (255, 220, 120), 150),
                                   (180, (255, 240, 170), 170),
                                   (300, (255, 190, 80),  180),
                                   (440, (255, 140, 40),  130),
                                   (580, (220, 150, 255), 100)):
                for k in range(cnt):
                    a = random.uniform(0, math.tau)
                    self.particles.append(Particle(
                        p.x, p.y,
                        math.cos(a) * (420 + ring),
                        math.sin(a) * (420 + ring),
                        0.96, col, 4.0
                    ))
            # ===== 360°卍字爆：旋转爆发 8 方向 12 段粒子 =====
            for base_a in [i * math.pi / 4 for i in range(8)]:
                for seg in range(12):
                    t0 = seg / 11
                    rad = 40 + t0 * 540
                    for (off, col) in ((0.0, (255, 200, 80)),
                                       (0.12, (255, 240, 160)),
                                       (-0.12, (255, 180, 50))):
                        a = base_a + off
                        self.particles.append(Particle(
                            p.x, p.y,
                            math.cos(a) * rad,
                            math.sin(a) * rad,
                            0.72, col, 3.4
                        ))
            # ===== 金身护盾：3 秒无敌 + 5 秒护盾计时 =====
            p.invulnerable = max(p.invulnerable, 4.0)
            p.shield_timer = max(p.shield_timer, 6.0)
            # 立即生成 9 座金佛护体（放进 buddha_hands kind="buddha"）— Q15 加强
            for i in range(9):
                a = i * (math.tau / 9)
                self.buddha_hands.append({
                    "kind": "buddha",  # 护体环绕金佛
                    "x": p.x + math.cos(a) * 80,
                    "y": p.y + math.sin(a) * 80,
                    "phase": a, "r": 24,
                    "life": 11.0, "max": 11.0,
                    "owner": p, "_dead": False,
                    "explode_r": 220, "explode_dmg": 7.5
                })
            self.burst(p.x, p.y, (255, 200, 80), 120, 620, size=6.0, life=1.3)
            self.shake = max(self.shake, 0.6)
            self._flash_msg = "不灭尊者·万佛降世！超华丽净化金光！"
            self._flash_timer = 2.0
            self._play("warn")
            return True
        if sk == "god":
            # 极律虚皇：万法归一·消耗100%所有能量，全屏爆伤+时空停止+圣光护罩
            if p.energy < 40:
                self._flash_msg = "能量不足(需40+)，万法归一无法启动"
                self._flash_timer = 1.0
                return True
            # 消耗全部能量（100%）
            p._energy_depleted = True
            all_energy = max(40.0, float(p.energy))
            p.energy = 0.0
            # 伤害/效果 按消耗能量线性放大（越多能量越霸气）— Q16 加强
            dmg_bonus = all_energy * 0.10
            stop_s = 5.0 + all_energy * 0.025
            shield_s = 12.0 + all_energy * 0.035
            # 全屏爆伤
            for s in self.stars:
                if s.danger and not s._dead:
                    self._damage_enemy(s, 9.0 + dmg_bonus * 1.2, owner=p)
                    dd = math.hypot(s.x - p.x, s.y - p.y) or 1
                    ddx = (s.x - p.x) / dd
                    ddy = (s.y - p.y) / dd
                    s.vx += ddx * (850 + all_energy * 2.5)
                    s.vy += ddy * (850 + all_energy * 2.5)
            # 时空停止
            self.time_freeze_timer = max(self.time_freeze_timer, stop_s)
            # 圣光护罩（10+秒）
            p.shield_timer = max(p.shield_timer, shield_s)
            p.invulnerable = max(p.invulnerable, 3.5)
            # 4 层圣光爆发（白/金/蓝/极白）— Q16 加强
            for ring, col, cnt in ((80, (255, 255, 200), 110),
                                   (200, (255, 240, 160), 130),
                                   (360, (160, 220, 255), 150),
                                   (520, (255, 255, 255), 150)):
                for k in range(cnt):
                    a = random.uniform(0, math.tau)
                    self.particles.append(Particle(
                        p.x, p.y,
                        math.cos(a) * (420 + ring),
                        math.sin(a) * (420 + ring),
                        0.95, col, 4.0
                    ))
            # 全屏 9 道极律蓝光柱（从天空落下）
            if not hasattr(self, "god_pillars"):
                self.god_pillars = []
            for i in range(12):
                a = i * (math.tau / 12)
                tx = p.x + math.cos(a) * 300
                ty = p.y + math.sin(a) * 300
                self.god_pillars.append({
                    "type": "pillar",
                    "x": tx, "y": ty, "r": 55,
                    "life": 1.0, "max": 1.0, "hit": False,
                    "owner": p, "_dead": False
                })
            self.burst(p.x, p.y, (255, 255, 200), 140, 720, size=6.6, life=1.4)
            self.shake = max(self.shake, 0.85)
            self._flash_msg = "极律虚皇·万法归一！时空停止+圣光护罩！"
            self._flash_timer = 2.2
            self._play("warn")
            return True
        # ===== 终极皮肤右键技能 =====
        if sk == "origin":
            return self._origin_right_click(mx, my)
        if sk == "paradox":
            return self._paradox_right_click(mx, my)
        if sk == "finality":
            return self._finality_right_click(mx, my)
        return False

    # ===== 终极皮肤：元素/炮类型定义 =====
    def _origin_elements(self):
        """生命起源：12种元素球 (名称, 颜色, 伤害, 特效类型)"""
        return [
            ("火球",   (255,  80,  40), 5.0, "burn"),     # 灼烧
            ("冰球",   ( 80, 200, 255), 4.0, "freeze"),    # 冻结
            ("电球",   (255, 230,  60), 4.5, "chain"),     # 连锁
            ("磁球",   (180,  80, 255), 3.5, "pull"),      # 吸引
            ("铁球",   (160, 160, 180), 6.0, "knock"),     # 击退
            ("暗球",   ( 80,  20, 100), 4.0, "lifesteal"), # 吸血
            ("黑洞",   ( 20,  10,  30), 8.0, "absorb"),    # 吞噬
            ("光球",   (255, 250, 200), 5.5, "pierce"),    # 穿透
            ("毒球",   ( 80, 220,  60), 3.0, "poison"),    # 中毒
            ("雷球",   (100, 140, 255), 5.0, "aoe"),       # 范围
            ("风球",   (120, 255, 180), 3.5, "spread"),    # 扩散
            ("土球",   (140, 100,  60), 7.0, "stun"),      # 眩晕
        ]

    def _paradox_cannons(self):
        """逆悖突进：4种圆柱炮 (名称, 颜色, 伤害, 特效类型)"""
        return [
            ("灭磁炮", (140,  30,  30), 6.0, "magnetic"),  # 暗红
            ("毒素炮", ( 30, 100,  40), 5.0, "poison"),     # 暗绿
            ("极冻炮", ( 20,  50, 120), 5.5, "freeze"),     # 暗蓝
            ("毁灭炮", ( 20,  20,  20), 9.0, "destroy"),    # 暗黑
        ]

    # ===== 生命起源 =====
    def _origin_left_click(self, mx, my):
        """生命起源左键：发射当前元素球（每次自动循环到下一元素，X键手动切换）"""
        p = self.player
        if not p or not p.alive:
            return
        if p._origin_cd > 0:
            return
        if p.energy < 3:
            self._flash_msg = "能量不足(需3)"
            self._flash_timer = 0.7
            return
        p.energy -= 3
        if p.energy <= 0: p._energy_depleted = True
        p._origin_cd = 0.18
        elems = self._origin_elements()
        idx = p._origin_elem_idx % len(elems)
        nm, col, dmg, eff = elems[idx]
        dx = mx - p.x; dy = my - p.y; d = math.hypot(dx, dy) or 1
        a0 = math.atan2(dy, dx)
        if not hasattr(self, "origin_balls"):
            self.origin_balls = []
        self.origin_balls.append({
            "x": p.x + dx / d * (p.r + 10), "y": p.y + dy / d * (p.r + 10),
            "vx": dx / d * 560, "vy": dy / d * 560,
            "r": 16, "color": col, "dmg": dmg, "eff": eff,
            "life": 2.5, "owner": p, "_dead": False, "hit": set(),
            "elem_idx": idx, "phase": 0.0
        })
        # 发射粒子
        for k in range(12):
            a = a0 + random.uniform(-0.3, 0.3)
            self.particles.append(Particle(
                p.x, p.y, math.cos(a) * 300, math.sin(a) * 300,
                0.35, col, 2.8))
        self._play("shoot")
        # 自动循环到下一元素
        p._origin_elem_idx = (idx + 1) % len(elems)

    def _origin_right_click(self, mx, my):
        """生命起源右键：召唤12元素球环绕护体8秒+HP加到5"""
        p = self.player
        if not p or not p.alive:
            return False
        if p.energy < 5:
            self._flash_msg = "能量不足(需5)"
            self._flash_timer = 1.0
            return True
        p.energy -= 5
        if p.energy <= 0: p._energy_depleted = True
        # HP加到5
        self.lives = max(self.lives, 5)
        # 召唤12元素环绕球
        elems = self._origin_elements()
        p._origin_orbs = []
        for i, (nm, col, dmg, eff) in enumerate(elems):
            p._origin_orbs.append({
                "angle": i * (math.tau / 12), "r": 90 + i * 4,
                "color": col, "dmg": dmg, "eff": eff,
                "elem_idx": i, "phase": 0.0
            })
        p._origin_orb_timer = 8.0
        self.burst(p.x, p.y, (100, 255, 180), 60, 500, size=4.0, life=1.0)
        self._flash_msg = "生命起源·万物复苏！12元素护体8秒！"
        self._flash_timer = 1.8
        self._play("powerup")
        return True

    # ===== 逆悖突进 =====
    def _paradox_left_click(self, mx, my):
        """逆悖突进左键：发射当前圆柱炮（每次自动循环，X键手动切换）"""
        p = self.player
        if not p or not p.alive:
            return
        if p._paradox_cd > 0:
            return
        if p.energy < 4:
            self._flash_msg = "能量不足(需4)"
            self._flash_timer = 0.7
            return
        p.energy -= 4
        if p.energy <= 0: p._energy_depleted = True
        p._paradox_cd = 0.35
        cannons = self._paradox_cannons()
        idx = p._paradox_cannon_idx % len(cannons)
        nm, col, dmg, eff = cannons[idx]
        dx = mx - p.x; dy = my - p.y; d = math.hypot(dx, dy) or 1
        a0 = math.atan2(dy, dx)
        if not hasattr(self, "paradox_beams"):
            self.paradox_beams = []
        # 圆柱炮：粗直线光束（短距离高伤害）
        self.paradox_beams.append({
            "x": p.x, "y": p.y, "angle": a0,
            "length": 600, "r": 22, "color": col,
            "dmg": dmg, "eff": eff,
            "life": 0.3, "max": 0.3,
            "owner": p, "_dead": False, "hit_cd": {}
        })
        # 炮口喷射粒子
        for k in range(20):
            a = a0 + random.uniform(-0.25, 0.25)
            self.particles.append(Particle(
                p.x + math.cos(a0) * p.r, p.y + math.sin(a0) * p.r,
                math.cos(a) * 400, math.sin(a) * 400,
                0.4, col, 3.2))
        self._play("shoot")
        # 自动循环
        p._paradox_cannon_idx = (idx + 1) % len(cannons)

    def _paradox_right_click(self, mx, my):
        """逆悖突进右键：展开6根光柱360度旋转击退+HP加到5"""
        p = self.player
        if not p or not p.alive:
            return False
        if p.energy < 5:
            self._flash_msg = "能量不足(需5)"
            self._flash_timer = 1.0
            return True
        p.energy -= 5
        if p.energy <= 0: p._energy_depleted = True
        # HP加到5
        self.lives = max(self.lives, 5)
        # 6根光柱
        p._paradox_pillars = []
        for i in range(6):
            p._paradox_pillars.append({
                "angle": i * (math.tau / 6),
                "r": 160, "color": (200, 100, 255),
                "dmg": 4.0, "hit_cd": {}
            })
        p._paradox_pillar_timer = 6.0
        self.burst(p.x, p.y, (200, 100, 255), 80, 560, size=5.0, life=1.2)
        self._flash_msg = "逆悖突进·六光柱360°旋转击退6秒！"
        self._flash_timer = 1.8
        self._play("powerup")
        return True

    # ===== 终焉 =====
    def _finality_left_click(self, mx, my):
        """终焉左键：投掷必中灭世长枪(穿透全屏+即死非Boss+Boss500伤害)+镰刀360旋转"""
        p = self.player
        if not p or not p.alive:
            return
        if p._finality_cd > 0:
            return
        if p.energy < 5:
            self._flash_msg = "能量不足(需5)"
            self._flash_timer = 0.7
            return
        p.energy -= 5
        if p.energy <= 0: p._energy_depleted = True
        p._finality_cd = 1.2
        dx = mx - p.x; dy = my - p.y; d = math.hypot(dx, dy) or 1
        a0 = math.atan2(dy, dx)
        if not hasattr(self, "finality_spears"):
            self.finality_spears = []
        # 灭世长枪：超高速穿透全屏
        self.finality_spears.append({
            "x": p.x, "y": p.y,
            "vx": dx / d * 1400, "vy": dy / d * 1400,
            "angle": a0, "r": 18, "length": 120,
            "life": 1.5, "owner": p, "_dead": False, "hit": set(),
            "dmg": 500  # Boss伤害；非Boss即死
        })
        # 镰刀360°旋转3秒
        p._finality_scythe_timer = 3.0
        # 发射粒子
        for k in range(30):
            a = a0 + random.uniform(-0.5, 0.5)
            self.particles.append(Particle(
                p.x, p.y, math.cos(a) * 380, math.sin(a) * 380,
                0.5, (255, 50, 50), 3.5))
        self._play("shoot")

    def _finality_right_click(self, mx, my):
        """终焉右键：无敌破坏死光（大范围血红黑激光3秒）+HP加到5"""
        p = self.player
        if not p or not p.alive:
            return False
        if p.energy < 8:
            self._flash_msg = "能量不足(需8)"
            self._flash_timer = 1.0
            return True
        p.energy -= 8
        if p.energy <= 0: p._energy_depleted = True
        # HP加到5
        self.lives = max(self.lives, 5)
        # 无敌3秒
        p.invuln = max(p.invuln, 3.0)
        # 破坏死光3秒
        p._finality_laser_timer = 3.0
        self.burst(p.x, p.y, (255, 30, 30), 120, 800, size=7.0, life=1.5)
        self.shake = max(self.shake, 1.0)
        self._flash_msg = "终焉·无敌破坏死光！3秒大范围毁灭！"
        self._flash_timer = 2.5
        self._play("warn")
        return True

    def _tri_left_click(self, mx, my):
        """三色灵球左键技能：红=吐炸弹，黄=护盾，蓝=加速。
        消耗40能量（不足则无法释放）。
        """
        p = self.player
        if not p or not p.alive:
            return
        if p.energy < 40.0:
            self._flash_msg = "能量不足(需40)，无法使用三色技能"
            self._flash_timer = 1.0
            return
        p.energy = max(0.0, p.energy - 40.0)
        if p.energy <= 0:
            p._energy_depleted = True
        if p.tri_mode == 0:
            # 红球：沿前进方向吐炸弹
            dx = p.x - p.prev_x
            dy = p.y - p.prev_y
            d = math.hypot(dx, dy)
            if d < 1.5:
                # 没在动，朝鼠标方向
                dx, dy = mx - p.x, my - p.y
                d = math.hypot(dx, dy) or 1
            nx, ny = dx / d, dy / d
            self.tri_bombs.append({
                "x": p.x + nx * (p.r + 8), "y": p.y + ny * (p.r + 8),
                "vx": nx * 200, "vy": ny * 200,
                "timer": 2.0, "max": 2.0,
                "owner": p, "_dead": False, "r": 12
            })
            self._flash_msg = "红球：吐出炸弹！2s后爆炸"
            self._flash_timer = 1.6
            self.burst(p.x, p.y, (255, 70, 90), 16, 180, size=2.8, life=0.4)
            self._play("shoot")
        elif p.tri_mode == 1:
            # 黄球：护盾
            p.shield_timer = 1.6
            self._flash_msg = "黄球：护盾激活！"
            self._flash_timer = 1.6
            self.burst(p.x, p.y, (255, 220, 80), 24, 220, size=3.0, life=0.5)
            self._play("powerup")
        elif p.tri_mode == 2:
            # 蓝球：2s 加速（比普通加速快20%）
            p._tri_boost_timer = 2.0
            self._flash_msg = "蓝球：极速加速！"
            self._flash_timer = 1.6
            self.burst(p.x, p.y, (90, 130, 255), 24, 220, size=3.0, life=0.5)
            self._play("powerup")

    def _sun_left_click(self, mx, my):
        """烈阳左键：发出太阳光排斥敌球（消耗20能量）。"""
        p = self.player
        if not p or not p.alive:
            return
        if p.energy < 20.0:
            self._flash_msg = "能量不足(需20)，无法发出烈阳光芒"
            self._flash_timer = 1.0
            return
        p.energy = max(0.0, p.energy - 20.0)
        if p.energy <= 0:
            p._energy_depleted = True
        # 发光排斥持续 2s
        p._sun_glow_timer = 2.0
        self.burst(p.x, p.y, (255, 220, 100), 30, 280, size=3.5, life=0.6)
        self._flash_msg = "烈阳光芒！敌球绕行"
        self._flash_timer = 1.2
        self._play("powerup")

    def _sun_global_blast(self, p):
        """烈阳右键：全局光波击退所有敌球。"""
        for s in self.stars:
            if not s.danger or s._dead:
                continue
            dx = s.x - p.x
            dy = s.y - p.y
            d = math.hypot(dx, dy) or 1
            # 全局击退：距离越近击退越强
            force = max(400, 900 - d * 0.5)
            s.vx += (dx / d) * force
            s.vy += (dy / d) * force
            self._damage_enemy(s, 1, p)
        self.burst(p.x, p.y, (255, 220, 100), 80, 500, size=5.0, life=1.2)
        self.burst(p.x, p.y, (255, 180, 60), 50, 380, size=4.0, life=0.8)
        self.shake = max(self.shake, 1.0)
        self._flash_msg = "全局光波击退！"
        self._flash_timer = 1.6
        self._play("shockwave")

    def _rainbow_left_click(self, mx, my):
        """虹光左键：消耗30能量，使用当前颜色对应的道具（时长50%）。"""
        p = self.player
        if not p or not p.alive:
            return
        if p.energy < 30.0:
            self._flash_msg = "能量不足，需30能量释放虹光效果"
            self._flash_timer = 1.0
            return
        p.energy = max(0.0, p.energy - 30.0)
        if p.energy <= 0:
            p._energy_depleted = True
        idx = getattr(p, "_rb_idx", 0)
        eff = RAINBOW_EFFECTS[idx]
        col = RAINBOW_COLORS[idx]
        # 先应用道具，再将时长压缩到 50%
        old_durations = dict(POWERUP_DURATION)
        for k in POWERUP_DURATION:
            POWERUP_DURATION[k] = POWERUP_DURATION[k] * 0.5
        self.apply_powerup(eff, p)
        POWERUP_DURATION.update(old_durations)
        self.burst(p.x, p.y, col, 28, 280, size=3.2, life=0.6)
        self._flash_msg = f"{RAINBOW_NAMES[idx]} (50%时长)"
        self._flash_timer = 1.2
        self._play("powerup")

    def _inferno_left_click(self, mx, my):
        """炼狱左键：消耗能量发射火球。"""
        p = self.player
        if not p or not p.alive:
            return
        if p.energy < 25.0:
            self._flash_msg = "能量不足，无法发射火球"
            self._flash_timer = 1.0
            return
        dx, dy = mx - p.x, my - p.y
        d = math.hypot(dx, dy) or 1
        self._spawn_fireball(p, dx / d, dy / d)
        p.energy = max(0.0, p.energy - 25.0)
        if p.energy <= 0:
            p._energy_depleted = True
        self._play("shoot")

    def _frost_left_click(self, mx, my):
        """霜冻左键：消耗能量发射冰粒，碰到敌人冻结。"""
        p = self.player
        if not p or not p.alive:
            return
        if p.energy < 15.0:
            self._flash_msg = "能量不足，无法发射冰粒"
            self._flash_timer = 1.0
            return
        dx, dy = mx - p.x, my - p.y
        d = math.hypot(dx, dy) or 1
        self.frost_pellets.append({
            "x": p.x, "y": p.y,
            "vx": dx / d * 260, "vy": dy / d * 260,
            "timer": 1.5, "r": 8, "owner": p, "_dead": False
        })
        p.energy = max(0.0, p.energy - 15.0)
        if p.energy <= 0:
            p._energy_depleted = True
        self._play("shoot")

    def _thunder_left_click(self, mx, my):
        """雷霆左键：消耗能量发射自动电球，碰到伤害+击退。"""
        p = self.player
        if not p or not p.alive:
            return
        if p.energy < 20.0:
            self._flash_msg = "能量不足，无法发射电球"
            self._flash_timer = 1.0
            return
        dx, dy = mx - p.x, my - p.y
        d = math.hypot(dx, dy) or 1
        self.thunder_balls.append({
            "x": p.x, "y": p.y,
            "vx": dx / d * 240, "vy": dy / d * 240,
            "timer": 2.0, "r": 10, "owner": p, "_dead": False
        })
        p.energy = max(0.0, p.energy - 20.0)
        if p.energy <= 0:
            p._energy_depleted = True
        self._play("thunder")

    def _void_left_click(self, mx, my):
        """深渊左键：发射螺旋型黑洞，存在2.5s，消耗50能量。"""
        p = self.player
        if not p or not p.alive:
            return
        if p.energy < 50.0:
            self._flash_msg = "能量不足(需50)，无法发射螺旋黑洞"
            self._flash_timer = 1.0
            return
        p.energy = max(0.0, p.energy - 50.0)
        if p.energy <= 0:
            p._energy_depleted = True
        dx, dy = mx - p.x, my - p.y
        d = math.hypot(dx, dy) or 1
        self.void_holes.append({
            "x": p.x, "y": p.y,
            "vx": dx / d * 200, "vy": dy / d * 200,
            "timer": 2.5, "max": 2.5, "r": 90, "owner": p,
            "_dead": False, "spiral": True,
            "spiral_phase": 0.0, "spiral_center": (mx, my)
        })
        self._play("powerup")
        self._flash_msg = "螺旋黑洞！3s"
        self._flash_timer = 1.2

    def _chaos_left_click(self, mx, my):
        """混沌左键：发射动态钩子（消耗30能量），未钩中摆动悬浮，钩中吸血+脉动。"""
        p = self.player
        if not p or not p.alive:
            return
        if p._chaos_hook is not None:
            # 已有钩子：取消（重发，不消耗能量）
            p._chaos_hook = None
        if p.energy < 30.0:
            self._flash_msg = "能量不足(需30)，无法发射混沌钩"
            self._flash_timer = 1.0
            return
        p.energy = max(0.0, p.energy - 30.0)
        if p.energy <= 0:
            p._energy_depleted = True
        dx, dy = mx - p.x, my - p.y
        d = math.hypot(dx, dy) or 1
        p._chaos_hook = {
            "x": p.x, "y": p.y,
            "vx": dx / d * 360, "vy": dy / d * 360,
            "target": None, "drain_timer": 0.0,
            "phase": 0,  # 0:飞出 1:悬浮 2:吸血
            "life": 6.0,  # 最多存在时间
            "mx": mx, "my": my,
            "t": 0.0,     # 动态时间累加，用于波形摆动
            "ang": math.atan2(dy, dx),  # 基础方向角（动态调整）
            "spiral": 0.0  # 悬浮时螺旋旋转角
        }
        self._play("shoot")

    # ============== 钻石皮肤左键技能 ==============
    def _judge_left_click(self, mx, my):
        """天罚之眼左键：审判光弹（带穿透，消耗15能量）。"""
        p = self.player
        if not p or not p.alive:
            return
        if p._judge_bullets_cd > 0:
            return
        if p.energy < 15:
            return
        p.energy -= 15
        if p.energy <= 0:
            p._energy_depleted = True
        p._judge_bullets_cd = 0.22
        dx = mx - p.x; dy = my - p.y
        d = math.hypot(dx, dy) or 1
        spd = 620
        self.bullets.append(Bullet(p.x, p.y, dx / d * spd, dy / d * spd, owner=p))
        # 再加两枚稍微散弹
        for ang_off in (-0.08, 0.08):
            a = math.atan2(dy, dx) + ang_off
            self.bullets.append(Bullet(p.x, p.y, math.cos(a) * spd, math.sin(a) * spd, owner=p))
        self.burst(p.x, p.y, (255, 240, 200), 10, 160, size=2.2, life=0.25)
        self._play("shoot")

    def _dragon_left_click(self, mx, my):
        """真龙帝皇左键：帝皇火球·龙焰追踪（消耗20能量）。"""
        p = self.player
        if not p or not p.alive:
            return
        if p._dragon_cd > 0:
            return
        if p.energy < 20:
            return
        p.energy -= 20
        if p.energy <= 0:
            p._energy_depleted = True
        p._dragon_cd = 0.3
        dx = mx - p.x; dy = my - p.y
        d = math.hypot(dx, dy) or 1
        # 找最近的目标追踪
        tgt = None; tgt_d = 1e9
        for s in self.stars:
            if s.danger and not s._dead:
                dd = math.hypot(s.x - mx, s.y - my)
                if dd < tgt_d:
                    tgt_d = dd; tgt = s
        if not hasattr(self, "dragon_fire"):
            self.dragon_fire = []
        self.dragon_fire.append({
            "x": p.x, "y": p.y,
            "vx": dx / d * 480, "vy": dy / d * 480,
            "life": 2.6, "r": 18, "owner": p, "target": tgt, "_dead": False
        })
        self.burst(p.x, p.y, (255, 180, 80), 14, 220, size=2.6, life=0.35)
        self._play("shoot")

    def _demon_left_click(self, mx, my):
        """九幽魔君左键：魔焰弹·毒雾腐蚀（消耗22能量）。"""
        p = self.player
        if not p or not p.alive:
            return
        if p._demon_cd > 0:
            return
        if p.energy < 22:
            return
        p.energy -= 22
        if p.energy <= 0:
            p._energy_depleted = True
        p._demon_cd = 0.35
        dx = mx - p.x; dy = my - p.y
        d = math.hypot(dx, dy) or 1
        if not hasattr(self, "demon_clouds"):
            self.demon_clouds = []
        # 3 发扇形
        for ang_off in (-0.18, 0.0, 0.18):
            a = math.atan2(dy, dx) + ang_off
            self.demon_clouds.append({
                "x": p.x, "y": p.y,
                "vx": math.cos(a) * 380, "vy": math.sin(a) * 380,
                "life": 2.0, "r": 22, "owner": p, "_dead": False
            })
        self.burst(p.x, p.y, (180, 60, 255), 16, 220, size=3.0, life=0.35)
        self._play("shoot")

    def _stellar_left_click(self, mx, my):
        """星海主宰左键：星轨弹·持续切割（消耗25能量）。"""
        p = self.player
        if not p or not p.alive:
            return
        if p._stellar_cd > 0:
            return
        if p.energy < 25:
            return
        p.energy -= 25
        if p.energy <= 0:
            p._energy_depleted = True
        p._stellar_cd = 0.4
        # 7 枚旋转星轨弹，从玩家向鼠标方向散开
        if not hasattr(self, "stellar_orbs"):
            self.stellar_orbs = []
        for n in range(-3, 4):
            a = math.atan2(my - p.y, mx - p.x) + n * 0.12
            self.stellar_orbs.append({
                "x": p.x, "y": p.y,
                "vx": math.cos(a) * 440, "vy": math.sin(a) * 440,
                "life": 1.8, "r": 14, "owner": p, "_dead": False
            })
        self.burst(p.x, p.y, (150, 220, 255), 18, 260, size=3.0, life=0.4)
        self._play("shoot")

    def _samsara_left_click(self, mx, my):
        """Q3：六道轮回左键：消耗50%能量，分裂6首子球，自动追踪敌方并造成爆炸和弹开。"""
        p = self.player
        if not p or not p.alive:
            return
        if p.energy < 20:
            self._flash_msg = "能量不足(需20+)，六道子球无法分裂"
            self._flash_timer = 0.7
            return
        # 消耗 50% 当前能量
        cost = p.energy * 0.5
        p.energy -= cost
        if p.energy <= 0:
            p._energy_depleted = True
        samsara_blades = getattr(self, "samsara_blades", None)
        if samsara_blades is None:
            self.samsara_blades = []
            samsara_blades = self.samsara_blades
        # 分裂 6 首子球：从玩家6方向散出，自动追踪最近敌人
        for i in range(6):
            a = i * (math.tau / 6)
            samsara_blades.append({
                "x": p.x, "y": p.y,
                "vx": math.cos(a) * 280, "vy": math.sin(a) * 280,
                "life": 3.5, "r": 16, "owner": p, "_dead": False,
                "pierced": set(),
                "track": True,       # Q3：自动追踪
                "explode": True,     # Q3：碰撞爆炸
                "explode_r": 120,
                "explode_dmg": 4.0 + cost * 0.03,
                "hit_cd": {}
            })
        self.burst(p.x, p.y, (200, 160, 255), 40, 380, size=4.0, life=0.7)
        self._play("powerup")

    def _寂灭_left_click(self, mx, my):
        """寂灭神皇左键：寂灭射线·瞬间湮灭小半径敌人（消耗60能量）。"""
        p = self.player
        if not p or not p.alive:
            return
        if p._寂灭_cd > 0:
            return
        if p.energy < 60:
            return
        p.energy -= 60
        if p.energy <= 0:
            p._energy_depleted = True
        p._寂灭_cd = 0.5
        # 寂灭射线：沿鼠标方向一条线，范围半径 40
        dx = mx - p.x; dy = my - p.y
        d = math.hypot(dx, dy) or 1
        for L in range(1, 30):
            bx = p.x + dx / d * L * 34
            by = p.y + dy / d * L * 34
            for s in self.stars:
                if s.danger and not s._dead:
                    if math.hypot(s.x - bx, s.y - by) < s.r + 40:
                        self._damage_enemy(s, 4.0, p)
            self.particles.append((bx, by, random.uniform(-12,12), random.uniform(-12,12),
                                   0.3, (255, 200, 255), 3.4))
        self.burst(p.x, p.y, (255, 200, 255), 20, 300, size=3.2, life=0.4)
        self._play("thunder")

    def _primal_left_click(self, mx, my):
        """鸿蒙之始左键：鸿蒙一炁·吸附范围内敌人到一点（消耗45能量）。"""
        p = self.player
        if not p or not p.alive:
            return
        if p._primal_cd > 0:
            return
        if p.energy < 45:
            return
        p.energy -= 45
        if p.energy <= 0:
            p._energy_depleted = True
        p._primal_cd = 0.7
        # 以 (mx, my) 为中心，300 半径内的所有敌人被吸向 (mx, my)
        R = 300
        for s in self.stars:
            if s.danger and not s._dead:
                dd = math.hypot(s.x - mx, s.y - my)
                if dd < R:
                    ddx = mx - s.x; ddy = my - s.y
                    L = math.hypot(ddx, ddy) or 1
                    force = 720
                    s.vx += ddx / L * force
                    s.vy += ddy / L * force
                    self._damage_enemy(s, 2.0, p)
        # 视觉：一炁漩涡
        for i in range(40):
            a = random.uniform(0, math.tau)
            rr = random.uniform(10, R)
            self.particles.append((mx + math.cos(a) * rr, my + math.sin(a) * rr,
                                   -math.cos(a) * 380, -math.sin(a) * 380,
                                   0.6, (220, 255, 200), 3.0))
        self.burst(mx, my, (220, 255, 200), 28, 360, size=4.2, life=0.7)
        self._play("powerup")

    def _taiji_left_click(self, mx, my):
        """太上无极左键：两仪剑·青红双剑自动连击（消耗20能量）。"""
        p = self.player
        if not p or not p.alive:
            return
        if p._taiji_cd > 0:
            return
        if p.energy < 20:
            return
        p.energy -= 20
        if p.energy <= 0:
            p._energy_depleted = True
        p._taiji_cd = 0.3
        # 两仪剑：两发穿透飞剑（先发射到鼠标方向，在目标点画圆返回）
        if not hasattr(self, "taiji_blades"):
            self.taiji_blades = []
        for sgn, col in ((-1, (90, 220, 255)), (1, (255, 90, 90))):
            a = math.atan2(my - p.y, mx - p.x) + sgn * 0.25
            self.taiji_blades.append({
                "x": p.x, "y": p.y,
                "vx": math.cos(a) * 500, "vy": math.sin(a) * 500,
                "life": 1.2, "r": 16, "owner": p, "col": col, "_dead": False
            })
        self._play("shoot")

    def _nirvana_left_click(self, mx, my):
        """大道涅槃左键：灼烧凤凰·向前发射灼烧凤凰弹（消耗35能量，冷却0.55s，1.5s后消失）。"""
        p = self.player
        if not p or not p.alive:
            return
        if p._nirvana_click_cd > 0:
            return
        if p.energy < 35:
            return
        p.energy -= 35
        if p.energy <= 0:
            p._energy_depleted = True
        p._nirvana_click_cd = 0.55
        # 灼烧凤凰：朝鼠标方向飞行，碰到敌人造成持续伤害
        if not hasattr(self, "nirvana_phoenix_list"):
            self.nirvana_phoenix_list = []
        dx = mx - p.x; dy = my - p.y; d = math.hypot(dx, dy) or 1
        speed = 460
        self.nirvana_phoenix_list.append({
            "x": p.x + dx / d * (p.r + 8),
            "y": p.y + dy / d * (p.r + 8),
            "vx": dx / d * speed,
            "vy": dy / d * speed,
            "life": 1.5, "max": 1.5, "r": 20,
            "owner": p, "_dead": False, "hit_cd": {}
        })
        # 凤凰起飞粒子
        for k in range(14):
            a = math.atan2(dy, dx) + random.uniform(-0.45, 0.45)
            self.particles.append(Particle(
                p.x + math.cos(a) * p.r,
                p.y + math.sin(a) * p.r,
                math.cos(a) * (220 + random.uniform(-50, 50)),
                math.sin(a) * (220 + random.uniform(-50, 50)),
                0.4, random.choice([(255, 200, 80), (255, 120, 40), (255, 240, 140)]), 3.0
            ))
        self._play("shoot")

    # ===== 第三页 至高霸气 9 个皮肤 左键技能 =====
    def _titan_left_click(self, mx, my):
        """裂空雷将左键：双雷锁敌·两枚追踪雷弹（低能耗 14 + 冷却 0.35s，远程好看特效）"""
        p = self.player
        if not p or not p.alive:
            return
        if p._titan_cd > 0:
            return
        if p.energy < 14:
            self._flash_msg = "能量不足(需14)，追踪雷弹未充能"
            self._flash_timer = 0.7
            return
        p.energy -= 14
        if p.energy <= 0: p._energy_depleted = True
        p._titan_cd = 0.35
        # 找最近 2 个敌人作为追踪目标
        cand = [(s, math.hypot(s.x - p.x, s.y - p.y)) for s in self.stars if s.danger and not s._dead]
        cand.sort(key=lambda x: x[1])
        targets = [c[0] for c in cand[:2]]
        # 如果没目标，朝鼠标方向直飞
        for i in range(2):
            tgt = targets[i] if i < len(targets) else None
            if tgt is not None:
                a0 = math.atan2(tgt.y - p.y, tgt.x - p.x)
            else:
                a0 = math.atan2(my - p.y, mx - p.x)
            a0 += (i - 0.5) * 0.22  # 两枚微偏开
            self.titan_hammers.append({
                "x": p.x, "y": p.y,
                "vx": math.cos(a0) * 420, "vy": math.sin(a0) * 420,
                "r": 15, "life": 3.2, "max": 3.2, "hit_cd": {},
                "owner": p, "_dead": False,
                "track_target": tgt,  # 追踪目标
                "spark_phase": 0.0
            })
            # 雷弹射出粒子
            for k in range(10):
                a = a0 + random.uniform(-0.4, 0.4)
                self.particles.append(Particle(
                    p.x + math.cos(a0) * p.r,
                    p.y + math.sin(a0) * p.r,
                    math.cos(a) * (220 + random.uniform(-50, 50)),
                    math.sin(a) * (220 + random.uniform(-50, 50)),
                    0.35, (120, 180, 255), 2.4
                ))
        self._play("shoot")

    def _qinglong_left_click(self, mx, my):
        """沧溟潮君左键：螺旋波浪柱·喷射螺旋水柱(长按连射至屏幕边缘，能耗8/次，冷却0.08s)"""
        p = self.player
        if not p or not p.alive:
            return
        if p._qinglong_cd > 0:
            return
        if p.energy < 8:
            self._flash_msg = "能量不足(需8)，螺旋水柱未充能"
            self._flash_timer = 0.7
            return
        p.energy -= 8
        if p.energy <= 0: p._energy_depleted = True
        p._qinglong_cd = 0.08  # 极快连射
        dx = mx - p.x; dy = my - p.y; d = math.hypot(dx, dy) or 1
        a0 = math.atan2(dy, dx)
        # 螺旋波浪柱：沿方向延伸的螺旋形水柱
        self.qinglong_dragons.append({
            "kind": "spiral_beam",  # 螺旋波浪柱
            "x": p.x, "y": p.y,
            "vx": math.cos(a0),
            "vy": math.sin(a0),
            "angle": a0,
            "length": 1200,
            "r": 14,
            "life": 0.22, "max": 0.22,
            "owner": p, "_dead": False, "hit_cd": {},
            "spiral_phase": 0.0,     # 螺旋相位（随时间旋转）
            "spiral_amp": 22,        # 螺旋振幅（波浪宽度）
            "spiral_freq": 0.06,     # 螺旋频率（沿长度的波数密度）
        })
        # 水柱喷射粒子
        for k in range(16):
            a = a0 + random.uniform(-0.18, 0.18)
            self.particles.append(Particle(
                p.x + math.cos(a0) * p.r,
                p.y + math.sin(a0) * p.r,
                math.cos(a) * (520 + random.uniform(-80, 80)),
                math.sin(a) * (520 + random.uniform(-80, 80)),
                0.3, (100, 230, 220), 2.6
            ))
        self._play("shoot")

    def _baihu_left_click(self, mx, my):
        """碎雪巡使左键：月牙刃·发射弧形月牙刃飞行物（接触爆炸，能耗18，冷却0.32s）"""
        p = self.player
        if not p or not p.alive:
            return
        if getattr(p, "_baihu_cd", 0) > 0:
            return
        if p.energy < 18:
            self._flash_msg = "能量不足(需18)，月牙刃未充能"
            self._flash_timer = 0.7
            return
        p.energy -= 18
        if p.energy <= 0: p._energy_depleted = True
        p._baihu_cd = 0.32
        dx = mx - p.x; dy = my - p.y; base = math.atan2(dy, dx)
        if not hasattr(self, "baihu_blades"):
            self.baihu_blades = []
        # 单道大月牙刃（弧形飞行 + 接触爆炸）
        self.baihu_blades.append({
            "x": p.x, "y": p.y,
            "vx": math.cos(base) * 520, "vy": math.sin(base) * 520,
            "r": 24, "life": 1.2, "max": 1.2, "hit": set(),
            "owner": p, "_dead": False, "crescent": True,
            "explode_r": 100, "explode_dmg": 4.0
        })
        # 月牙喷射粒子
        for k in range(24):
            a = base + random.uniform(-0.5, 0.5)
            self.particles.append(Particle(
                p.x + math.cos(base) * p.r,
                p.y + math.sin(base) * p.r,
                math.cos(a) * (320 + random.uniform(-60, 60)),
                math.sin(a) * (320 + random.uniform(-60, 60)),
                0.45, (255, 255, 255), 2.8
            ))
        self._play("shoot")

    def _zhuque_left_click(self, mx, my):
        """燎原武侯左键：燎原连珠·高射速穿透天火连射（远程好看特效，能耗15）"""
        p = self.player
        if not p or not p.alive:
            return
        if p._zhuque_cd > 0:
            return
        if p.energy < 15:
            self._flash_msg = "能量不足(需15)，燎原火未充能"
            self._flash_timer = 0.7
            return
        p.energy -= 15
        if p.energy <= 0: p._energy_depleted = True
        p._zhuque_cd = 0.22  # 高射速
        dx = mx - p.x; dy = my - p.y; d = math.hypot(dx, dy) or 1
        # 三连发（一发能耗=15，连珠3颗，视觉连贯）
        for k in range(3):
            a0 = math.atan2(dy, dx) + random.uniform(-0.06, 0.06)
            self.zhuque_fire.append({
                "x": p.x + dx/d * (p.r + 10 + k * 3),
                "y": p.y + dy/d * (p.r + 10 + k * 3),
                "vx": math.cos(a0) * 640, "vy": math.sin(a0) * 640,
                "r": 11, "life": 1.8, "max": 1.8, "hit": set(),
                "owner": p, "_dead": False
            })
        # 尾焰粒子
        for k in range(18):
            a = math.atan2(dy, dx) + random.uniform(-0.4, 0.4)
            self.particles.append(Particle(
                p.x + dx/d * p.r,
                p.y + dy/d * p.r,
                math.cos(a) * (320 + random.uniform(-50, 80)),
                math.sin(a) * (320 + random.uniform(-50, 80)),
                0.35,
                random.choice([(255, 120, 60), (255, 200, 80), (255, 80, 40)]),
                2.6
            ))
        self._play("shoot")

    def _xuanwu_left_click(self, mx, my):
        """玄冰卫圣左键：玄冰锥·召唤单支巨冰锥(单点爆炸+冻结，能耗35)"""
        p = self.player
        if not p or not p.alive:
            return
        if p._xuanwu_cd > 0:
            return
        if p.energy < 35:
            self._flash_msg = "能量不足(需35)，玄冰锥未凝聚"
            self._flash_timer = 0.7
            return
        p.energy -= 35
        if p.energy <= 0: p._energy_depleted = True
        p._xuanwu_cd = 0.55
        dx = mx - p.x; dy = my - p.y; base = math.atan2(dy, dx)
        # 单支巨冰锥（朝鼠标）
        self.xuanwu_ices.append({
            "x": p.x + math.cos(base) * p.r,
            "y": p.y + math.sin(base) * p.r,
            "vx": math.cos(base) * 520, "vy": math.sin(base) * 520,
            "r": 26, "life": 1.8, "max": 1.8,
            "owner": p, "_dead": False,
            "big_spike": True,  # 单支巨冰锥：撞后爆炸 + 冻结
            "pierced": False
        })
        # 冰晶粒子
        for k in range(22):
            a = base + random.uniform(-0.3, 0.3)
            self.particles.append(Particle(
                p.x + math.cos(base) * p.r,
                p.y + math.sin(base) * p.r,
                math.cos(a) * (360 + random.uniform(-60, 60)),
                math.sin(a) * (360 + random.uniform(-60, 60)),
                0.4, (160, 220, 255), 2.8
            ))
        self._play("shoot")

    def _stargod_left_click(self, mx, my):
        """星陨领主左键：星裂陨·大陨石砸落后爆裂成4颗小陨石（远程爆炸+范围伤害，能耗45）"""
        p = self.player
        if not p or not p.alive:
            return
        if p._stargod_cd > 0:
            return
        if p.energy < 45:
            self._flash_msg = "能量不足(需45)，无法召唤星裂陨"
            self._flash_timer = 0.8
            return
        p.energy -= 45
        if p.energy <= 0: p._energy_depleted = True
        p._stargod_cd = 0.85
        # 1 颗大陨石朝鼠标方向（从天而降）
        base = math.atan2(my - p.y, mx - p.x)
        sx = p.x + math.cos(base) * (p.r + 20) - (my - p.y) * 0.4
        sy = p.y + math.sin(base) * (p.r + 20) + (mx - p.x) * 0.4
        self.stargod_meteors.append({
            "x": sx, "y": sy,
            "vx": math.cos(base) * 320, "vy": math.sin(base) * 320,
            "r": 36, "life": 3.0, "max": 3.0,
            "owner": p, "_dead": False,
            "big_meteor": True,  # 爆炸时裂成 4 颗小陨石
            "split_target_x": mx, "split_target_y": my
        })
        # 尾焰粒子
        for k in range(24):
            a = base + random.uniform(-0.4, 0.4)
            self.particles.append(Particle(
                sx, sy,
                math.cos(a) * (280 + random.uniform(-50, 60)),
                math.sin(a) * (280 + random.uniform(-50, 60)),
                0.5,
                random.choice([(150, 220, 255), (100, 180, 255), (200, 240, 255)]),
                3.0
            ))
        self._play("warn")

    def _chrono_left_click(self, mx, my):
        """时空猎手左键：裂空闪·向前快闪一大步（能耗15，冷却0.4s，瞬移+0.3s无敌+残影）"""
        p = self.player
        if not p or not p.alive:
            return
        if p._chrono_cd > 0:
            return
        if p.energy < 15:
            self._flash_msg = "能量不足(需15)，裂空闪未充能"
            self._flash_timer = 0.7
            return
        p.energy -= 15
        if p.energy <= 0: p._energy_depleted = True
        p._chrono_cd = 0.4
        dx = mx - p.x; dy = my - p.y; d = math.hypot(dx, dy) or 1
        nx = dx / d; ny = dy / d
        # 快闪距离 300px（限制在屏幕内）
        land_x = p.x + nx * 300
        land_y = p.y + ny * 300
        land_x = max(p.r, min(WIDTH - p.r, land_x))
        land_y = max(p.r, min(HEIGHT - p.r, land_y))
        # 残影粒子（沿路径 10 段紫色幻影）
        for k in range(11):
            t_ = k / 10
            sx = p.x + (land_x - p.x) * t_
            sy = p.y + (land_y - p.y) * t_
            for col in ((180, 120, 255), (220, 180, 255), (140, 90, 255)):
                self.particles.append(Particle(
                    sx + random.uniform(-4, 4),
                    sy + random.uniform(-4, 4),
                    random.uniform(-40, 40),
                    random.uniform(-40, 40),
                    0.5 - t_ * 0.25, col, 3.2
                ))
        # 瞬移 + 0.3s 无敌
        p.x = land_x; p.y = land_y
        p.invulnerable = max(getattr(p, "invulnerable", 0.0), 0.3)
        self._play("shockwave")

    def _buddha_left_click(self, mx, my):
        """不灭尊者左键：舍利子球·最多加6颗子球贪吃蛇叠加巡游（敌碰球爆炸连锁，碰我则球挡伤害减数量，能耗30）"""
        p = self.player
        if not p or not p.alive:
            return
        if p._buddha_cd > 0:
            return
        if p.energy < 30:
            self._flash_msg = "能量不足(需30)，舍利子球未凝聚"
            self._flash_timer = 0.8
            return
        # 最多加 6 颗（超过则不加，仅提示）
        arr = getattr(p, "_buddha_satellites", None)
        if arr is None:
            p._buddha_satellites = []
            arr = p._buddha_satellites
        if len(arr) >= 6:
            self._flash_msg = "舍利子球已达上限(6颗)，无法再新增"
            self._flash_timer = 0.9
            return
        p.energy -= 30
        if p.energy <= 0: p._energy_depleted = True
        p._buddha_cd = 0.55
        # 加在尾部（按已有数量的角度间隔，形成贪吃蛇/卫星串）
        ang = math.atan2(my - p.y, mx - p.x) + len(arr) * 0.55
        arr.append({
            "x": p.x + math.cos(ang) * (p.r + 18),
            "y": p.y + math.sin(ang) * (p.r + 18),
            "vx": 0.0, "vy": 0.0,
            "r": 14, "owner": p,
            "hp": 2, "explode_dmg": 5.5, "explode_r": 150,
            "_dead": False
        })
        # 金色粒子
        for k in range(24):
            a = random.uniform(0, math.tau)
            rr = random.uniform(20, 80)
            self.particles.append(Particle(
                p.x, p.y,
                math.cos(a) * (220 + random.uniform(-40, 60)),
                math.sin(a) * (220 + random.uniform(-40, 60)),
                0.5,
                random.choice([(255, 220, 120), (255, 240, 160), (255, 200, 80)]),
                2.8
            ))
        self._play("powerup")

    def _god_left_click(self, mx, my):
        """极律虚皇左键：虚皇圣律·蓝色光柱穿透+击退（远程好看特效，能耗30）"""
        p = self.player
        if not p or not p.alive:
            return
        if p._god_cd > 0:
            return
        if p.energy < 30:
            self._flash_msg = "能量不足(需30)，虚皇圣律未充能"
            self._flash_timer = 0.8
            return
        p.energy -= 30
        if p.energy <= 0: p._energy_depleted = True
        p._god_cd = 0.42
        dx = mx - p.x; dy = my - p.y; d = math.hypot(dx, dy) or 1
        a0 = math.atan2(dy, dx)
        # 朝鼠标方向 1 道穿透蓝光柱（宽 26，长 1400，持续 0.5s，扫过即扣血+击退）
        if not hasattr(self, "god_pillars"):
            self.god_pillars = []
        # 用 god_pillars 数组存"光柱"；字段区分 type="beam"
        self.god_pillars.append({
            "type": "beam",
            "x": p.x, "y": p.y,
            "angle": a0,
            "width": 26, "length": 1500,
            "life": 0.5, "max": 0.5,
            "owner": p, "_dead": False,
            "hit": set(),  # 已命中敌人
            "knockback": 420
        })
        # 蓝白能量柱粒子爆发
        for ring, col in ((60, (120, 200, 255)), (130, (200, 240, 255)), (220, (160, 220, 255))):
            for k in range(22):
                a = a0 + random.uniform(-0.45, 0.45)
                self.particles.append(Particle(
                    p.x + math.cos(a0) * p.r,
                    p.y + math.sin(a0) * p.r,
                    math.cos(a) * (420 + random.uniform(-60, 120)),
                    math.sin(a) * (420 + random.uniform(-60, 120)),
                    0.45, col, 3.2
                ))
        self.shake = max(self.shake, 0.25)
        self._play("thunder")

    def _update_page3_skills(self, dt):
        """第三页 9 个皮肤的技能更新（全面重制为新技能体系）"""
        p0 = self.player
        # ===== 1. 裂空雷将：追踪雷弹（左键 2 枚 + 右键 6 枚落地即爆） =====
        for b in self.titan_hammers:
            if b["_dead"]: continue
            # 追踪逻辑（如果有 track_target，优先锁定）
            tgt = b.get("track_target")
            if tgt is None or getattr(tgt, "_dead", True):
                # 自动找最近目标（右键雷弹也能追踪）
                best_s, best_d = None, 1e9
                for s in self.stars:
                    if s.danger and not s._dead:
                        dd = math.hypot(s.x - b["x"], s.y - b["y"])
                        if dd < best_d and dd < 500:
                            best_d, best_s = dd, s
                tgt = best_s
                b["track_target"] = tgt
            if tgt is not None and not getattr(tgt, "_dead", True):
                dx = tgt.x - b["x"]; dy = tgt.y - b["y"]
                d_ = math.hypot(dx, dy) or 1
                b["vx"] = lerp(b["vx"], dx/d_ * 460, min(1.0, 6.0 * dt))
                b["vy"] = lerp(b["vy"], dy/d_ * 460, min(1.0, 6.0 * dt))
            b["x"] += b["vx"] * dt; b["y"] += b["vy"] * dt
            b["life"] -= dt
            # 雷尾粒子
            if random.random() < 0.85:
                self.particles.append(Particle(
                    b["x"], b["y"],
                    random.uniform(-40, 40), random.uniform(-40, 40),
                    0.25, (120, 180, 255), 2.8
                ))
            if b["life"] <= 0 or b["x"] < -80 or b["x"] > WIDTH + 80 or b["y"] < -80 or b["y"] > HEIGHT + 80:
                # 寿命结束爆炸（不扣血的小爆）
                self.burst(b["x"], b["y"], (120, 180, 255), 40, 360, size=4.0, life=0.7)
                b["_dead"] = True; continue
            # 碰到敌人：穿透扣血 + 0.3s 冷却（左键追踪弹）
            if not b.get("global_bomb"):
                for s in self.stars:
                    if s.danger and not s._dead:
                        sid = id(s)
                        cd = b["hit_cd"].get(sid, 0)
                        if cd > 0:
                            b["hit_cd"][sid] = max(0, cd - dt)
                            continue
                        if math.hypot(s.x - b["x"], s.y - b["y"]) < s.r + b["r"]:
                            self._damage_enemy(s, 3.0, b["owner"],
                                               knock=(b["vx"] * 0.35, b["vy"] * 0.35))
                            b["hit_cd"][sid] = 0.32
                            # 电链粒子
                            for _ in range(4):
                                self.particles.append(Particle(
                                    (b["x"] + s.x) / 2, (b["y"] + s.y) / 2,
                                    random.uniform(-40, 40), random.uniform(-40, 40),
                                    0.15, (120, 220, 255), 2.6
                                ))
        self.titan_hammers = [b for b in self.titan_hammers if not b["_dead"]]

        # ===== 2. 沧溟潮君：高压双水炮(ball 穿透+击退) + 六道潮卷(tornado 护体) =====
        if p0 and p0.alive and p0._qinglong_timer > 0:
            p0._qinglong_timer = max(0.0, p0._qinglong_timer - dt)
        for b in self.qinglong_dragons:
            if b["_dead"]: continue
            b["life"] -= dt
            if b["life"] <= 0:
                b["_dead"] = True; continue
            if b.get("kind") == "ball":
                # 高压水炮：穿透 + 击退 + 命中减速/喷水粒子
                b["x"] += b["vx"] * dt; b["y"] += b["vy"] * dt
                if random.random() < 0.9:
                    self.particles.append(Particle(
                        b["x"], b["y"],
                        random.uniform(-40, 40), random.uniform(-40, 40),
                        0.25, (100, 230, 200), 2.6
                    ))
                if b["x"] < -60 or b["x"] > WIDTH + 60 or b["y"] < -60 or b["y"] > HEIGHT + 60:
                    b["_dead"] = True; continue
                pierced = b.setdefault("pierced", set())
                for s in self.stars:
                    if s.danger and not s._dead and id(s) not in pierced:
                        if math.hypot(s.x - b["x"], s.y - b["y"]) < s.r + b["r"]:
                            pierced.add(id(s))
                            kb = 420 if b.get("knockback") else 260
                            dxu = b["vx"]; dyu = b["vy"]
                            sp = math.hypot(dxu, dyu) or 1
                            self._damage_enemy(s, 2.8, b["owner"],
                                               knock=(dxu / sp * kb, dyu / sp * kb))
            elif b.get("kind") == "tornado":
                # 六道潮卷：围绕玩家旋转 + 碰撞爆炸 + 攻击敌人
                b["phase"] = b.get("phase", 0.0) + dt * 2.2
                orbit = (p0.r if (p0 and p0.alive) else 50) + 110 + 28 * math.sin(b["phase"] * 1.2)
                if p0 and p0.alive:
                    tx = p0.x + math.cos(b["phase"]) * orbit
                    ty = p0.y + math.sin(b["phase"]) * orbit
                    ddx = tx - b["x"]; ddy = ty - b["y"]
                    b["vx"] = lerp(b.get("vx", 0.0), ddx * 8, min(1.0, dt * 8))
                    b["vy"] = lerp(b.get("vy", 0.0), ddy * 8, min(1.0, dt * 8))
                b["x"] += b.get("vx", 0.0) * dt; b["y"] += b.get("vy", 0.0) * dt
                # 潮卷水花粒子
                if random.random() < 0.6:
                    self.particles.append(Particle(
                        b["x"], b["y"],
                        random.uniform(-60, 60), random.uniform(-60, 60),
                        0.35, (120, 220, 210), 2.8
                    ))
                # 碰敌人爆炸
                exploded = False
                for s in self.stars:
                    if s.danger and not s._dead:
                        if math.hypot(s.x - b["x"], s.y - b["y"]) < s.r + b["r"]:
                            exploded = True; break
                if exploded:
                    R = b.get("explode_r", 160)
                    for s in list(self.stars):
                        if s.danger and not s._dead:
                            dd = math.hypot(s.x - b["x"], s.y - b["y"])
                            if dd < R:
                                f = 1 - dd / R
                                self._damage_enemy(s, b.get("explode_dmg", 5.0) * f + 2.0, b["owner"])
                                ddx = s.x - b["x"]; ddy = s.y - b["y"]; d0 = dd or 1
                                s.vx += ddx / d0 * 560 * f
                                s.vy += ddy / d0 * 560 * f
                    self.burst(b["x"], b["y"], (80, 220, 180), 80, 480, size=5.2, life=1.0)
                    b["_dead"] = True
            elif b.get("kind") in ("beam", "spiral_beam"):
                # 高压水柱/螺旋波浪柱（不移动，存在期间持续伤害+击退+水花）
                ang = b.get("angle", 0.0)
                length = b.get("length", 1200)
                ax = b["x"]; ay = b["y"]
                bx_ = ax + math.cos(ang) * length
                by_ = ay + math.sin(ang) * length
                abx = bx_ - ax; aby = by_ - ay
                ab2 = abx * abx + aby * aby or 1.0
                r = b.get("r", 8)
                hit_cd = b.setdefault("hit_cd", {})
                # 螺旋相位推进
                if b.get("kind") == "spiral_beam":
                    b["spiral_phase"] = b.get("spiral_phase", 0.0) + dt * 8.0
                # 水花粒子（沿水柱随机分布）
                if random.random() < 0.95:
                    t_ = random.uniform(0.0, 1.0)
                    px = ax + abx * t_
                    py = ay + aby * t_
                    self.particles.append(Particle(
                        px + random.uniform(-4, 4), py + random.uniform(-4, 4),
                        random.uniform(-40, 40), random.uniform(-40, 40),
                        0.2, (100, 230, 220), 2.4
                    ))
                # 沿直线伤害敌人（点到线段距离，螺旋柱判定半径加大）
                coll_r = r + (b.get("spiral_amp", 0) if b.get("kind") == "spiral_beam" else 0)
                for s in self.stars:
                    if s.danger and not s._dead:
                        sid = id(s)
                        if hit_cd.get(sid, 0) > 0:
                            hit_cd[sid] -= dt
                            continue
                        apx = s.x - ax; apy = s.y - ay
                        t_ = max(0.0, min(1.0, (apx * abx + apy * aby) / ab2))
                        cx_ = ax + abx * t_
                        cy_ = ay + aby * t_
                        dist = math.hypot(s.x - cx_, s.y - cy_)
                        if dist < s.r + coll_r:
                            dmg = 3.0 if b.get("kind") == "spiral_beam" else 2.5
                            self._damage_enemy(s, dmg, b["owner"],
                                               knock=(math.cos(ang) * 360, math.sin(ang) * 360))
                            s.hit_flash = 0.2
                            hit_cd[sid] = 0.12  # 短冷却，持续喷射
                            # 命中水花
                            for _ in range(4):
                                a = random.uniform(0, math.tau)
                                self.particles.append(Particle(
                                    s.x, s.y,
                                    math.cos(a) * random.uniform(40, 140),
                                    math.sin(a) * random.uniform(40, 140),
                                    0.25, (120, 220, 210), 2.6
                                ))
        self.qinglong_dragons = [b for b in self.qinglong_dragons if not b["_dead"]]

        # ===== 3. 碎雪巡使：三重碎雪刃（近程大爆炸）+ 4雪煞影分身 =====
        if not hasattr(self, "baihu_blades"): self.baihu_blades = []
        for b in self.baihu_blades:
            if b["_dead"]: continue
            b["x"] += b["vx"] * dt; b["y"] += b["vy"] * dt
            b["life"] -= dt
            if random.random() < 0.75:
                self.particles.append(Particle(
                    b["x"], b["y"],
                    random.uniform(-40, 40), random.uniform(-40, 40),
                    0.25, (255, 255, 255), 2.6
                ))
            # 雪刃：碰到敌人 OR 寿命结束 都爆炸
            exploded = False
            for s in self.stars:
                if s.danger and not s._dead and id(s) not in b.setdefault("hit", set()):
                    if math.hypot(s.x - b["x"], s.y - b["y"]) < s.r + b["r"]:
                        b["hit"].add(id(s)); exploded = True; break
            if b["life"] <= 0 or b["x"] < -60 or b["x"] > WIDTH + 60 or b["y"] < -60 or b["y"] > HEIGHT + 60:
                exploded = True
            if exploded:
                R = b.get("explode_r", 120)
                for s in list(self.stars):
                    if s.danger and not s._dead:
                        dd = math.hypot(s.x - b["x"], s.y - b["y"])
                        if dd < R:
                            f = 1 - dd / R
                            self._damage_enemy(s, b.get("explode_dmg", 4.5) * f + 1.5, b["owner"])
                self.burst(b["x"], b["y"], (240, 245, 255), 60, 420, size=4.6, life=0.8)
                b["_dead"] = True
        self.baihu_blades = [b for b in self.baihu_blades if not b["_dead"]]
        # 雪煞影分身（4 只）
        for b in self.baihu_shadows:
            if b["_dead"]: continue
            b["x"] += b["vx"] * dt; b["y"] += b["vy"] * dt
            b["life"] -= dt
            if random.random() < 0.8:
                self.particles.append(Particle(
                    b["x"], b["y"],
                    random.uniform(-40, 40), random.uniform(-40, 40),
                    0.25, (255, 255, 255), 2.8
                ))
            exploded = False
            if (b["life"] <= 0 or b["x"] < -80 or b["x"] > WIDTH + 80
                    or b["y"] < -80 or b["y"] > HEIGHT + 80):
                exploded = True
            else:
                for s in self.stars:
                    if s.danger and not s._dead:
                        if math.hypot(s.x - b["x"], s.y - b["y"]) < s.r + b["r"]:
                            exploded = True; break
            if exploded:
                R = b.get("explode_r", 180)
                for s in list(self.stars):
                    if s.danger and not s._dead:
                        dd = math.hypot(s.x - b["x"], s.y - b["y"])
                        if dd < R:
                            f = 1 - dd / R
                            self._damage_enemy(s, b.get("explode_dmg", 5.5) * f + 2.5, b["owner"])
                            ddx = s.x - b["x"]; ddy = s.y - b["y"]; d0 = dd or 1
                            s.vx += ddx / d0 * 620 * f
                            s.vy += ddy / d0 * 620 * f
                self.burst(b["x"], b["y"], (245, 250, 255), 80, 480, size=5.2, life=1.0)
                b["_dead"] = True
        self.baihu_shadows = [b for b in self.baihu_shadows if not b["_dead"]]
        # 圆环刃（baihu_rings：360度扩张圆环，厚度内敌人受伤+击退）
        if not hasattr(self, "baihu_rings"): self.baihu_rings = []
        for ring in self.baihu_rings:
            if ring["_dead"]: continue
            ring["life"] -= dt
            # 半径按 expand_speed 扩张
            ring["r"] += ring["expand_speed"] * dt
            # 沿圆环散落粒子
            if random.random() < 0.9:
                a = random.uniform(0, math.tau)
                self.particles.append(Particle(
                    ring["x"] + math.cos(a) * ring["r"],
                    ring["y"] + math.sin(a) * ring["r"],
                    random.uniform(-30, 30), random.uniform(-30, 30),
                    0.3, (240, 250, 255), 2.8
                ))
            # 圆环厚度内（r-30 ~ r+30）的敌人受伤 + 击退（每敌仅一次）
            for s in list(self.stars):
                if s.danger and not s._dead and id(s) not in ring["hit"]:
                    dd = math.hypot(s.x - ring["x"], s.y - ring["y"])
                    if ring["r"] - 30 < dd < ring["r"] + 30:
                        ring["hit"].add(id(s))
                        self._damage_enemy(s, ring["dmg"], ring["owner"])
                        ddx = s.x - ring["x"]; ddy = s.y - ring["y"]; d0 = dd or 1
                        s.vx += ddx / d0 * 420
                        s.vy += ddy / d0 * 420
            # 超过最大半径 → 移除
            if ring["r"] > ring["max_r"]:
                ring["_dead"] = True
        self.baihu_rings = [r for r in self.baihu_rings if not r["_dead"]]

        # ===== 4. 燎原武侯：燎原连珠（穿透三连发） =====
        for b in self.zhuque_fire:
            if b["_dead"]: continue
            b["x"] += b["vx"] * dt; b["y"] += b["vy"] * dt
            b["life"] -= dt
            if random.random() < 0.95:
                self.particles.append(Particle(
                    b["x"], b["y"],
                    random.uniform(-40, 40), random.uniform(-40, 40),
                    0.3, random.choice([(255, 120, 60), (255, 200, 80), (255, 80, 40)]), 2.8
                ))
            if b["life"] <= 0 or b["x"] < -60 or b["x"] > WIDTH + 60 or b["y"] < -60 or b["y"] > HEIGHT + 60:
                b["_dead"] = True; continue
            for s in self.stars:
                if s.danger and not s._dead and id(s) not in b["hit"]:
                    if math.hypot(s.x - b["x"], s.y - b["y"]) < s.r + b["r"]:
                        b["hit"].add(id(s))
                        dxu = b["vx"]; dyu = b["vy"]; sp = math.hypot(dxu, dyu) or 1
                        self._damage_enemy(s, 3.0, b["owner"],
                                           knock=(dxu / sp * 260, dyu / sp * 260))
        self.zhuque_fire = [b for b in self.zhuque_fire if not b["_dead"]]
        # 火龙卷风（zhuque_tornados：前进 + 吸附敌人 + 持续 tick 伤害）
        if not hasattr(self, "zhuque_tornados"): self.zhuque_tornados = []
        for b in self.zhuque_tornados:
            if b["_dead"]: continue
            b["x"] += b["vx"] * dt; b["y"] += b["vy"] * dt
            b["life"] -= dt
            b["spin_phase"] += dt * 8.0
            # 火焰漩涡粒子
            if random.random() < 0.95:
                a = random.uniform(0, math.tau)
                rr = random.uniform(0, b["r"])
                self.particles.append(Particle(
                    b["x"] + math.cos(a) * rr,
                    b["y"] + math.sin(a) * rr,
                    math.cos(a + b["spin_phase"]) * 60,
                    math.sin(a + b["spin_phase"]) * 60,
                    0.4, random.choice([(255, 120, 60), (255, 200, 80), (255, 80, 40)]), 3.0
                ))
            # 吸附 + 持续伤害：r 内敌人被吸向中心，速度同步龙卷风，按 0.2s tick 受伤
            for s in list(self.stars):
                if s.danger and not s._dead:
                    dd = math.hypot(s.x - b["x"], s.y - b["y"])
                    if dd < b["r"]:
                        ddx = b["x"] - s.x; ddy = b["y"] - s.y; d0 = dd or 1
                        s.vx = lerp(s.vx, b["vx"] + ddx / d0 * 120, min(1.0, dt * 4))
                        s.vy = lerp(s.vy, b["vy"] + ddy / d0 * 120, min(1.0, dt * 4))
                        last = b["hit_cd"].get(id(s), 0.0) - dt
                        if last <= 0:
                            self._damage_enemy(s, 2.0, b["owner"])
                            last = 0.2
                        b["hit_cd"][id(s)] = last
            if b["life"] <= 0:
                b["_dead"] = True
        self.zhuque_tornados = [b for b in self.zhuque_tornados if not b["_dead"]]

        # ===== 5. 玄冰卫圣：单冰锥(左键) + 冰锥雨(右键36根,单点不穿透) =====
        for b in self.xuanwu_ices:
            if b["_dead"]: continue
            b["x"] += b["vx"] * dt; b["y"] += b["vy"] * dt
            b["life"] -= dt
            if random.random() < 0.7:
                self.particles.append(Particle(
                    b["x"], b["y"],
                    random.uniform(-30, 30), random.uniform(-30, 30),
                    0.25, (160, 220, 255), 2.6
                ))
            if b["life"] <= 0 or b["x"] < -80 or b["x"] > WIDTH + 80 or b["y"] < -80 or b["y"] > HEIGHT + 80:
                b["_dead"] = True; continue
            hit_s = None
            for s in self.stars:
                if s.danger and not s._dead:
                    if math.hypot(s.x - b["x"], s.y - b["y"]) < s.r + b["r"]:
                        hit_s = s; break
            if hit_s is not None:
                if b.get("big_spike"):
                    # 左键巨冰锥：爆炸 + 冻结（半径 200）
                    R = 200
                    for s in list(self.stars):
                        if s.danger and not s._dead:
                            dd = math.hypot(s.x - b["x"], s.y - b["y"])
                            if dd < R:
                                f = 1 - dd / R
                                self._damage_enemy(s, 4.5 * f + 2.0, b["owner"])
                                s.frozen_timer = max(s.frozen_timer, 2.5)
                                ddx = s.x - b["x"]; ddy = s.y - b["y"]; d0 = dd or 1
                                s.vx += ddx / d0 * 420 * f
                                s.vy += ddy / d0 * 420 * f
                    self.burst(b["x"], b["y"], (160, 220, 255), 90, 520, size=5.4, life=1.1)
                else:
                    # 冰锥雨（rain_spike）：单点不穿透（只伤命中那一只，高伤+冻结，不爆炸AOE）
                    self._damage_enemy(hit_s, 6.0, b["owner"])
                    hit_s.frozen_timer = max(hit_s.frozen_timer, 3.0)
                    # 仅在命中点散出冰花（无AOE）
                    for _ in range(20):
                        a = random.uniform(0, math.tau)
                        self.particles.append(Particle(
                            b["x"], b["y"],
                            math.cos(a) * 180, math.sin(a) * 180,
                            0.4, (160, 220, 255), 2.6
                        ))
                b["_dead"] = True
        self.xuanwu_ices = [b for b in self.xuanwu_ices if not b["_dead"]]

        # ===== 6. 星陨领主：大陨石爆4小陨石 + 八曜护体恒星（碰一个爆一个）=====
        for b in self.stargod_meteors:
            if b["_dead"]: continue
            b["x"] += b["vx"] * dt; b["y"] += b["vy"] * dt
            b["life"] -= dt
            if random.random() < 0.8:
                self.particles.append(Particle(
                    b["x"], b["y"],
                    random.uniform(-50, 50), random.uniform(-50, 50),
                    0.3, random.choice([(150, 220, 255), (100, 180, 255)]), 3.0
                ))
            exploded = False
            if b["y"] > HEIGHT + 60 or b["life"] <= 0:
                if b["y"] <= HEIGHT + 60 or b["life"] <= 0:
                    exploded = True
            else:
                for s in self.stars:
                    if s.danger and not s._dead:
                        if math.hypot(s.x - b["x"], s.y - b["y"]) < s.r + b["r"]:
                            exploded = True; break
            if exploded:
                R = 220 if b.get("big_meteor") else 150
                dmg = 4.5 if b.get("big_meteor") else 2.8
                for s in list(self.stars):
                    if s.danger and not s._dead:
                        dd = math.hypot(s.x - b["x"], s.y - b["y"])
                        if dd < R:
                            f = 1 - dd / R
                            self._damage_enemy(s, dmg * f + 1.2, b["owner"])
                            ddx = s.x - b["x"]; ddy = s.y - b["y"]; d0 = dd or 1
                            s.vx += ddx / d0 * (520 if b.get("big_meteor") else 320) * f
                            s.vy += ddy / d0 * (520 if b.get("big_meteor") else 320) * f
                self.burst(b["x"], b["y"], (150, 220, 255), 70 if b.get("big_meteor") else 40,
                           460 if b.get("big_meteor") else 300,
                           size=5.0 if b.get("big_meteor") else 3.2,
                           life=0.9 if b.get("big_meteor") else 0.6)
                # 如果是大陨石 → 爆裂成 4 颗小陨石（十字方向）
                if b.get("big_meteor"):
                    for k in range(4):
                        ang = k * (math.tau / 4) + random.uniform(-0.15, 0.15)
                        self.stargod_meteors.append({
                            "x": b["x"], "y": b["y"],
                            "vx": math.cos(ang) * 260 + random.uniform(-40, 40),
                            "vy": math.sin(ang) * 260 + random.uniform(-40, 40),
                            "r": 20, "life": 1.6, "max": 1.6,
                            "owner": b.get("owner"), "_dead": False,
                            "big_meteor": False
                        })
                b["_dead"] = True
        self.stargod_meteors = [b for b in self.stargod_meteors if not b["_dead"]]
        # 八曜护体恒星（碰一个爆一个 + 击退 + 敌人来袭自动吸附攻击）
        if p0 and p0.alive and p0._stargod_timer > 0:
            p0._stargod_timer = max(0.0, p0._stargod_timer - dt)
            if not hasattr(p0, "_stargod_phase") or len(p0._stargod_phase) < 8:
                p0._stargod_phase = [i * math.tau / 8 for i in range(8)]
            if not hasattr(p0, "_stargod_sun_hp") or len(p0._stargod_sun_hp) < 8:
                p0._stargod_sun_hp = [2 for _ in range(8)]
            # _stargod_attacking：8 布尔，标记该颗是否正在出击
            if not hasattr(p0, "_stargod_attacking") or len(p0._stargod_attacking) < 8:
                p0._stargod_attacking = [False for _ in range(8)]
            # _stargod_atk_pos：出击中的恒星当前位置
            if not hasattr(p0, "_stargod_atk_pos") or len(p0._stargod_atk_pos) < 8:
                p0._stargod_atk_pos = [(0.0, 0.0) for _ in range(8)]
            # _stargod_atk_state：0=轨道, 1=出击, 2=返回
            if not hasattr(p0, "_stargod_atk_state") or len(p0._stargod_atk_state) < 8:
                p0._stargod_atk_state = [0 for _ in range(8)]
            # _stargod_atk_target：出击目标
            if not hasattr(p0, "_stargod_atk_target") or len(p0._stargod_atk_target) < 8:
                p0._stargod_atk_target = [None for _ in range(8)]
            # _stargod_atk_hit：本回合是否已命中
            if not hasattr(p0, "_stargod_atk_hit") or len(p0._stargod_atk_hit) < 8:
                p0._stargod_atk_hit = [False for _ in range(8)]
            for i in range(8):
                if p0._stargod_sun_hp[i] <= 0:
                    continue  # 该颗已爆
                p0._stargod_phase[i] += dt * 2.6
                orbit = p0.r + 120
                ox_s = p0.x + math.cos(p0._stargod_phase[i]) * orbit
                oy_s = p0.y + math.sin(p0._stargod_phase[i]) * orbit
                sr = 22
                state = p0._stargod_atk_state[i]
                if state == 0:
                    # 轨道运行：检测 200px 内的敌人 → 自动出击
                    target = None
                    for s in self.stars:
                        if s.danger and not s._dead:
                            if math.hypot(s.x - ox_s, s.y - oy_s) < 200:
                                target = s; break
                    if target is not None:
                        p0._stargod_atk_state[i] = 1
                        p0._stargod_atk_pos[i] = (ox_s, oy_s)
                        p0._stargod_atk_target[i] = target
                        p0._stargod_atk_hit[i] = False
                        p0._stargod_attacking[i] = True
                if state == 1:
                    # 出击中：飞向目标
                    tx, ty = p0._stargod_atk_pos[i]
                    target = p0._stargod_atk_target[i]
                    if target is None or getattr(target, "_dead", True) or not target.danger:
                        p0._stargod_atk_state[i] = 2  # 目标丢失 → 返回
                    else:
                        dx_a = target.x - tx; dy_a = target.y - ty
                        d_a = math.hypot(dx_a, dy_a) or 1
                        speed = 520
                        tx += dx_a / d_a * speed * dt
                        ty += dy_a / d_a * speed * dt
                        p0._stargod_atk_pos[i] = (tx, ty)
                        # 命中：伤害 + 吸附（拉向恒星），然后返回
                        if math.hypot(target.x - tx, target.y - ty) < target.r + sr:
                            if not p0._stargod_atk_hit[i]:
                                self._damage_enemy(target, 4.0, p0)
                                p0._stargod_atk_hit[i] = True
                            ddx = tx - target.x; ddy = ty - target.y
                            d0 = math.hypot(ddx, ddy) or 1
                            target.vx += ddx / d0 * 200 * dt
                            target.vy += ddy / d0 * 200 * dt
                            p0._stargod_atk_state[i] = 2
                    if random.random() < 0.6:
                        self.particles.append(Particle(
                            p0._stargod_atk_pos[i][0], p0._stargod_atk_pos[i][1],
                            random.uniform(-30, 30), random.uniform(-30, 30),
                            0.25, (255, 230, 120), 2.8
                        ))
                if state == 2:
                    # 返回轨道
                    tx, ty = p0._stargod_atk_pos[i]
                    dx_a = ox_s - tx; dy_a = oy_s - ty
                    d_a = math.hypot(dx_a, dy_a)
                    if d_a < 10:
                        p0._stargod_atk_state[i] = 0
                        p0._stargod_attacking[i] = False
                    else:
                        speed = 600
                        tx += dx_a / d_a * speed * dt
                        ty += dy_a / d_a * speed * dt
                        p0._stargod_atk_pos[i] = (tx, ty)
                    if random.random() < 0.5:
                        self.particles.append(Particle(
                            tx, ty,
                            random.uniform(-30, 30), random.uniform(-30, 30),
                            0.25, (255, 230, 120), 2.8
                        ))
                # 计算最终位置：轨道或出击位置
                if state == 0:
                    sx, sy = ox_s, oy_s
                else:
                    sx, sy = p0._stargod_atk_pos[i]
                # 恒星尾焰
                if random.random() < 0.5:
                    self.particles.append(Particle(
                        sx, sy,
                        random.uniform(-30, 30), random.uniform(-30, 30),
                        0.25, (255, 230, 120), 2.8
                    ))
                # 碰敌人：该颗立即爆炸消失（hp 减到 0），爆炸带击退
                exploded_i = False
                for s in self.stars:
                    if s.danger and not s._dead:
                        if math.hypot(s.x - sx, s.y - sy) < s.r + sr:
                            exploded_i = True; break
                if exploded_i:
                    R = 210
                    for s in list(self.stars):
                        if s.danger and not s._dead:
                            dd = math.hypot(s.x - sx, s.y - sy)
                            if dd < R:
                                f = 1 - dd / R
                                self._damage_enemy(s, 5.0 * f + 3.0, p0)
                                ddx = s.x - sx; ddy = s.y - sy; d0 = dd or 1
                                s.vx += ddx / d0 * 720 * f
                                s.vy += ddy / d0 * 720 * f
                    self.burst(sx, sy, (255, 230, 120), 90, 520, size=5.6, life=1.1)
                    p0._stargod_sun_hp[i] = 0
                    p0._stargod_attacking[i] = False
                    p0._stargod_atk_state[i] = 0

        # ===== 7. 时空猎手：裂空爪痕（chrono_claws 3道AOE） =====
        if not hasattr(self, "chrono_claws"): self.chrono_claws = []
        for b in self.chrono_claws:
            if b["_dead"]: continue
            b["x"] += b["vx"] * dt; b["y"] += b["vy"] * dt
            b["life"] -= dt
            if random.random() < 0.9:
                self.particles.append(Particle(
                    b["x"], b["y"],
                    random.uniform(-50, 50), random.uniform(-50, 50),
                    0.3, random.choice([(180, 120, 255), (220, 180, 255)]), 3.0
                ))
            exploded = False
            for s in self.stars:
                if s.danger and not s._dead and id(s) not in b.setdefault("hit", set()):
                    if math.hypot(s.x - b["x"], s.y - b["y"]) < s.r + b["r"]:
                        b["hit"].add(id(s)); exploded = True; break
            if b["life"] <= 0 or b["x"] < -80 or b["x"] > WIDTH + 80 or b["y"] < -80 or b["y"] > HEIGHT + 80:
                exploded = True
            if exploded:
                R = b.get("explode_r", 170)
                for s in list(self.stars):
                    if s.danger and not s._dead:
                        dd = math.hypot(s.x - b["x"], s.y - b["y"])
                        if dd < R:
                            f = 1 - dd / R
                            self._damage_enemy(s, b.get("explode_dmg", 5.0) * f + 2.0, b["owner"])
                            ddx = s.x - b["x"]; ddy = s.y - b["y"]; d0 = dd or 1
                            s.vx += ddx / d0 * 540 * f
                            s.vy += ddy / d0 * 540 * f
                self.burst(b["x"], b["y"], (180, 120, 255), 80, 480, size=5.4, life=1.0)
                b["_dead"] = True
        self.chrono_claws = [b for b in self.chrono_claws if not b["_dead"]]
        # 钩链/巨爪（chrono_hooks）
        if not hasattr(self, "chrono_hooks"): self.chrono_hooks = []
        for h in self.chrono_hooks:
            if h["_dead"]: continue
            owner = h["owner"]
            if owner is None or not owner.alive:
                h["_dead"] = True; continue
            if h.get("kind") == "giant_claw":
                # Q4：巨爪裂空·向前飞行，碰撞敌人造成伤害+击退
                h["x"] += h["vx"] * dt; h["y"] += h["vy"] * dt
                h["life"] -= dt
                if h["life"] <= 0:
                    h["_dead"] = True; continue
                if (h["x"] < -80 or h["x"] > WIDTH + 80
                        or h["y"] < -80 or h["y"] > HEIGHT + 80):
                    h["_dead"] = True; continue
                # 紫色拖尾粒子
                if random.random() < 0.9:
                    self.particles.append(Particle(
                        h["x"], h["y"],
                        random.uniform(-40, 40), random.uniform(-40, 40),
                        0.3, (180, 120, 255), 3.0
                    ))
                # 碰撞敌人：伤害 + 击退（每个敌人只命中一次）
                hit_set = h.setdefault("hit", set())
                ang = h.get("angle", 0.0)
                for s in self.stars:
                    if s.danger and not s._dead and id(s) not in hit_set:
                        if math.hypot(s.x - h["x"], s.y - h["y"]) < s.r + h["r"]:
                            hit_set.add(id(s))
                            self._damage_enemy(s, h.get("dmg", 6.0), owner,
                                               knock=(math.cos(ang) * h.get("knockback", 520),
                                                      math.sin(ang) * h.get("knockback", 520)))
                            s.hit_flash = 0.25
                            # 击中爆裂粒子
                            self.burst(s.x, s.y, (200, 140, 255), 18, 360, size=3.2, life=0.5)
                # 旋转角度
                h["angle"] = ang + dt * 8.0
            else:
                # 旧版钩链（兼容存档）
                h["_dead"] = True
        self.chrono_hooks = [h for h in self.chrono_hooks if not h["_dead"]]

        # ===== 8. 不灭尊者：buddha_hands（9金佛护体） + 舍利子球（6颗卫星） =====
        for b in self.buddha_hands:
            if b["_dead"]: continue
            b["life"] -= dt
            if b["life"] <= 0:
                # 寿命到：不爆炸（护体环绕金佛会周期爆炸）
                b["_dead"] = True; continue
            if b.get("kind") == "buddha":
                # 环绕金佛：围绕玩家公转 + 周期净化爆炸
                b["phase"] = b.get("phase", 0.0) + dt * 1.6
                orbit = (p0.r if (p0 and p0.alive) else 50) + 140
                if p0 and p0.alive:
                    tx = p0.x + math.cos(b["phase"]) * orbit
                    ty = p0.y + math.sin(b["phase"]) * orbit
                    ddx = tx - b["x"]; ddy = ty - b["y"]
                    b["vx"] = lerp(b.get("vx", 0.0), ddx * 8, min(1.0, dt * 8))
                    b["vy"] = lerp(b.get("vy", 0.0), ddy * 8, min(1.0, dt * 8))
                b["x"] += b.get("vx", 0.0) * dt; b["y"] += b.get("vy", 0.0) * dt
                # 金粉粒子
                if random.random() < 0.6:
                    self.particles.append(Particle(
                        b["x"], b["y"],
                        random.uniform(-40, 40), random.uniform(-40, 40),
                        0.3, random.choice([(255, 220, 120), (255, 240, 160)]), 2.8
                    ))
                # 周期爆炸（每 1.3s 一次）
                b["pulse_acc"] = b.get("pulse_acc", random.random() * 1.3) + dt
                if b["pulse_acc"] >= 1.3:
                    b["pulse_acc"] = 0.0
                    R = b.get("explode_r", 180)
                    for s in list(self.stars):
                        if s.danger and not s._dead:
                            dd = math.hypot(s.x - b["x"], s.y - b["y"])
                            if dd < R:
                                f = 1 - dd / R
                                self._damage_enemy(s, b.get("explode_dmg", 5.5) * f + 2.5, b["owner"])
                    self.burst(b["x"], b["y"], (255, 220, 120), 60, 420, size=4.8, life=0.9)
                # 碰敌人：金佛立即爆炸消失
                exploded = False
                for s in self.stars:
                    if s.danger and not s._dead:
                        if math.hypot(s.x - b["x"], s.y - b["y"]) < s.r + b["r"]:
                            exploded = True; break
                if exploded:
                    R = b.get("explode_r", 180)
                    for s in list(self.stars):
                        if s.danger and not s._dead:
                            dd = math.hypot(s.x - b["x"], s.y - b["y"])
                            if dd < R:
                                f = 1 - dd / R
                                self._damage_enemy(s, b.get("explode_dmg", 5.5) * f + 3.0, b["owner"])
                    self.burst(b["x"], b["y"], (255, 220, 120), 80, 480, size=5.4, life=1.0)
                    b["_dead"] = True
            else:
                # 老款佛手（保留兼容，直线击退）
                b["x"] += b.get("vx", 0) * dt; b["y"] += b.get("vy", 0) * dt
                if b["x"] < -60 or b["x"] > WIDTH + 60 or b["y"] < -60 or b["y"] > HEIGHT + 60:
                    b["_dead"] = True; continue
                for s in self.stars:
                    if s.danger and not s._dead:
                        if math.hypot(s.x - b["x"], s.y - b["y"]) < s.r + b["r"]:
                            dx_ = s.x - b["x"]; dy_ = s.y - b["y"]; d_ = math.hypot(dx_, dy_) or 1
                            self._damage_enemy(s, 3.2, b["owner"],
                                               knock=(dx_ / d_ * 700, dy_ / d_ * 700))
        self.buddha_hands = [b for b in self.buddha_hands if not b["_dead"]]
        # 舍利子球（6 颗贪吃蛇叠加巡游）：碰敌爆炸 + 碰我挡伤
        for pp in self.players:
            sats = getattr(pp, "_buddha_satellites", None)
            if not sats or not pp.alive:
                continue
            # --- 移动 & 贪吃蛇链：上一颗/玩家位置 ---
            for idx, sat in enumerate(sats):
                if sat["_dead"]:
                    continue
                # 目标位置：前面那颗（玩家=idx0前面就是玩家）
                if idx == 0:
                    tx, ty = pp.x, pp.y
                else:
                    prev = sats[idx - 1]
                    tx, ty = prev["x"], prev["y"]
                # 跟在前面那一颗后面（稍微偏移，形成串）
                dxu = pp.x - (tx if idx == 0 else pp.x)
                dyu = pp.y - (ty if idx == 0 else pp.y)
                # 简单策略：在"前一颗方向"的相对位置跟随
                if idx == 0:
                    offset_a = math.atan2(pp.y - (pp.prev_y or pp.y),
                                          pp.x - (pp.prev_x or pp.x - 1)) + math.pi
                    if abs(pp.x - (pp.prev_x or pp.x)) < 0.1 and abs(pp.y - (pp.prev_y or pp.y)) < 0.1:
                        offset_a += idx * 0.45
                    tx = pp.x + math.cos(offset_a) * (pp.r + 22)
                    ty = pp.y + math.sin(offset_a) * (pp.r + 22)
                else:
                    tx = sats[idx - 1]["x"]
                    ty = sats[idx - 1]["y"]
                    # 保持一点距离
                    ddx = tx - sat["x"]; ddy = ty - sat["y"]
                    d0 = math.hypot(ddx, ddy) or 1
                    ideal_d = 34
                    tx = sat["x"] + ddx / d0 * (d0 - ideal_d)
                    ty = sat["y"] + ddy / d0 * (d0 - ideal_d)
                    # 再加一点链角度（形成贪吃蛇形状）
                    chain_a = math.atan2(pp.y - ty, pp.x - tx) + idx * 0.25
                    tx += math.cos(chain_a) * 6
                    ty += math.sin(chain_a) * 6
                ddx = tx - sat["x"]; ddy = ty - sat["y"]
                sat["vx"] = lerp(sat["vx"], ddx * 10, min(1.0, dt * 10))
                sat["vy"] = lerp(sat["vy"], ddy * 10, min(1.0, dt * 10))
                sat["x"] += sat["vx"] * dt
                sat["y"] += sat["vy"] * dt
                # 金粉粒子
                if random.random() < 0.4:
                    self.particles.append(Particle(
                        sat["x"], sat["y"],
                        random.uniform(-20, 20), random.uniform(-20, 20),
                        0.25, (255, 220, 120), 2.4
                    ))
                # 碰敌人：舍利球爆炸，后面的球接上来（该位置标记 dead，后续补位）
                for s in self.stars:
                    if s.danger and not s._dead:
                        if math.hypot(s.x - sat["x"], s.y - sat["y"]) < s.r + sat["r"]:
                            # 爆炸 150 半径
                            R = sat.get("explode_r", 150)
                            for s2 in list(self.stars):
                                if s2.danger and not s2._dead:
                                    dd = math.hypot(s2.x - sat["x"], s2.y - sat["y"])
                                    if dd < R:
                                        f = 1 - dd / R
                                        self._damage_enemy(s2, sat.get("explode_dmg", 5.5) * f + 2.0, pp)
                            self.burst(sat["x"], sat["y"], (255, 220, 120), 60, 420, size=4.6, life=0.9)
                            sat["_dead"] = True
                            break
            # 清理 dead 的卫星，并把后续的往前补（自动衔接）
            pp._buddha_satellites = [s for s in sats if not s["_dead"]]
        # （舍利子球"碰我则球挡伤害"在玩家受击主判定处拦截处理）

        # ===== 9. 极律虚皇：蓝光柱(beam) + 老式光柱(pillar) =====
        for b in self.god_pillars:
            if b["_dead"]: continue
            b["life"] -= dt
            if b.get("type") == "beam":
                # 蓝光柱：持续性扇形（从玩家发出），扫过扣血+击退，每个敌人只中一次
                owner = b.get("owner")
                if owner is None or not getattr(owner, "alive", True):
                    b["_dead"] = True; continue
                bx, by = owner.x, owner.y
                angle = b.get("angle", 0.0)
                width = b.get("width", 26)
                length = b.get("length", 1500)
                hit_set = b.setdefault("hit", set())
                kb = b.get("knockback", 420)
                for s in self.stars:
                    if s.danger and not s._dead and id(s) not in hit_set:
                        dx_ = s.x - bx; dy_ = s.y - by
                        dist_along = dx_ * math.cos(angle) + dy_ * math.sin(angle)
                        dist_perp = abs(-dx_ * math.sin(angle) + dy_ * math.cos(angle))
                        if -width / 2 - s.r <= dist_perp <= width / 2 + s.r and 0 <= dist_along <= length:
                            hit_set.add(id(s))
                            self._damage_enemy(s, 3.4, owner,
                                               knock=(math.cos(angle) * kb, math.sin(angle) * kb))
                            s.hit_flash = 0.25
                # 尾焰粒子
                if random.random() < 0.85:
                    for k in range(3):
                        t_ = random.random()
                        px = bx + math.cos(angle) * length * t_
                        py = by + math.sin(angle) * length * t_
                        perp_off = random.uniform(-width * 0.45, width * 0.45)
                        px += -math.sin(angle) * perp_off
                        py += math.cos(angle) * perp_off
                        self.particles.append(Particle(
                            px, py,
                            random.uniform(-30, 30), random.uniform(-30, 30),
                            0.25, random.choice([(120, 200, 255), (200, 240, 255), (160, 220, 255)]), 3.0
                        ))
                if b["life"] <= 0:
                    b["_dead"] = True; continue
            else:
                # 老式 pillar（从天空落下的 9 道极律光柱）
                if not b.get("hit"):
                    b["hit"] = True
                    R = b["r"] + 30
                    for s in self.stars:
                        if s.danger and not s._dead:
                            dd = math.hypot(s.x - b["x"], s.y - b["y"])
                            if dd < R:
                                f = 1 - dd / R
                                self._damage_enemy(s, 6.0 * f + 2.5, b["owner"])
                                ddx = s.x - b["x"]; ddy = s.y - b["y"]; d0 = dd or 1
                                s.vx += ddx / d0 * 520 * f
                                s.vy += ddy / d0 * 520 * f
                    self.burst(b["x"], b["y"], (255, 255, 200), 90, 520, size=5.6, life=1.1)
                if b["life"] <= 0:
                    b["_dead"] = True; continue
        self.god_pillars = [b for b in self.god_pillars if not b["_dead"]]

        # ===== 终极皮肤效果更新 =====
        # 生命起源：元素球弹道
        if not hasattr(self, "origin_balls"): self.origin_balls = []
        for b in self.origin_balls:
            if b["_dead"]: continue
            b["x"] += b["vx"] * dt; b["y"] += b["vy"] * dt
            b["life"] -= dt; b["phase"] += dt * 5
            if b["life"] <= 0 or b["x"] < -60 or b["x"] > WIDTH + 60 or b["y"] < -60 or b["y"] > HEIGHT + 60:
                b["_dead"] = True; continue
            # 拖尾粒子
            if random.random() < 0.7:
                self.particles.append(Particle(
                    b["x"], b["y"], random.uniform(-30, 30), random.uniform(-30, 30),
                    0.25, b["color"], 2.4))
            # 碰撞敌人
            for s in self.stars:
                if s.danger and not s._dead and id(s) not in b["hit"]:
                    if math.hypot(s.x - b["x"], s.y - b["y"]) < s.r + b["r"]:
                        b["hit"].add(id(s))
                        eff = b.get("eff", "burn")
                        if eff == "pierce":
                            # 穿透：不消失，继续伤害
                            self._damage_enemy(s, b["dmg"], b["owner"])
                        elif eff == "absorb":
                            # 黑洞：吸收+大伤害
                            self._damage_enemy(s, b["dmg"], b["owner"])
                            self.burst(s.x, s.y, b["color"], 30, 360, size=3.5, life=0.6)
                            b["_dead"] = True
                        else:
                            self._damage_enemy(s, b["dmg"], b["owner"])
                            # 特效
                            if eff == "freeze":
                                s.frozen_timer = max(s.frozen_timer, 2.0)
                            elif eff == "knock":
                                sp = math.hypot(b["vx"], b["vy"]) or 1
                                s.vx += b["vx"] / sp * 400
                                s.vy += b["vy"] / sp * 400
                            elif eff == "pull":
                                dxu = b["x"] - s.x; dyu = b["y"] - s.y; d0 = math.hypot(dxu, dyu) or 1
                                s.vx += dxu / d0 * 300
                                s.vy += dyu / d0 * 300
                            elif eff == "lifesteal":
                                self.lives = min(5, self.lives + 1)
                            elif eff == "aoe":
                                self.burst(s.x, s.y, b["color"], 20, 280, size=3.0, life=0.5)
                            elif eff == "burn":
                                # 灼烧：额外伤害 + 火焰粒子
                                self._damage_enemy(s, b["dmg"] * 0.5, b["owner"])
                                self.burst(s.x, s.y, (255, 120, 30), 16, 200, size=3.5, life=0.6)
                            elif eff == "poison":
                                # 中毒：减速 + 绿色毒雾
                                s.vx *= 0.5; s.vy *= 0.5
                                self.burst(s.x, s.y, (60, 200, 40), 14, 180, size=3.0, life=0.5)
                            elif eff == "chain":
                                # 连锁：闪电链到最近2个敌人
                                chained = 0
                                for s2 in self.stars:
                                    if s2.danger and not s2._dead and s2 is not s:
                                        if math.hypot(s2.x - s.x, s2.y - s.y) < 180:
                                            self._damage_enemy(s2, b["dmg"] * 0.6, b["owner"])
                                            self.burst(s2.x, s2.y, (255, 230, 60), 8, 160, size=2.5, life=0.4)
                                            chained += 1
                                            if chained >= 2:
                                                break
                            elif eff == "spread":
                                # 扩散：命中点向四周发射4个小弹
                                for sa in range(4):
                                    a = sa * (math.tau / 4) + random.uniform(-0.3, 0.3)
                                    self.origin_balls.append({
                                        "x": s.x, "y": s.y,
                                        "vx": math.cos(a) * 380, "vy": math.sin(a) * 380,
                                        "r": 10, "color": b["color"], "dmg": b["dmg"] * 0.5,
                                        "eff": "burn", "life": 0.8, "owner": b["owner"],
                                        "_dead": False, "hit": set(), "elem_idx": idx, "phase": 0.0
                                    })
                            elif eff == "stun":
                                # 眩晕：短暂冻结 + 黄色火花
                                s.frozen_timer = max(s.frozen_timer, 1.2)
                                self.burst(s.x, s.y, (255, 220, 60), 12, 200, size=3.0, life=0.5)
                            self.burst(s.x, s.y, b["color"], 12, 240, size=2.5, life=0.4)
                            if eff != "pierce":
                                b["_dead"] = True
                        break
        self.origin_balls = [b for b in self.origin_balls if not b["_dead"]]

        # 生命起源：12元素环绕球（护体）
        for pp in self.players:
            if pp._origin_orb_timer > 0 and pp._origin_orbs:
                for orb in pp._origin_orbs:
                    orb["angle"] += dt * 1.8
                    orb["phase"] += dt * 4
                    ox = pp.x + math.cos(orb["angle"]) * orb["r"]
                    oy = pp.y + math.sin(orb["angle"]) * orb["r"]
                    # 碰敌人：伤害+特效
                    for s in self.stars:
                        if s.danger and not s._dead:
                            if math.hypot(s.x - ox, s.y - oy) < s.r + 14:
                                self._damage_enemy(s, orb["dmg"] * dt * 3, pp)
                                s.hit_flash = 0.15
                    # 粒子
                    if random.random() < 0.3:
                        self.particles.append(Particle(
                            ox, oy, random.uniform(-20, 20), random.uniform(-20, 20),
                            0.2, orb["color"], 2.0))

        # 逆悖突进：圆柱炮光束
        if not hasattr(self, "paradox_beams"): self.paradox_beams = []
        for b in self.paradox_beams:
            if b["_dead"]: continue
            b["life"] -= dt
            if b["life"] <= 0:
                b["_dead"] = True; continue
            ang = b["angle"]; length = b["length"]; r = b["r"]
            ax, ay = b["x"], b["y"]
            bx_ = ax + math.cos(ang) * length; by_ = ay + math.sin(ang) * length
            abx = bx_ - ax; aby = by_ - ay; ab2 = abx * abx + aby * aby or 1
            hit_cd = b.setdefault("hit_cd", {})
            for s in self.stars:
                if s.danger and not s._dead:
                    sid = id(s)
                    if hit_cd.get(sid, 0) > 0:
                        hit_cd[sid] -= dt; continue
                    apx = s.x - ax; apy = s.y - ay
                    t_ = max(0, min(1, (apx * abx + apy * aby) / ab2))
                    cx_ = ax + abx * t_; cy_ = ay + aby * t_
                    if math.hypot(s.x - cx_, s.y - cy_) < s.r + r:
                        self._damage_enemy(s, b["dmg"], b["owner"],
                                           knock=(math.cos(ang) * 300, math.sin(ang) * 300))
                        if b["eff"] == "freeze":
                            # 极冻炮：冻结敌人
                            s.frozen_timer = max(s.frozen_timer, 1.5)
                            self.burst(s.x, s.y, (80, 180, 255), 8, 160, size=2.5, life=0.4)
                        elif b["eff"] == "magnetic":
                            # 灭磁炮：吸引敌人向光束中心
                            dxu = cx_ - s.x; dyu = cy_ - s.y; d0 = math.hypot(dxu, dyu) or 1
                            s.vx += dxu / d0 * 250
                            s.vy += dyu / d0 * 250
                            self.burst(s.x, s.y, (180, 40, 40), 8, 160, size=2.5, life=0.4)
                        elif b["eff"] == "poison":
                            # 毒素炮：减速 + 绿色毒雾
                            s.vx *= 0.4; s.vy *= 0.4
                            self.burst(s.x, s.y, (40, 180, 50), 10, 180, size=3.0, life=0.5)
                        elif b["eff"] == "destroy":
                            # 毁灭炮：额外大伤害 + 爆炸
                            self._damage_enemy(s, b["dmg"] * 0.8, b["owner"])
                            self.burst(s.x, s.y, (60, 60, 60), 16, 280, size=4.0, life=0.6)
                            self.shake = max(self.shake, 0.15)
                        s.hit_flash = 0.2
                        hit_cd[sid] = 0.15
        self.paradox_beams = [b for b in self.paradox_beams if not b["_dead"]]

        # 逆悖突进：6根光柱360度旋转
        for pp in self.players:
            if pp._paradox_pillar_timer > 0 and pp._paradox_pillars:
                for pillar in pp._paradox_pillars:
                    pillar["angle"] += dt * 2.5
                    px = pp.x + math.cos(pillar["angle"]) * pillar["r"]
                    py = pp.y + math.sin(pillar["angle"]) * pillar["r"]
                    # 碰敌人：伤害+击退
                    for s in self.stars:
                        if s.danger and not s._dead:
                            sid = id(s)
                            if pillar["hit_cd"].get(sid, 0) > 0:
                                pillar["hit_cd"][sid] -= dt; continue
                            if math.hypot(s.x - px, s.y - py) < s.r + 30:
                                self._damage_enemy(s, pillar["dmg"], pp)
                                dxu = s.x - pp.x; dyu = s.y - pp.y; d0 = math.hypot(dxu, dyu) or 1
                                s.vx += dxu / d0 * 500; s.vy += dyu / d0 * 500
                                s.hit_flash = 0.2
                                pillar["hit_cd"][sid] = 0.3
                    # 粒子
                    if random.random() < 0.5:
                        self.particles.append(Particle(
                            px, py, random.uniform(-30, 30), random.uniform(-30, 30),
                            0.25, pillar["color"], 2.5))

        # 终焉：灭世长枪
        if not hasattr(self, "finality_spears"): self.finality_spears = []
        for sp in self.finality_spears:
            if sp["_dead"]: continue
            sp["x"] += sp["vx"] * dt; sp["y"] += sp["vy"] * dt
            sp["life"] -= dt
            if sp["life"] <= 0 or sp["x"] < -100 or sp["x"] > WIDTH + 100 or sp["y"] < -100 or sp["y"] > HEIGHT + 100:
                sp["_dead"] = True; continue
            # 拖尾粒子
            for k in range(3):
                self.particles.append(Particle(
                    sp["x"] + random.uniform(-8, 8), sp["y"] + random.uniform(-8, 8),
                    random.uniform(-60, 60), random.uniform(-60, 60),
                    0.3, (255, 50, 50), 3.0))
            # 碰撞敌人：穿透+即死非Boss+Boss500伤害
            for s in self.stars:
                if s.danger and not s._dead and id(s) not in sp["hit"]:
                    if math.hypot(s.x - sp["x"], s.y - sp["y"]) < s.r + sp["r"]:
                        sp["hit"].add(id(s))
                        if getattr(s, "is_boss", False) or getattr(s, "_endless_boss", False):
                            # Boss：500伤害
                            self._damage_enemy(s, sp["dmg"], sp["owner"])
                        else:
                            # 非Boss：即死
                            self._damage_enemy(s, 99999, sp["owner"])
                        self.burst(s.x, s.y, (255, 50, 50), 40, 500, size=4.5, life=0.8)
        self.finality_spears = [sp for sp in self.finality_spears if not sp["_dead"]]

        # 终焉：镰刀360°旋转
        for pp in self.players:
            if pp._finality_scythe_timer > 0:
                scythe_r = pp.r + 120
                for i in range(4):
                    a = pygame.time.get_ticks() * 0.008 + i * (math.pi / 2)
                    sx = pp.x + math.cos(a) * scythe_r
                    sy = pp.y + math.sin(a) * scythe_r
                    # 碰敌人：击退+爆炸
                    for s in self.stars:
                        if s.danger and not s._dead:
                            if math.hypot(s.x - sx, s.y - sy) < s.r + 30:
                                self._damage_enemy(s, 8.0, pp)
                                dxu = s.x - pp.x; dyu = s.y - pp.y; d0 = math.hypot(dxu, dyu) or 1
                                s.vx += dxu / d0 * 600; s.vy += dyu / d0 * 600
                                s.hit_flash = 0.3
                                self.burst(s.x, s.y, (255, 80, 80), 15, 320, size=3.0, life=0.5)

        # 终焉：无敌破坏死光
        for pp in self.players:
            if pp._finality_laser_timer > 0:
                # 360°全屏激光伤害
                for s in self.stars:
                    if s.danger and not s._dead:
                        d = math.hypot(s.x - pp.x, s.y - pp.y)
                        if d < 400:
                            self._damage_enemy(s, 15.0 * dt * 10, pp)
                            s.hit_flash = 0.2
                            # 击退
                            if d > 1:
                                s.vx += (s.x - pp.x) / d * 200 * dt
                                s.vy += (s.y - pp.y) / d * 200 * dt

        # ===== 公共：第三页皮肤冷却倒计时（每个 player） =====
        for pp in self.players:
            # 各种冷却
            for fld in ("_titan_cd", "_qinglong_cd", "_baihu_cd",
                        "_zhuque_cd", "_xuanwu_cd", "_stargod_cd",
                        "_chrono_cd", "_buddha_cd", "_god_cd"):
                if hasattr(pp, fld):
                    setattr(pp, fld, max(0.0, getattr(pp, fld) - dt))
            # 领域 / 无敌 / 复活被动倒计时
            for fld in ("_titan_domain", "_qinglong_timer", "_xuanwu_timer",
                        "_stargod_timer", "_buddha_timer", "_god_timer", "_zhuque_timer"):
                if hasattr(pp, fld):
                    setattr(pp, fld, max(0.0, getattr(pp, fld) - dt))


    def _update_tri_bombs(self, dt):
        """三色红球炸弹：移动、倒计时、爆炸、被吞噬判定。"""
        if not self.tri_bombs:
            return
        for b in self.tri_bombs:
            if b["_dead"]:
                continue
            b["x"] += b["vx"] * dt
            b["y"] += b["vy"] * dt
            b["vx"] *= 0.96
            b["vy"] *= 0.96
            # 边界反弹
            if b["x"] < b["r"] or b["x"] > WIDTH - b["r"]:
                b["vx"] *= -0.6
                b["x"] = clamp(b["x"], b["r"], WIDTH - b["r"])
            if b["y"] < b["r"] or b["y"] > HEIGHT - b["r"]:
                b["vy"] *= -0.6
                b["y"] = clamp(b["y"], b["r"], HEIGHT - b["r"])
            b["timer"] -= dt
            # 检测被敌方吞噬（敌球比炸弹大）
            for s in self.stars:
                if s.danger and not s._dead:
                    if math.hypot(s.x - b["x"], s.y - b["y"]) < s.r + b["r"]:
                        if s.r > b["r"]:
                            b["_dead"] = True
                            self.burst(b["x"], b["y"], (100, 100, 100), 10, 160, size=2.2, life=0.3)
                            self._flash_msg = "炸弹被吞噬，技能无效"
                            self._flash_timer = 1.0
                            break
            if b["_dead"]:
                continue
            # 倒计时归零 → 爆炸
            if b["timer"] <= 0:
                b["_dead"] = True
                self._tri_bomb_explode(b)
        self.tri_bombs = [b for b in self.tri_bombs if not b["_dead"]]

    def _tri_bomb_explode(self, b):
        """三色炸弹爆炸：消灭范围内敌方，为拥有者回复能量。"""
        ex_r = 130
        owner = b["owner"]
        killed = 0
        for s in self.stars:
            if s.danger and not s._dead:
                if math.hypot(s.x - b["x"], s.y - b["y"]) < ex_r + s.r:
                    self._kill_enemy(s, owner)
                    killed += 1
        # 爆炸视觉 + 震屏
        self.burst(b["x"], b["y"], (255, 120, 60), 50, 360, size=4.0, life=0.8)
        self.burst(b["x"], b["y"], (255, 240, 120), 30, 260, size=3.2, life=0.5)
        self.shake = max(self.shake, 0.8)
        self._play("bomb")
        # 每消灭一个敌方回复 20 能量
        if owner and owner.alive:
            owner.energy = min(100.0, owner.energy + killed * 20.0)
            if killed > 0:
                self._flash_msg = f"炸弹爆炸！消灭 {killed} 敌，+{killed*20} 能量"
                self._flash_timer = 1.6

    def _spawn_fireball(self, p, dx, dy):
        """炼狱皮肤：发射火球（投射物）。"""
        if not hasattr(self, "fireballs"):
            self.fireballs = []
        self.fireballs.append({
            "x": p.x + dx * (p.r + 6), "y": p.y + dy * (p.r + 6),
            "vx": dx * 460, "vy": dy * 460, "r": 10,
            "life": 1.2, "owner": p, "_dead": False
        })
        self.burst(p.x + dx * p.r, p.y + dy * p.r, (255, 120, 40), 12, 180, size=2.6, life=0.35)

    def _sun_blast(self, p, dx, dy):
        """太阳皮肤：定向光波击退。"""
        # 沿方向 90° 扇形击退敌球
        for s in self.stars:
            if not s.danger or s._dead:
                continue
            sx, sy = s.x - p.x, s.y - p.y
            dist = math.hypot(sx, sy)
            if dist > 260 + s.r:
                continue
            # 点积判断方向
            if dist > 0:
                nx, ny = sx / dist, sy / dist
                if nx * dx + ny * dy > 0.3:  # 扇形 ±70°
                    s.vx += nx * 600
                    s.vy += ny * 600
                    self._damage_enemy(s, 1, p)
        self.burst(p.x, p.y, (255, 240, 120), 30, 320, size=3.0, life=0.6)
        self._play("shockwave")

    def _update_frost_pellets(self, dt):
        """霜冻冰粒：移动、碰撞冻结敌人。"""
        if not self.frost_pellets:
            return
        for fp in self.frost_pellets:
            if fp["_dead"]:
                continue
            fp["x"] += fp["vx"] * dt
            fp["y"] += fp["vy"] * dt
            fp["timer"] -= dt
            # 边界反弹
            if fp["x"] < fp["r"] or fp["x"] > WIDTH - fp["r"]:
                fp["vx"] *= -0.7
                fp["x"] = clamp(fp["x"], fp["r"], WIDTH - fp["r"])
            if fp["y"] < fp["r"] or fp["y"] > HEIGHT - fp["r"]:
                fp["vy"] *= -0.7
                fp["y"] = clamp(fp["y"], fp["r"], HEIGHT - fp["r"])
            if fp["timer"] <= 0:
                fp["_dead"] = True
                continue
            # 碰撞冻结
            for s in self.stars:
                if s.danger and not s._dead:
                    if math.hypot(s.x - fp["x"], s.y - fp["y"]) < s.r + fp["r"]:
                        # 冻结：打 frozen_timer（星体会自动减速），并瞬间压到极低速度
                        s.frozen_timer = max(s.frozen_timer, 2.4)
                        s.vx *= 0.05
                        s.vy *= 0.05
                        s.hit_flash = 0.25
                        # 冻结视觉
                        self.burst(fp["x"], fp["y"], (150, 220, 255), 18, 200, size=2.8, life=0.45)
                        for zz in range(12):
                            a = zz * (math.tau / 12)
                            self.particles.append(
                                (s.x + math.cos(a) * s.r * 0.8,
                                 s.y + math.sin(a) * s.r * 0.8,
                                 math.cos(a) * 80, math.sin(a) * 80,
                                 0.7, (220, 240, 255), 2.4))
                        fp["_dead"] = True
                        break
        self.frost_pellets = [fp for fp in self.frost_pellets if not fp["_dead"]]

    def _update_thunder(self, dt):
        """雷霆电球移动伤害+击退；雷电场周围放电。"""
        if self.thunder_field_timer > 0:
            self.thunder_field_timer -= dt
            p = self.player
            if p and p.alive:
                # 每 0.15s 对周围 200 内敌球放闪电+伤害
                now = pygame.time.get_ticks()
                if now - getattr(self, "_tf_cd", -999) > 150:
                    self._tf_cd = now
                    for s in self.stars:
                        if s.danger and not s._dead:
                            if math.hypot(s.x - p.x, s.y - p.y) < 200 + p.r:
                                self._chain_bolt((p.x, p.y), (s.x, s.y))
                                self._damage_enemy(s, 1.2, p)
                                # 击退
                                dx = s.x - p.x
                                dy = s.y - p.y
                                d = math.hypot(dx, dy) or 1
                                s.vx += dx / d * 120
                                s.vy += dy / d * 120
                    # 视觉粒子
                    for _ in range(4):
                        a = random.uniform(0, math.tau)
                        self.particles.append(Particle(
                            p.x, p.y,
                            math.cos(a) * 260, math.sin(a) * 260,
                            0.22, (255, 240, 120), 2.6))
        if not self.thunder_balls:
            return
        for tb in self.thunder_balls:
            if tb["_dead"]:
                continue
            tb["x"] += tb["vx"] * dt
            tb["y"] += tb["vy"] * dt
            tb["timer"] -= dt
            # 自动追踪最近敌人
            tgt = None
            tdist = 160
            for s in self.stars:
                if s.danger and not s._dead:
                    dd = math.hypot(s.x - tb["x"], s.y - tb["y"])
                    if dd < tdist:
                        tdist = dd
                        tgt = s
            if tgt is not None:
                dx = tgt.x - tb["x"]
                dy = tgt.y - tb["y"]
                dd = math.hypot(dx, dy) or 1
                tb["vx"] += dx / dd * 600 * dt
                tb["vy"] += dy / dd * 600 * dt
            # 限速
            vv = math.hypot(tb["vx"], tb["vy"])
            if vv > 500:
                tb["vx"] = tb["vx"] / vv * 500
                tb["vy"] = tb["vy"] / vv * 500
            if tb["timer"] <= 0:
                tb["_dead"] = True
                continue
            # 碰撞伤害+击退
            for s in self.stars:
                if s.danger and not s._dead:
                    if math.hypot(s.x - tb["x"], s.y - tb["y"]) < s.r + tb["r"]:
                        dx = s.x - tb["x"]
                        dy = s.y - tb["y"]
                        dd = math.hypot(dx, dy) or 1
                        self._chain_bolt((tb["x"], tb["y"]), (s.x, s.y))
                        self._damage_enemy(s, 2, tb["owner"],
                                           knock=(dx / dd * 260, dy / dd * 260))
                        self.burst(tb["x"], tb["y"], (255, 240, 120), 16, 220, size=2.8, life=0.4)
                        tb["_dead"] = True
                        break
        self.thunder_balls = [tb for tb in self.thunder_balls if not tb["_dead"]]

    def _update_void_holes(self, dt):
        """深渊黑洞：移动、吸引吞噬敌人。"""
        if not self.void_holes:
            return
        for bh in self.void_holes:
            if bh["_dead"]:
                continue
            bh["timer"] -= dt
            # c8：深渊黑洞沿自己方向持续移动（仅轻微减速保持方向感）
            # 螺旋黑洞：一边螺旋一边沿初速方向前进
            if bh.get("spiral"):
                # 防御：未初始化 spiral_phase 时给默认值（避免 KeyError）
                if "spiral_phase" not in bh:
                    bh["spiral_phase"] = 0.0
                bh["spiral_phase"] += dt * 5.2
                # 相对于自身当前位置周围做螺旋偏移（而不是锚定鼠标点）
                rad = 50 + 60 * (1 - bh["timer"] / bh["max"])
                # 沿初速方向做直线 + 小范围螺旋抖动
                sp = math.hypot(bh.get("vx", 0), bh.get("vy", 0))
                if sp < 120:
                    # 保底速度（避免停住）
                    orig_vx = bh.get("_orig_vx", bh.get("vx", 0))
                    orig_vy = bh.get("_orig_vy", bh.get("vy", 0))
                    if "_orig_vx" not in bh:
                        bh["_orig_vx"] = orig_vx
                        bh["_orig_vy"] = orig_vy
                    osp = math.hypot(orig_vx, orig_vy) or 1
                    bh["vx"] = orig_vx / osp * 200
                    bh["vy"] = orig_vy / osp * 200
                # 叠加螺旋绕圈（围绕自己前方的动态点）
                phase = bh["spiral_phase"]
                bh["_spiral_dx"] = math.cos(phase) * rad * 0.35
                bh["_spiral_dy"] = math.sin(phase) * rad * 0.35
            else:
                # 6 向黑洞：保持初速方向；轻微减速
                sp = math.hypot(bh.get("vx", 0), bh.get("vy", 0))
                if sp < 140:
                    orig_vx = bh.get("_orig_vx", bh["vx"])
                    orig_vy = bh.get("_orig_vy", bh["vy"])
                    if "_orig_vx" not in bh:
                        bh["_orig_vx"] = orig_vx
                        bh["_orig_vy"] = orig_vy
                    osp = math.hypot(orig_vx, orig_vy) or 1
                    bh["vx"] = orig_vx / osp * 260
                    bh["vy"] = orig_vy / osp * 260
            bh["x"] += bh["vx"] * dt
            bh["y"] += bh["vy"] * dt
            # 位置再叠加螺旋抖动
            if bh.get("spiral"):
                bh["x"] += bh.get("_spiral_dx", 0) * dt * 1.6
                bh["y"] += bh.get("_spiral_dy", 0) * dt * 1.6
            # 极轻微减速（避免停下；保持沿释放方向运动感）
            bh["vx"] *= math.pow(0.985, dt * 60)
            bh["vy"] *= math.pow(0.985, dt * 60)
            # 边界约束
            bh["x"] = clamp(bh["x"], bh["r"], WIDTH - bh["r"])
            bh["y"] = clamp(bh["y"], bh["r"], HEIGHT - bh["r"])
            if bh["timer"] <= 0:
                bh["_dead"] = True
                continue
            # 吸引/排斥 + 吞噬
            bh_type = bh.get("bh_type", "attract")
            for s in self.stars:
                if s._dead:
                    continue
                dx = bh["x"] - s.x
                dy = bh["y"] - s.y
                dd = math.hypot(dx, dy) or 1
                if dd < bh["r"] + s.r:
                    force = 1 - dd / (bh["r"] + s.r)
                    if bh_type == "repel":
                        # 蓝圆：排斥（推离）
                        s.vx -= dx / dd * force * 900 * dt
                        s.vy -= dy / dd * force * 900 * dt
                    else:
                        # 红圆：吸入（拉向）
                        s.vx += dx / dd * force * 900 * dt
                        s.vy += dy / dd * force * 900 * dt
                # 吸入判定：仅红圆(attract)吞噬
                if bh_type != "repel" and dd < bh["r"] * 0.45:
                    self._kill_enemy(s, bh["owner"])
            # 视觉粒子
            if random.random() < 0.8:
                a = random.uniform(0, math.tau)
                col = (80, 160, 255) if bh_type == "repel" else (255, 80, 80)
                self.particles.append(Particle(
                    bh["x"] + math.cos(a) * bh["r"],
                    bh["y"] + math.sin(a) * bh["r"],
                    -math.cos(a) * 120, -math.sin(a) * 120,
                    0.3, col, 2.6))
        self.void_holes = [bh for bh in self.void_holes if not bh["_dead"]]

    def _update_chaos(self, dt):
        """混沌：钩子吸血；六剑模式。（取消原无限能量，左键钩子消耗30能，右键六剑正常消耗）"""
        p = self.player
        if not p or not p.alive:
            return
        # 钩子（动态：飞出自动吸附+悬浮大范围吸附+连线灼烧+吸血脉动）
        h = p._chaos_hook
        if h is not None:
            h["life"] -= dt
            h["t"] += dt
            # 灼烧连线：每帧对靠近"玩家→钩子"连线的敌人造成灼烧伤害（宽度22px）
            def _seg_dst2(ax, ay, bx, by, px, py):
                abx, aby = bx - ax, by - ay
                apx, apy = px - ax, py - ay
                ab2 = max(1e-6, abx * abx + aby * aby)
                t_ = max(0.0, min(1.0, (apx * abx + apy * aby) / ab2))
                cx, cy = ax + abx * t_, ay + aby * t_
                return (px - cx) ** 2 + (py - cy) ** 2
            burn_w = 26.0
            for s in self.stars:
                if s._dead or not s.danger:
                    continue
                # 跳过已经被钩住吸血的目标
                if h["phase"] == 2 and h["target"] is s:
                    continue
                d2_ = _seg_dst2(p.x, p.y, h["x"], h["y"], s.x, s.y)
                rr = s.r + burn_w
                if d2_ < rr * rr:
                    self._damage_enemy(s, 4.0 * dt, p)
                    # 轻微火花粒子
                    if random.random() < 0.5:
                        a_ = random.uniform(0, math.tau)
                        self.particles.append((s.x + math.cos(a_) * s.r,
                                              s.y + math.sin(a_) * s.r,
                                              random.uniform(-10, 10), random.uniform(-10, 10),
                                              0.35, (255, 160, 60), 2.2))
            if h["life"] <= 0:
                p._chaos_hook = None
            else:
                if h["phase"] == 0:  # 飞出（途中自动吸附附近敌人）
                    h["x"] += h["vx"] * dt
                    h["y"] += h["vy"] * dt
                    h["ang"] = math.atan2(h["vy"], h["vx"])
                    # 飞出途中就近吸附（普通半径38，追击模式下放大到50+半径）
                    near_tgt = None
                    near_d = 9999
                    homing = h.get("_homing_tgt")
                    cap_base = 50 if homing else 38
                    for s in self.stars:
                        if s.danger and not s._dead:
                            dd = math.hypot(s.x - h["x"], s.y - h["y"])
                            cap = s.r + cap_base
                            if dd < cap and dd < near_d:
                                near_d = dd
                                near_tgt = s
                    if near_tgt is not None:
                        # 命中！
                        h["target"] = near_tgt
                        h["phase"] = 2
                        h["_homing_tgt"] = None
                        self._play("ehit")
                    else:
                        # 追击模式：到达目标半径内进入悬浮
                        if homing and (homing is None or getattr(homing, "_dead", False) or
                                       math.hypot(h["x"] - homing.x, h["y"] - homing.y) < max(6, homing.r * 0.4)):
                            h["_homing_tgt"] = None
                            h["mx"], h["my"] = h["x"], h["y"]
                            h["phase"] = 1
                            h["vx"] *= 0
                            h["vy"] *= 0
                            h["spiral"] = 0.0
                        # 正常飞出：飞到鼠标附近进入悬浮
                        elif not homing:
                            dist_to_mouse = math.hypot(h["x"] - h["mx"], h["y"] - h["my"])
                            if dist_to_mouse < 40:
                                h["phase"] = 1
                                h["vx"] *= 0
                                h["vy"] *= 0
                                h["spiral"] = 0.0
                elif h["phase"] == 1:  # 悬浮：螺旋摆动 + 大范围吸附最近敌人
                    h["spiral"] += dt * 2.5
                    # 悬浮点在目标点周围 36px 做大螺旋，扩大搜索圈
                    ox = h["mx"] + math.cos(h["spiral"]) * 36
                    oy = h["my"] + math.sin(h["spiral"]) * 36
                    h["x"] += (ox - h["x"]) * dt * 5.0
                    h["y"] += (oy - h["y"]) * dt * 5.0
                    tgt = None
                    tdist = 150  # 吸附范围扩大到 150
                    for s in self.stars:
                        if s.danger and not s._dead:
                            dd = math.hypot(s.x - h["x"], s.y - h["y"]) - s.r
                            if dd < tdist:
                                tdist = dd
                                tgt = s
                    if tgt is not None:
                        # 立刻飞过去钩中：加速冲刺向目标
                        ddx, ddy = tgt.x - h["x"], tgt.y - h["y"]
                        dlen = math.hypot(ddx, ddy) or 1
                        h["vx"] = ddx / dlen * 520
                        h["vy"] = ddy / dlen * 520
                        h["_homing_tgt"] = tgt
                        h["phase"] = 0
                elif h["phase"] == 2:  # 吸血中 + 脉动
                    t = h["target"]
                    if t is None or t._dead:
                        p._chaos_hook = None
                    else:
                        pulse = math.sin(h["t"] * 8.0) * 3
                        h["x"] = t.x + math.cos(h["t"] * 2.0) * pulse
                        h["y"] = t.y + math.sin(h["t"] * 2.0) * pulse
                        h["ang"] = math.atan2(h["y"] - p.y, h["x"] - p.x)
                        # 吸血放缓：0.4s 一次，每次伤害 0.5（持续但轻柔）
                        h["drain_timer"] += dt
                        if h["drain_timer"] >= 0.40:
                            h["drain_timer"] = 0
                            dmg = 1
                            t.hp -= dmg
                            self._damage_enemy(t, dmg, p)
                            # 玩家增大放缓
                            p.r = min(120.0, math.sqrt(p.r * p.r + 0.5))
                            # 加血（最多5格，每两次吸1点）
                            if not hasattr(h, "_hp_cnt"):
                                h["_hp_cnt"] = 0
                            h["_hp_cnt"] += 1
                            if h["_hp_cnt"] % 2 == 0:
                                if p._chaos_hp < 5:
                                    p._chaos_hp += 1
                            if t._dead:
                                p._chaos_hook = None
        # 六剑模式
        if p._chaos_sword_timer > 0:
            p._chaos_sword_timer -= dt
            # 剑刃范围 = p.r + 90
            swordR = p.r + 90
            for s in self.stars:
                if s._dead or not s.danger:
                    continue
                dd = math.hypot(s.x - p.x, s.y - p.y)
                if dd < swordR + s.r:
                    if s.r < p.r:
                        # 比自己小：吞噬
                        self._kill_enemy(s, p)
                    else:
                        # 比自己大：砍击+击退
                        dx = s.x - p.x
                        dy = s.y - p.y
                        d_ = math.hypot(dx, dy) or 1
                        self._damage_enemy(s, 2.5 * dt, p,
                                           knock=(dx / d_ * 320, dy / d_ * 320))

    def _do_shockwave(self, p):
        """光波：击退范围内敌球并造成伤害。"""
        self._play("shockwave")
        self.shake = max(self.shake, 0.6)
        radius = 240
        self.burst(p.x, p.y, (255, 200, 80), 60, 380, size=4.0, life=0.8)
        for s in self.stars:
            if not s.danger or s._dead:
                continue
            d = math.hypot(s.x - p.x, s.y - p.y)
            if d < radius:
                # 光波削减生命 + 击退
                if d > 0:
                    push = 600 / max(d, 20)
                    kx = (s.x - p.x) / d * push * 8
                    ky = (s.y - p.y) / d * push * 8
                else:
                    kx = ky = 0
                self._damage_enemy(s, 2, p, knock=(kx, ky))

    def _skin_move_mul(self, p):
        """皮肤移速倍率：三色蓝球加速时 +20%。"""
        if self.active_skin == "tri" and getattr(p, "_tri_boost_timer", 0) > 0:
            return 1.2
        return 1.0

    # ---- 武器（光枪/光刃）自动攻击 ----
    def _aim_dir(self, p):
        dx = p.x - p.prev_x
        dy = p.y - p.prev_y
        if math.hypot(dx, dy) > 1.5:
            return math.atan2(dy, dx)
        best = None
        bd = 1e9
        for s in self.stars:
            if s.danger:
                d = math.hypot(s.x - p.x, s.y - p.y)
                if d < bd:
                    bd = d
                    best = s
        if best:
            return math.atan2(best.y - p.y, best.x - p.x)
        return 0.0

    def _kill_enemy(self, s, owner):
        if s._dead:
            return
        s._dead = True
        self.score += int(s.r * 8)
        self.best = max(self.best, self.score)
        self._total_kills = getattr(self, "_total_kills", 0) + 1
        # 无尽模式：击杀加分 + Boss 额外分
        if getattr(self, "_endless_mode", False):
            if getattr(s, "_endless_boss", False):
                self._endless_score = getattr(self, "_endless_score", 0) + 2000
            else:
                self._endless_score = getattr(self, "_endless_score", 0) + 100
            # Q2：打败大怪计入击败数（含Boss）
            self._endless_killed = getattr(self, "_endless_killed", 0) + 1
        if owner is not None:
            owner.r = min(120.0, math.sqrt(owner.r * owner.r + s.r * s.r * 0.08))
        # 六道轮回印：被标记敌人死亡返还标记者能量
        if getattr(s, "_samsara_mark", False):
            o = getattr(s, "_samsara_owner", None)
            if o is not None and o.alive:
                gain = 30 + int(s.r * 1.2)
                o.energy = min(100.0, o.energy + gain)
                for i in range(16):
                    a = random.uniform(0, math.tau)
                    self.particles.append((s.x, s.y,
                                           math.cos(a) * 180, math.sin(a) * 180,
                                           0.5, (220, 180, 255), 2.8))
        # 敌人死亡爆金币（根据半径大小有概率掉1-3个）
        drop_cnt = 0
        p = min(0.55, 0.25 + s.r * 0.01)
        if random.random() < p:
            drop_cnt = 1
            if s.r > 20 and random.random() < 0.35:
                drop_cnt = 2
                if s.r > 30 and random.random() < 0.3:
                    drop_cnt = 3
            for _ in range(drop_cnt):
                self.coin_pickups.append({
                    "x": s.x + random.uniform(-10, 10),
                    "y": s.y + random.uniform(-10, 10),
                    "phase": random.uniform(0, math.tau),
                    "life": 12.0, "_dead": False})
        # c7：恐怖种死亡分裂 1~2 个小恐怖球（体积 55% 原大小）
        if getattr(s, "horror_split_count", 0) > 0 and s.r >= 10:
            splits = s.horror_split_count
            new_r = s.r * 0.55
            for i in range(splits):
                ang = random.uniform(0, math.tau)
                spd = 140 + random.uniform(-20, 40)
                vx = math.cos(ang) * spd
                vy = math.sin(ang) * spd
                col = (150, 10, 30)
                sub_tier = max(0, s.tier - 1)
                child = Star(s.x, s.y, vx, vy, new_r, col, True,
                             tier=sub_tier, kind="horror")
                # 小恐怖球不再继续分裂（避免无限分裂）
                child.horror_split_count = 0
                self.stars.append(child)
            # 分裂爆散特效
            self.burst(s.x, s.y, (120, 0, 20), 24, 300, size=3.2, life=0.55)
        self.burst(s.x, s.y, s.color, int(10 + s.r), 260, size=2.8, life=0.5)
        self._play("pop")

    def _damage_enemy(self, s, dmg, owner=None, knock=None):
        """非吞噬性攻击削减生命值，归零才毁灭。knock=(kx,ky) 可选击退。"""
        if s._dead or not s.danger:
            return
        # 至高神皇：15秒内所有伤害×2（含所有调用）
        if owner is not None and getattr(owner, "_god_timer", 0) > 0:
            dmg = dmg * 2.0
        s.hp -= dmg
        s.hit_flash = 0.18
        if knock is not None:
            s.vx += knock[0]
            s.vy += knock[1]
        # 受击小特效 + 音效
        self.burst(s.x, s.y, (255, 240, 200), 6, 180, size=2.2, life=0.3)
        if s.hp <= 0:
            self._kill_enemy(s, owner)
            self._play("edie")
        else:
            self._play("ehit")

    def _update_diamond_projectiles(self, dt):
        """更新龙焰追踪弹、魔焰毒雾、星轨弹、两仪剑 并做碰撞伤害。"""
        for arr_name in ("dragon_fire", "demon_clouds", "stellar_orbs", "taiji_blades"):
            arr = getattr(self, arr_name, [])
            if not arr:
                continue
            for b in arr:
                if b["_dead"]:
                    continue
                p = b.get("owner")
                # 龙焰：追踪最近危险目标
                if arr_name == "dragon_fire":
                    tgt = b.get("target")
                    if tgt is None or tgt._dead:
                        tgt = None; nd = 1e9
                        for s in self.stars:
                            if s.danger and not s._dead:
                                dd = math.hypot(s.x - b["x"], s.y - b["y"])
                                if dd < nd:
                                    nd = dd; tgt = s
                        b["target"] = tgt
                    if tgt is not None:
                        dx = tgt.x - b["x"]; dy = tgt.y - b["y"]
                        d = math.hypot(dx, dy) or 1
                        k = min(1.0, 3.8 * dt)
                        b["vx"] = lerp(b["vx"], dx / d * 520, k)
                        b["vy"] = lerp(b["vy"], dy / d * 520, k)
                    # 拖尾粒子
                    if random.random() < 0.7:
                        self.particles.append((b["x"], b["y"],
                                               random.uniform(-40, 40), random.uniform(-40, 40),
                                               0.35, (255, 180, 80), 3.0))
                elif arr_name == "demon_clouds":
                    # 略微减速散逸 + 碰撞给腐蚀
                    b["vx"] *= math.pow(0.9, dt * 6)
                    b["vy"] *= math.pow(0.9, dt * 6)
                    if random.random() < 0.9:
                        self.particles.append((b["x"], b["y"],
                                               random.uniform(-60, 60), random.uniform(-60, 60),
                                               0.45, (120, 60, 200), 2.8))
                elif arr_name == "stellar_orbs":
                    if random.random() < 0.9:
                        self.particles.append((b["x"], b["y"],
                                               random.uniform(-50, 50), random.uniform(-50, 50),
                                               0.3, (150, 220, 255), 2.6))
                elif arr_name == "taiji_blades":
                    # 两仪剑穿透+发光
                    if random.random() < 0.9:
                        self.particles.append((b["x"], b["y"],
                                               random.uniform(-30, 30), random.uniform(-30, 30),
                                               0.22, b["col"], 2.8))
                # 位置
                b["x"] += b["vx"] * dt
                b["y"] += b["vy"] * dt
                b["life"] -= dt
                if (b["life"] <= 0 or b["x"] < -120 or b["x"] > WIDTH + 120
                        or b["y"] < -120 or b["y"] > HEIGHT + 120):
                    b["_dead"] = True
                    continue
                # 碰撞
                r = b.get("r", 14)
                for s in self.stars:
                    if s.danger and not s._dead:
                        if math.hypot(s.x - b["x"], s.y - b["y"]) < s.r + r:
                            dmg_map = {"dragon_fire": 3.2, "demon_clouds": 2.4,
                                       "stellar_orbs": 1.8, "taiji_blades": 2.8}
                            dmg = dmg_map[arr_name]
                            self._damage_enemy(s, dmg, p)
                            # 龙焰&星轨&太剑：穿透；毒云：穿
                            if arr_name != "dragon_fire" and arr_name != "demon_clouds" \
                                    and arr_name != "stellar_orbs" and arr_name != "taiji_blades":
                                b["_dead"] = True
                                break
            setattr(self, arr_name, [x for x in arr if not x["_dead"]])

    def _update_advanced_diamond_effects(self, dt):
        """六道轮回刃 + 寂灭创世莲 + 六道领域 + 寂灭脉冲 + 太极自动双剑 的更新与碰撞。"""
        # --- 六道轮回刃：穿透、被击中敌人自动被轮回印标记 ---
        for b in self.samsara_blades:
            if b["_dead"]:
                continue
            p = b.get("owner")
            # 拖尾粒子（紫白色）
            if random.random() < 0.95:
                self.particles.append((b["x"], b["y"],
                                       random.uniform(-40, 40), random.uniform(-40, 40),
                                       0.3, (200, 160, 255), 2.8))
            # Q3：自动追踪最近敌人
            if b.get("track"):
                tgt = None; tgt_d = 1e9
                for s in self.stars:
                    if s.danger and not s._dead:
                        dd = math.hypot(s.x - b["x"], s.y - b["y"])
                        if dd < tgt_d:
                            tgt_d = dd; tgt = s
                if tgt and tgt_d < 600:
                    ddx = tgt.x - b["x"]; ddy = tgt.y - b["y"]
                    L = tgt_d or 1
                    spd = math.hypot(b["vx"], b["vy"]) or 1
                    # 逐步转向目标
                    b["vx"] = lerp(b["vx"], ddx / L * max(spd, 320), min(1.0, dt * 4.0))
                    b["vy"] = lerp(b["vy"], ddy / L * max(spd, 320), min(1.0, dt * 4.0))
            b["x"] += b["vx"] * dt; b["y"] += b["vy"] * dt
            b["life"] -= dt
            if (b["life"] <= 0 or b["x"] < -120 or b["x"] > WIDTH + 120
                    or b["y"] < -120 or b["y"] > HEIGHT + 120):
                if b.get("explode"):
                    # 到期也爆炸
                    R = b.get("explode_r", 120)
                    dmg = b.get("explode_dmg", 4.0)
                    for s in list(self.stars):
                        if s.danger and not s._dead:
                            dd = math.hypot(s.x - b["x"], s.y - b["y"])
                            if dd < R:
                                f = 1 - dd / R
                                self._damage_enemy(s, dmg * f + 1.5, p)
                                ddx = s.x - b["x"]; ddy = s.y - b["y"]; d0 = dd or 1
                                s.vx += ddx / d0 * 400 * f
                                s.vy += ddy / d0 * 400 * f
                    self.burst(b["x"], b["y"], (200, 160, 255), 30, 320, size=3.8, life=0.6)
                b["_dead"] = True
                continue
            pierced = b.get("pierced", set())
            r = b.get("r", 15)
            for s in self.stars:
                if s.danger and not s._dead and id(s) not in pierced:
                    if math.hypot(s.x - b["x"], s.y - b["y"]) < s.r + r:
                        if b.get("explode"):
                            # Q3：碰撞爆炸+弹开
                            R = b.get("explode_r", 120)
                            dmg = b.get("explode_dmg", 4.0)
                            for s2 in list(self.stars):
                                if s2.danger and not s2._dead:
                                    dd = math.hypot(s2.x - b["x"], s2.y - b["y"])
                                    if dd < R:
                                        f = 1 - dd / R
                                        self._damage_enemy(s2, dmg * f + 1.5, p)
                                        ddx = s2.x - b["x"]; ddy = s2.y - b["y"]; d0 = dd or 1
                                        s2.vx += ddx / d0 * 480 * f
                                        s2.vy += ddy / d0 * 480 * f
                            self.burst(b["x"], b["y"], (200, 160, 255), 35, 360, size=4.0, life=0.7)
                            b["_dead"] = True
                            break
                        else:
                            self._damage_enemy(s, 3.2, p)
                            pierced.add(id(s))
                            s._samsara_mark = True
                            s._samsara_owner = p
        self.samsara_blades = [x for x in self.samsara_blades if not x["_dead"]]

        # --- 大道涅槃·灼烧凤凰：向前飞行，碰到敌人造成持续灼烧伤害，1.5s 后消失 ---
        if hasattr(self, "nirvana_phoenix_list"):
            for ph in self.nirvana_phoenix_list:
                if ph["_dead"]:
                    continue
                p = ph.get("owner")
                ph["x"] += ph["vx"] * dt
                ph["y"] += ph["vy"] * dt
                ph["life"] -= dt
                # 火焰拖尾粒子（橙黄色）
                if random.random() < 0.95:
                    for _ in range(2):
                        self.particles.append((
                            ph["x"] + random.uniform(-6, 6),
                            ph["y"] + random.uniform(-6, 6),
                            random.uniform(-30, 30), random.uniform(-30, 30),
                            random.uniform(0.3, 0.6),
                            random.choice([(255, 200, 80), (255, 120, 40), (255, 240, 140)]),
                            random.uniform(2.5, 4.0)
                        ))
                # 出界或寿命到期
                if (ph["life"] <= 0 or ph["x"] < -120 or ph["x"] > WIDTH + 120
                        or ph["y"] < -120 or ph["y"] > HEIGHT + 120):
                    # 消失时小火爆
                    self.burst(ph["x"], ph["y"], (255, 200, 80), 18, 260, size=3.6, life=0.5)
                    ph["_dead"] = True
                    continue
                # 碰撞敌人造成持续伤害（hit_cd 防止每帧命中同一敌人）
                r = ph.get("r", 20)
                hit_cd = ph.setdefault("hit_cd", {})
                for s in self.stars:
                    if s.danger and not s._dead:
                        sid = id(s)
                        if hit_cd.get(sid, 0) > 0:
                            hit_cd[sid] -= dt
                            continue
                        if math.hypot(s.x - ph["x"], s.y - ph["y"]) < s.r + r:
                            self._damage_enemy(s, 3.5, p)
                            s.hit_flash = 0.25
                            hit_cd[sid] = 0.4  # 0.4s 冷却避免每帧命中
                            # 灼烧小粒子
                            for _ in range(5):
                                a = random.uniform(0, math.tau)
                                self.particles.append((
                                    s.x, s.y,
                                    math.cos(a) * random.uniform(40, 140),
                                    math.sin(a) * random.uniform(40, 140),
                                    0.3, (255, 160, 60), 2.6
                                ))
            self.nirvana_phoenix_list = [x for x in self.nirvana_phoenix_list if not x["_dead"]]

        # --- 寂灭·创世莲：围绕玩家缓慢公转，碰撞即爆炸；周期爆发莲花弹幕 ---
        lotus = getattr(self, "寂灭_lotus", None)
        if lotus:
            for l in lotus:
                if l["_dead"]:
                    continue
                p = l.get("owner")
                # Q4：毁灭火莲 — 固定位置，闪烁，倒计时结束后大范围爆炸
                if l.get("fire_lotus"):
                    l["timer"] -= dt
                    l["life"] -= dt
                    # 闪烁粒子（越来越快）
                    flicker_rate = 0.02 + (3.0 - max(0, l["timer"])) * 0.03
                    if random.random() < flicker_rate * 60 * dt:
                        for i in range(8):
                            a = random.uniform(0, math.tau)
                            rr = random.uniform(5, l["r"])
                            self.particles.append((
                                l["x"] + math.cos(a) * rr * 0.2,
                                l["y"] + math.sin(a) * rr * 0.2,
                                math.cos(a) * random.uniform(30, 120),
                                math.sin(a) * random.uniform(30, 120),
                                0.4,
                                random.choice([(255, 100, 30), (255, 160, 60), (255, 60, 20)]),
                                3.0
                            ))
                    # 倒计时结束 → 大范围爆炸（自身无影响）
                    if l["timer"] <= 0:
                        R = l.get("explode_r", 320)
                        dmg = l.get("explode_dmg", 9.0)
                        for s in list(self.stars):
                            if s.danger and not s._dead:
                                dd = math.hypot(s.x - l["x"], s.y - l["y"])
                                if dd < R:
                                    f = 1 - dd / R
                                    self._damage_enemy(s, dmg * f + 2.0, p)
                                    s.hit_flash = 0.3
                                    ddx = s.x - l["x"]; ddy = s.y - l["y"]; d0 = dd or 1
                                    s.vx += ddx / d0 * 600 * f
                                    s.vy += ddy / d0 * 600 * f
                        # 超大爆炸特效
                        for ring, col, cnt in ((60, (255, 100, 30), 80),
                                               (150, (255, 160, 60), 100),
                                               (280, (255, 60, 20), 120)):
                            for k in range(cnt):
                                a = random.uniform(0, math.tau)
                                self.particles.append((
                                    l["x"], l["y"],
                                    math.cos(a) * (300 + ring),
                                    math.sin(a) * (300 + ring),
                                    0.9, col, 4.6
                                ))
                        self.burst(l["x"], l["y"], (255, 100, 30), 100, 600, size=6.0, life=1.2)
                        self.shake = max(self.shake, 0.8)
                        l["_dead"] = True
                    continue
                # 按 phase 缓慢公转
                l["phase"] += dt * 0.8
                if p and p.alive:
                    cx = p.x + math.cos(l["phase"]) * 90
                    cy = p.y + math.sin(l["phase"]) * 90
                    dx = cx - l["x"]; dy = cy - l["y"]
                    l["vx"] = lerp(l["vx"], dx * 7.0, min(1.0, dt * 7.0))
                    l["vy"] = lerp(l["vy"], dy * 7.0, min(1.0, dt * 7.0))
                l["x"] += l["vx"] * dt; l["y"] += l["vy"] * dt
                l["life"] -= dt
                # 莲花花瓣粒子
                if random.random() < 0.6:
                    self.particles.append((l["x"], l["y"],
                                           random.uniform(-40, 40), random.uniform(-40, 40),
                                           0.35, (255, 210, 255), 2.4))
                # 爆炸判定
                r = l.get("r", 34)
                exploded = False
                if l["life"] <= 0:
                    exploded = True
                else:
                    for s in self.stars:
                        if s.danger and not s._dead:
                            if math.hypot(s.x - l["x"], s.y - l["y"]) < s.r + r:
                                exploded = True
                                break
                if exploded:
                    # 莲花爆炸：大范围伤害+粒子
                    R = 180
                    for s in list(self.stars):
                        if s.danger and not s._dead:
                            dd = math.hypot(s.x - l["x"], s.y - l["y"])
                            if dd < R:
                                self._damage_enemy(s, 6.0, p)
                                s.hit_flash = 0.25
                    for i in range(70):
                        a = random.uniform(0, math.tau)
                        rr = random.uniform(0, R)
                        self.particles.append((
                            l["x"] + math.cos(a) * rr * 0.1,
                            l["y"] + math.sin(a) * rr * 0.1,
                            math.cos(a) * (180 + rr),
                            math.sin(a) * (180 + rr),
                            0.8,
                            random.choice([(255, 210, 255), (255, 240, 255), (220, 170, 255)]),
                            3.8))
                    self.burst(l["x"], l["y"], (255, 200, 255), 55, 460, size=4.6, life=0.9)
                    l["_dead"] = True
            self.寂灭_lotus = [x for x in self.寂灭_lotus if not x["_dead"]]

        # --- 每个玩家：六道轮回领域 & 寂灭脉冲 & 太极自动两仪剑 ---
        for p in self.players:
            if not p.alive:
                continue
            # 六道轮回领域：拉敌 + 每 0.8s 周期爆炸
            dom = getattr(p, "_samsara_domain", 0.0)
            if dom > 0:
                dom = max(0.0, dom - dt)
                p._samsara_domain = dom
                ph = getattr(p, "_samsara_domain_phase", 0.0) + dt
                p._samsara_domain_phase = ph
                # 拉敌（360半径）
                R = 360
                for s in self.stars:
                    if s.danger and not s._dead:
                        dd = math.hypot(s.x - p.x, s.y - p.y)
                        if 0 < dd < R:
                            ddx = p.x - s.x; ddy = p.y - s.y
                            L_ = dd
                            s.vx += ddx / L_ * 260 * dt
                            s.vy += ddy / L_ * 260 * dt
                # 每 0.8s 一次轮回爆炸
                if ph >= 0.8:
                    p._samsara_domain_phase = 0.0
                    for s in list(self.stars):
                        if s.danger and not s._dead:
                            dd = math.hypot(s.x - p.x, s.y - p.y)
                            if dd < R:
                                self._damage_enemy(s, 3.0, p)
                                s._samsara_mark = True
                                s._samsara_owner = p
                    for ring, col in ((90, (200, 160, 255)), (240, (230, 210, 255))):
                        for i in range(60):
                            a = i * (math.tau / 60)
                            self.particles.append((
                                p.x, p.y,
                                math.cos(a) * (280 + ring),
                                math.sin(a) * (280 + ring),
                                0.6, col, 3.4))
                    self.shake = max(self.shake, 0.25)

            # 寂灭脉冲：每 ~0.8s 一次全屏小范围寂灭光波，共 3 次
            pul = getattr(p, "_寂灭_pulse_timer", 0.0)
            if pul > 0:
                pul = max(0.0, pul - dt)
                p._寂灭_pulse_timer = pul
                if pul <= 0.001 and getattr(p, "_寂灭_pulse_count", 0) > 0:
                    p._寂灭_pulse_count = getattr(p, "_寂灭_pulse_count", 0) - 1
                    # 全屏寂灭光波
                    for s in list(self.stars):
                        if s.danger and not s._dead:
                            self._damage_enemy(s, 5.0, p)
                            s.hit_flash = 0.25
                    # 从玩家发出 3 层全屏扩张冲击波（视觉）
                    for rr, col, cnt in ((60, (255, 200, 255), 80),
                                         (180, (255, 240, 255), 100),
                                         (380, (220, 170, 255), 120)):
                        for i in range(cnt):
                            a = random.uniform(0, math.tau)
                            self.particles.append((
                                p.x, p.y,
                                math.cos(a) * (520 + rr),
                                math.sin(a) * (520 + rr),
                                0.85, col, 4.4))
                    self.shake = max(self.shake, 0.55)
                    self._play("shockwave")
                    if getattr(p, "_寂灭_pulse_count", 0) > 0:
                        p._寂灭_pulse_timer = 0.8

            # 太极阵自动两仪剑：每 0.45s 向最近 2 个敌人各射一发
            tjt = getattr(p, "_taiji_timer", 0.0)
            if tjt > 0:
                bp = getattr(p, "_taiji_blade_phase", 0.0) + dt
                p._taiji_blade_phase = bp
                if bp >= 0.85:
                    p._taiji_blade_phase = 0.0
                    # 找最近 2 个危险敌人
                    tgts = []
                    for s in self.stars:
                        if s.danger and not s._dead:
                            tgts.append((s, math.hypot(s.x - p.x, s.y - p.y)))
                    tgts.sort(key=lambda x: x[1])
                    tgts = tgts[:2]
                    if not tgts:
                        # 无敌人：朝鼠标方向射
                        mx, my = pygame.mouse.get_pos()
                        tgts = [({"x": mx, "y": my}, 1)]
                    for s_or_t, _ in tgts:
                        tx = s_or_t["x"] if isinstance(s_or_t, dict) else s_or_t.x
                        ty = s_or_t["y"] if isinstance(s_or_t, dict) else s_or_t.y
                        a0 = math.atan2(ty - p.y, tx - p.x)
                        for sgn, col in ((-1, (90, 220, 255)), (1, (255, 90, 90))):
                            a = a0 + sgn * 0.25
                            self.taiji_blades.append({
                                "x": p.x, "y": p.y,
                                "vx": math.cos(a) * 520, "vy": math.sin(a) * 520,
                                "life": 1.2, "r": 16, "owner": p, "col": col, "_dead": False
                            })

            # 大道涅槃·金火球护体：带长拖尾的金火球环绕 360° 旋转，每 0.3s 对半径 120 内敌人造成 4.0 伤害
            norb = getattr(p, "_nirvana_orbit", 0.0)
            if norb > 0:
                norb = max(0.0, norb - dt)
                p._nirvana_orbit = norb
                # 环绕相位推进（一圈 ~1.2s）
                ph = getattr(p, "_nirvana_orbit_phase", 0.0) + dt * 5.2
                p._nirvana_orbit_phase = ph
                orbit_r = p.r + 36
                fx = p.x + math.cos(ph) * orbit_r
                fy = p.y + math.sin(ph) * orbit_r
                # 金火球核心（高亮金色）
                self.particles.append((
                    fx, fy,
                    0, 0,
                    0.25,
                    (255, 240, 160),
                    5.0
                ))
                # 长拖尾：沿反速度方向延伸 6 段
                prev_ph = ph - 0.12
                pfx = p.x + math.cos(prev_ph) * orbit_r
                pfy = p.y + math.sin(prev_ph) * orbit_r
                tdx = pfx - fx
                tdy = pfy - fy
                for ti in range(6):
                    off = (ti + 1) * 5.0
                    life = 0.5 - ti * 0.07
                    size = max(1.5, 4.5 - ti * 0.6)
                    self.particles.append((
                        fx + tdx * (ti + 1) * 0.3 + random.uniform(-2, 2),
                        fy + tdy * (ti + 1) * 0.3 + random.uniform(-2, 2),
                        tdx * 0.5 + random.uniform(-20, 20),
                        tdy * 0.5 + random.uniform(-20, 20),
                        life,
                        random.choice([(255, 200, 80), (255, 160, 40), (255, 240, 140)]),
                        size
                    ))
                # 反向第二颗金火球（180° 对称）
                fx2 = p.x + math.cos(ph + math.pi) * orbit_r
                fy2 = p.y + math.sin(ph + math.pi) * orbit_r
                self.particles.append((
                    fx2, fy2,
                    0, 0,
                    0.25,
                    (255, 240, 160),
                    5.0
                ))
                prev_ph2 = ph + math.pi - 0.12
                pfx2 = p.x + math.cos(prev_ph2) * orbit_r
                pfy2 = p.y + math.sin(prev_ph2) * orbit_r
                tdx2 = pfx2 - fx2
                tdy2 = pfy2 - fy2
                for ti in range(6):
                    off = (ti + 1) * 5.0
                    life = 0.5 - ti * 0.07
                    size = max(1.5, 4.5 - ti * 0.6)
                    self.particles.append((
                        fx2 + tdx2 * (ti + 1) * 0.3 + random.uniform(-2, 2),
                        fy2 + tdy2 * (ti + 1) * 0.3 + random.uniform(-2, 2),
                        tdx2 * 0.5 + random.uniform(-20, 20),
                        tdy2 * 0.5 + random.uniform(-20, 20),
                        life,
                        random.choice([(255, 200, 80), (255, 160, 40), (255, 240, 140)]),
                        size
                    ))
                # 每 0.3s 一次范围伤害（半径 120，伤害 4.0）
                tick = getattr(p, "_nirvana_orbit_tick", 0.0) + dt
                if tick >= 0.3:
                    p._nirvana_orbit_tick = 0.0
                    R = 120
                    for s in list(self.stars):
                        if s.danger and not s._dead:
                            if math.hypot(s.x - p.x, s.y - p.y) < R:
                                self._damage_enemy(s, 4.0, p)
                                s.hit_flash = 0.2
                else:
                    p._nirvana_orbit_tick = tick

    def _update_worm(self, s, dt):
        """虫群 AI：长条身段跟随头部 + 一定概率包围玩家。
        虫子头部 = s.x/s.y；身段沿历史轨迹跟随。
        """
        # 选定目标：随机选一名活着的玩家
        if not s.worm_target or not s.worm_target.alive:
            alive_ps = [p for p in self.players if p.alive]
            if alive_ps:
                s.worm_target = random.choice(alive_ps)
            else:
                s.worm_target = None
        # 30% 概率进入包围模式：绕玩家圆周运动
        if s.worm_target and random.random() < 0.005:
            s.worm_orbit = random.uniform(80, 160)  # 包围半径
        if s.worm_target and s.worm_orbit > 0:
            tp = s.worm_target
            # 切向方向：保持距离 = worm_orbit
            dx = s.x - tp.x
            dy = s.y - tp.y
            d = math.hypot(dx, dy) or 1
            # 径向修正：拉/推到目标半径
            radial = (d - s.worm_orbit) * 1.6
            nx, ny = dx / d, dy / d
            # 切向（顺时针）
            tx, ty = -ny, nx
            target_vx = tx * 180 + nx * radial
            target_vy = ty * 180 + ny * radial
            s.vx += (target_vx - s.vx) * min(1, 3 * dt)
            s.vy += (target_vy - s.vy) * min(1, 3 * dt)
        # 虫身段跟随：每段朝前一段位置缓慢插值
        prev_x, prev_y = s.x, s.y
        seg_r = max(3, s.r * 0.55)
        for i, (sx, sy) in enumerate(s.segments):
            # 距离前一段保持 seg_r*1.4
            tx, ty = prev_x, prev_y
            dx, dy = tx - sx, ty - sy
            d = math.hypot(dx, dy) or 1
            target_d = seg_r * 1.4
            if d > target_d:
                # 拉近到 target_d
                k = (d - target_d) / d
                nx, ny = dx / d, dy / d
                new_x = sx + nx * (d - target_d) * min(1, 8 * dt)
                new_y = sy + ny * (d - target_d) * min(1, 8 * dt)
            else:
                new_x, new_y = sx, sy
            s.segments[i] = (new_x, new_y)
            prev_x, prev_y = new_x, new_y

    # ---------- 长蛇多球节：每节都是真实的 Star，中间攻击后分节 ----------
    def _spawn_snake(self, x, y, vx, vy, r, tier=0):
        """创建一条多球节长蛇，从蛇头开始逐节排列，返回蛇头。
        每一节都是独立的 Star（danger=True, kind="snake"），共享同一个链 snake_chain。
        """
        # c10 长蛇加强：节数增加 30%；最多 14 节
        base = 5 + max(0, tier)
        seg_count = min(14, int(base * 1.3))
        if seg_count < 2:
            seg_count = 2
        # 每节半径 = r（头部略大，其余节略小，c10 整体半径+5% 更粗）
        r_head = r * 1.05
        r_body = r * 0.90
        # 颜色：按 tier 从青紫到金红
        pal = [
            (110, 180, 255),
            (180, 130, 255),
            (255, 150, 220),
            (255, 200, 90),
        ]
        col = pal[min(len(pal) - 1, tier)]
        # 计算从入口 (x,y) 沿反速度方向逐节排布
        ang = math.atan2(vy, vx)
        spacing = (r_head + r_body) * 0.92
        # 创建各节
        chain = []
        for i in range(seg_count):
            # 节位置：x - i*spacing * cos(ang)
            ri = r_head if i == 0 else r_body
            sxi = x - math.cos(ang) * spacing * i
            syi = y - math.sin(ang) * spacing * i
            # 初始速度全部和蛇头一致
            star = Star(sxi, syi, vx * 1.0, vy * 1.0, ri, col, True, tier=tier, kind="snake")
            # 蛇头属性
            if i == 0:
                star.snake_head_flag = True
                star.snake_prev = None
            else:
                star.snake_head_flag = False
                star.snake_prev = chain[i - 1]
            chain.append(star)
        # 把同一个链引用给所有节
        for s in chain:
            s.snake_chain = chain
            # c10 长蛇加强：每节 HP × 1.3
            s.max_hp = max(1, int(round(s.max_hp * 1.3)))
            s.hp = s.max_hp
        # 蛇头自动启用轻度追踪（c10）
        chain[0].chase_player = 1
        # 将所有节加入 stars
        for s in chain:
            self.stars.append(s)
        return chain[0]

    def _split_snake_chain_at(self, chain, break_idx):
        """在 chain[break_idx] 和 chain[break_idx+1] 之间拆开为两条子链。
        会更新：snake_chain、snake_head_flag、snake_prev。
        """
        # 前半：chain[0..break_idx]
        first_half = chain[0: break_idx + 1]
        second_half = chain[break_idx + 1:]
        for s in first_half:
            s.snake_chain = first_half
        for s in second_half:
            s.snake_chain = second_half
        second_half[0].snake_head_flag = True
        second_half[0].snake_prev = None
        # 第一颗（原蛇头）仍是蛇头
        first_half[0].snake_head_flag = True
        # second_half[0] 可能之前 snake_prev 是 first_half[-1]
        # 断节后成为蛇头
        first_half[-1].snake_prev = first_half[-1].snake_prev if False else None
        # 重连 first_half 的 snake_prev
        for j in range(1, len(first_half)):
            first_half[j].snake_prev = first_half[j - 1]
        for j in range(1, len(second_half)):
            second_half[j].snake_prev = second_half[j - 1]

    def _update_snakes(self, dt):
        """每帧更新所有长蛇链：蛇头追踪玩家，其余节牵引跟随前一节。
        同时检测某一节死亡→在该位置拆链。"""
        # 先找到所有"蛇头"，每条链只处理一次（靠蛇头来更新）
        heads = []
        for s in self.stars:
            if s.kind == "snake" and s.snake_head_flag and not s._dead:
                heads.append(s)
        for head in heads:
            chain = head.snake_chain
            if not chain or chain[0] is not head:
                continue
            # 清理死亡节：先把死亡节从 chain 里取出，用拆链手法拆开
            # 找到所有 dead 的下标（必须从后往前，否则索引混乱）
            dead_idxes = [i for i, s in enumerate(chain) if s._dead]
            # 反向拆链：从后往前逐个在 dead_idx 处断开（只拆 dead_idx）
            processed = set()
            # 先拆 dead_idx 和其后的节
            # 简单做法：遍历链，如果一节 dead，就和前面断开；dead 自己从链中移除
            # 这里采用更稳妥策略：遇到 dead 节就从链中剔除
            if dead_idxes:
                # 构造新链：只包含非 dead 节，然后在 dead 节原位置之后拆为新链
                alive = [s for s in chain if not s._dead]
                # 对每个 dead_idx 点（对应原 chain），我们在 alive 链里找到最近的两个原链相邻点：
                # 简化：拆分点 = 最大原下标 < dead_idx
                new_chains = []
                cur = [alive[0]] if alive else []
                for j in range(1, len(alive)):
                    prev_s = cur[-1]
                    next_s = alive[j]
                    prev_i = chain.index(prev_s)
                    next_i = chain.index(next_s)
                    # 如果 prev_i 和 next_i 之间有任何 dead_idx，则断开
                    between = False
                    for di in dead_idxes:
                        if prev_i < di < next_i:
                            between = True
                            break
                    if between:
                        new_chains.append(cur)
                        cur = [next_s]
                    else:
                        cur.append(next_s)
                if cur:
                    new_chains.append(cur)
                # 把每条 new_chain 应用回去
                for nc in new_chains:
                    for s in nc:
                        s.snake_chain = nc
                    # 蛇头标记 + prev 重连
                    nc[0].snake_head_flag = True
                    nc[0].snake_prev = None
                    for j_ in range(1, len(nc)):
                        nc[j_].snake_head_flag = False
                        nc[j_].snake_prev = nc[j_ - 1]
                # 避免下面再次处理：continue 本条旧 chain
                continue
            # --- 蛇头 AI：朝最近玩家轻微追踪 ---
            tgt_p = None
            tgt_d = 1e9
            for p in self.players:
                if not p.alive:
                    continue
                dd = math.hypot(p.x - head.x, p.y - head.y)
                if dd < tgt_d:
                    tgt_d = dd
                    tgt_p = p
            if tgt_p is not None:
                dx = tgt_p.x - head.x
                dy = tgt_p.y - head.y
                d = math.hypot(dx, dy) or 1
                sp_ = math.hypot(head.vx, head.vy) or 140
                # 轻微转向（不剧烈）
                target_vx = dx / d * sp_
                target_vy = dy / d * sp_
                mix = 0.85
                head.vx = head.vx * mix + target_vx * (1 - mix)
                head.vy = head.vy * mix + target_vy * (1 - mix)
            # 正常移动 head
            head.x += head.vx * dt
            head.y += head.vy * dt
            head.phase += head.spin * dt
            if head.hit_flash > 0:
                head.hit_flash -= dt
            # --- 后面的节：跟随前一节，保持 seg_r*1.4 距离 ---
            for j in range(1, len(chain)):
                seg = chain[j]
                prev = seg.snake_prev
                if prev is None:
                    prev = chain[j - 1]
                target_d = (prev.r + seg.r) * 1.08
                dx = prev.x - seg.x
                dy = prev.y - seg.y
                d = math.hypot(dx, dy) or 1e-6
                # 每一节速度跟随前一节：牵引到 target_d 距离
                desired_x = prev.x - dx / d * target_d
                desired_y = prev.y - dy / d * target_d
                # 平滑插值移动
                k = min(1.0, 12.0 * dt)
                seg.x = seg.x + (desired_x - seg.x) * k
                seg.y = seg.y + (desired_y - seg.y) * k
                # vx/vy 也跟随前一节的方向（便于边界反弹）
                seg.vx = seg.vx * 0.92 + prev.vx * 0.08
                seg.vy = seg.vy * 0.92 + prev.vy * 0.08
                if seg.hit_flash > 0:
                    seg.hit_flash -= dt
                seg.phase += seg.spin * dt

    def _update_weapons(self, dt):
        # 自动开火
        for p in self.players:
            if not p.alive or p.weapon_type is None or p.weapon_cd > 0:
                continue
            aim = self._aim_dir(p)
            p.weapon_ang = aim
            if p.weapon_type == "GUN":
                p.weapon_cd = 0.35
                spd = 760
                self.bullets.append(Bullet(p.x, p.y, math.cos(aim) * spd,
                                           math.sin(aim) * spd, owner=p))
                self._play("shoot")
            # SWORD 改为 360° 旋刃（见 blade_spins，拾取时触发）
        # 子弹移动 + 命中（光枪削减生命值）
        for b in self.bullets:
            b.update(dt)
            for s in self.stars:
                if s.danger and not s._dead:
                    if math.hypot(s.x - b.x, s.y - b.y) < s.r + 4:
                        self._damage_enemy(s, 1, b.owner)
                        b._dead = True
                        break
        self.bullets = [b for b in self.bullets if not b._dead and b.life > 0
                        and -30 < b.x < WIDTH + 30 and -30 < b.y < HEIGHT + 30]
        # 挥砍特效衰减
        for sw in self.sweeps:
            sw["life"] -= dt
        self.sweeps = [sw for sw in self.sweeps if sw["life"] > 0]
        # 炼狱火球更新
        if hasattr(self, "fireballs") and self.fireballs:
            for fb in self.fireballs:
                fb["x"] += fb["vx"] * dt
                fb["y"] += fb["vy"] * dt
                fb["life"] -= dt
                # 命中敌球
                for s in self.stars:
                    if s.danger and not s._dead and not fb["_dead"]:
                        if math.hypot(s.x - fb["x"], s.y - fb["y"]) < s.r + fb["r"]:
                            self._damage_enemy(s, 2, fb["owner"])
                            self.burst(fb["x"], fb["y"], (255, 120, 40), 14, 220, size=2.8, life=0.45)
                            fb["_dead"] = True
                            break
                # 拖尾
                if random.random() < 0.6:
                    self.particles.append(Particle(
                        fb["x"], fb["y"], 0, 0, 0.3, (255, 120, 40), 2.6))
            self.fireballs = [fb for fb in self.fireballs
                              if not fb["_dead"] and fb["life"] > 0
                              and -30 < fb["x"] < WIDTH + 30 and -30 < fb["y"] < HEIGHT + 30]

    def apply_powerup(self, ptype, p=None):
        if p is None:
            p = self.player
        self._play("powerup")
        col = POWERUP_COLORS[ptype]
        self.burst(p.x, p.y, col, 30, 300, size=3.2, life=0.7)
        if ptype == "SHIELD":
            p.shield_timer = POWERUP_DURATION["SHIELD"]
        elif ptype == "MAGNET":
            p.magnet_timer = POWERUP_DURATION["MAGNET"]
        elif ptype == "TIME":
            self.time_slow_timer = POWERUP_DURATION["TIME"]
        elif ptype == "DOUBLE":
            self.double_timer = POWERUP_DURATION["DOUBLE"]
        elif ptype == "BOMB":
            for s in self.stars:
                if s.danger and s.r > p.r * 0.9:
                    self.burst(s.x, s.y, NEON_ORANGE, 22, 300, size=3.0, life=0.6)
                    self.score += int(s.r * 5)
                    s._dead = True
            self.stars = [s for s in self.stars if not s._dead]
            self.shake = max(self.shake, 0.7)
            self._play("bomb")
        elif ptype == "SHRINK":
            p.r = max(14, p.r * 0.55)
        elif ptype == "SCORE":
            self.score += 500
        elif ptype == "LIFE":
            self.lives = min(5, self.lives + 1)
        elif ptype == "PHANTOM":
            # 幻影：短暂无敌穿透，可穿过敌球不受伤害
            p.phantom_timer = POWERUP_DURATION["PHANTOM"]
            p.invuln = max(p.invuln, POWERUP_DURATION["PHANTOM"])
            self._play("phantom")
        elif ptype == "BLACKHOLE":
            self.blackhole = {"x": p.x, "y": p.y, "life": 4.0, "r": 140}
        elif ptype == "GUN":
            p.weapon_type = "GUN"
            p.weapon_timer = POWERUP_DURATION["GUN"]
            p.weapon_cd = 0.0
        elif ptype == "SWORD":
            # 光刃：360° 旋刃持续 4s，碰到的敌方削减生命（带命中冷却）
            self.blade_spins.append({"owner": p, "angle": 0.0,
                                     "life": 4.0, "max": 4.0, "r": p.r * 4.6})
            self._play("slash")

    def _eat(self, s, p, dashing, big=False):
        growth = 0.075 if big else 0.045
        p.r = math.sqrt(p.r * p.r + s.r * s.r * growth)
        p.r = min(p.r, 90)
        self.combo += 1
        self.combo_peak = max(self.combo_peak, self.combo)
        self._max_combo = max(getattr(self, "_max_combo", 0), self.combo)
        self.combo_timer = 2.5
        mult = 1 + self.combo // 5
        if self.double_timer > 0:
            mult *= 2
        base = s.r * 8
        if big:
            base *= 2.2
        gain = int(base * mult) + (20 if dashing else 0)
        self.score += gain
        self.level_eaten += 1
        self._max_eaten = max(getattr(self, "_max_eaten", 0), self.level_eaten)
        self.best = max(self.best, self.score)
        # Q2：无尽模式吞噬计入击败数（敌方+1，小球+0.25）
        if getattr(self, "_endless_mode", False):
            if s.danger:
                self._endless_killed = getattr(self, "_endless_killed", 0) + 1.0
            else:
                self._endless_killed = getattr(self, "_endless_killed", 0) + 0.25
        self._play("big" if big else "eat")
        cnt = int(10 + s.r) * (2 if big else 1)
        self.burst(s.x, s.y, s.color, cnt, 220 + (140 if dashing else 0),
                   size=2.6, life=0.55)
        if big:
            self.shake = max(self.shake, 0.25)

    def _hit(self, s, p, dashing):
        # ===== 复活类印记优先触发（朱雀涅槃 / 大道涅槃）=====
        if getattr(p, "_zhuque_revive", False):
            p._zhuque_revive = False
            p._zhuque_timer = 0.0
            # 原地复活爆炸清屏 320 半径 + 恢复满血+大小还原
            p.invuln = 2.4
            p.flash = 0.8
            self.lives = max(self.lives, 5)
            p.r = max(p.r, 18.0)
            self.shake = max(self.shake, 1.1)
            for s2 in list(self.stars):
                if s2.danger and not s2._dead:
                    if math.hypot(s2.x - p.x, s2.y - p.y) < 320:
                        self._damage_enemy(s2, 8.0, p)
            for i in range(90):
                a = random.uniform(0, math.tau)
                sp = random.uniform(160, 520)
                self.particles.append(Particle(
                    p.x, p.y, math.cos(a) * sp, math.sin(a) * sp,
                    random.uniform(0.4, 0.9),
                    random.choice([(255, 120, 60), (255, 200, 60),
                                   (255, 60, 80), (255, 240, 160)]),
                    random.uniform(2.6, 5.2)))
            self.burst(p.x, p.y, (255, 120, 60), 90, 460, size=5.8, life=1.2)
            self._flash_msg = "朱雀涅槃·复活清屏！"
            self._flash_timer = 2.2
            self._play("powerup")
            return
        if getattr(p, "_nirvana_revive", False):
            p._nirvana_revive = False
            p.invuln = 3.0
            self.lives = min(5, self.lives + 3)
            p.r = max(p.r, 18.0)
            self.shake = max(self.shake, 0.9)
            # 爆炸清屏
            for s2 in list(self.stars):
                if s2.danger and not s2._dead:
                    if math.hypot(s2.x - p.x, s2.y - p.y) < 260:
                        self._damage_enemy(s2, 6.0, p)
            self.burst(p.x, p.y, (255, 220, 120), 80, 440, size=5.2, life=1.1)
            self._flash_msg = "不灭金身·涅槃复活！"
            self._flash_timer = 1.8
            self._play("powerup")
            return
        self.lives -= 1
        self.combo = 0
        p.invuln = 1.4
        p.flash = 0.4
        p.r = max(10, p.r * 0.82)
        self.shake = max(self.shake, 0.9)
        self.burst(p.x, p.y, NEON_RED, 36, 360, size=3.2, life=0.7)
        self.burst(s.x, s.y, s.color, 24, 280, size=2.6, life=0.6)
        if self.lives <= 0:
            self.burst(p.x, p.y, p.color, 80, 420, size=4.0, life=1.0)
            self.shake = 1.2
            self._play("death")
            if self.drone_on:
                self.sounds.stop_drone()
                self.drone_on = False
            if getattr(self, "_endless_mode", False):
                # 无尽模式结束：保存高分并返回地图
                self._endless_end()
            else:
                self.state = self.OVER
                self.over_timer = 0.0
        else:
            self._play("hit")

    # ---- 绘制 ----
    def draw(self, mx, my):
        ox = oy = 0
        if self.shake > 0:
            amp = self.shake * 16
            ox = random.uniform(-amp, amp)
            oy = random.uniform(-amp, amp)

        if self.state == self.MAP:
            self._draw_map(mx, my)
            # 弹窗 / 确认框 / 崩溃信息在 MAP 态也要绘制
            self._draw_overlays(mx, my)
            return

        ref = self.player if self.player.alive else self.players[-1]
        px_off = (WIDTH / 2 - ref.x) * 0.03
        py_off = (HEIGHT / 2 - ref.y) * 0.03
        self._draw_bg(px_off + ox, py_off + oy)
        # 氛围粒子
        self._draw_ambient(px_off + ox, py_off + oy)
        # 后期移动背景干扰
        self._draw_interfere()

        # 黑洞
        if self.blackhole is not None:
            self._draw_blackhole(self.blackhole, ox, oy)

        # 星体（可吃判定按最大玩家半径）
        max_pr = max((p.r for p in self.players if p.alive), default=18.0)
        for s in self.stars:
            if s.danger:
                eatable = max_pr > s.r * 1.05
                r_draw = s.r * (1 + 0.06 * math.sin(s.phase * 3))
                self._draw_enemy(s, ox, oy, r_draw, eatable)
            else:
                draw_entity(self.screen, s.x + ox, s.y + oy, s.r, s.color, glow_alpha=150)

        # 道具
        for pu in self.powerups:
            self._draw_powerup(pu, ox, oy)
        # 金币
        for c in self.coin_pickups:
            self._draw_coin(c, ox, oy)

        # 粒子（历史代码有的直接塞 tuple，这里统一归一化为 Particle 实例避免 AttributeError）
        arr = self.particles
        for i in range(len(arr)):
            it = arr[i]
            if isinstance(it, tuple) and len(it) == 7:
                arr[i] = Particle(it[0], it[1], it[2], it[3], it[4], it[5], it[6])
        for pp in self.particles:
            pp.draw(self.screen, ox, oy)
        # 子弹
        for b in self.bullets:
            g = get_glow(7, (255, 230, 120), alpha=180)
            self.screen.blit(g, g.get_rect(center=(int(b.x + ox), int(b.y + oy))),
                             special_flags=pygame.BLEND_RGB_ADD)
            pygame.draw.circle(self.screen, (255, 240, 200),
                               (int(b.x + ox), int(b.y + oy)), 3)
        # 炼狱火球
        if hasattr(self, "fireballs"):
            for fb in self.fireballs:
                g = get_glow(int(fb["r"] * 1.6), (255, 120, 40), alpha=200)
                self.screen.blit(g, g.get_rect(center=(int(fb["x"] + ox), int(fb["y"] + oy))),
                                 special_flags=pygame.BLEND_RGB_ADD)
                pygame.draw.circle(self.screen, (255, 200, 120),
                                   (int(fb["x"] + ox), int(fb["y"] + oy)), int(fb["r"]))
        # 三色红球炸弹
        for b in self.tri_bombs:
            bx, by = b["x"] + ox, b["y"] + oy
            # 闪烁色（快爆炸时变红）
            ratio = b["timer"] / b["max"]
            if ratio < 0.3:
                col = (255, 60, 60) if int(pygame.time.get_ticks() * 0.02) % 2 == 0 else (255, 200, 80)
            else:
                col = (255, 140, 60)
            g = get_glow(int(b["r"] * 2.2), col, alpha=200)
            self.screen.blit(g, g.get_rect(center=(int(bx), int(by))),
                             special_flags=pygame.BLEND_RGB_ADD)
            pygame.draw.circle(self.screen, col, (int(bx), int(by)), int(b["r"]))
            pygame.draw.circle(self.screen, (255, 240, 200), (int(bx), int(by)), int(b["r"]), 2)
            # 倒计时数字
            self._text(f"{b['timer']:.1f}", bx, by - b["r"] - 14, 15,
                       (255, 240, 120), center=True, bold=True)
        # 霜冻冰粒
        for fp in self.frost_pellets:
            fx, fy = fp["x"] + ox, fp["y"] + oy
            g = get_glow(int(fp["r"] * 2.5), (120, 200, 255), alpha=180)
            self.screen.blit(g, g.get_rect(center=(int(fx), int(fy))),
                             special_flags=pygame.BLEND_RGB_ADD)
            pygame.draw.circle(self.screen, (200, 240, 255), (int(fx), int(fy)), int(fp["r"]))
            # 六角冰晶图案
            for ki in range(6):
                ka = ki * (math.tau / 6)
                pygame.draw.line(self.screen, (150, 220, 255),
                                 (int(fx), int(fy)),
                                 (int(fx + math.cos(ka) * fp["r"] * 1.6),
                                  int(fy + math.sin(ka) * fp["r"] * 1.6)), 1)
        # 雷霆电球
        for tb in self.thunder_balls:
            tx, ty = tb["x"] + ox, tb["y"] + oy
            g = get_glow(int(tb["r"] * 2.8), (255, 240, 120), alpha=200)
            self.screen.blit(g, g.get_rect(center=(int(tx), int(ty))),
                             special_flags=pygame.BLEND_RGB_ADD)
            pygame.draw.circle(self.screen, (255, 240, 120), (int(tx), int(ty)), int(tb["r"]))
            # 闪电毛刺
            for _ in range(6):
                a = random.uniform(0, math.tau)
                L = tb["r"] * 2.2
                pygame.draw.line(self.screen, (255, 240, 120),
                                 (int(tx), int(ty)),
                                 (int(tx + math.cos(a) * L),
                                  int(ty + math.sin(a) * L)), 1)
        # 深渊黑洞（多螺旋）- 鸿蒙之始双黑洞：蓝(排斥)/红(吸入)
        for bh in self.void_holes:
            hx, hy = bh["x"] + ox, bh["y"] + oy
            hr = int(bh["r"])
            bh_type = bh.get("bh_type", "attract")
            # 蓝排斥 / 红吸入 / 默认紫
            if bh_type == "repel":
                glow_col, core_col, arm_col, ring_col = (80, 160, 255), (0, 20, 60), (100, 180, 255), (80, 160, 255)
            elif bh_type == "attract":
                glow_col, core_col, arm_col, ring_col = (255, 80, 80), (60, 0, 0), (255, 100, 100), (255, 80, 80)
            else:
                glow_col, core_col, arm_col, ring_col = (150, 70, 220), (30, 0, 60), (180, 90, 255), (150, 70, 220)
            g = get_glow(hr, glow_col, alpha=180)
            self.screen.blit(g, g.get_rect(center=(int(hx), int(hy))),
                             special_flags=pygame.BLEND_RGB_ADD)
            pygame.draw.circle(self.screen, core_col, (int(hx), int(hy)), int(hr * 0.6))
            # 螺旋臂
            t = pygame.time.get_ticks() * 0.005
            for arm in range(3):
                for k in range(12):
                    a = t + arm * (math.tau / 3) + k * 0.25
                    rr = k * (hr / 12.0)
                    px = hx + math.cos(a) * rr
                    py = hy + math.sin(a) * rr
                    pygame.draw.circle(self.screen, arm_col,
                                       (int(px), int(py)), max(1, int(3 - k * 0.18)))
            pygame.draw.circle(self.screen, ring_col, (int(hx), int(hy)), int(hr), 2)
        # 光刃挥砍特效
        for sw in self.sweeps:
            t = clamp(sw["life"] / sw["max"], 0, 1)
            r = sw["r"]
            col = (90, 255, 220)
            for k in range(7):
                a = sw["ang"] - 0.9 + (k / 6) * 1.8
                x = sw["x"] + math.cos(a) * r * (0.4 + 0.6 * (1 - t))
                y = sw["y"] + math.sin(a) * r * (0.4 + 0.6 * (1 - t))
                gg = get_glow(10, col, alpha=int(200 * t))
                self.screen.blit(gg, gg.get_rect(center=(int(x + ox), int(y + oy))),
                                 special_flags=pygame.BLEND_RGB_ADD)
            pygame.draw.arc(self.screen, col,
                            pygame.Rect(int(sw["x"] + ox - r), int(sw["y"] + oy - r),
                                        int(r * 2), int(r * 2)),
                            sw["ang"] - 0.9, sw["ang"] + 0.9, 3)
        # 光刃 360° 旋刃特效
        for bl in self.blade_spins:
            owner = bl["owner"]
            if not owner.alive:
                continue
            t = clamp(bl["life"] / bl["max"], 0, 1)
            r = bl["r"]
            col = (90, 255, 220)
            cx = owner.x + ox
            cy = owner.y + oy
            # 旋刃外环
            gg = get_glow(r * 1.1, col, alpha=int(80 * t))
            self.screen.blit(gg, gg.get_rect(center=(int(cx), int(cy))),
                             special_flags=pygame.BLEND_RGB_ADD)
            # 双刀刃
            for k in range(2):
                a = bl["angle"] + k * math.pi
                x1 = cx + math.cos(a) * (owner.r + 4)
                y1 = cy + math.sin(a) * (owner.r + 4)
                x2 = cx + math.cos(a) * r
                y2 = cy + math.sin(a) * r
                pygame.draw.line(self.screen, col, (x1, y1), (x2, y2), 4)
                g2 = get_glow(12, col, alpha=int(220 * t))
                self.screen.blit(g2, g2.get_rect(center=(int(x2), int(y2))),
                                 special_flags=pygame.BLEND_RGB_ADD)
            # 外环弧
            pygame.draw.circle(self.screen, col, (int(cx), int(cy)), int(r), 1)

        # ===== 钻石皮肤特效绘制 =====
        # 龙焰追踪弹
        for b in getattr(self, "dragon_fire", []):
            bx, by = b["x"] + ox, b["y"] + oy
            rr = int(b["r"])
            g = get_glow(rr * 3, (255, 180, 80), alpha=200)
            self.screen.blit(g, g.get_rect(center=(int(bx), int(by))),
                             special_flags=pygame.BLEND_RGB_ADD)
            pygame.draw.circle(self.screen, (255, 200, 100), (int(bx), int(by)), rr)
            pygame.draw.circle(self.screen, (255, 120, 40), (int(bx), int(by)), max(2, rr // 2))
        # 魔焰毒雾
        for b in getattr(self, "demon_clouds", []):
            bx, by = b["x"] + ox, b["y"] + oy
            rr = int(b["r"])
            g = get_glow(rr * 3, (140, 60, 255), alpha=170)
            self.screen.blit(g, g.get_rect(center=(int(bx), int(by))),
                             special_flags=pygame.BLEND_RGB_ADD)
            pygame.draw.circle(self.screen, (180, 80, 255), (int(bx), int(by)), rr, 2)
        # 星轨弹
        for b in getattr(self, "stellar_orbs", []):
            bx, by = b["x"] + ox, b["y"] + oy
            rr = int(b["r"])
            g = get_glow(rr * 3, (120, 200, 255), alpha=180)
            self.screen.blit(g, g.get_rect(center=(int(bx), int(by))),
                             special_flags=pygame.BLEND_RGB_ADD)
            pygame.draw.circle(self.screen, (180, 230, 255), (int(bx), int(by)), rr)
            # 十字星芒
            for sgn_a in (0, math.pi / 2):
                pygame.draw.line(self.screen, (220, 240, 255),
                                 (int(bx + math.cos(sgn_a) * rr * 1.8),
                                  int(by + math.sin(sgn_a) * rr * 1.8)),
                                 (int(bx - math.cos(sgn_a) * rr * 1.8),
                                  int(by - math.sin(sgn_a) * rr * 1.8)), 1)
        # 两仪剑
        for b in getattr(self, "taiji_blades", []):
            bx, by = b["x"] + ox, b["y"] + oy
            rr = int(b["r"])
            col = b["col"]
            g = get_glow(rr * 2.6, col, alpha=200)
            self.screen.blit(g, g.get_rect(center=(int(bx), int(by))),
                             special_flags=pygame.BLEND_RGB_ADD)
            # 长剑：沿速度方向
            ang = math.atan2(b["vy"], b["vx"])
            for sgn in (-1, 1):
                ex = bx + math.cos(ang) * rr * 1.8 * sgn
                ey = by + math.sin(ang) * rr * 1.8 * sgn
                pygame.draw.line(self.screen, col, (int(bx), int(by)), (int(ex), int(ey)), 3)

        # ========================================================
        # ===== 第三页·至高霸气 9 大皮肤·技能投射物/护体绘制 =====
        # ========================================================
        # 1. 裂空雷将：追踪雷弹 + 全局落地雷
        for b in getattr(self, "titan_hammers", []):
            bx, by = b["x"] + ox, b["y"] + oy
            rr = int(b["r"])
            col = (120, 180, 255) if not b.get("global_bomb") else (200, 230, 255)
            gg = get_glow(rr * 3, col, alpha=200)
            self.screen.blit(gg, gg.get_rect(center=(int(bx), int(by))),
                             special_flags=pygame.BLEND_RGB_ADD)
            pygame.draw.circle(self.screen, col, (int(bx), int(by)), rr)
            pygame.draw.circle(self.screen, (255, 255, 255), (int(bx), int(by)), max(2, rr // 2))
            # 四周锯齿闪电（4 道）
            for si in range(4):
                sa = si * math.pi / 2 + pygame.time.get_ticks() * 0.012
                sx2 = bx + math.cos(sa) * (rr + 8 + random.uniform(-2, 2))
                sy2 = by + math.sin(sa) * (rr + 8 + random.uniform(-2, 2))
                pygame.draw.line(self.screen, (220, 240, 255),
                                 (int(bx), int(by)), (int(sx2), int(sy2)), 2)
        # 2. 沧溟潮君：高压水柱(beam矩形) + 六道潮卷(tornado) + 高压水炮(ball)
        for b in getattr(self, "qinglong_dragons", []):
            bx, by = b["x"] + ox, b["y"] + oy
            rr = int(b["r"])
            if b.get("kind") == "tornado":
                # 潮卷：多层旋转水环 + 水柱
                col1, col2 = (60, 220, 160), (120, 240, 200)
                g0 = get_glow(rr * 3.4, col1, alpha=180)
                self.screen.blit(g0, g0.get_rect(center=(int(bx), int(by))),
                                 special_flags=pygame.BLEND_RGB_ADD)
                tt = pygame.time.get_ticks() * 0.01
                for li in range(3):
                    rect = pygame.Rect(0, 0, int(rr * (2 + li * 0.6)), int(rr * (2 + li * 0.6)))
                    rect.center = (int(bx), int(by))
                    pygame.draw.arc(self.screen, [col1, col2, (180, 250, 220)][li],
                                    rect, tt + li, tt + li + 4, 3)
                pygame.draw.circle(self.screen, (200, 250, 230), (int(bx), int(by)), max(2, rr - 6))
            elif b.get("kind") == "spiral_beam":
                # 螺旋波浪柱：沿方向延伸的正弦螺旋水柱
                ang = b.get("angle", 0.0)
                length = b.get("length", 1200)
                amp = b.get("spiral_amp", 22)
                freq = b.get("spiral_freq", 0.06)
                ph = b.get("spiral_phase", 0.0)
                # 螺旋法线方向（垂直于水柱方向）
                nx = -math.sin(ang); ny = math.cos(ang)
                # 生成螺旋路径上的点
                pts = []
                steps = 60
                for si in range(steps + 1):
                    t_ = si / steps
                    dist = length * t_
                    # 螺旋偏移：正弦波 + 相位旋转
                    wave = amp * math.sin(dist * freq + ph)
                    px = bx + math.cos(ang) * dist + nx * wave
                    py = by + math.sin(ang) * dist + ny * wave
                    pts.append((int(px), int(py)))
                # 外层光晕（沿螺旋路径多点）
                g0 = get_glow(rr * 3, (80, 220, 200), alpha=140)
                for si in range(0, len(pts), 6):
                    self.screen.blit(g0, g0.get_rect(center=pts[si]),
                                     special_flags=pygame.BLEND_RGB_ADD)
                # 螺旋主体：三层连线（外深→内亮）
                if len(pts) >= 2:
                    pygame.draw.lines(self.screen, (30, 140, 170), False, pts, rr * 2)
                    pygame.draw.lines(self.screen, (100, 230, 220), False, pts, rr)
                    pygame.draw.lines(self.screen, (220, 250, 255), False, pts, max(2, rr // 2))
                # 螺旋光斑（沿路径旋转的水珠）
                for si in range(0, len(pts), 8):
                    pygame.draw.circle(self.screen, (180, 250, 240), pts[si], max(2, rr // 3))
            elif b.get("kind") == "beam":
                # Q4：高压水柱·长矩形单水柱
                ang = b.get("angle", 0.0)
                length = b.get("length", 1200)
                ex = bx + math.cos(ang) * length
                ey = by + math.sin(ang) * length
                # 外层光晕
                g0 = get_glow(rr * 4, (80, 220, 200), alpha=160)
                # 沿水柱多点光晕
                for t_ in (0.15, 0.4, 0.65, 0.9):
                    mx_ = bx + (ex - bx) * t_
                    my_ = by + (ey - by) * t_
                    self.screen.blit(g0, g0.get_rect(center=(int(mx_), int(my_))),
                                     special_flags=pygame.BLEND_RGB_ADD)
                # 矩形主体（外层深色 + 内层亮色）
                pygame.draw.line(self.screen, (40, 160, 180),
                                 (int(bx), int(by)), (int(ex), int(ey)), rr * 2)
                pygame.draw.line(self.screen, (120, 230, 220),
                                 (int(bx), int(by)), (int(ex), int(ey)), rr)
                pygame.draw.line(self.screen, (220, 250, 255),
                                 (int(bx), int(by)), (int(ex), int(ey)), max(2, rr // 2))
            else:
                # 高压水炮球：细长水滴状 + 尾焰
                ang = math.atan2(b["vy"], b["vx"])
                g0 = get_glow(rr * 3, (80, 220, 180), alpha=200)
                self.screen.blit(g0, g0.get_rect(center=(int(bx), int(by))),
                                 special_flags=pygame.BLEND_RGB_ADD)
                # 椭圆主体
                for si in range(2):
                    sgn = (-1, 1)[si]
                    ex = bx + math.cos(ang) * rr * 2.2 * sgn
                    ey = by + math.sin(ang) * rr * 2.2 * sgn
                    pygame.draw.line(self.screen, (80, 220, 180),
                                     (int(bx - math.cos(ang) * rr),
                                      int(by - math.sin(ang) * rr)),
                                     (int(ex), int(ey)), rr + 2)
                pygame.draw.circle(self.screen, (200, 250, 220), (int(bx), int(by)), rr)
        # 3. 碎雪巡使：月牙刃 + 圆环刃 + 雪煞影分身
        for b in getattr(self, "baihu_blades", []):
            bx, by = b["x"] + ox, b["y"] + oy
            rr = int(b["r"])
            ang = math.atan2(b["vy"], b["vx"])
            g0 = get_glow(rr * 3.2, (240, 250, 255), alpha=190)
            self.screen.blit(g0, g0.get_rect(center=(int(bx), int(by))),
                             special_flags=pygame.BLEND_RGB_ADD)
            if b.get("crescent"):
                # 月牙刃：白色弧形月牙
                rect = pygame.Rect(0, 0, int(rr * 2.8), int(rr * 2.8))
                rect.center = (int(bx), int(by))
                pygame.draw.arc(self.screen, (255, 255, 255), rect,
                                ang - 0.9, ang + 0.9, max(2, rr - 2))
                pygame.draw.arc(self.screen, (210, 230, 255), rect,
                                ang - 0.9, ang + 0.9, max(1, rr // 2))
            else:
                # 三瓣刀型（旧款兼容）
                for si in (-1, 0, 1):
                    a2 = ang + si * 0.4
                    ex = bx + math.cos(a2) * rr * 2.2
                    ey = by + math.sin(a2) * rr * 2.2
                    pygame.draw.line(self.screen, (255, 255, 255),
                                     (int(bx), int(by)), (int(ex), int(ey)), rr - 2)
                pygame.draw.circle(self.screen, (210, 230, 255), (int(bx), int(by)), max(3, rr // 2))
        # 圆环刃（baihu_rings：白蓝扩张圆环）
        for ring in getattr(self, "baihu_rings", []):
            rx, ry = ring["x"] + ox, ring["y"] + oy
            rr = int(ring["r"])
            if rr < 2: continue
            g0 = get_glow(max(4, rr * 2), (200, 230, 255), alpha=120)
            self.screen.blit(g0, g0.get_rect(center=(int(rx), int(ry))),
                             special_flags=pygame.BLEND_RGB_ADD)
            pygame.draw.circle(self.screen, (255, 255, 255),
                               (int(rx), int(ry)), rr, 4)
            pygame.draw.circle(self.screen, (180, 220, 255),
                               (int(rx), int(ry)), max(1, rr - 4), 2)
        for b in getattr(self, "baihu_shadows", []):
            bx, by = b["x"] + ox, b["y"] + oy
            rr = int(b["r"])
            g0 = get_glow(rr * 3.2, (220, 235, 255), alpha=170)
            self.screen.blit(g0, g0.get_rect(center=(int(bx), int(by))),
                             special_flags=pygame.BLEND_RGB_ADD)
            # 雪煞王字+耳朵：参考皮肤外观做个小型白虎头
            for si in range(2):
                sgn = -1 if si == 0 else 1
                ex = bx + sgn * rr * 0.55
                ey = by - rr * 0.85
                pygame.draw.line(self.screen, (240, 240, 240),
                                 (int(ex), int(ey + 6)),
                                 (int(ex - sgn * 3), int(ey - 8)), 2)
            pygame.draw.circle(self.screen, (240, 245, 255), (int(bx), int(by)), rr)
            pygame.draw.circle(self.screen, (180, 200, 220), (int(bx), int(by)), max(2, rr // 3))
        # 4. 燎原武侯：穿透三连火弹
        for b in getattr(self, "zhuque_fire", []):
            bx, by = b["x"] + ox, b["y"] + oy
            rr = int(b["r"])
            col = random.choice([(255, 120, 60), (255, 200, 80), (255, 80, 40)])
            g0 = get_glow(rr * 3.4, col, alpha=200)
            self.screen.blit(g0, g0.get_rect(center=(int(bx), int(by))),
                             special_flags=pygame.BLEND_RGB_ADD)
            pygame.draw.circle(self.screen, col, (int(bx), int(by)), rr)
            pygame.draw.circle(self.screen, (255, 240, 180), (int(bx), int(by)), max(2, rr // 2))
        # 火龙卷风（zhuque_tornados：多层旋转火圈）
        for b in getattr(self, "zhuque_tornados", []):
            bx, by = b["x"] + ox, b["y"] + oy
            rr = int(b["r"])
            sp = b.get("spin_phase", 0.0)
            g0 = get_glow(rr * 2.6, (255, 120, 60), alpha=160)
            self.screen.blit(g0, g0.get_rect(center=(int(bx), int(by))),
                             special_flags=pygame.BLEND_RGB_ADD)
            # 多层旋转火圈（橙红黄交替）
            for li in range(4):
                rad = rr - li * 14
                if rad < 4: break
                col = [(255, 80, 40), (255, 140, 60), (255, 200, 80), (255, 240, 160)][li]
                for k in range(8):
                    a = sp * (1 if li % 2 == 0 else -1) + k * (math.tau / 8)
                    px = bx + math.cos(a) * rad
                    py = by + math.sin(a) * rad
                    pygame.draw.circle(self.screen, col, (int(px), int(py)), 5)
        # 5. 玄冰卫圣：大冰锥 + 冰锥雨
        for b in getattr(self, "xuanwu_ices", []):
            bx, by = b["x"] + ox, b["y"] + oy
            rr = int(b["r"])
            big = b.get("big_spike", False)
            ang = math.atan2(b["vy"], b["vx"])
            base_col = (160, 220, 255) if not big else (120, 190, 255)
            g0 = get_glow(rr * (3 if not big else 3.6), base_col, alpha=190)
            self.screen.blit(g0, g0.get_rect(center=(int(bx), int(by))),
                             special_flags=pygame.BLEND_RGB_ADD)
            # 冰锥：尖头朝运动方向的三角锥
            tip_x = bx + math.cos(ang) * rr * (2.6 if big else 2)
            tip_y = by + math.sin(ang) * rr * (2.6 if big else 2)
            left_a = ang + math.pi * 0.62
            right_a = ang - math.pi * 0.62
            pts = [(tip_x, tip_y),
                   (bx + math.cos(left_a) * rr, by + math.sin(left_a) * rr),
                   (bx + math.cos(right_a) * rr, by + math.sin(right_a) * rr)]
            pygame.draw.polygon(self.screen, base_col,
                                [(int(xx), int(yy)) for xx, yy in pts])
            pygame.draw.polygon(self.screen, (230, 248, 255),
                                [(int(xx * 0.75 + tip_x * 0.25),
                                  int(yy * 0.75 + tip_y * 0.25))
                                 for xx, yy in pts])
            if big:
                # 大冰锥加个冰环
                pygame.draw.circle(self.screen, (200, 235, 255),
                                   (int(bx), int(by)), rr + 5, 2)
        # 6. 星陨领主：大陨石 + 爆裂小陨石
        for b in getattr(self, "stargod_meteors", []):
            bx, by = b["x"] + ox, b["y"] + oy
            rr = int(b["r"])
            big = b.get("big_meteor", False)
            # Q2：星海主宰陨石改为宇宙蓝白色调（不再是饼干色棕黄）
            col_core = (180, 230, 255) if big else (210, 240, 255)
            col_outer = (80, 160, 255) if big else (120, 190, 255)
            g0 = get_glow(rr * (3.4 if big else 2.8), col_outer, alpha=200)
            self.screen.blit(g0, g0.get_rect(center=(int(bx), int(by))),
                             special_flags=pygame.BLEND_RGB_ADD)
            # 陨石：外圈星空环 + 内星核 + 拖焰
            pygame.draw.circle(self.screen, col_outer, (int(bx), int(by)), rr)
            pygame.draw.circle(self.screen, col_core, (int(bx), int(by)), max(3, rr - 4))
            # 表面星斑（深蓝紫，不再是棕色饼干坑）
            for ki in range(3):
                ka = ki * (math.tau / 3) + pygame.time.get_ticks() * 0.003
                kx = bx + math.cos(ka) * (rr * 0.45)
                ky = by + math.sin(ka) * (rr * 0.45)
                pygame.draw.circle(self.screen, (40, 80, 160),
                                   (int(kx), int(ky)), max(1, rr // 6))
        # 7. 时空猎手：裂空爪痕（三道撕裂AOE）
        for b in getattr(self, "chrono_claws", []):
            bx, by = b["x"] + ox, b["y"] + oy
            rr = int(b["r"])
            ang = math.atan2(b["vy"], b["vx"])
            g0 = get_glow(rr * 3.4, (180, 120, 255), alpha=200)
            self.screen.blit(g0, g0.get_rect(center=(int(bx), int(by))),
                             special_flags=pygame.BLEND_RGB_ADD)
            # 三道爪形：弧形斜切
            for si in (-1, 0, 1):
                a0 = ang + si * 0.35
                rect = pygame.Rect(0, 0, int(rr * 2.4), int(rr * 2.4))
                rect.center = (int(bx), int(by))
                pygame.draw.arc(self.screen, (220, 180, 255), rect, a0 - 0.6, a0 + 0.6, rr - 4)
            pygame.draw.circle(self.screen, (240, 220, 255),
                               (int(bx + math.cos(ang) * rr),
                                int(by + math.sin(ang) * rr)), 3)
        # 钩链/巨爪（chrono_hooks）
        for h in getattr(self, "chrono_hooks", []):
            owner = h["owner"]
            if owner is None or not owner.alive:
                continue
            hx, hy = h["x"] + ox, h["y"] + oy
            if h.get("kind") == "giant_claw":
                # Q4：巨爪裂空·巨大紫色爪子（旋转+发光+三爪指）
                rr = int(h["r"])
                ang = h.get("angle", 0.0)
                g0 = get_glow(rr * 3, (180, 120, 255), alpha=200)
                self.screen.blit(g0, g0.get_rect(center=(int(hx), int(hy))),
                                 special_flags=pygame.BLEND_RGB_ADD)
                # 三根爪指（向外伸展的弧形线条）
                for i in range(3):
                    fa = ang + (i - 1) * 0.6
                    tx = hx + math.cos(fa) * rr * 1.8
                    ty = hy + math.sin(fa) * rr * 1.8
                    # 爪指主体
                    pygame.draw.line(self.screen, (200, 140, 255),
                                     (int(hx), int(hy)), (int(tx), int(ty)), rr // 3 + 2)
                    pygame.draw.line(self.screen, (240, 200, 255),
                                     (int(hx), int(hy)), (int(tx), int(ty)), max(2, rr // 6))
                    # 爪尖
                    pygame.draw.circle(self.screen, (255, 230, 255),
                                       (int(tx), int(ty)), max(3, rr // 4))
                # 中心核心
                pygame.draw.circle(self.screen, (180, 120, 255), (int(hx), int(hy)), rr // 2)
                pygame.draw.circle(self.screen, (255, 255, 255), (int(hx), int(hy)), max(2, rr // 4))
            else:
                # 旧版钩链渲染（兼容）
                px, py = owner.x + ox, owner.y + oy
                dx_c = hx - px; dy_c = hy - py
                seg = 12
                for k in range(seg + 1):
                    t_ = k / seg
                    cx_ = px + dx_c * t_
                    cy_ = py + dy_c * t_
                    rad = 3 if k % 2 == 0 else 2
                    pygame.draw.circle(self.screen, (180, 120, 255),
                                       (int(cx_), int(cy_)), rad)
                g0 = get_glow(28, (180, 120, 255), alpha=180)
                self.screen.blit(g0, g0.get_rect(center=(int(hx), int(hy))),
                                 special_flags=pygame.BLEND_RGB_ADD)
                pygame.draw.circle(self.screen, (220, 180, 255), (int(hx), int(hy)), int(h["r"]))
                pygame.draw.circle(self.screen, (255, 255, 255), (int(hx), int(hy)), max(2, int(h["r"]) // 2))
        # 8. 不灭尊者：9 座护体金佛（buddha_hands kind=buddha）
        for b in getattr(self, "buddha_hands", []):
            bx, by = b["x"] + ox, b["y"] + oy
            rr = int(b["r"])
            if b.get("kind") == "buddha":
                # 小金佛：金身圆光 + 肉髻 + 白毫
                g0 = get_glow(rr * 3.2, (255, 210, 100), alpha=180)
                self.screen.blit(g0, g0.get_rect(center=(int(bx), int(by))),
                                 special_flags=pygame.BLEND_RGB_ADD)
                pygame.draw.circle(self.screen, (255, 200, 80), (int(bx), int(by)), rr)
                pygame.draw.circle(self.screen, (255, 230, 140), (int(bx), int(by)), max(3, rr - 4))
                # 头光 3 层
                for li, col in enumerate([(255, 220, 100), (255, 240, 160), (255, 255, 200)]):
                    pygame.draw.circle(self.screen, col, (int(bx), int(by)),
                                       rr + 4 + li * 3, 1)
                # 头顶肉髻
                pygame.draw.ellipse(self.screen, (255, 180, 40),
                                    pygame.Rect(int(bx - 3), int(by - rr - 6), 6, 8))
            else:
                pygame.draw.circle(self.screen, (255, 200, 80), (int(bx), int(by)), rr)
        # 9. 极律虚皇：蓝光柱(beam) + 落地 9 道光柱(pillar)
        for b in getattr(self, "god_pillars", []):
            if b.get("type") == "beam":
                # 蓝光柱：从玩家发出的扇形长条
                owner = b.get("owner") or self.player
                bx, by = owner.x + ox, owner.y + oy
                ang = b.get("angle", 0.0)
                w_ = b.get("width", 26)
                L = b.get("length", 1500)
                t_life = clamp(b["life"] / b.get("max", 0.35), 0, 1)
                # 3 层发光层
                for li, (w_mul, col_, al_) in enumerate([
                    (1.8, (120, 200, 255), 70),
                    (1.2, (160, 220, 255), 110),
                    (0.7, (220, 240, 255), 160),
                ]):
                    actual_w = w_ * w_mul * t_life
                    # 长四边形：4 个点
                    perp_x, perp_y = -math.sin(ang), math.cos(ang)
                    p1 = (bx - perp_x * actual_w / 2, by - perp_y * actual_w / 2)
                    p2 = (bx + perp_x * actual_w / 2, by + perp_y * actual_w / 2)
                    p3 = (bx + math.cos(ang) * L + perp_x * actual_w / 2,
                          by + math.sin(ang) * L + perp_y * actual_w / 2)
                    p4 = (bx + math.cos(ang) * L - perp_x * actual_w / 2,
                          by + math.sin(ang) * L - perp_y * actual_w / 2)
                    pygame.draw.polygon(self.screen, (*col_, al_),
                                        [(int(xx), int(yy)) for xx, yy in [p1, p2, p3, p4]])
            else:
                # 落地光柱(pillar)：从天际落下的巨型柱
                bx, by = b["x"] + ox, b["y"] + oy
                rr = int(b["r"])
                t_life = clamp(b["life"] / b.get("max", 1.0), 0, 1)
                h2 = int(HEIGHT * 1.4 * t_life)  # 从天到地
                rect = pygame.Rect(int(bx - rr), int(by - h2), int(rr * 2), h2)
                # 外层光柱
                for li, (al_, wm, col_) in enumerate([
                    (60, 1.8, (160, 220, 255)),
                    (120, 1.2, (200, 240, 255)),
                    (200, 0.7, (255, 255, 220)),
                ]):
                    sub = pygame.Surface((int(rr * 2 * wm), h2), pygame.SRCALPHA)
                    sub.fill((*col_, al_))
                    self.screen.blit(sub, sub.get_rect(center=(int(bx), int(by - h2 / 2))),
                                     special_flags=pygame.BLEND_RGB_ADD)
                # 底部光圈
                g0 = get_glow(rr * 3, (255, 255, 220), alpha=200)
                self.screen.blit(g0, g0.get_rect(center=(int(bx), int(by))),
                                 special_flags=pygame.BLEND_RGB_ADD)
        # 不灭尊者：舍利卫星子球（在玩家周围单独绘制）
        for p in self.players:
            sats = getattr(p, "_buddha_satellites", None)
            if not sats or not p.alive:
                continue
            for sat in sats:
                sx, sy = sat["x"] + ox, sat["y"] + oy
                rr = int(sat["r"])
                g0 = get_glow(rr * 3, (255, 220, 120), alpha=190)
                self.screen.blit(g0, g0.get_rect(center=(int(sx), int(sy))),
                                 special_flags=pygame.BLEND_RGB_ADD)
                pygame.draw.circle(self.screen, (255, 200, 80), (int(sx), int(sy)), rr)
                pygame.draw.circle(self.screen, (255, 240, 180), (int(sx), int(sy)), max(2, rr // 2))
                # 小卍字两点
                for (dx2, dy2) in [(-2, -2), (2, -2), (2, 2), (-2, 2)]:
                    pygame.draw.rect(self.screen, (255, 180, 40),
                                     pygame.Rect(int(sx + dx2 - 1), int(sy + dy2 - 1), 2, 2))

        # ===== 终极皮肤效果渲染 =====
        # 生命起源：元素球弹道
        for b in getattr(self, "origin_balls", []):
            bx, by = b["x"] + ox, b["y"] + oy
            rr = int(b["r"])
            col = b["color"]
            g0 = get_glow(rr * 3, col, alpha=200)
            self.screen.blit(g0, g0.get_rect(center=(int(bx), int(by))),
                             special_flags=pygame.BLEND_RGB_ADD)
            pygame.draw.circle(self.screen, col, (int(bx), int(by)), rr)
            pygame.draw.circle(self.screen, (255, 255, 255), (int(bx), int(by)), max(2, rr // 2))
            # 旋转光斑
            ph = b.get("phase", 0)
            for k in range(3):
                a = ph + k * (math.tau / 3)
                sx2 = bx + math.cos(a) * (rr + 6)
                sy2 = by + math.sin(a) * (rr + 6)
                pygame.draw.circle(self.screen, col, (int(sx2), int(sy2)), 3)

        # 生命起源：12元素环绕球
        for pp in self.players:
            if pp._origin_orb_timer > 0 and pp._origin_orbs:
                for orb in pp._origin_orbs:
                    ox2 = pp.x + math.cos(orb["angle"]) * orb["r"] + ox
                    oy2 = pp.y + math.sin(orb["angle"]) * orb["r"] + oy
                    col = orb["color"]
                    g0 = get_glow(30, col, alpha=180)
                    self.screen.blit(g0, g0.get_rect(center=(int(ox2), int(oy2))),
                                     special_flags=pygame.BLEND_RGB_ADD)
                    pygame.draw.circle(self.screen, col, (int(ox2), int(oy2)), 12)
                    pygame.draw.circle(self.screen, (255, 255, 255), (int(ox2), int(oy2)), 5)

        # 逆悖突进：圆柱炮光束
        for b in getattr(self, "paradox_beams", []):
            bx, by = b["x"] + ox, b["y"] + oy
            ang = b["angle"]; length = b["length"]; rr = int(b["r"])
            ex = bx + math.cos(ang) * length; ey = by + math.sin(ang) * length
            col = b["color"]
            g0 = get_glow(rr * 3, col, alpha=160)
            for t_ in (0.2, 0.5, 0.8):
                mx_ = bx + (ex - bx) * t_; my_ = by + (ey - by) * t_
                self.screen.blit(g0, g0.get_rect(center=(int(mx_), int(my_))),
                                 special_flags=pygame.BLEND_RGB_ADD)
            # 三层矩形光束
            pygame.draw.line(self.screen, tuple(max(0, c - 40) for c in col),
                             (int(bx), int(by)), (int(ex), int(ey)), rr * 2)
            pygame.draw.line(self.screen, col,
                             (int(bx), int(by)), (int(ex), int(ey)), rr)
            pygame.draw.line(self.screen, (255, 255, 255),
                             (int(bx), int(by)), (int(ex), int(ey)), max(2, rr // 3))

        # 逆悖突进：6根光柱360度旋转
        for pp in self.players:
            if pp._paradox_pillar_timer > 0 and pp._paradox_pillars:
                for pillar in pp._paradox_pillars:
                    px = pp.x + math.cos(pillar["angle"]) * pillar["r"] + ox
                    py = pp.y + math.sin(pillar["angle"]) * pillar["r"] + oy
                    col = pillar["color"]
                    # 从天到地的光柱
                    g0 = get_glow(50, col, alpha=180)
                    self.screen.blit(g0, g0.get_rect(center=(int(px), int(py))),
                                     special_flags=pygame.BLEND_RGB_ADD)
                    pygame.draw.line(self.screen, col,
                                     (int(px), 0), (int(px), HEIGHT), 16)
                    pygame.draw.line(self.screen, tuple(min(255, c + 60) for c in col),
                                     (int(px), 0), (int(px), HEIGHT), 8)
                    pygame.draw.circle(self.screen, (255, 255, 255), (int(px), int(py)), 10)

        # 终焉：灭世长枪
        for sp in getattr(self, "finality_spears", []):
            sx, sy = sp["x"] + ox, sp["y"] + oy
            ang = sp["angle"]; length = sp.get("length", 120)
            ex = sx + math.cos(ang) * length; ey = sy + math.sin(ang) * length
            # 尾部
            tx = sx - math.cos(ang) * length * 0.8; ty = sy - math.sin(ang) * length * 0.8
            g0 = get_glow(40, (255, 50, 50), alpha=220)
            self.screen.blit(g0, g0.get_rect(center=(int(sx), int(sy))),
                             special_flags=pygame.BLEND_RGB_ADD)
            # 长枪主体（三层）
            pygame.draw.line(self.screen, (120, 20, 20), (int(tx), int(ty)), (int(ex), int(ey)), 14)
            pygame.draw.line(self.screen, (255, 50, 50), (int(tx), int(ty)), (int(ex), int(ey)), 8)
            pygame.draw.line(self.screen, (255, 200, 200), (int(tx), int(ty)), (int(ex), int(ey)), 3)
            # 枪尖
            pygame.draw.circle(self.screen, (255, 255, 255), (int(ex), int(ey)), 8)

        # 终焉：镰刀360°旋转
        for pp in self.players:
            if pp._finality_scythe_timer > 0:
                scythe_r = pp.r + 120
                cx, cy = pp.x + ox, pp.y + oy
                for i in range(4):
                    a = pygame.time.get_ticks() * 0.008 + i * (math.pi / 2)
                    sx2 = cx + math.cos(a) * scythe_r
                    sy2 = cy + math.sin(a) * scythe_r
                    # 镰刀弧线
                    g0 = get_glow(35, (255, 50, 50), alpha=180)
                    self.screen.blit(g0, g0.get_rect(center=(int(sx2), int(sy2))),
                                     special_flags=pygame.BLEND_RGB_ADD)
                    # 弧形镰刀刃
                    for k in range(5):
                        ka = a + (k - 2) * 0.15
                        kx = cx + math.cos(ka) * (scythe_r + k * 4)
                        ky = cy + math.sin(ka) * (scythe_r + k * 4)
                        pygame.draw.circle(self.screen, (255, 80, 80), (int(kx), int(ky)), 8 - k)
                    # 镰刀柄
                    pygame.draw.line(self.screen, (180, 40, 40),
                                     (int(cx), int(cy)), (int(sx2), int(sy2)), 3)

        # 终焉：无敌破坏死光
        for pp in self.players:
            if pp._finality_laser_timer > 0:
                cx, cy = pp.x + ox, pp.y + oy
                t = pygame.time.get_ticks() * 0.005
                # 360°放射状血红黑激光
                for i in range(16):
                    a = i * (math.tau / 16) + t
                    ex = cx + math.cos(a) * 500
                    ey = cy + math.sin(a) * 500
                    # 三层激光
                    pygame.draw.line(self.screen, (60, 0, 0),
                                     (int(cx), int(cy)), (int(ex), int(ey)), 24)
                    pygame.draw.line(self.screen, (180, 20, 20),
                                     (int(cx), int(cy)), (int(ex), int(ey)), 14)
                    pygame.draw.line(self.screen, (255, 60, 60),
                                     (int(cx), int(cy)), (int(ex), int(ey)), 6)
                    pygame.draw.line(self.screen, (255, 200, 200),
                                     (int(cx), int(cy)), (int(ex), int(ey)), 2)
                # 中心血红黑核
                g0 = get_glow(120, (255, 0, 0), alpha=220)
                self.screen.blit(g0, g0.get_rect(center=(int(cx), int(cy))),
                                 special_flags=pygame.BLEND_RGB_ADD)
                pygame.draw.circle(self.screen, (20, 0, 0), (int(cx), int(cy)), 30)
                pygame.draw.circle(self.screen, (255, 30, 30), (int(cx), int(cy)), 20)
                pygame.draw.circle(self.screen, (255, 200, 200), (int(cx), int(cy)), 8)

        # 玩家
        for p in self.players:
            if p.alive:
                self._draw_one_player(p, ox, oy)
        # 分裂子细胞
        for c in self.split_cells:
            if c.alive:
                self._draw_one_player(c, ox, oy)
        # 分裂连线（主球↔子细胞）
        if self.split_cells and self.player.alive:
            for c in self.split_cells:
                if c.alive:
                    pygame.draw.line(self.screen, self.player.color,
                                     (self.player.x + ox, self.player.y + oy),
                                     (c.x + ox, c.y + oy), 1)

        # 时停色调
        if self.time_slow_timer > 0:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            a = int(40 + 20 * math.sin(pygame.time.get_ticks() * 0.008))
            overlay.fill((40, 90, 180, a))
            self.screen.blit(overlay, (0, 0))
        # 恐怖 / 关卡氛围覆盖（含暗角、火光、闪电）
        self._draw_horror_overlay()
        # 双倍分色调
        if self.double_timer > 0:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((255, 140, 60, 18))
            self.screen.blit(overlay, (0, 0))

        self._draw_ui()

        if self.state == self.PAUSED:
            self._overlay_pause()
        elif self.state == self.LEVEL_COMPLETE:
            self._overlay_level_complete()
        elif self.state == self.VICTORY:
            self._overlay_victory()
        elif self.state == self.OVER:
            self._overlay_over()
        # 全局提示信息（F2 解锁等）
        if self._flash_timer > 0 and self._flash_msg:
            a = min(1.0, self._flash_timer / 0.4)
            # 支持多行 \n 自动换行
            fl = self._flash_msg.split("\n")
            fy = 110
            for ln in fl:
                if len(ln) > 54:
                    subl = self._wrap_text(ln, 820, 18)
                    for sl in subl:
                        self._text(sl, WIDTH // 2, fy, 18,
                                   (255, 230, 120), bold=True, center=True)
                        fy += 24
                else:
                    self._text(ln, WIDTH // 2, fy, 18,
                               (255, 230, 120), bold=True, center=True)
                    fy += 24

        # ===== 弹窗 / 确认框 / 崩溃信息 =====
        self._draw_overlays(mx, my)

    def _draw_overlays(self, mx, my):
        """绘制所有覆盖层：ESC退出确认、崩溃弹窗、通用Modal、成就提示。"""
        # ===== Q7：成就解锁提示（右上角栈式显示）=====
        if self._ach_toasts:
            ty = 70
            for t in self._ach_toasts[:4]:  # 最多同时显示 4 条
                nm = t.get("name", "")
                timer = t.get("timer", 0)
                alpha = min(1.0, timer / 0.5)  # 淡出
                bw_, bh_ = 360, 52
                bx_ = WIDTH - bw_ - 16
                by_ = ty
                # 背景框
                s = pygame.Surface((bw_, bh_), pygame.SRCALPHA)
                s.fill((20, 40, 20, int(220 * alpha)))
                pygame.draw.rect(s, (120, 220, 120, int(255 * alpha)),
                                 s.get_rect(), 2, border_radius=10)
                self.screen.blit(s, (bx_, by_))
                # 文字
                self._text("[成就解锁]", bx_ + 14, by_ + 10, 14,
                           (120, 220, 120), bold=True)
                self._text(nm, bx_ + 14, by_ + 30, 16,
                           (240, 255, 220), bold=True)
                ty += bh_ + 8
        # ===== ESC 退出确认弹窗（Y退出 / N、ESC、回车、空格 取消）=====
        if getattr(self, "_confirm_exit", False):
            self._dim(200)
            bx, by, bw, bh = WIDTH // 2 - 280, HEIGHT // 2 - 100, 560, 200
            pygame.draw.rect(self.screen, (14, 16, 36), (bx, by, bw, bh), border_radius=20)
            pygame.draw.rect(self.screen, NEON_PINK, (bx, by, bw, bh), 3, border_radius=20)
            self._text("确定要退出游戏吗？", WIDTH // 2, HEIGHT // 2 - 50,
                       30, NEON_PINK, bold=True, center=True)
            self._text("按 Y 确认退出      按 N / ESC / 空格 取消返回", WIDTH // 2, HEIGHT // 2 + 10,
                       18, (220, 220, 255), center=True)
            self._text("（所有进度会自动保存到 stardust_save.json）", WIDTH // 2, HEIGHT // 2 + 50,
                       14, (160, 160, 190), center=True)

        # ===== 崩溃信息弹窗：显示异常并提示 _exception.log 文件路径 =====
        if getattr(self, "_crash_info", None) is not None:
            short_msg, _tb_text = self._crash_info
            wait = max(0.0, getattr(self, "_crash_wait", 0.0))
            self._dim(230)
            bx, by, bw, bh = WIDTH // 2 - 360, HEIGHT // 2 - 180, 720, 360
            pygame.draw.rect(self.screen, (20, 8, 18), (bx, by, bw, bh), border_radius=18)
            pygame.draw.rect(self.screen, (255, 70, 80), (bx, by, bw, bh), 3, border_radius=18)
            self._text("!! 游戏运行异常", WIDTH // 2, by + 20, 24, (255, 90, 100), bold=True, center=True)
            lines = self._wrap_text(f"错误：{short_msg}", 640, 16, bold=False)
            ly = by + 60
            for ln in lines[:5]:
                self._text(ln, WIDTH // 2, ly, 16, (255, 200, 160), center=True)
                ly += 22
            ly += 8
            self._text("详细堆栈已保存到：_exception.log", WIDTH // 2, ly, 15,
                       (200, 220, 255), center=True)
            ly += 28
            self._text("把这个文件内容发给开发者即可快速定位问题！", WIDTH // 2, ly, 14,
                       (160, 200, 160), center=True)
            ly += 40
            self._text(f"{wait:.1f} 秒后自动退出（按任意键立即退出）", WIDTH // 2, by + bh - 30,
                       16, (220, 200, 120), center=True)

        # ===== 通用弹窗 Modal（导出/导入/兑换码 结果/输入等）=====
        if getattr(self, "_modal", None) is not None:
            m = self._modal
            self._dim(210)
            title = m.get("title", "提示")
            col = m.get("col", NEON_CYAN)
            lines = m.get("body_lines", [])
            line_h = 22
            n_lines = max(1, len(lines))
            has_input = m.get("input") is not None
            extra = 90 if has_input else 0
            bh = max(200, 110 + n_lines * line_h + extra)
            bw = 680 if has_input else 620
            bx = WIDTH // 2 - bw // 2
            by = HEIGHT // 2 - bh // 2
            pygame.draw.rect(self.screen, (10, 12, 28), (bx, by, bw, bh), border_radius=18)
            pygame.draw.rect(self.screen, col, (bx, by, bw, bh), 3, border_radius=18)
            self._text(title, WIDTH // 2, by + 28, 26, col, bold=True, center=True)
            ly = by + 70
            for ln in lines:
                if ly + 20 > by + bh - (100 if has_input else 90):
                    break
                sub = self._wrap_text(ln, bw - 80, 18)
                for s in sub:
                    self._text(s, WIDTH // 2, ly, 18, (240, 240, 255), center=True)
                    ly += 24
            if has_input:
                uly = by + bh - 100
                self._text(m.get("input_title", "请输入："), bx + 40, uly - 4, 18,
                           NEON_YELLOW, bold=True)
                input_rect = pygame.Rect(bx + 40, uly + 22, bw - 80, 44)
                ib_hover = input_rect.collidepoint(*pygame.mouse.get_pos())
                pygame.draw.rect(self.screen, (18, 20, 40), input_rect, border_radius=10)
                pygame.draw.rect(self.screen, (NEON_YELLOW if ib_hover else col),
                                 input_rect, 2, border_radius=10)
                cur_in = str(m.get("input", ""))
                caret = "|" if int(pygame.time.get_ticks() / 400) % 2 == 0 else " "
                self._text(cur_in + caret, input_rect.centerx, input_rect.centery - 11,
                           22, WHITE, bold=True, center=True)
                m["_input_rect"] = input_rect
            # 关闭/确定按钮
            ok_txt = m.get("ok_txt", "确定")
            ok_rect = pygame.Rect(bx + bw - 180, by + bh - 60, 150, 46)
            ok_hover = ok_rect.collidepoint(*pygame.mouse.get_pos())
            pygame.draw.rect(self.screen, (18, 22, 42), ok_rect, border_radius=10)
            pygame.draw.rect(self.screen, (col if ok_hover else (160, 160, 190)),
                             ok_rect, 2, border_radius=10)
            self._text(ok_txt, ok_rect.centerx, ok_rect.centery - 11, 20,
                       col if ok_hover else WHITE, bold=True, center=True)
            m["_ok_rect"] = ok_rect
            # 关闭按钮 (X) 在右上角
            close_rect = pygame.Rect(bx + bw - 36, by + 8, 28, 28)
            close_hover = close_rect.collidepoint(*pygame.mouse.get_pos())
            pygame.draw.rect(self.screen, (40, 10, 10), close_rect, border_radius=6)
            pygame.draw.rect(self.screen, (NEON_RED if close_hover else (180, 60, 60)),
                             close_rect, 2, border_radius=6)
            self._text("X", close_rect.centerx, close_rect.centery - 9, 16,
                       NEON_RED if close_hover else WHITE, bold=True, center=True)
            m["_close_rect"] = close_rect
            # 如需粘贴/复制按钮（导出弹窗）
            if m.get("has_copy"):
                cp_rect = pygame.Rect(bx + 30, by + bh - 60, 150, 46)
                cp_hover = cp_rect.collidepoint(*pygame.mouse.get_pos())
                pygame.draw.rect(self.screen, (18, 22, 42), cp_rect, border_radius=10)
                pygame.draw.rect(self.screen, (NEON_GREEN if cp_hover else DIM),
                                 cp_rect, 2, border_radius=10)
                self._text("复制到剪贴板", cp_rect.centerx, cp_rect.centery - 11, 18,
                           NEON_GREEN if cp_hover else WHITE, bold=True, center=True)
                m["_copy_rect"] = cp_rect
            # 保存弹窗整体矩形，用于点击外部检测
            m["_rect"] = pygame.Rect(bx, by, bw, bh)

    def _draw_one_player(self, p, ox, oy):
        show = True
        if p.invuln > 0:
            show = int(p.invuln * 20) % 2 == 0
        if not show or self.state == self.OVER:
            return
        is_sub = getattr(p, "_is_sub", False)
        base_col = self._skin_color(p) if (not is_sub and p is self.player) else p.color
        col = NEON_RED if p.flash > 0 else base_col
        # 加速时发光逐渐变亮
        dg = getattr(p, "dash_glow", 0.0)
        glow_alpha = int(170 + 80 * dg)
        # 出生闪光
        if p.spawn_flash > 0:
            ring = get_glow(p.r * (2.6 + p.spawn_flash), base_col,
                            alpha=int(180 * p.spawn_flash))
            self.screen.blit(ring, ring.get_rect(center=(int(p.x + ox), int(p.y + oy))),
                             special_flags=pygame.BLEND_RGB_ADD)
        draw_entity(self.screen, p.x + ox, p.y + oy, p.r, col, glow_alpha=glow_alpha)
        # 加速发光额外光晕（渐亮）
        if dg > 0.01:
            extra = get_glow(p.r * (2.0 + 1.6 * dg), NEON_PINK, alpha=int(120 * dg))
            self.screen.blit(extra, extra.get_rect(center=(int(p.x + ox), int(p.y + oy))),
                             special_flags=pygame.BLEND_RGB_ADD)
        # 友方标识：旋转双弧光环（与敌方尖刺区分）
        tt = pygame.time.get_ticks() * 0.003
        ring_r = p.r + 5
        for k in range(2):
            a0 = tt + k * math.pi
            rect = pygame.Rect(0, 0, int(ring_r * 2), int(ring_r * 2))
            rect.center = (int(p.x + ox), int(p.y + oy))
            pygame.draw.arc(self.screen, base_col, rect, a0, a0 + math.pi * 0.7, 2)
        # 武器图标（持有时在球边缘指示朝向；子细胞不显示）
        if p.weapon_type is not None and not is_sub:
            wcol = POWERUP_COLORS[p.weapon_type]
            wx = p.x + math.cos(p.weapon_ang) * (p.r + 10)
            wy = p.y + math.sin(p.weapon_ang) * (p.r + 10)
            ex = p.x + math.cos(p.weapon_ang) * (p.r + 26)
            ey = p.y + math.sin(p.weapon_ang) * (p.r + 26)
            pygame.draw.line(self.screen, wcol,
                             (wx + ox, wy + oy), (ex + ox, ey + oy), 3)
            self._text(POWERUP_LETTER[p.weapon_type],
                       p.x + ox, p.y + oy - p.r - 16, 13, wcol, center=True)
        # 护盾
        if p.shield_timer > 0:
            rad = p.r + 9 + math.sin(pygame.time.get_ticks() * 0.012) * 3
            pygame.draw.circle(self.screen, NEON_CYAN,
                               (int(p.x + ox), int(p.y + oy)), int(rad), 2)
            g = get_glow(rad + 6, NEON_CYAN, alpha=70)
            self.screen.blit(g, g.get_rect(center=(int(p.x + ox), int(p.y + oy))),
                             special_flags=pygame.BLEND_RGB_ADD)
        # 磁吸范围
        if p.magnet_timer > 0:
            pygame.draw.circle(self.screen, NEON_PURPLE,
                               (int(p.x + ox), int(p.y + oy)), 200, 1)
        # 加速光环 + 速度线
        if getattr(p, "_was_dashing", False) and p.energy > 0:
            ring = get_glow(p.r * 3.0, NEON_PINK, alpha=150)
            self.screen.blit(ring, ring.get_rect(center=(int(p.x + ox), int(p.y + oy))),
                             special_flags=pygame.BLEND_RGB_ADD)
            pdx = p.x - p.prev_x
            pdy = p.y - p.prev_y
            pd = math.hypot(pdx, pdy)
            if pd > 1:
                ux, uy = pdx / pd, pdy / pd
                for i in range(4):
                    back = p.r + 6 + i * 8
                    tx = p.x - ux * back
                    ty = p.y - uy * back
                    g = get_glow(6, NEON_PINK, alpha=170 - i * 38)
                    self.screen.blit(g, g.get_rect(center=(int(tx + ox), int(ty + oy))),
                                     special_flags=pygame.BLEND_RGB_ADD)
        # 皮肤专属霸气外观（仅主玩家）
        if not is_sub and p is self.player and self.active_skin:
            self._draw_skin_aura(p, ox, oy)
        # 混沌六剑（主玩家专用）
        if not is_sub and self.active_skin == "chaos" and p._chaos_sword_timer > 0:
            self._draw_chaos_swords(p, ox, oy)
        # 混沌钩子
        if not is_sub and self.active_skin == "chaos" and p._chaos_hook is not None:
            self._draw_chaos_hook(p, ox, oy)
        # 混沌生命值条（5格）
        if not is_sub and self.active_skin == "chaos":
            self._draw_chaos_hp(p, ox, oy)
        # 2P 编号（子细胞不显示）
        if self.num_players == 2 and not is_sub:
            txt = get_font(12, True).render(f"P{p.pid}", True, WHITE)
            self.screen.blit(txt, txt.get_rect(center=(int(p.x + ox), int(p.y + oy - p.r - 12))))

    def _draw_skin_aura(self, p, ox, oy):
        """每种皮肤的独特球体外观与光环特效。"""
        sk = self.active_skin
        cx, cy = p.x + ox, p.y + oy
        t = pygame.time.get_ticks() * 0.001
        r = p.r
        if sk == "tri":
            # 三色灵球：根据当前形态显示对应光环
            mode = p.tri_mode
            if mode == 0:
                # 红球：脉动红环 + 火星
                pulse = r + 8 + 4 * math.sin(t * 6)
                pygame.draw.circle(self.screen, (255, 70, 90),
                                   (int(cx), int(cy)), int(pulse), 2)
                for i in range(8):
                    a = t * 3 + i * (math.tau / 8)
                    px = cx + math.cos(a) * (r + 6)
                    py = cy + math.sin(a) * (r + 6)
                    self.particles.append(Particle(
                        px, py, math.cos(a) * 30, math.sin(a) * 30 - 20,
                        0.3, (255, 100, 100), 2.4))
            elif mode == 1:
                # 黄球：护盾光环
                pulse = r + 10 + 3 * math.sin(t * 4)
                pygame.draw.circle(self.screen, (255, 220, 80),
                                   (int(cx), int(cy)), int(pulse), 2)
                for i in range(6):
                    a = t * 2 + i * (math.tau / 6)
                    px = cx + math.cos(a) * (r + 8)
                    py = cy + math.sin(a) * (r + 8)
                    pygame.draw.circle(self.screen, (255, 240, 120),
                                       (int(px), int(py)), 2)
            else:
                # 蓝球：速度线 + 气流
                for i in range(6):
                    a = t * 4 + i * (math.tau / 6)
                    L = r + 12 + 8 * math.sin(t * 8 + i)
                    pygame.draw.line(self.screen, (90, 130, 255),
                                     (cx + math.cos(a) * r, cy + math.sin(a) * r),
                                     (cx + math.cos(a) * L, cy + math.sin(a) * L), 2)
                if getattr(p, "_tri_boost_timer", 0) > 0:
                    g = get_glow(r * 2.6, (90, 130, 255), alpha=140)
                    self.screen.blit(g, g.get_rect(center=(int(cx), int(cy))),
                                     special_flags=pygame.BLEND_RGB_ADD)
        elif sk == "moon":
            # 月华：弯月遮罩 + 冰晶
            pygame.draw.circle(self.screen, (40, 50, 80),
                               (int(cx + r * 0.4), int(cy - r * 0.2)), int(r * 0.8))
            for i in range(5):
                a = t + i * (math.tau / 5)
                px = cx + math.cos(a) * (r + 8)
                py = cy + math.sin(a) * (r + 8)
                pygame.draw.line(self.screen, (220, 240, 255),
                                 (px, py), (px + math.cos(a) * 4, py + math.sin(a) * 4), 2)
        elif sk == "sun":
            # 烈阳：放射光芒 + 发光排斥时更强
            glow_active = getattr(p, "_sun_glow_timer", 0) > 0
            rays = 20 if glow_active else 12
            for i in range(rays):
                a = t * 1.5 + i * (math.tau / rays)
                L = r + (16 if glow_active else 10) + 6 * math.sin(t * 4 + i)
                col = (255, 240, 120) if glow_active else (255, 200, 80)
                pygame.draw.line(self.screen, col,
                                 (cx + math.cos(a) * r, cy + math.sin(a) * r),
                                 (cx + math.cos(a) * L, cy + math.sin(a) * L),
                                 3 if glow_active else 2)
            if glow_active:
                g = get_glow(r * 3.0, (255, 220, 100), alpha=160)
                self.screen.blit(g, g.get_rect(center=(int(cx), int(cy))),
                                 special_flags=pygame.BLEND_RGB_ADD)
        elif sk == "rainbow":
            # 虹光：七彩环
            for i in range(7):
                c = RAINBOW_COLORS[i]
                a0 = t * 2 + i * (math.tau / 7)
                rect = pygame.Rect(0, 0, int(r * 2 + 10 + i * 2), int(r * 2 + 10 + i * 2))
                rect.center = (int(cx), int(cy))
                pygame.draw.arc(self.screen, c, rect, a0, a0 + 0.5, 2)
        elif sk == "void":
            # 紫渊黑洞：吸积漩涡
            for i in range(3):
                a = t * 3 + i * (math.tau / 3)
                rr = r + 6 + i * 4
                for k in range(6):
                    aa = a + k * 0.3
                    px = cx + math.cos(aa) * (rr + k * 2)
                    py = cy + math.sin(aa) * (rr + k * 2)
                    pygame.draw.circle(self.screen, (180, 90, 255),
                                       (int(px), int(py)), 1)
        elif sk == "inferno":
            # 炼狱：跳动火焰环
            ring_active = getattr(p, "_inferno_ring_timer", 0) > 0
            ring_r = p._inferno_base_r * 3 if ring_active else 0
            for i in range(14):
                a = t * 4 + i * (math.tau / 14)
                L = r + 8 + 8 * (0.5 + 0.5 * math.sin(t * 8 + i * 1.3))
                col = (255, 90 + int(80 * math.sin(t * 6 + i)), 30)
                pygame.draw.line(self.screen, col,
                                 (cx + math.cos(a) * r, cy + math.sin(a) * r),
                                 (cx + math.cos(a) * L, cy + math.sin(a) * L), 3)
            # 灼烧环激活时：外圈大火焰环
            if ring_active and ring_r > 0:
                ring_r_draw = int(ring_r)
                pygame.draw.circle(self.screen, (255, 60, 10),
                                   (int(cx), int(cy)), ring_r_draw, 4)
                pygame.draw.circle(self.screen, (255, 140, 40),
                                   (int(cx), int(cy)), ring_r_draw - 4, 2)
                # 倒计时
                self._text(f"{p._inferno_ring_timer:.1f}s", cx, cy - ring_r_draw - 12,
                           13, (255, 200, 80), center=True, bold=True)
            g = get_glow(r * 2.2, (255, 80, 20), alpha=90)
            self.screen.blit(g, g.get_rect(center=(int(cx), int(cy))),
                             special_flags=pygame.BLEND_RGB_ADD)
        elif sk == "frost":
            # 霜冻：六角冰晶
            for i in range(6):
                a = t * 0.8 + i * (math.tau / 6)
                ex = cx + math.cos(a) * (r + 10)
                ey = cy + math.sin(a) * (r + 10)
                pygame.draw.line(self.screen, (180, 230, 255),
                                 (cx + math.cos(a) * r, cy + math.sin(a) * r), (ex, ey), 2)
                pygame.draw.line(self.screen, (180, 230, 255),
                                 (ex, ey), (ex + math.cos(a + 0.5) * 4, ey + math.sin(a + 0.5) * 4), 1)
                pygame.draw.line(self.screen, (180, 230, 255),
                                 (ex, ey), (ex + math.cos(a - 0.5) * 4, ey + math.sin(a - 0.5) * 4), 1)
        elif sk == "thunder":
            # 雷霆：电弧抖动
            for i in range(8):
                a = t * 5 + i * (math.tau / 8)
                steps = 3
                px, py = cx + math.cos(a) * r, cy + math.sin(a) * r
                for k in range(steps):
                    ex = cx + math.cos(a) * (r + 6 + k * 4) + random.uniform(-3, 3)
                    ey = cy + math.sin(a) * (r + 6 + k * 4) + random.uniform(-3, 3)
                    pygame.draw.line(self.screen, (255, 240, 120), (px, py), (ex, ey), 2)
                    px, py = ex, ey
        elif sk == "chaos":
            # 混沌魔神：独特王者光环（非病毒/刺球风格）
            # 多层紫金圆环 + 十字星芒 + 中央符文
            pygame.draw.circle(self.screen, (40, 10, 60), (int(cx), int(cy)), int(r + 2))
            # 紫金双层环
            for layer, (col, w, rmult, sp) in enumerate([
                ((200, 80, 255), 3, 1.12, 2.5),
                ((255, 215, 80), 2, 1.28, -1.8),
                ((150, 70, 220), 2, 1.42, 1.2),
            ]):
                for seg in range(8):
                    a0 = t * sp + seg * (math.tau / 8)
                    a1 = a0 + 0.35
                    rect = pygame.Rect(0, 0, int(r * 2 * rmult), int(r * 2 * rmult))
                    rect.center = (int(cx), int(cy))
                    pygame.draw.arc(self.screen, col, rect, a0, a1, w)
            # 十字星芒（四条直线光）
            for i in range(4):
                a = t * 0.5 + i * (math.tau / 4)
                pygame.draw.line(self.screen, (255, 240, 200),
                                 (cx + math.cos(a) * r, cy + math.sin(a) * r),
                                 (cx + math.cos(a) * (r + 22),
                                  cy + math.sin(a) * (r + 22)), 2)
                pygame.draw.line(self.screen, (200, 80, 255),
                                 (cx - math.cos(a) * (r + 2),
                                  cy - math.sin(a) * (r + 2)),
                                 (cx - math.cos(a) * (r + 14),
                                  cy - math.sin(a) * (r + 14)), 1)
            # 中央符文光点
            for i in range(4):
                a = t * 4 + i * (math.tau / 4)
                px = cx + math.cos(a) * (r * 0.5)
                py = cy + math.sin(a) * (r * 0.5)
                pygame.draw.circle(self.screen, (255, 230, 150),
                                   (int(px), int(py)), 2)
            g = get_glow(r * 2.8, (200, 80, 255), alpha=110)
            self.screen.blit(g, g.get_rect(center=(int(cx), int(cy))),
                             special_flags=pygame.BLEND_RGB_ADD)
        # ===== 第二页 钻石霸气皮肤 专属外观（9 个） =====
        elif sk == "judge":
            # 天罚之眼：中心瞳孔 + 6 翼羽 + 外圈审判圣环
            pygame.draw.circle(self.screen, (255, 240, 150),
                               (int(cx), int(cy)), int(r * 0.55), 2)
            pygame.draw.circle(self.screen, (255, 180, 80),
                               (int(cx), int(cy)), int(r * 0.30), 0)
            # 6 翼羽光弧
            for i in range(6):
                a = t * 0.6 + i * (math.tau / 6)
                r1 = r + 6; r2 = r + 22
                pts = []
                for k in range(5):
                    aa = a + (k - 2) * 0.06
                    rr = r1 if k in (0, 4) else (r2 if k == 2 else (r1 + r2) * 0.5)
                    pts.append((cx + math.cos(aa) * rr, cy + math.sin(aa) * rr))
                if len(pts) >= 2:
                    pygame.draw.lines(self.screen, (255, 230, 180), False,
                                      [(int(x), int(y)) for x, y in pts], 2)
            # 审判圣环（双层反向旋转）
            for sp, col_, w, rm in (( 1.6, (255, 240, 200), 2, 1.30),
                                    (-1.2, (255, 160, 100), 2, 1.50)):
                rect = pygame.Rect(0, 0, int(r * 2 * rm), int(r * 2 * rm))
                rect.center = (int(cx), int(cy))
                a0 = t * sp
                pygame.draw.arc(self.screen, col_, rect, a0, a0 + 2.2, w)
            g = get_glow(r * 2.8, (255, 220, 130), alpha=120)
            self.screen.blit(g, g.get_rect(center=(int(cx), int(cy))),
                             special_flags=pygame.BLEND_RGB_ADD)
        elif sk == "dragon":
            # 真龙帝皇：头顶龙角 + 金色王冠 + 双龙须 + 双层金红龙纹环
            # 龙角
            for i in range(2):
                sgn = -1 if i == 0 else 1
                for k in range(4):
                    kk = k / 3
                    a = math.radians(60 * sgn) - sgn * kk * 0.15
                    rr = r + 4 + kk * 20
                    px_ = cx + math.cos(a) * rr
                    py_ = cy + math.sin(a) * rr
                    if k > 0:
                        pygame.draw.line(self.screen, (255, 150, 60),
                                         (int(px), int(py)), (int(px_), int(py_)), 3)
                    px, py = px_, py_
            # 金色王冠：上方 5 个齿
            crown_y = cy - r - 8
            for i in range(5):
                sgn_ = i - 2
                base_x = cx + sgn_ * (r * 0.28)
                top_x = base_x
                top_y = crown_y - 14 - (0 if i in (0, 4) else (6 if i in (1, 3) else 14))
                pygame.draw.polygon(self.screen, (255, 210, 80), [
                    (int(base_x - 5), int(crown_y)),
                    (int(top_x), int(top_y)),
                    (int(base_x + 5), int(crown_y))
                ])
            # 双龙须（飘带）
            for i in range(2):
                sgn = -1 if i == 0 else 1
                px_ = py_ = None
                for k in range(6):
                    kk = k / 5
                    a = math.radians(150 * sgn)
                    fx = cx + math.cos(a) * r * 0.7
                    fy = cy + math.sin(a) * r * 0.7
                    bx = fx - sgn * 28 * kk + math.sin(t * 4 + k) * 5
                    by = fy + 30 * kk
                    if k > 0 and px_ is not None:
                        pygame.draw.line(self.screen, (255, 210, 140),
                                         (int(px_), int(py_)),
                                         (int(bx), int(by)), 2)
                    px_, py_ = bx, by
            # 双层金红龙纹环
            for sp, col_, rm, w in ((1.8, (255, 120, 50), 1.28, 3),
                                    (-1.4, (255, 220, 120), 1.50, 2)):
                rect = pygame.Rect(0, 0, int(r * 2 * rm), int(r * 2 * rm))
                rect.center = (int(cx), int(cy))
                a0 = t * sp
                for seg in range(6):
                    a1 = a0 + seg * (math.tau / 6)
                    a2 = a1 + 0.38
                    pygame.draw.arc(self.screen, col_, rect, a1, a2, w)
            g = get_glow(r * 2.8, (255, 170, 80), alpha=130)
            self.screen.blit(g, g.get_rect(center=(int(cx), int(cy))),
                             special_flags=pygame.BLEND_RGB_ADD)
        elif sk == "demon":
            # 九幽魔君：恶魔双角 + 紫黑魔焰 + 骷髅鬼面 + 死亡光环
            # 双角
            for i in range(2):
                sgn = -1 if i == 0 else 1
                pts_ = []
                for k in range(6):
                    kk = k / 5
                    a = math.radians(75 * sgn) - sgn * kk * 0.25
                    rr = r + 6 + kk * 22
                    pts_.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr))
                if len(pts_) >= 2:
                    pygame.draw.lines(self.screen, (120, 60, 200), False,
                                      [(int(x), int(y)) for x, y in pts_], 3)
            # 骷髅鬼面：双眼 + 嘴
            eye_off = r * 0.34
            pygame.draw.circle(self.screen, (255, 60, 120),
                               (int(cx - eye_off), int(cy - r * 0.15)), int(r * 0.12), 0)
            pygame.draw.circle(self.screen, (255, 60, 120),
                               (int(cx + eye_off), int(cy - r * 0.15)), int(r * 0.12), 0)
            pygame.draw.rect(self.screen, (220, 220, 230),
                             (int(cx - r * 0.28), int(cy + r * 0.10),
                              int(r * 0.56), int(r * 0.08)), 0)
            # 紫黑魔焰跳动（外焰）
            for i in range(16):
                a = t * 3 + i * (math.tau / 16)
                flick = 0.5 + 0.5 * math.sin(t * 9 + i * 1.3)
                L = r + 10 + 14 * flick
                col_ = (180 + int(40 * flick), 40, 200 + int(55 * flick))
                pygame.draw.line(self.screen, col_,
                                 (cx + math.cos(a) * r, cy + math.sin(a) * r),
                                 (cx + math.cos(a) * L, cy + math.sin(a) * L), 2)
            # 死亡光环（双旋转环）
            for sp, col_, rm in ((2.2, (140, 50, 220), 1.30),
                                 (-1.6, (220, 140, 255), 1.55)):
                rect = pygame.Rect(0, 0, int(r * 2 * rm), int(r * 2 * rm))
                rect.center = (int(cx), int(cy))
                a0 = t * sp
                for seg in range(5):
                    a1 = a0 + seg * (math.tau / 5)
                    a2 = a1 + 0.5
                    pygame.draw.arc(self.screen, col_, rect, a1, a2, 2)
            g = get_glow(r * 2.8, (130, 60, 220), alpha=120)
            self.screen.blit(g, g.get_rect(center=(int(cx), int(cy))),
                             special_flags=pygame.BLEND_RGB_ADD)
        elif sk == "stellar":
            # 星海主宰：8 颗环绕恒星 + 星轨光晕 + 星云粒子尾
            # 8 颗不同颜色恒星
            star_cols = [(255, 220, 120), (150, 220, 255), (220, 160, 255),
                         (255, 150, 130), (180, 255, 220), (255, 200, 200),
                         (180, 200, 255), (255, 255, 200)]
            for i in range(8):
                a = t * 1.6 + i * (math.tau / 8)
                rr = r + 16 + 4 * math.sin(t * 2 + i)
                sx_ = cx + math.cos(a) * rr
                sy_ = cy + math.sin(a) * rr
                gcol = star_cols[i % len(star_cols)]
                pygame.draw.circle(self.screen, gcol, (int(sx_), int(sy_)), int(r * 0.26), 0)
                g = get_glow(r * 0.9, gcol, alpha=150)
                self.screen.blit(g, g.get_rect(center=(int(sx_), int(sy_))),
                                 special_flags=pygame.BLEND_RGB_ADD)
            # 星轨光圈（双层）
            for sp, col_, rm, w in ((0.8, (150, 220, 255), 1.30, 2),
                                    (-0.5, (220, 200, 255), 1.65, 1)):
                rect = pygame.Rect(0, 0, int(r * 2 * rm), int(r * 2 * rm))
                rect.center = (int(cx), int(cy))
                a0 = t * sp
                for seg in range(10):
                    a1 = a0 + seg * (math.tau / 10)
                    a2 = a1 + 0.22
                    pygame.draw.arc(self.screen, col_, rect, a1, a2, w)
            # 星云飘出粒子
            if random.random() < 0.7:
                a_rand = random.uniform(0, math.tau)
                self.particles.append(Particle(
                    cx + math.cos(a_rand) * r,
                    cy + math.sin(a_rand) * r,
                    math.cos(a_rand) * 50 + random.uniform(-30, 30),
                    math.sin(a_rand) * 50 + random.uniform(-30, 30),
                    0.5,
                    random.choice([(150, 220, 255), (220, 200, 255), (255, 255, 200)]),
                    2.2
                ))
            g = get_glow(r * 3.0, (150, 220, 255), alpha=120)
            self.screen.blit(g, g.get_rect(center=(int(cx), int(cy))),
                             special_flags=pygame.BLEND_RGB_ADD)
        elif sk == "samsara":
            # 六道轮回：六芒轮回印 + 六道旋转扇叶 + 中心紫罗太极 + 轮回粒子
            # 六芒星（六道）
            for i in range(6):
                a = t * 1.3 + i * (math.tau / 6)
                # 扇叶
                pts = [(cx, cy)]
                for k in range(4):
                    kk = k / 3
                    aa = a + (kk - 0.5) * 0.55
                    rr = r + 6 + kk * 22
                    pts.append((cx + math.cos(aa) * rr, cy + math.sin(aa) * rr))
                if len(pts) >= 3:
                    pygame.draw.polygon(self.screen, (200, 160, 255),
                                        [(int(x), int(y)) for x, y in pts], 0)
                    pygame.draw.polygon(self.screen, (230, 210, 255),
                                        [(int(x), int(y)) for x, y in pts], 1)
            # 中心紫罗太极（双色鱼）
            r_mid = int(r * 0.65)
            rect_mid = pygame.Rect(0, 0, r_mid * 2, r_mid * 2)
            rect_mid.center = (int(cx), int(cy))
            # 上半圆紫
            pygame.draw.arc(self.screen, (200, 120, 255), rect_mid, 0, math.pi, r_mid)
            # 下半圆白
            pygame.draw.arc(self.screen, (250, 240, 255), rect_mid, math.pi, math.tau, r_mid)
            # 中心眼
            pygame.draw.circle(self.screen, (250, 240, 255),
                               (int(cx), int(cy - r_mid // 2)), max(2, r_mid // 5), 0)
            pygame.draw.circle(self.screen, (200, 120, 255),
                               (int(cx), int(cy + r_mid // 2)), max(2, r_mid // 5), 0)
            # 外圈三道轮回环
            for sp, col_, rm, w in (( 2.1, (200, 120, 255), 1.35, 2),
                                    (-1.7, (230, 210, 255), 1.60, 2),
                                    ( 1.0, (180, 90, 255), 1.85, 2)):
                rect = pygame.Rect(0, 0, int(r * 2 * rm), int(r * 2 * rm))
                rect.center = (int(cx), int(cy))
                a0 = t * sp
                for seg in range(6):
                    a1 = a0 + seg * (math.tau / 6)
                    a2 = a1 + 0.35
                    pygame.draw.arc(self.screen, col_, rect, a1, a2, w)
            # 轮回粒子（不断旋转飞出）
            if random.random() < 0.8:
                a_rand = random.uniform(0, math.tau)
                self.particles.append(Particle(
                    cx + math.cos(a_rand) * r,
                    cy + math.sin(a_rand) * r,
                    math.cos(a_rand) * 70,
                    math.sin(a_rand) * 70,
                    0.5, (200, 160, 255), 2.4
                ))
            g = get_glow(r * 3.0, (200, 150, 255), alpha=130)
            self.screen.blit(g, g.get_rect(center=(int(cx), int(cy))),
                             special_flags=pygame.BLEND_RGB_ADD)
        elif sk == "寂灭":
            # 寂灭神皇：创世莲花 + 粉白金三圈莲华 + 寂灭神光十字 + 梵文粒子
            # 创世莲花：8 瓣 粉色花瓣
            for i in range(8):
                a = t * 1.0 + i * (math.tau / 8)
                pts = [(cx, cy)]
                for k in range(5):
                    kk = k / 4
                    aa = a + (kk - 0.5) * 0.42
                    rr = r + 4 + kk * 26
                    pts.append((cx + math.cos(aa) * rr, cy + math.sin(aa) * rr))
                if len(pts) >= 3:
                    pygame.draw.polygon(self.screen, (255, 180, 240),
                                        [(int(x), int(y)) for x, y in pts], 0)
                    pygame.draw.polygon(self.screen, (255, 240, 255),
                                        [(int(x), int(y)) for x, y in pts], 1)
            # 中心莲房（金色 + 白圈）
            pygame.draw.circle(self.screen, (255, 240, 210),
                               (int(cx), int(cy)), int(r * 0.55), 0)
            pygame.draw.circle(self.screen, (255, 220, 140),
                               (int(cx), int(cy)), int(r * 0.35), 0)
            # 寂灭神光十字（粉白金十字光）
            for i in range(4):
                a = t * 0.3 + i * (math.tau / 4)
                L1 = r + 8; L2 = r + 30
                pygame.draw.line(self.screen, (255, 240, 255),
                                 (cx + math.cos(a) * L1, cy + math.sin(a) * L1),
                                 (cx + math.cos(a) * L2, cy + math.sin(a) * L2), 3)
            # 三圈莲华光环
            for sp, col_, rm, w in (( 1.5, (255, 200, 255), 1.30, 2),
                                    (-1.1, (255, 240, 255), 1.60, 2),
                                    ( 0.7, (255, 220, 200), 1.90, 2)):
                rect = pygame.Rect(0, 0, int(r * 2 * rm), int(r * 2 * rm))
                rect.center = (int(cx), int(cy))
                a0 = t * sp
                for seg in range(7):
                    a1 = a0 + seg * (math.tau / 7)
                    a2 = a1 + 0.28
                    pygame.draw.arc(self.screen, col_, rect, a1, a2, w)
            # 梵文/莲花粉粒子
            if random.random() < 0.9:
                a_rand = random.uniform(0, math.tau)
                self.particles.append(Particle(
                    cx + math.cos(a_rand) * r,
                    cy + math.sin(a_rand) * r,
                    math.cos(a_rand) * 60 + random.uniform(-30, 30),
                    math.sin(a_rand) * 60 + random.uniform(-30, 30),
                    0.55,
                    random.choice([(255, 200, 255), (255, 240, 255), (255, 220, 200)]),
                    2.4
                ))
            g = get_glow(r * 3.0, (255, 200, 255), alpha=140)
            self.screen.blit(g, g.get_rect(center=(int(cx), int(cy))),
                             special_flags=pygame.BLEND_RGB_ADD)
        elif sk == "primal":
            # 鸿蒙之始：阴阳双生鱼 + 混沌双色粒子流 + 三圈鸿蒙道环
            # 阴阳鱼（太极，但颜色更柔和：青白 + 玄黑）
            r_mid = int(r * 0.8)
            rect_mid = pygame.Rect(0, 0, r_mid * 2, r_mid * 2)
            rect_mid.center = (int(cx), int(cy))
            # 上半圆：青白
            pygame.draw.arc(self.screen, (220, 255, 200), rect_mid, 0, math.pi, r_mid)
            # 下半圆：玄黑（带金边）
            pygame.draw.arc(self.screen, (60, 80, 60), rect_mid, math.pi, math.tau, r_mid)
            # 阴阳眼
            pygame.draw.circle(self.screen, (60, 80, 60),
                               (int(cx), int(cy - r_mid // 2)), max(2, r_mid // 5), 0)
            pygame.draw.circle(self.screen, (220, 255, 200),
                               (int(cx), int(cy + r_mid // 2)), max(2, r_mid // 5), 0)
            # 两仪眼边金边
            pygame.draw.circle(self.screen, (255, 240, 160),
                               (int(cx), int(cy - r_mid // 2)), max(2, r_mid // 5) + 1, 1)
            pygame.draw.circle(self.screen, (255, 240, 160),
                               (int(cx), int(cy + r_mid // 2)), max(2, r_mid // 5) + 1, 1)
            # 混沌双色粒子流（青/黑对向旋转）
            for i in range(12):
                a = t * 2.5 + i * (math.tau / 12)
                rr1 = r + 14 + 4 * math.sin(t * 2 + i)
                col_a = (220, 255, 200) if i % 2 == 0 else (60, 80, 60)
                pygame.draw.circle(self.screen, col_a,
                                   (int(cx + math.cos(a) * rr1),
                                    int(cy + math.sin(a) * rr1)), 2)
            # 三圈鸿蒙道环（金 + 青 + 黑）
            for sp, col_, rm, w in (( 1.8, (255, 240, 160), 1.32, 3),
                                    (-1.3, (220, 255, 200), 1.60, 2),
                                    ( 0.9, (80, 100, 80), 1.88, 2)):
                rect = pygame.Rect(0, 0, int(r * 2 * rm), int(r * 2 * rm))
                rect.center = (int(cx), int(cy))
                a0 = t * sp
                for seg in range(8):
                    a1 = a0 + seg * (math.tau / 8)
                    a2 = a1 + 0.28
                    pygame.draw.arc(self.screen, col_, rect, a1, a2, w)
            g = get_glow(r * 3.0, (220, 255, 200), alpha=130)
            self.screen.blit(g, g.get_rect(center=(int(cx), int(cy))),
                             special_flags=pygame.BLEND_RGB_ADD)
        elif sk == "taiji":
            # 太上无极：青红太极 + 两仪四象旋转 + 八卦符文 + 双剑流光
            # 中心青红太极
            r_mid = int(r * 0.75)
            rect_mid = pygame.Rect(0, 0, r_mid * 2, r_mid * 2)
            rect_mid.center = (int(cx), int(cy))
            pygame.draw.arc(self.screen, (90, 220, 255), rect_mid, 0, math.pi, r_mid)
            pygame.draw.arc(self.screen, (255, 90, 90),   rect_mid, math.pi, math.tau, r_mid)
            pygame.draw.circle(self.screen, (255, 90, 90),
                               (int(cx), int(cy - r_mid // 2)), max(2, r_mid // 5), 0)
            pygame.draw.circle(self.screen, (90, 220, 255),
                               (int(cx), int(cy + r_mid // 2)), max(2, r_mid // 5), 0)
            # 四象（四片扇叶：青红白黑）
            four_cols = [(90, 220, 255), (255, 90, 90), (255, 255, 255), (40, 40, 40)]
            for i in range(4):
                a = t * 1.2 + i * (math.tau / 4)
                pts = [(cx, cy)]
                for k in range(4):
                    kk = k / 3
                    aa = a + (kk - 0.5) * 0.50
                    rr = r + 4 + kk * 22
                    pts.append((cx + math.cos(aa) * rr, cy + math.sin(aa) * rr))
                if len(pts) >= 3:
                    pygame.draw.polygon(self.screen, four_cols[i % 4],
                                        [(int(x), int(y)) for x, y in pts], 0)
                    pygame.draw.polygon(self.screen, (255, 255, 255),
                                        [(int(x), int(y)) for x, y in pts], 1)
            # 八卦符文点（8 个颜色点，随机金/白/青/红）
            for i in range(8):
                a = t * 0.7 + i * (math.tau / 8)
                rr = r + 30
                col_ = [(255, 220, 120), (255, 255, 255),
                        (90, 220, 255), (255, 90, 90)][i % 4]
                pygame.draw.circle(self.screen, col_,
                                   (int(cx + math.cos(a) * rr),
                                    int(cy + math.sin(a) * rr)), 2)
            # 太极阵激活时：外圈两仪剑光环
            if getattr(p, "_taiji_timer", 0) > 0:
                for sp, col_, rm in ((1.8, (90, 220, 255), 1.55),
                                     (-1.4, (255, 90, 90), 1.85)):
                    rect = pygame.Rect(0, 0, int(r * 2 * rm), int(r * 2 * rm))
                    rect.center = (int(cx), int(cy))
                    a0 = t * sp
                    for seg in range(10):
                        a1 = a0 + seg * (math.tau / 10)
                        a2 = a1 + 0.22
                        pygame.draw.arc(self.screen, col_, rect, a1, a2, 2)
                # 激活时：双剑流光（青红两色光点旋转）
                for i in range(6):
                    a = t * 3 + i * (math.tau / 6)
                    rr = r + 50
                    col_ = (90, 220, 255) if i % 2 == 0 else (255, 90, 90)
                    pygame.draw.circle(self.screen, col_,
                                       (int(cx + math.cos(a) * rr),
                                        int(cy + math.sin(a) * rr)), 3)
            g = get_glow(r * 3.0, (240, 240, 220), alpha=130)
            self.screen.blit(g, g.get_rect(center=(int(cx), int(cy))),
                             special_flags=pygame.BLEND_RGB_ADD)
        elif sk == "nirvana":
            # 大道涅槃：金身佛光 + 8 瓣金色涅槃莲 + 涅槃光晕 + 九字金粉粒子
            # 金身佛陀圆光（内三层）
            for rm, col_, w in ((1.10, (255, 200, 100), 0),
                                (1.18, (255, 240, 170), 2),
                                (1.26, (255, 220, 120), 2)):
                rr_ = int(r * rm)
                pygame.draw.circle(self.screen, col_,
                                   (int(cx), int(cy)), rr_, w)
            # 8 瓣涅槃莲（金色）
            for i in range(8):
                a = t * 0.9 + i * (math.tau / 8)
                pts = [(cx, cy)]
                for k in range(5):
                    kk = k / 4
                    aa = a + (kk - 0.5) * 0.40
                    rr = r + 6 + kk * 28
                    pts.append((cx + math.cos(aa) * rr, cy + math.sin(aa) * rr))
                if len(pts) >= 3:
                    pygame.draw.polygon(self.screen, (255, 210, 110),
                                        [(int(x), int(y)) for x, y in pts], 0)
                    pygame.draw.polygon(self.screen, (255, 250, 200),
                                        [(int(x), int(y)) for x, y in pts], 1)
            # 九字真言点（9 颗金粉环绕）
            for i in range(9):
                a = t * 1.4 + i * (math.tau / 9)
                rr = r + 36
                col_ = [(255, 220, 120), (255, 250, 200), (255, 180, 80)][i % 3]
                pygame.draw.circle(self.screen, col_,
                                   (int(cx + math.cos(a) * rr),
                                    int(cy + math.sin(a) * rr)), 3)
            # 不灭金身激活时：外圈双层极金光圈 + 金色星尘尾
            if getattr(p, "_nirvana_timer", 0) > 0:
                for sp, col_, rm, w in (( 1.6, (255, 220, 120), 1.60, 3),
                                        (-1.2, (255, 250, 200), 1.90, 3),
                                        ( 0.8, (255, 180, 80),  2.20, 2)):
                    rect = pygame.Rect(0, 0, int(r * 2 * rm), int(r * 2 * rm))
                    rect.center = (int(cx), int(cy))
                    a0 = t * sp
                    for seg in range(10):
                        a1 = a0 + seg * (math.tau / 10)
                        a2 = a1 + 0.22
                        pygame.draw.arc(self.screen, col_, rect, a1, a2, w)
            # 金粉粒子（不断上升飘出）
            if random.random() < 0.85:
                a_rand = random.uniform(0, math.tau)
                self.particles.append(Particle(
                    cx + math.cos(a_rand) * r,
                    cy + math.sin(a_rand) * r,
                    random.uniform(-30, 30),
                    -60 + random.uniform(-20, 20),
                    0.6,
                    random.choice([(255, 220, 120), (255, 250, 200), (255, 180, 80)]),
                    2.4
                ))
            g = get_glow(r * 3.0, (255, 220, 120), alpha=150)
            self.screen.blit(g, g.get_rect(center=(int(cx), int(cy))),
                             special_flags=pygame.BLEND_RGB_ADD)
        # ===== 第三页 至高霸气皮肤 专属外观 =====
        elif sk == "titan":
            # 雷神泰坦：外围闪电王冠 + 雷霆脉动环 + 电场发光
            pygame.draw.circle(self.screen, (80, 140, 220),
                               (int(cx), int(cy)), int(r + 6), 2)
            for i in range(5):
                a = t * 2.0 + i * (math.tau / 5)
                base_x = cx + math.cos(a) * (r + 10)
                base_y = cy + math.sin(a) * (r + 10)
                # 闪电尖端（锯齿）
                tip_x = base_x + math.cos(a) * 16 + random.uniform(-4, 4)
                tip_y = base_y + math.sin(a) * 16 + random.uniform(-4, 4)
                mid_x = (base_x + tip_x) / 2 + random.uniform(-5, 5)
                mid_y = (base_y + tip_y) / 2 + random.uniform(-5, 5)
                pygame.draw.lines(self.screen, (255, 240, 200), False,
                                  [(int(base_x), int(base_y)),
                                   (int(mid_x), int(mid_y)),
                                   (int(tip_x), int(tip_y))], 2)
            # 雷霆领域激活时：外圈大紫电光环 + 实时提示（裂空雷将·新称号）
            if getattr(p, "_titan_domain", 0) > 0:
                pygame.draw.circle(self.screen, (120, 220, 255),
                                   (int(cx), int(cy)), int(r + 48), 4)
                self._text(f"裂空雷将·雷霆领域 {p._titan_domain:.1f}s",
                           cx, cy - r - 56, 13, (120, 180, 255),
                           center=True, bold=True)
            g = get_glow(r * 2.4, (120, 180, 255), alpha=120)
            self.screen.blit(g, g.get_rect(center=(int(cx), int(cy))),
                             special_flags=pygame.BLEND_RGB_ADD)
        elif sk == "qinglong":
            # 青龙帝君：头顶龙角 + 身上青蓝鳞片 + 东方龙须
            for i in range(2):
                sgn = -1 if i == 0 else 1
                a = math.radians(70 * sgn)
                hx = cx + math.cos(a) * (r + 6)
                hy = cy + math.sin(a) * (r + 6)
                tx = cx + math.cos(a - 0.3) * (r + 24)
                ty = cy + math.sin(a - 0.3) * (r + 24)
                pygame.draw.line(self.screen, (80, 220, 140),
                                 (int(hx), int(hy)), (int(tx), int(ty)), 4)
            # 鳞片：围绕 9 片
            for i in range(9):
                a = t * 1.3 + i * (math.tau / 9)
                px = cx + math.cos(a) * (r + 3)
                py = cy + math.sin(a) * (r + 3)
                pygame.draw.circle(self.screen, (60, 220, 160),
                                   (int(px), int(py)), 3)
            # 龙须：2 条长飘带
            for i in range(2):
                sgn = -1 if i == 0 else 1
                px_ = py_ = None
                for k in range(5):
                    kk = k / 4
                    a = math.radians(155 * sgn)
                    fx = cx + math.cos(a) * r
                    fy = cy + math.sin(a) * r
                    bx = fx - sgn * 20 * kk + math.sin(t * 5 + k) * 3
                    by = fy + 22 * kk
                    if k > 0 and px_ is not None:
                        pygame.draw.line(self.screen, (140, 255, 200),
                                         (int(px_), int(py_)),
                                         (int(bx), int(by)), 2)
                    px_, py_ = bx, by
            # 护体激活：提示（沧溟潮君·新称号）
            if getattr(p, "_qinglong_timer", 0) > 0:
                self._text(f"沧溟潮君·沧海横流 {p._qinglong_timer:.1f}s",
                           cx, cy - r - 36, 13, (60, 220, 160),
                           center=True, bold=True)
            g = get_glow(r * 2.4, (60, 220, 160), alpha=110)
            self.screen.blit(g, g.get_rect(center=(int(cx), int(cy))),
                             special_flags=pygame.BLEND_RGB_ADD)
        elif sk == "baihu":
            # 白虎杀皇：耳朵 + 额王 + 条纹 + 白金色披风
            # 耳朵
            for i in range(2):
                sgn = -1 if i == 0 else 1
                ex = cx + sgn * (r * 0.55)
                ey = cy - r * 0.85
                pts = [(ex, ey + 10), (ex - sgn * 5, ey - 14), (ex + sgn * 8, ey - 2)]
                pygame.draw.polygon(self.screen, (240, 240, 240),
                                    [(int(x), int(y)) for x, y in pts])
                pygame.draw.polygon(self.screen, (255, 200, 180),
                                    [(int(x * 0.85 + ex * 0.15),
                                      int(y * 0.85 + ey * 0.15))
                                     for x, y in pts])
            # 额王（黑色"王"）：用粗横杠 + 1 竖画个王
            wx, wy = cx, cy - r * 0.25
            for (dx_, dy_, w, h) in [(-8, -6, 16, 2), (-8, -2, 16, 2),
                                     (-8, 2, 16, 2), (-1, -6, 2, 10)]:
                pygame.draw.rect(self.screen, (0, 0, 0),
                                 pygame.Rect(int(wx + dx_), int(wy + dy_), w, h))
            # 条纹：身体周围 7 道黑纹
            for i in range(7):
                a = t * 0.9 + i * (math.tau / 7)
                x1 = cx + math.cos(a) * (r - 2)
                y1 = cy + math.sin(a) * (r - 2)
                x2 = cx + math.cos(a) * (r + 4)
                y2 = cy + math.sin(a) * (r + 4)
                pygame.draw.line(self.screen, (0, 0, 0),
                                 (int(x1), int(y1)), (int(x2), int(y2)), 3)
            g = get_glow(r * 2.2, (255, 255, 255), alpha=90)
            self.screen.blit(g, g.get_rect(center=(int(cx), int(cy))),
                             special_flags=pygame.BLEND_RGB_ADD)
        elif sk == "zhuque":
            # 朱雀圣皇：火焰尾羽 + 凤冠 + 火环
            # 凤冠（头顶 3 根彩羽）
            for i in range(3):
                sgn = -1 + i
                a = math.radians(-90 + sgn * 15)
                fx = cx + math.cos(a) * r
                fy = cy + math.sin(a) * r
                tx = cx + math.cos(a * 0.8) * (r + 26)
                ty = cy + math.sin(a) * (r + 24)
                col = [(255, 60, 80), (255, 220, 40), (255, 120, 40)][i]
                pygame.draw.line(self.screen, col,
                                 (int(fx), int(fy)), (int(tx), int(ty)), 4)
                pygame.draw.circle(self.screen, col, (int(tx), int(ty)), 3)
            # 火尾羽：后向放射 9 根
            for i in range(9):
                a = math.radians(180 - 60 + i * 15) + math.sin(t * 4 + i) * 0.1
                x1 = cx + math.cos(a) * (r - 2)
                y1 = cy + math.sin(a) * (r - 2)
                x2 = cx + math.cos(a) * (r + 14 + 6 * math.sin(t * 5 + i))
                y2 = cy + math.sin(a) * (r + 14 + 6 * math.sin(t * 5 + i))
                col = random.choice([(255, 80, 30), (255, 180, 40), (255, 240, 80)])
                pygame.draw.line(self.screen, col,
                                 (int(x1), int(y1)), (int(x2), int(y2)), 3)
            # 涅槃印记激活
            if getattr(p, "_zhuque_revive", False):
                self._text(f"涅槃印记", cx, cy - r - 22,
                           12, (255, 120, 60), center=True, bold=True)
            g = get_glow(r * 2.6, (255, 120, 60), alpha=120)
            self.screen.blit(g, g.get_rect(center=(int(cx), int(cy))),
                             special_flags=pygame.BLEND_RGB_ADD)
        elif sk == "xuanwu":
            # 玄武帝尊：玄武巨龟壳纹理 + 蛇纹缠绕 + 帝王紫黑底座
            # 龟壳：围绕圆的 13 块板
            for i in range(13):
                a = i * (math.tau / 13)
                x1 = cx + math.cos(a) * (r - 2)
                y1 = cy + math.sin(a) * (r - 2)
                x2 = cx + math.cos(a) * (r + 10)
                y2 = cy + math.sin(a) * (r + 10)
                pygame.draw.line(self.screen, (60, 80, 160),
                                 (int(x1), int(y1)), (int(x2), int(y2)), 3)
            # 龟壳分区（六边花纹）
            for i in range(6):
                a = t * 0.5 + i * (math.tau / 6)
                px = cx + math.cos(a) * (r * 0.55)
                py = cy + math.sin(a) * (r * 0.55)
                pts = []
                for k in range(6):
                    kk = k * (math.tau / 6) + a
                    pts.append((int(px + math.cos(kk) * 4.2),
                                int(py + math.sin(kk) * 4.2)))
                pygame.draw.polygon(self.screen, (100, 140, 220), pts)
            # 缠绕蛇：绕 2 圈螺旋
            for i in range(24):
                a = t * 1.2 + i * 0.45
                rr = r + 5 + (i % 3) * 2
                sx = cx + math.cos(a) * rr
                sy = cy + math.sin(a) * rr
                pygame.draw.circle(self.screen, (80, 240, 120),
                                   (int(sx), int(sy)), 2)
            if getattr(p, "_xuanwu_timer", 0) > 0:
                # 护盾激活：巨大玄武光环（玄冰卫圣·新称号）
                pygame.draw.circle(self.screen, (120, 200, 255),
                                   (int(cx), int(cy)), int(r + 40), 5)
                pygame.draw.circle(self.screen, (80, 220, 140),
                                   (int(cx), int(cy)), int(r + 30), 2)
                self._text(f"玄冰卫圣·寒冰守护 {p._xuanwu_timer:.1f}s",
                           cx, cy - r - 48, 13, (80, 140, 220),
                           center=True, bold=True)
            g = get_glow(r * 2.4, (80, 140, 220), alpha=120)
            self.screen.blit(g, g.get_rect(center=(int(cx), int(cy))),
                             special_flags=pygame.BLEND_RGB_ADD)
        elif sk == "stargod":
            # 星辰古神：周围 8 颗恒星轨道 + 拖尾 + 星轨连线（出击时显示出击位置）
            orbit = r + 22
            n = 8
            phase = getattr(p, "_stargod_phase", [i * math.tau / n for i in range(n)])
            atk_state = getattr(p, "_stargod_atk_state", [0 for _ in range(n)])
            atk_pos = getattr(p, "_stargod_atk_pos", [(0.0, 0.0) for _ in range(n)])
            pts = []
            for i in range(n):
                a = phase[i] if len(phase) > i else t * 2 + i * (math.tau / n)
                ox_s = cx + math.cos(a) * orbit
                oy_s = cy + math.sin(a) * orbit
                # 出击中：使用出击位置（世界坐标 + 绘制偏移）
                if i < len(atk_state) and atk_state[i] != 0 and i < len(atk_pos):
                    sx = atk_pos[i][0] + (cx - p.x)
                    sy = atk_pos[i][1] + (cy - p.y)
                else:
                    sx, sy = ox_s, oy_s
                pts.append((sx, sy))
                # 恒星本体（渐变色）
                col1 = (255, 230, 120)
                col2 = (255, 160, 60)
                glow_ = get_glow(16, col1, alpha=150)
                self.screen.blit(glow_, glow_.get_rect(center=(int(sx), int(sy))),
                                 special_flags=pygame.BLEND_RGB_ADD)
                pygame.draw.circle(self.screen, col2, (int(sx), int(sy)), 5)
                pygame.draw.circle(self.screen, col1, (int(sx), int(sy)), 3)
            # 轨道虚线环 + 星连线
            for i in range(n):
                x1, y1 = pts[i]
                x2, y2 = pts[(i + 1) % n]
                # 连线（淡金色）
                pygame.draw.line(self.screen, (255, 230, 140),
                                 (int(x1), int(y1)), (int(x2), int(y2)), 1)
            # 轨道圆
            for i in range(36):
                a = i * (math.tau / 36)
                x_ = cx + math.cos(a) * orbit
                y_ = cy + math.sin(a) * orbit
                pygame.draw.circle(self.screen, (255, 240, 180),
                                   (int(x_), int(y_)), 1)
            if getattr(p, "_stargod_timer", 0) > 0:
                self._text(f"星陨领主·八曜护世 {p._stargod_timer:.1f}s",
                           cx, cy - r - 40, 13, (255, 230, 120),
                           center=True, bold=True)
            g = get_glow(r * 2.6, (255, 230, 120), alpha=100)
            self.screen.blit(g, g.get_rect(center=(int(cx), int(cy))),
                             special_flags=pygame.BLEND_RGB_ADD)
        elif sk == "chrono":
            # 时空帝主：双螺旋时间之环 + 中央时钟刻度 + 紫银光辉
            # 双环反向转
            for (sp, w, rr, col) in [
                (2.4, 2, r + 12, (180, 120, 255)),
                (-1.8, 2, r + 20, (220, 220, 255))
            ]:
                rect = pygame.Rect(0, 0, int(rr * 2), int(rr * 2))
                rect.center = (int(cx), int(cy))
                for seg in range(6):
                    a0 = t * sp + seg * (math.tau / 6)
                    a1 = a0 + 0.4
                    pygame.draw.arc(self.screen, col, rect, a0, a1, w)
            # 中央时钟刻度（12 小点）
            for i in range(12):
                a = i * (math.tau / 12) + t * 0.3
                px = cx + math.cos(a) * (r * 0.7)
                py = cy + math.sin(a) * (r * 0.7)
                pygame.draw.circle(self.screen, (255, 255, 240),
                                   (int(px), int(py)), 2)
            # 指针（2 根）
            for i, (sp_, len_, col) in enumerate([
                (6.0, r * 0.7, (255, 240, 255)),
                (-2.4, r * 0.5, (180, 120, 255))
            ]):
                a_ = t * sp_
                pygame.draw.line(self.screen, col, (int(cx), int(cy)),
                                 (int(cx + math.cos(a_) * len_),
                                  int(cy + math.sin(a_) * len_)), 2)
            if getattr(self, "time_freeze_timer", 0) > 0:
                self._text(f"时空冻结 {self.time_freeze_timer:.1f}s",
                           cx, cy - r - 42, 13, (180, 120, 255),
                           center=True, bold=True)
            g = get_glow(r * 2.6, (180, 120, 255), alpha=120)
            self.screen.blit(g, g.get_rect(center=(int(cx), int(cy))),
                             special_flags=pygame.BLEND_RGB_ADD)
        elif sk == "buddha":
            # 万佛之祖：头顶肉髻 + 头光 + 身后 9 个卍字 + 眉心白毫
            # 身后头光（9 色光环，像佛光）
            for i, col in enumerate([
                (255, 200, 80), (255, 230, 120), (255, 210, 60),
                (255, 250, 160), (255, 230, 140)
            ]):
                pygame.draw.circle(self.screen, col,
                                   (int(cx), int(cy)), int(r + 14 + i * 4), 2)
            # 头顶肉髻（金色凸起）
            ttx, tty = cx, cy - r - 4
            pygame.draw.ellipse(self.screen, (255, 180, 40),
                                pygame.Rect(int(ttx - 6), int(tty - 10), 12, 14))
            # 眉心白毫
            pygame.draw.circle(self.screen, (255, 255, 255),
                               (int(cx), int(cy - r * 0.2)), 2)
            # 身后 9 个卍字，围绕一圈
            for i in range(9):
                a = t * 0.8 + i * (math.tau / 9)
                sx = cx + math.cos(a) * (r + 28)
                sy = cy + math.sin(a) * (r + 28)
                # 卍字（用 6 条短横画）
                col_s = (255, 200, 60)
                sz = 4
                # 卍= 中心 + 四端各自一个折
                for (dx_, dy_) in [(-sz, -sz), (0, -sz),
                                   (sz, 0), (sz, sz), (0, sz), (-sz, 0)]:
                    pygame.draw.rect(self.screen, col_s,
                                     pygame.Rect(int(sx + dx_), int(sy + dy_), 2, 2))
            if getattr(p, "_buddha_timer", 0) > 0:
                self._text(f"不灭尊者·万佛降世 {p._buddha_timer:.1f}s",
                           cx, cy - r - 54, 13, (255, 200, 80),
                           center=True, bold=True)
            g = get_glow(r * 3.0, (255, 210, 100), alpha=120)
            self.screen.blit(g, g.get_rect(center=(int(cx), int(cy))),
                             special_flags=pygame.BLEND_RGB_ADD)
        elif sk == "god":
            # 至高神皇：4 翼巨大圣翼 + 皇冠 + 全视之眼（背景之眼）+ 神辉光环
            # 背景神辉
            g0 = get_glow(r * 4.2, (255, 255, 220), alpha=80)
            self.screen.blit(g0, g0.get_rect(center=(int(cx), int(cy))),
                             special_flags=pygame.BLEND_RGB_ADD)
            # 4 翼圣翼（2 对上下翼）
            for i in range(4):
                sgn = -1 if (i // 2) == 0 else 1  # 上下
                side = -1 if i % 2 == 0 else 1    # 左右
                base_a = math.radians((-75 if sgn < 0 else 75) + side * 20)
                base_x = cx + side * (r + 6)
                base_y = cy + (-r * 0.3 if sgn < 0 else r * 0.3)
                # 每片翼羽毛 5 根
                for k in range(5):
                    kk = k / 4
                    ang = base_a + side * kk * 0.5
                    tip_x = base_x + math.cos(ang) * (22 + (4 - k) * 4)
                    tip_y = base_y + math.sin(ang) * (22 + (4 - k) * 4)
                    feather_col = (255, 255, 255) if k % 2 == 0 else (255, 240, 180)
                    pygame.draw.line(self.screen, feather_col,
                                     (int(base_x), int(base_y)),
                                     (int(tip_x), int(tip_y)), 4 - k // 2)
            # 皇冠（8 个尖齿）
            cx_, cy_ = cx, cy - r - 10
            for i in range(9):
                hgt = 18 if i % 2 == 0 else 10
                x_ = cx_ - 18 + i * (36 / 8)
                pts = [(x_, cy_), (x_ + (18 / 8), cy_ - hgt), (x_ + (36 / 8), cy_)]
                pygame.draw.polygon(self.screen, (255, 210, 60),
                                    [(int(px), int(py)) for px, py in pts])
            # 全视之眼（中心外瞳孔 + 白色圆眼）
            eye_col = (255, 255, 160)
            pygame.draw.circle(self.screen, (255, 255, 255),
                               (int(cx), int(cy)), int(r * 0.35))
            pygame.draw.circle(self.screen, (200, 160, 60),
                               (int(cx), int(cy)), int(r * 0.22))
            pygame.draw.circle(self.screen, (0, 0, 0),
                               (int(cx), int(cy)), int(r * 0.12))
            # 提示（极律虚皇·新称号）
            if getattr(p, "_god_timer", 0) > 0:
                self._text(f"极律虚皇·万法归一 {p._god_timer:.1f}s",
                           cx, cy - r - 62, 14,
                           (255, 240, 140), center=True, bold=True)
            g = get_glow(r * 2.6, (255, 255, 200), alpha=140)
            self.screen.blit(g, g.get_rect(center=(int(cx), int(cy))),
                             special_flags=pygame.BLEND_RGB_ADD)
        elif sk == "origin":
            # 生命起源：创世之力·12色元素环 + 生命之树光芒 + 脉动创世核
            elems = self._origin_elements() if hasattr(self, "_origin_elements") else None
            # 创世核脉动光晕
            pulse = 1.0 + 0.15 * math.sin(t * 4)
            g0 = get_glow(r * 3.5 * pulse, (100, 255, 180), alpha=100)
            self.screen.blit(g0, g0.get_rect(center=(int(cx), int(cy))),
                             special_flags=pygame.BLEND_RGB_ADD)
            # 12 色元素旋转环
            if elems:
                for i, (nm, col, dmg, eff) in enumerate(elems):
                    a = t * 1.2 + i * (math.tau / 12)
                    orb_r = r + 16 + 4 * math.sin(t * 5 + i)
                    px = cx + math.cos(a) * orb_r
                    py = cy + math.sin(a) * orb_r
                    g_orb = get_glow(14, col, alpha=160)
                    self.screen.blit(g_orb, g_orb.get_rect(center=(int(px), int(py))),
                                     special_flags=pygame.BLEND_RGB_ADD)
                    pygame.draw.circle(self.screen, col, (int(px), int(py)), 5)
            # 生命之树：6 道放射光线
            for i in range(6):
                a = t * 0.5 + i * (math.tau / 6)
                ex = cx + math.cos(a) * (r + 40)
                ey = cy + math.sin(a) * (r + 40)
                pygame.draw.line(self.screen, (120, 255, 180),
                                 (int(cx), int(cy)), (int(ex), int(ey)), 2)
            # 创世核（白绿色脉动球）
            pygame.draw.circle(self.screen, (255, 255, 255),
                               (int(cx), int(cy)), int(r * 0.4))
            pygame.draw.circle(self.screen, (100, 255, 180),
                               (int(cx), int(cy)), int(r * 0.25))
        elif sk == "paradox":
            # 逆悖突进：悖论之力·紫黑扭曲空间 + 裂隙闪电 + 暗能漩涡
            pulse = 1.0 + 0.2 * math.sin(t * 5)
            g0 = get_glow(r * 3.8 * pulse, (200, 100, 255), alpha=110)
            self.screen.blit(g0, g0.get_rect(center=(int(cx), int(cy))),
                             special_flags=pygame.BLEND_RGB_ADD)
            # 暗能漩涡：3 层旋转扭曲环
            for li in range(3):
                rr = r + 14 + li * 8
                rect = pygame.Rect(0, 0, int(rr * 2), int(rr * 2))
                rect.center = (int(cx), int(cy))
                col_v = [(160, 60, 220), (200, 100, 255), (240, 180, 255)][li]
                pygame.draw.arc(self.screen, col_v, rect,
                                t * (2 + li) + li, t * (2 + li) + li + 3.5, 3)
            # 裂隙闪电（4 道随机锯齿线）
            for i in range(4):
                a = t * 3 + i * (math.tau / 4)
                seg_n = 5
                prev_x, prev_y = cx, cy
                for si in range(1, seg_n + 1):
                    dist = r + 10 + si * 8
                    jitter = random.uniform(-6, 6)
                    px = cx + math.cos(a) * dist + jitter
                    py = cy + math.sin(a) * dist + jitter
                    pygame.draw.line(self.screen, (220, 160, 255),
                                     (int(prev_x), int(prev_y)), (int(px), int(py)), 2)
                    prev_x, prev_y = px, py
            # 暗核（紫黑色脉动球）
            pygame.draw.circle(self.screen, (60, 20, 80),
                               (int(cx), int(cy)), int(r * 0.45))
            pygame.draw.circle(self.screen, (200, 100, 255),
                               (int(cx), int(cy)), int(r * 0.28))
            pygame.draw.circle(self.screen, (255, 220, 255),
                               (int(cx), int(cy)), int(r * 0.12))
        elif sk == "finality":
            # 终焉：毁灭之力·血红黑末日光环 + 死亡镰刀影 + 灭世黑核
            pulse = 1.0 + 0.25 * math.sin(t * 3)
            g0 = get_glow(r * 4.2 * pulse, (255, 30, 30), alpha=130)
            self.screen.blit(g0, g0.get_rect(center=(int(cx), int(cy))),
                             special_flags=pygame.BLEND_RGB_ADD)
            # 末日血环：3 层旋转血色弧
            for li in range(3):
                rr = r + 12 + li * 10
                rect = pygame.Rect(0, 0, int(rr * 2), int(rr * 2))
                rect.center = (int(cx), int(cy))
                col_r = [(180, 20, 20), (220, 40, 40), (255, 80, 80)][li]
                pygame.draw.arc(self.screen, col_r, rect,
                                -t * (1.5 + li * 0.5) + li, -t * (1.5 + li * 0.5) + li + 4, 3)
            # 死亡镰刀影（2 把旋转暗影镰刀）
            for i in range(2):
                a = t * 1.5 + i * math.pi
                scythe_r = r + 30
                # 镰刀弧
                for k in range(6):
                    ka = a + (k - 3) * 0.12
                    kx = cx + math.cos(ka) * (scythe_r + k * 3)
                    ky = cy + math.sin(ka) * (scythe_r + k * 3)
                    pygame.draw.circle(self.screen, (255, 50, 50),
                                       (int(kx), int(ky)), 5 - k // 2)
                # 镰刀柄
                pygame.draw.line(self.screen, (120, 20, 20),
                                 (int(cx), int(cy)),
                                 (int(cx + math.cos(a) * scythe_r),
                                  int(cy + math.sin(a) * scythe_r)), 2)
            # 灭世黑核（血红黑三层）
            pygame.draw.circle(self.screen, (40, 0, 0),
                               (int(cx), int(cy)), int(r * 0.5))
            pygame.draw.circle(self.screen, (200, 20, 20),
                               (int(cx), int(cy)), int(r * 0.32))
            pygame.draw.circle(self.screen, (255, 100, 100),
                               (int(cx), int(cy)), int(r * 0.15))

    def _draw_chaos_swords(self, p, ox, oy):
        """混沌六剑：6 把长剑环绕球体，有砍击感。"""
        cx, cy = p.x + ox, p.y + oy
        t = pygame.time.get_ticks() * 0.001
        r = p.r
        sword_r = r + 60
        # 剑刃长度
        for i in range(6):
            # 旋转 + 前后摆动
            base_a = t * 1.8 + i * (math.tau / 6)
            swing = 12 * math.sin(t * 6 + i * 1.1)
            # 剑柄
            hilt_r = r + 18
            hx = cx + math.cos(base_a) * hilt_r
            hy = cy + math.sin(base_a) * hilt_r
            # 剑尖
            tip_r = sword_r + swing
            tx = cx + math.cos(base_a) * tip_r
            ty = cy + math.sin(base_a) * tip_r
            # 剑身渐变光
            sword_col1 = (255, 240, 200)
            sword_col2 = (200, 80, 255)
            pygame.draw.line(self.screen, sword_col2,
                             (int(hx), int(hy)), (int(tx), int(ty)), 6)
            pygame.draw.line(self.screen, sword_col1,
                             (int(hx), int(hy)), (int(tx), int(ty)), 2)
            # 护手
            perp_a = base_a + math.tau / 4
            gx1 = hx + math.cos(perp_a) * 8
            gy1 = hy + math.sin(perp_a) * 8
            gx2 = hx - math.cos(perp_a) * 8
            gy2 = hy - math.sin(perp_a) * 8
            pygame.draw.line(self.screen, (180, 150, 80),
                             (int(gx1), int(gy1)), (int(gx2), int(gy2)), 3)
        # 六剑倒计时
        self._text(f"六剑 {p._chaos_sword_timer:.1f}s", cx, cy - sword_r - 16,
                   12, (255, 240, 200), center=True, bold=True)

    def _draw_chaos_hook(self, p, ox, oy):
        """混沌钩子：动态绳索（正弦波形摆动）+ 旋转钩尖 + 脉动光晕。"""
        h = p._chaos_hook
        if h is None:
            return
        cx, cy = p.x + ox, p.y + oy
        hx, hy = h["x"] + ox, h["y"] + oy
        # 方向与时间
        a = math.atan2(hy - cy, hx - cx)
        perp_a = a + math.pi / 2
        t = h["t"]
        # 动态锁链：沿路径画节点，带正弦波形摆动（垂直于连接方向）
        steps = 16
        dist = math.hypot(hx - cx, hy - cy)
        wave_amp = 10 + 3 * math.sin(t * 6.0)  # 振幅脉动
        for i in range(steps):
            tt = i / (steps - 1)
            # 基础位置
            bx = cx + (hx - cx) * tt
            by = cy + (hy - cy) * tt
            # 正弦偏移（两端振幅为0，中间最大）
            wave = math.sin(tt * math.pi) * math.sin(tt * 2 * math.pi + t * 4.5) * wave_amp
            nx = bx + math.cos(perp_a) * wave
            ny = by + math.sin(perp_a) * wave
            col = (200, 160, 70) if i % 2 == 0 else (140, 110, 50)
            pygame.draw.circle(self.screen, col, (int(nx), int(ny)), 2 if i % 2 == 0 else 3)
        # 旋转钩尖（动态旋转钩爪）
        spin = t * 5.0 if h["phase"] != 2 else t * 9.0
        hook_r = 7
        # 脉动光晕
        pulse = 1.0 + 0.25 * math.sin(t * 10.0)
        head_col = (220, 90, 255) if h["phase"] == 2 else (255, 240, 200)
        glow_sz = int(26 * pulse)
        g = get_glow(glow_sz, head_col, alpha=180 if h["phase"] == 2 else 140)
        self.screen.blit(g, g.get_rect(center=(int(hx), int(hy))),
                         special_flags=pygame.BLEND_RGB_ADD)
        pygame.draw.circle(self.screen, head_col, (int(hx), int(hy)), hook_r)
        pygame.draw.circle(self.screen, WHITE, (int(hx), int(hy)), hook_r, 2)
        # 4 个钩尖围绕钩头旋转（形成旋转的攻击感）
        for k in range(4):
            ang = a + spin + k * (math.pi / 2)
            tip_len = 12 if k % 2 == 0 else 8
            tx = hx + math.cos(ang) * tip_len
            ty = hy + math.sin(ang) * tip_len
            tip_col = (255, 160, 255) if h["phase"] == 2 else (255, 240, 200)
            pygame.draw.line(self.screen, tip_col,
                             (int(hx), int(hy)),
                             (int(tx), int(ty)), 2)
            # 小尖端
            sub = ang + 0.4
            pygame.draw.line(self.screen, tip_col,
                             (int(tx), int(ty)),
                             (int(tx + math.cos(sub - 2.1) * 4),
                              int(ty + math.sin(sub - 2.1) * 4)), 2)
        # 吸血时红光效果
        if h["phase"] == 2:
            self._text("吸血中", hx, hy - 32, 14,
                       (255, 80, 80), center=True, bold=True)
            # 血粒子沿绳索飘向玩家
            for kk in range(2):
                bt = (t * 1.2 + kk * 0.5) % 1.0
                bbx = cx + (hx - cx) * (1.0 - bt)
                bby = cy + (hy - cy) * (1.0 - bt)
                bwave = math.sin(bt * math.pi) * math.sin(bt * math.pi * 2 + t * 4.5) * wave_amp * 0.6
                bbx += math.cos(perp_a) * bwave
                bby += math.sin(perp_a) * bwave
                gg = get_glow(8, (255, 60, 60), alpha=150)
                self.screen.blit(gg, gg.get_rect(center=(int(bbx), int(bby))),
                                 special_flags=pygame.BLEND_RGB_ADD)

    def _draw_chaos_hp(self, p, ox, oy):
        """混沌魔神 5 格血条。"""
        cx, cy = p.x + ox, p.y + oy
        r = p.r
        total = 5
        hp = max(1, min(total, p._chaos_hp))
        cell_w = 16
        gap = 2
        total_w = total * cell_w + (total - 1) * gap
        start_x = cx - total_w // 2
        y = cy - r - 26
        for i in range(total):
            x = start_x + i * (cell_w + gap)
            rect = pygame.Rect(x, y, cell_w, 7)
            if i < hp:
                pygame.draw.rect(self.screen, (255, 70, 70), rect, border_radius=2)
                pygame.draw.rect(self.screen, (255, 180, 180), rect, 1, border_radius=2)
            else:
                pygame.draw.rect(self.screen, (60, 60, 80), rect, border_radius=2)
                pygame.draw.rect(self.screen, (100, 100, 120), rect, 1, border_radius=2)

    # ---- 敌方球：4 种强度外观（凶恶邪恶风） ----
    def _draw_enemy(self, s, ox, oy, r_draw, eatable):
        cx, cy = s.x + ox, s.y + oy
        base = s.color
        # 邪恶暗光：危险血红光晕；可吃时改为翠绿（不再像太阳）
        evil_glow = (255, 40, 60) if not eatable else (90, 255, 130)
        col = base if not eatable else (130, 230, 150)
        tier = s.tier
        # 主体（更暗的实体 + 邪光）
        pygame.draw.circle(self.screen, (6, 4, 8), (int(cx), int(cy)), int(r_draw))
        eg = get_glow(r_draw * 1.9, evil_glow, alpha=150)
        self.screen.blit(eg, eg.get_rect(center=(int(cx), int(cy))),
                         special_flags=pygame.BLEND_RGB_ADD)
        pygame.draw.circle(self.screen, col, (int(cx), int(cy)), int(r_draw * 0.92))
        # 暗色边缘
        pygame.draw.circle(self.screen, (20, 6, 12), (int(cx), int(cy)), int(r_draw), 2)
        # 可吃高亮：绿色虚环（区别于正义太阳）
        if eatable:
            seg = 16
            for i in range(seg):
                if i % 2 == 0:
                    a0 = s.phase + i * (math.tau / seg)
                    a1 = a0 + (math.tau / seg) * 0.5
                    p0 = (cx + math.cos(a0) * (r_draw + 4), cy + math.sin(a0) * (r_draw + 4))
                    p1 = (cx + math.cos(a1) * (r_draw + 4), cy + math.sin(a1) * (r_draw + 4))
                    pygame.draw.line(self.screen, (130, 255, 150), p0, p1, 2)
        # 邪恶尖刺：不规则、参差
        n_spikes = [7, 9, 11, 13][tier]
        spike_len = [1.3, 1.45, 1.55, 1.7][tier]
        sw = [2, 2, 3, 3][tier]
        for i in range(n_spikes):
            # 参差不齐的刺长
            jitter = 0.78 + 0.4 * ((i * 37 % 7) / 7.0)
            a = s.phase + i * (math.tau / n_spikes)
            L = r_draw * spike_len * jitter
            x1 = cx + math.cos(a) * r_draw * 0.98
            y1 = cy + math.sin(a) * r_draw * 0.98
            x2 = cx + math.cos(a) * L
            y2 = cy + math.sin(a) * L
            pygame.draw.line(self.screen, col, (x1, y1), (x2, y2), sw)
            # 刺尖暗红点
            pygame.draw.circle(self.screen, (255, 60, 60), (int(x2), int(y2)), max(1, sw))
        # 邪恶之眼（所有等级都有，等级越高越凶）
        eye_r = max(2, r_draw * (0.10 + 0.04 * tier))
        ex = cx + math.cos(s.phase * 0.8) * r_draw * 0.25
        ey = cy + math.sin(s.phase * 0.8) * r_draw * 0.18
        pygame.draw.circle(self.screen, (255, 220, 60), (int(ex), int(ey)), int(eye_r))
        pygame.draw.circle(self.screen, (0, 0, 0), (int(ex), int(ey)), max(1, int(eye_r * 0.5)))
        # 等级 2+：断裂邪环
        if tier >= 2:
            ring_r = r_draw + 9
            seg = 14
            for i in range(seg):
                if i % 2 == 0:
                    a0 = s.phase * 0.7 + i * (math.tau / seg)
                    a1 = a0 + (math.tau / seg) * 0.6
                    p0 = (cx + math.cos(a0) * ring_r, cy + math.sin(a0) * ring_r)
                    p1 = (cx + math.cos(a1) * ring_r, cy + math.sin(a1) * ring_r)
                    pygame.draw.line(self.screen, (160, 30, 60), p0, p1, 2)
        # 等级 3：深渊血核 + 黑紫外环
        if tier >= 3:
            ring2 = r_draw + 16
            pygame.draw.circle(self.screen, (40, 0, 20), (int(cx), int(cy)), int(ring2), 1)
            core_r = max(2, r_draw * 0.32 * (1 + 0.25 * math.sin(s.phase * 4)))
            pygame.draw.circle(self.screen, (255, 30, 40), (int(cx), int(cy)), int(core_r))
            g = get_glow(core_r * 3.2, (255, 20, 40), alpha=170)
            self.screen.blit(g, g.get_rect(center=(int(cx), int(cy))),
                             special_flags=pygame.BLEND_RGB_ADD)
        # ---- 种族特化外观 ----
        kind = getattr(s, "kind", "spike")
        if kind == "virus":
            # 病毒：蛋白质壳上的绿色Knob突起
            kn = 8
            for i in range(kn):
                a = s.sub_phase + i * (math.tau / kn)
                kx = cx + math.cos(a) * r_draw * 0.82
                ky = cy + math.sin(a) * r_draw * 0.82
                pygame.draw.line(self.screen, (40, 120, 50),
                                 (cx + math.cos(a) * r_draw * 0.55, cy + math.sin(a) * r_draw * 0.55),
                                 (kx, ky), 2)
                pygame.draw.circle(self.screen, (120, 255, 140), (int(kx), int(ky)),
                                   max(2, int(r_draw * 0.13)))
        elif kind == "tri":
            # 三球体：3 颗卫星球绕核心 120° 旋转
            orb_r = max(3, r_draw * 0.34)
            orbit = r_draw * 0.62
            for i in range(3):
                a = s.sub_phase + i * (math.tau / 3)
                ox2 = cx + math.cos(a) * orbit
                oy2 = cy + math.sin(a) * orbit
                og = get_glow(orb_r * 2.0, (180, 80, 255), alpha=120)
                self.screen.blit(og, og.get_rect(center=(int(ox2), int(oy2))),
                                 special_flags=pygame.BLEND_RGB_ADD)
                pygame.draw.circle(self.screen, (170, 90, 230), (int(ox2), int(oy2)), int(orb_r))
                pygame.draw.circle(self.screen, (240, 200, 255), (int(ox2), int(oy2)), int(orb_r), 1)
        elif kind == "dual":
            # 双球体：2 颗较大球体绕中心旋转
            orb_r = max(3, r_draw * 0.5)
            orbit = r_draw * 0.42
            for i in range(2):
                a = s.sub_phase + i * math.pi
                ox2 = cx + math.cos(a) * orbit
                oy2 = cy + math.sin(a) * orbit
                og = get_glow(orb_r * 1.8, (255, 150, 60), alpha=130)
                self.screen.blit(og, og.get_rect(center=(int(ox2), int(oy2))),
                                 special_flags=pygame.BLEND_RGB_ADD)
                pygame.draw.circle(self.screen, (220, 130, 50), (int(ox2), int(oy2)), int(orb_r))
                pygame.draw.circle(self.screen, (255, 220, 160), (int(ox2), int(oy2)), int(orb_r), 1)
        elif kind == "worm":
            # 虫群：长条虫身（从尾到头由细到粗），头部带邪眼
            seg_r = max(3, r_draw * 0.55)
            n = len(s.segments)
            for i in range(n - 1, -1, -1):
                sx, sy = s.segments[i]
                # 由尾到头逐渐变粗
                t_ratio = 1.0 - i / max(1, n)  # 0=尾 1=头
                rr = max(2, seg_r * (0.5 + 0.5 * t_ratio))
                sg = get_glow(rr * 1.6, (100, 220, 90), alpha=110)
                self.screen.blit(sg, sg.get_rect(center=(int(sx + ox), int(sy + oy))),
                                 special_flags=pygame.BLEND_RGB_ADD)
                pygame.draw.circle(self.screen, (60, 160, 70),
                                   (int(sx + ox), int(sy + oy)), int(rr))
                pygame.draw.circle(self.screen, (180, 255, 180),
                                   (int(sx + ox), int(sy + oy)), int(rr), 1)
            # 头部邪眼
            eye_r = max(2, r_draw * 0.18)
            ex = cx + math.cos(s.phase * 1.2) * r_draw * 0.3
            ey = cy + math.sin(s.phase * 1.2) * r_draw * 0.22
            pygame.draw.circle(self.screen, (255, 80, 80), (int(ex), int(ey)), int(eye_r))
            pygame.draw.circle(self.screen, (0, 0, 0), (int(ex), int(ey)), max(1, int(eye_r * 0.5)))
        elif kind == "snake":
            # 长蛇多球节：每一节都是独立的 Star，在自己的 draw_star 中分别绘制
            # 这里只绘制节的外观：带斑点+蛇信（仅蛇头）+蛇鳞高光
            # 底色：s.color 是链的基色，节越靠后越偏深
            chain = getattr(s, "snake_chain", None)
            # 节的位置索引：0=蛇头
            if chain is not None and s in chain:
                idx = chain.index(s)
                total = max(1, len(chain))
                # 从蛇头到蛇尾逐渐偏深
                shade = 1.0 - idx / total * 0.45
                cbase = tuple(max(0, min(255, int(c * shade))) for c in s.color)
            else:
                cbase = s.color
            # 发光
            glow = get_glow(r_draw * 2.2, cbase, alpha=110)
            self.screen.blit(glow, glow.get_rect(center=(int(cx), int(cy))),
                             special_flags=pygame.BLEND_RGB_ADD)
            pygame.draw.circle(self.screen, cbase, (int(cx), int(cy)), int(r_draw))
            # 蛇鳞：每节上方 3 个暗斑
            sc = tuple(max(0, min(255, int(c * 0.55))) for c in cbase)
            for ang_off in (-0.6, 0, 0.6):
                a_ = s.phase * 0.6 + ang_off
                sdx = cx + math.cos(a_) * r_draw * 0.38
                sdy = cy + math.sin(a_) * r_draw * 0.38
                pygame.draw.circle(self.screen, sc, (int(sdx), int(sdy)), max(1, int(r_draw * 0.18)))
            pygame.draw.circle(self.screen, (255, 255, 255), (int(cx), int(cy)), int(r_draw), 1)
            # 蛇头额外：画蛇信 + 双眼
            if getattr(s, "snake_head_flag", False):
                # 双眼
                vr = max(2, r_draw * 0.18)
                ph = s.phase
                e1x = cx + math.cos(ph - 0.55) * r_draw * 0.55
                e1y = cy + math.sin(ph - 0.55) * r_draw * 0.55
                e2x = cx + math.cos(ph + 0.55) * r_draw * 0.55
                e2y = cy + math.sin(ph + 0.55) * r_draw * 0.55
                for (ex_, ey_) in ((e1x, e1y), (e2x, e2y)):
                    pygame.draw.circle(self.screen, (255, 255, 255), (int(ex_), int(ey_)), int(vr))
                    pygame.draw.circle(self.screen, (30, 10, 10), (int(ex_), int(ey_)), max(1, int(vr * 0.6)))
                # 蛇信（分叉）
                tng_ang = math.atan2(s.vy, s.vx) if math.hypot(s.vx, s.vy) > 1e-3 else ph
                tong_len = r_draw * 0.8
                tx1 = cx + math.cos(tng_ang) * tong_len * 1.02
                ty1 = cy + math.sin(tng_ang) * tong_len * 1.02
                # 分叉
                fork_a1 = tng_ang + 0.35
                fork_a2 = tng_ang - 0.35
                fork_r = tong_len * 0.35
                pygame.draw.line(self.screen, (255, 60, 90),
                                 (int(cx + math.cos(tng_ang) * r_draw * 0.95),
                                  int(cy + math.sin(tng_ang) * r_draw * 0.95)),
                                 (int(tx1), int(ty1)), max(1, int(r_draw * 0.12)))
                pygame.draw.line(self.screen, (255, 60, 90),
                                 (int(tx1), int(ty1)),
                                 (int(tx1 + math.cos(fork_a1) * fork_r),
                                  int(ty1 + math.sin(fork_a1) * fork_r)),
                                 max(1, int(r_draw * 0.1)))
                pygame.draw.line(self.screen, (255, 60, 90),
                                 (int(tx1), int(ty1)),
                                 (int(tx1 + math.cos(fork_a2) * fork_r),
                                  int(ty1 + math.sin(fork_a2) * fork_r)),
                                 max(1, int(r_draw * 0.1)))
        elif kind == "horror":
            # c7：恐怖外形敌人（血红骷髅脸 + 双牛角 + 嘴部尖牙 + 黑紫气息）
            # 底色：暗血红
            base_col = (120, 0, 20)
            dark_col = (60, 0, 10)
            pygame.draw.circle(self.screen, base_col, (int(cx), int(cy)), int(r_draw))
            pygame.draw.circle(self.screen, (200, 30, 40), (int(cx), int(cy)), int(r_draw), 2)
            # 外圈黑紫气息（呼吸脉动）
            t = pygame.time.get_ticks() * 0.003
            aura = 1.0 + 0.08 * math.sin(t * 3.2)
            g = get_glow(r_draw * 3.4 * aura, (50, 0, 60), alpha=150)
            self.screen.blit(g, g.get_rect(center=(int(cx), int(cy))),
                             special_flags=pygame.BLEND_RGB_ADD)
            # 双牛角（从额头两侧向上）
            horn_L_ang = s.phase - 2.1
            horn_R_ang = s.phase - 1.04
            horn_base = r_draw * 0.92
            horn_len = r_draw * 1.15
            # 左牛角
            hl_bx = cx + math.cos(horn_L_ang) * horn_base
            hl_by = cy + math.sin(horn_L_ang) * horn_base
            hl_tx = cx + math.cos(horn_L_ang) * (horn_base + horn_len)
            hl_ty = cy + math.sin(horn_L_ang) * (horn_base + horn_len)
            pygame.draw.line(self.screen, (110, 80, 30),
                             (int(hl_bx), int(hl_by)), (int(hl_tx), int(hl_ty)), max(2, int(r_draw * 0.22)))
            pygame.draw.line(self.screen, (190, 150, 60),
                             (int(hl_bx), int(hl_by)), (int(hl_tx), int(hl_ty)), max(1, int(r_draw * 0.08)))
            # 右牛角
            hr_bx = cx + math.cos(horn_R_ang) * horn_base
            hr_by = cy + math.sin(horn_R_ang) * horn_base
            hr_tx = cx + math.cos(horn_R_ang) * (horn_base + horn_len)
            hr_ty = cy + math.sin(horn_R_ang) * (horn_base + horn_len)
            pygame.draw.line(self.screen, (110, 80, 30),
                             (int(hr_bx), int(hr_by)), (int(hr_tx), int(hr_ty)), max(2, int(r_draw * 0.22)))
            pygame.draw.line(self.screen, (190, 150, 60),
                             (int(hr_bx), int(hr_by)), (int(hr_tx), int(hr_ty)), max(1, int(r_draw * 0.08)))
            # 骷髅脸眼窝（两个大黑洞）
            eye_r = max(2, int(r_draw * 0.26))
            ex_ = s.phase * 0.35
            ey_ = s.phase * 0.25
            e1x = cx + math.cos(-0.9 + ex_) * r_draw * 0.42
            e1y = cy + math.sin(-0.3 + ey_) * r_draw * 0.30
            e2x = cx + math.cos(0.9 + ex_) * r_draw * 0.42
            e2y = cy + math.sin(-0.3 + ey_) * r_draw * 0.30
            for (ex_i, ey_i) in ((e1x, e1y), (e2x, e2y)):
                # 黑洞眼窝
                pygame.draw.circle(self.screen, dark_col, (int(ex_i), int(ey_i)), int(eye_r))
                # 中央燃烧红点
                flame = 0.6 + 0.4 * math.sin(t * 9 + ex_i)
                g2 = get_glow(eye_r * 2.2 * flame, (255, 50, 40), alpha=180)
                self.screen.blit(g2, g2.get_rect(center=(int(ex_i), int(ey_i))),
                                 special_flags=pygame.BLEND_RGB_ADD)
                pygame.draw.circle(self.screen, (255, 100, 60), (int(ex_i), int(ey_i)),
                                   max(1, int(eye_r * 0.5)))
            # 骷髅鼻（倒三角）
            nose_r = max(1, int(r_draw * 0.10))
            pygame.draw.polygon(self.screen, dark_col, [
                (int(cx - nose_r), int(cy + r_draw * 0.05)),
                (int(cx + nose_r), int(cy + r_draw * 0.05)),
                (int(cx), int(cy + r_draw * 0.25)),
            ])
            # 嘴部尖牙（上颚一排白色尖牙 + 下颚暗色尖牙，交错 6 颗）
            mouth_w = r_draw * 0.72
            teeth_top_y = cy + r_draw * 0.42
            teeth_bot_y = cy + r_draw * 0.66
            n_teeth = 6
            for j in range(n_teeth):
                tx_ = cx - mouth_w / 2 + (j + 0.5) * (mouth_w / n_teeth)
                # 上牙向下
                pygame.draw.polygon(self.screen, (255, 250, 230), [
                    (int(tx_ - r_draw * 0.05), int(teeth_top_y)),
                    (int(tx_ + r_draw * 0.05), int(teeth_top_y)),
                    (int(tx_), int(teeth_top_y + r_draw * 0.18)),
                ])
                # 下牙向上（交错位置）
                bx_ = cx - mouth_w / 2 + (j + 0.0) * (mouth_w / n_teeth)
                pygame.draw.polygon(self.screen, (230, 220, 190), [
                    (int(bx_ - r_draw * 0.045), int(teeth_bot_y)),
                    (int(bx_ + r_draw * 0.045), int(teeth_bot_y)),
                    (int(bx_), int(teeth_bot_y - r_draw * 0.16)),
                ])
            # 嘴部暗色底色（在牙齿后面）
            pygame.draw.rect(self.screen, (20, 0, 6),
                             (int(cx - mouth_w / 2 + r_draw * 0.03),
                              int(teeth_top_y + 1),
                              int(mouth_w - r_draw * 0.06),
                              int(teeth_bot_y - teeth_top_y - 1)))
            # 血滴从嘴角滑落（动态向下流动）
            drip_t = (t * 0.8) % 1.0
            for corner_dx in (-r_draw * 0.38, r_draw * 0.38):
                dcy = cy + r_draw * 0.55 + drip_t * r_draw * 0.7
                if dcy < cy + r_draw * 1.3:
                    pygame.draw.circle(self.screen, (200, 30, 40),
                                       (int(cx + corner_dx), int(dcy)),
                                       max(1, int(r_draw * 0.08)))
            # 周围飘出黑紫气息粒子
            if random.random() < 0.4:
                pa = random.uniform(0, math.tau)
                pr_ = r_draw + 5
                pvx = math.cos(pa) * random.uniform(10, 40)
                pvy = math.sin(pa) * random.uniform(10, 40) - 20
                self.particles.append((cx + math.cos(pa) * pr_,
                                       cy + math.sin(pa) * pr_,
                                       pvx, pvy, 0.5,
                                       (70, 10, 90), 2.6))
        # ===== t7：新增 6 种反派球体外观 =====
        elif kind == "spider":
            # 黑紫蜘蛛：8 条长毛腿 + 红眼 + 腹部斑纹 + 毒腺点
            body_col = (50, 10, 40)
            hair_col = (90, 20, 70)
            pygame.draw.circle(self.screen, body_col, (int(cx), int(cy)), int(r_draw))
            pygame.draw.circle(self.screen, (110, 40, 90), (int(cx), int(cy)), int(r_draw), 2)
            # 8 条长腿（每腿带关节毛）
            leg_len = r_draw * 1.55
            for i in range(8):
                a_base = s.phase * 0.6 + i * (math.tau / 8)
                # 腿的分段：先外再内画两次不同色
                for (mul, col_, sw_) in ((1.55, hair_col, 2), (1.55, (230, 230, 230), 1)):
                    la = a_base
                    # 外关节弯
                    mid_a = la + (0.25 if i % 2 == 0 else -0.25)
                    mid_x = cx + math.cos(mid_a) * (r_draw * 0.95)
                    mid_y = cy + math.sin(mid_a) * (r_draw * 0.95)
                    tip_x = cx + math.cos(la) * leg_len
                    tip_y = cy + math.sin(la) * leg_len
                    pygame.draw.line(self.screen, col_, (int(cx), int(cy)),
                                     (int(mid_x), int(mid_y)), sw_)
                    pygame.draw.line(self.screen, col_, (int(mid_x), int(mid_y)),
                                     (int(tip_x), int(tip_y)), sw_)
                # 足尖毒腺红点
                tip_x = cx + math.cos(a_base) * leg_len
                tip_y = cy + math.sin(a_base) * leg_len
                pygame.draw.circle(self.screen, (255, 40, 40), (int(tip_x), int(tip_y)),
                                   max(1, int(r_draw * 0.09)))
            # 腹部斑纹（4 块对称黑段）
            for (a_off, rad) in ((-0.6, 0.28), (0.6, 0.28), (-1.6, 0.20), (1.6, 0.20)):
                bx = cx + math.cos(s.phase * 0.3 + a_off) * r_draw * 0.55
                by = cy + math.sin(s.phase * 0.3 + a_off) * r_draw * 0.45
                pygame.draw.circle(self.screen, (20, 0, 20), (int(bx), int(by)),
                                   max(1, int(r_draw * rad)))
            # 两颗凸出的红色大眼 + 黑色瞳孔
            ey_r = max(2, r_draw * 0.22)
            e1a = s.phase * 0.5 - 0.55
            e2a = s.phase * 0.5 + 0.55
            for ea in (e1a, e2a):
                eex = cx + math.cos(ea) * r_draw * 0.5
                eey = cy + math.sin(ea) * r_draw * 0.38
                g2 = get_glow(ey_r * 2.4, (255, 30, 30), alpha=190)
                self.screen.blit(g2, g2.get_rect(center=(int(eex), int(eey))),
                                 special_flags=pygame.BLEND_RGB_ADD)
                pygame.draw.circle(self.screen, (255, 50, 50), (int(eex), int(eey)), int(ey_r))
                pygame.draw.circle(self.screen, (0, 0, 0), (int(eex), int(eey)),
                                   max(1, int(ey_r * 0.55)))
        elif kind == "centipede":
            # 蜈蚣：12节长身 + 每节双毒腿 + 头部巨毒牙 + 黑边
            # 节身绘制（与 worm 类似，紫黑渐变）
            seg_r = max(3, r_draw * 0.55)
            n = len(s.segments)
            for i in range(n - 1, -1, -1):
                sx_, sy_ = s.segments[i]
                t_ratio = 1.0 - i / max(1, n)
                rr = max(2, seg_r * (0.55 + 0.45 * t_ratio))
                # 底色紫 + 每节描黑边
                cbg = (150, 20, 170) if i % 2 == 0 else (90, 10, 110)
                sg = get_glow(rr * 1.7, cbg, alpha=100)
                self.screen.blit(sg, sg.get_rect(center=(int(sx_ + ox), int(sy_ + oy))),
                                 special_flags=pygame.BLEND_RGB_ADD)
                pygame.draw.circle(self.screen, cbg,
                                   (int(sx_ + ox), int(sy_ + oy)), int(rr))
                pygame.draw.circle(self.screen, (20, 0, 25),
                                   (int(sx_ + ox), int(sy_ + oy)), int(rr), 1)
                # 每节两条毒腿（交替方向）
                leg_len = rr * 1.2
                for dir_ in (-1, 1):
                    la_ = s.phase + (1.0 if i % 2 == 0 else -1.0) * 0.25
                    off_x = math.cos(la_ + dir_ * math.pi / 2) * rr * 0.8
                    off_y = math.sin(la_ + dir_ * math.pi / 2) * rr * 0.8
                    tipx = sx_ + ox + math.cos(la_ + dir_ * math.pi / 2) * leg_len * 1.35
                    tipy = sy_ + oy + math.sin(la_ + dir_ * math.pi / 2) * leg_len * 1.35
                    pygame.draw.line(self.screen, (255, 220, 40),
                                     (int(sx_ + ox + off_x), int(sy_ + oy + off_y)),
                                     (int(tipx), int(tipy)), 2)
            # 头部：两颗毒牙 + 红眼
            head_x, head_y = (s.segments[0] if s.segments else (cx, cy))
            hx = head_x + ox; hy = head_y + oy
            fang_r = max(2, r_draw * 0.16)
            # 两颗外伸毒牙
            for fdir_ in (-0.35, 0.35):
                tx_ = hx + math.cos(s.phase + fdir_) * (r_draw * 1.15)
                ty_ = hy + math.sin(s.phase + fdir_) * (r_draw * 1.15)
                pygame.draw.polygon(self.screen, (255, 255, 180), [
                    (int(hx + math.cos(s.phase + fdir_) * r_draw * 0.8),
                     int(hy + math.sin(s.phase + fdir_) * r_draw * 0.8)),
                    (int(hx + math.cos(s.phase + fdir_ + 0.12) * r_draw * 0.8),
                     int(hy + math.sin(s.phase + fdir_ + 0.12) * r_draw * 0.8)),
                    (int(tx_), int(ty_)),
                ])
            # 红眼
            pygame.draw.circle(self.screen, (255, 60, 60),
                               (int(hx - r_draw * 0.28), int(hy - r_draw * 0.18)),
                               int(max(1, fang_r)))
            pygame.draw.circle(self.screen, (255, 60, 60),
                               (int(hx + r_draw * 0.28), int(hy - r_draw * 0.18)),
                               int(max(1, fang_r)))
        elif kind == "ghost":
            # 幽灵：半透明球 + 鬼脸（黑洞眼+下垂舌）+ 寒气粒子 + 飘动感
            t2 = pygame.time.get_ticks() * 0.0025
            # 半透明覆盖（BLEND_PREMULTIPLIED 兼容）
            sf = pygame.Surface((int(r_draw * 5), int(r_draw * 5)), pygame.SRCALPHA)
            sf_cx = int(r_draw * 2.5)
            sf_cy = int(r_draw * 2.5)
            a_ = 180 + int(20 * math.sin(t2 * 4))
            pygame.draw.circle(sf, (235, 245, 255, a_), (sf_cx, sf_cy - int(r_draw * 0.2)), int(r_draw * 1.05))
            # 飘动感：下方波浪形"裙摆"
            skirt_y = sf_cy + int(r_draw * 0.55)
            for k in range(8):
                sway = int(math.sin(t2 * 2.5 + k * 0.6) * r_draw * 0.15)
                pygame.draw.polygon(sf, (235, 245, 255, max(100, a_ - 50)), [
                    (sf_cx - int(r_draw * 1.0) + k * int(r_draw * 0.28), skirt_y),
                    (sf_cx - int(r_draw * 0.86) + k * int(r_draw * 0.28), skirt_y + int(r_draw * 0.6) + sway),
                    (sf_cx - int(r_draw * 0.72) + k * int(r_draw * 0.28), skirt_y),
                ])
            # 黑洞眼
            for edx_ in (-r_draw * 0.36, r_draw * 0.36):
                pygame.draw.circle(sf, (10, 10, 30, 220),
                                   (int(sf_cx + edx_), int(sf_cy - r_draw * 0.05)),
                                   max(2, int(r_draw * 0.22)))
            # 大张嘴（下弯黑色大嘴）
            mouth_y = int(sf_cy + r_draw * 0.35)
            pygame.draw.arc(sf, (10, 10, 30, 220),
                            (sf_cx - int(r_draw * 0.45), mouth_y - int(r_draw * 0.2),
                             sf_cx + int(r_draw * 0.45), mouth_y + int(r_draw * 0.55)),
                            math.pi, math.tau, max(2, int(r_draw * 0.1)))
            # 下垂舌头（中间）
            tongue_l = r_draw * 0.55 + math.sin(t2 * 3.2) * r_draw * 0.08
            pygame.draw.rect(sf, (255, 120, 140, 210),
                             (int(sf_cx - r_draw * 0.08), mouth_y + 1,
                              max(2, int(r_draw * 0.16)), int(tongue_l)),
                             border_radius=3)
            self.screen.blit(sf, (int(cx) - int(r_draw * 2.5), int(cy) - int(r_draw * 2.5)),
                             special_flags=pygame.BLEND_PREMULTIPLIED)
            # 寒气粒子
            if random.random() < 0.45:
                pa2 = random.uniform(0, math.tau)
                self.particles.append(
                    (cx + math.cos(pa2) * r_draw * 0.85,
                     cy + math.sin(pa2) * r_draw * 0.85 - 10,
                     math.cos(pa2) * 15 - 5,
                     math.sin(pa2) * 15 - 35,
                     0.6, (180, 220, 255), 2.0))
        elif kind == "turtle":
            # 玄武龟：六边形甲壳 + 头 4 爪 尾 + 板纹（13块）
            t2 = pygame.time.get_ticks() * 0.0025
            pts = []
            shell_r = r_draw * 1.05
            for k in range(6):
                a_ = s.phase + k * math.pi / 3
                pts.append((int(cx + math.cos(a_) * shell_r),
                            int(cy + math.sin(a_) * shell_r)))
            shell_col = (40, 110, 70)
            shell_edge = (220, 220, 120)
            pygame.draw.polygon(self.screen, shell_col, pts)
            pygame.draw.polygon(self.screen, shell_edge, pts, 2)
            # 13 块板纹：中央1块 + 中圈6块 + 外圈6块
            # 中央
            pygame.draw.circle(self.screen, (30, 70, 45), (int(cx), int(cy)),
                               max(1, int(r_draw * 0.32)))
            # 中圈 6 块（较小）
            for k in range(6):
                a_ = s.phase + k * math.pi / 3 + math.pi / 6
                px2 = cx + math.cos(a_) * r_draw * 0.58
                py2 = cy + math.sin(a_) * r_draw * 0.58
                pygame.draw.circle(self.screen, (30, 70, 45),
                                   (int(px2), int(py2)), max(1, int(r_draw * 0.18)), 1)
            # 外圈 6 块（贴边）
            for k in range(6):
                a_ = s.phase + k * math.pi / 3
                px2 = cx + math.cos(a_) * r_draw * 0.88
                py2 = cy + math.sin(a_) * r_draw * 0.88
                pygame.draw.circle(self.screen, (20, 60, 40),
                                   (int(px2), int(py2)), max(1, int(r_draw * 0.12)))
            # 头：前方伸出来的黄头（方向=s.phase）
            head_a = s.phase
            head_r = r_draw * 0.45
            hx = cx + math.cos(head_a) * shell_r * 0.98
            hy = cy + math.sin(head_a) * shell_r * 0.98
            pygame.draw.circle(self.screen, (240, 220, 130), (int(hx), int(hy)), int(head_r))
            pygame.draw.circle(self.screen, (80, 60, 20), (int(hx), int(hy)), int(head_r), 1)
            # 头部两小眼
            for hea in (-0.3, 0.3):
                ex_ = hx + math.cos(head_a + hea) * head_r * 0.45
                ey_ = hy + math.sin(head_a + hea) * head_r * 0.45
                pygame.draw.circle(self.screen, (10, 10, 10),
                                   (int(ex_), int(ey_)), max(1, int(head_r * 0.18)))
            # 4 爪（四个对角）
            for (a_dir, flip) in ((head_a + math.pi/2 + 0.1, 1),
                                   (head_a - math.pi/2 - 0.1, 1),
                                   (head_a + math.pi - math.pi/2 + 0.1, -1),
                                   (head_a + math.pi + math.pi/2 - 0.1, -1)):
                lx = cx + math.cos(a_dir) * shell_r * 0.95
                ly = cy + math.sin(a_dir) * shell_r * 0.95
                for claw in (-0.2, 0, 0.2):
                    tip_a = a_dir + claw * 0.7
                    tx_ = lx + math.cos(tip_a) * r_draw * 0.45
                    ty_ = ly + math.sin(tip_a) * r_draw * 0.45
                    pygame.draw.line(self.screen, (200, 180, 90),
                                     (int(lx), int(ly)), (int(tx_), int(ty_)), 3)
            # 小尾巴（对头反向）
            tail_a = head_a + math.pi
            tbx = cx + math.cos(tail_a) * shell_r * 0.92
            tby = cy + math.sin(tail_a) * shell_r * 0.92
            ttx = cx + math.cos(tail_a) * (shell_r * 1.25 + r_draw * 0.25 * math.sin(t2 * 3 + s.phase))
            tty = cy + math.sin(tail_a) * (shell_r * 1.25 + r_draw * 0.25 * math.sin(t2 * 3 + s.phase))
            pygame.draw.line(self.screen, (160, 120, 60),
                             (int(tbx), int(tby)), (int(ttx), int(tty)), 3)
        elif kind == "oxdemon":
            # 牛魔王：巨大双弯牛角 + 鼻环 + 顶部红鬃毛 + 怒目横条 + 獠牙
            base_col = (150, 60, 30)
            pygame.draw.circle(self.screen, base_col, (int(cx), int(cy)), int(r_draw))
            pygame.draw.circle(self.screen, (240, 160, 100), (int(cx), int(cy)), int(r_draw), 2)
            # 双弯牛角（从额头两侧向上大弯）
            for sign_ in (-1, 1):
                horn_a = s.phase + sign_ * 0.9 - 1.2
                horn_seg = 10
                last_x, last_y = cx + math.cos(horn_a) * r_draw * 0.9, cy + math.sin(horn_a) * r_draw * 0.9
                for k in range(1, horn_seg + 1):
                    t_ = k / horn_seg
                    bend_a = horn_a + sign_ * t_ * 1.6
                    rr = r_draw * (0.9 + t_ * 1.25)
                    nx = cx + math.cos(bend_a) * rr
                    ny = cy + math.sin(bend_a) * rr * 0.95
                    thick = max(2, int(r_draw * 0.18 * (1 - t_ * 0.45)))
                    pygame.draw.line(self.screen, (220, 210, 170),
                                     (int(last_x), int(last_y)), (int(nx), int(ny)), thick)
                    pygame.draw.line(self.screen, (120, 100, 70),
                                     (int(last_x), int(last_y)), (int(nx), int(ny)), 1)
                    last_x, last_y = nx, ny
            # 顶部红鬃毛（一排尖刺毛）
            mane_a0 = s.phase - 1.7
            for k in range(8):
                ma = mane_a0 + k * (3.4 / 7)
                base_ma_x = cx + math.cos(ma) * r_draw * 0.92
                base_ma_y = cy + math.sin(ma) * r_draw * 0.92
                tip_ma_x = cx + math.cos(ma) * r_draw * 1.35
                tip_ma_y = cy + math.sin(ma) * r_draw * 1.35
                pygame.draw.line(self.screen, (230, 50, 40),
                                 (int(base_ma_x), int(base_ma_y)),
                                 (int(tip_ma_x), int(tip_ma_y)), 3)
            # 鼻环（银色大圆环）
            nr_x = cx + math.cos(s.phase - 0.05) * r_draw * 0.35
            nr_y = cy + math.sin(s.phase - 0.05) * r_draw * 0.42
            pygame.draw.circle(self.screen, (220, 220, 240),
                               (int(nr_x), int(nr_y)), max(2, int(r_draw * 0.28)), 2)
            # 怒目横条（红色长眼+黑瞳孔）
            for edx in (-r_draw * 0.35, r_draw * 0.35):
                ex3 = cx + edx
                ey3 = cy - r_draw * 0.18
                pygame.draw.rect(self.screen, (255, 60, 50),
                                 (int(ex3 - r_draw * 0.25), int(ey3 - r_draw * 0.09),
                                  max(4, int(r_draw * 0.5)), max(2, int(r_draw * 0.18))),
                                 border_radius=2)
                pygame.draw.rect(self.screen, (0, 0, 0),
                                 (int(ex3 - 3), int(ey3 - r_draw * 0.09),
                                  6, max(2, int(r_draw * 0.18))))
            # 獠牙（下牙向上两颗白色大牙）
            for tdx in (-r_draw * 0.28, r_draw * 0.28):
                tox = cx + tdx
                toy = cy + r_draw * 0.55
                pygame.draw.polygon(self.screen, (255, 250, 220), [
                    (int(tox - r_draw * 0.09), int(toy)),
                    (int(tox + r_draw * 0.09), int(toy)),
                    (int(tox), int(toy - r_draw * 0.5)),
                ])
            # 气息：牛魔火焰粒子
            if random.random() < 0.45:
                pa3 = random.uniform(-math.pi*0.8, -math.pi*0.2) + s.phase
                pr3 = r_draw + 4
                self.particles.append(
                    (cx + math.cos(pa3) * pr3, cy + math.sin(pa3) * pr3,
                     math.cos(pa3) * 25, math.sin(pa3) * 25 - 18,
                     0.55, (255, 120, 30), 2.6))
        elif kind == "fangshe":
            # 毒蛇 fangshe（单球）：毒牙+毒雾+竖瞳+蛇信
            g = get_glow(r_draw * 2.6, (160, 220, 30), alpha=120)
            self.screen.blit(g, g.get_rect(center=(int(cx), int(cy))),
                             special_flags=pygame.BLEND_RGB_ADD)
            pygame.draw.circle(self.screen, (160, 220, 30), (int(cx), int(cy)), int(r_draw))
            # 暗绿鳞片斑纹（5 片）
            for (a_off_, rad_) in ((0, 0.22), (-0.9, 0.18), (0.9, 0.18),
                                   (-1.9, 0.14), (1.9, 0.14)):
                spx = cx + math.cos(s.phase * 0.6 + a_off_) * r_draw * 0.55
                spy = cy + math.sin(s.phase * 0.6 + a_off_) * r_draw * 0.5
                pygame.draw.circle(self.screen, (80, 150, 20),
                                   (int(spx), int(spy)), max(1, int(r_draw * rad_)))
            pygame.draw.circle(self.screen, (255, 255, 255),
                               (int(cx), int(cy)), int(r_draw), 1)
            # 两颗毒牙（上下各两颗，黄色+白色）
            for (side, yoff, updown) in ((-1, -0.25, +1), (1, -0.25, +1),
                                         (-0.6, +0.3, -1), (0.6, +0.3, -1)):
                tx_ = cx + side * r_draw * 0.28
                ty_ = cy + yoff * r_draw
                tipx = tx_
                tipy = ty_ + updown * r_draw * 0.38
                pygame.draw.polygon(self.screen, (255, 255, 200), [
                    (int(tx_ - r_draw * 0.07), int(ty_)),
                    (int(tx_ + r_draw * 0.07), int(ty_)),
                    (int(tipx), int(tipy)),
                ])
            # 竖瞳血眼
            eye_r = max(2, int(r_draw * 0.22))
            for edx_ in (-r_draw * 0.38, r_draw * 0.38):
                ex_ = cx + edx_
                ey_ = cy - r_draw * 0.22
                pygame.draw.circle(self.screen, (255, 240, 240),
                                   (int(ex_), int(ey_)), eye_r)
                # 竖瞳（细长黑椭圆）
                pygame.draw.rect(self.screen, (10, 0, 0),
                                 (int(ex_ - max(1, r_draw * 0.05)),
                                  int(ey_ - eye_r * 0.7),
                                  max(2, int(r_draw * 0.1)), max(2, int(eye_r * 1.4))))
            # 蛇信（分叉）
            tng_a = math.atan2(s.vy, s.vx) if math.hypot(s.vx, s.vy) > 1e-3 else s.phase
            tong_len = r_draw * 0.95
            tx1 = cx + math.cos(tng_a) * r_draw * 1.05
            ty1 = cy + math.sin(tng_a) * r_draw * 1.05
            pygame.draw.line(self.screen, (255, 40, 90),
                             (int(cx + math.cos(tng_a) * r_draw * 0.92),
                              int(cy + math.sin(tng_a) * r_draw * 0.92)),
                             (int(tx1), int(ty1)), max(2, int(r_draw * 0.13)))
            for fa in (tng_a + 0.35, tng_a - 0.35):
                fx_ = tx1 + math.cos(fa) * r_draw * 0.32
                fy_ = ty1 + math.sin(fa) * r_draw * 0.32
                pygame.draw.line(self.screen, (255, 40, 90),
                                 (int(tx1), int(ty1)),
                                 (int(fx_), int(fy_)), max(1, int(r_draw * 0.1)))
            # 毒雾（绿色半透明粒子外溢）
            if random.random() < 0.45:
                pa4 = random.uniform(0, math.tau)
                pr4 = r_draw + 5
                self.particles.append(
                    (cx + math.cos(pa4) * pr4,
                     cy + math.sin(pa4) * pr4,
                     math.cos(pa4) * random.uniform(8, 28),
                     math.sin(pa4) * random.uniform(8, 28),
                     0.55, (120, 255, 80), 2.4))
        # 霜冻：敌人被冻结视觉（冰蓝色覆盖光晕 + 六角冰晶 + 十字冰裂纹）
        if getattr(s, "frozen_timer", 0) > 0:
            ft = s.frozen_timer
            # 外晕（越剩余时间越长越浓）
            ice_a = int(140 * min(1.0, ft / 1.2))
            g_ice = get_glow(r_draw * 2.8, (120, 220, 255), alpha=ice_a)
            self.screen.blit(g_ice, g_ice.get_rect(center=(int(cx), int(cy))),
                             special_flags=pygame.BLEND_RGB_ADD)
            # 冻结外圈厚边
            pygame.draw.circle(self.screen, (220, 240, 255), (int(cx), int(cy)),
                               int(r_draw + 3), 3)
            # 六角冰晶围绕（6 个方向 + 动态旋转）
            ice_rot = pygame.time.get_ticks() * 0.0012
            for k in range(6):
                a_ice = ice_rot + k * (math.tau / 6)
                ix2 = cx + math.cos(a_ice) * (r_draw + 7)
                iy2 = cy + math.sin(a_ice) * (r_draw + 7)
                # 冰晶短刺
                tx_ = cx + math.cos(a_ice) * (r_draw + 14)
                ty_ = cy + math.sin(a_ice) * (r_draw + 14)
                pygame.draw.line(self.screen, (200, 235, 255),
                                 (int(ix2), int(iy2)), (int(tx_), int(ty_)), 2)
                # 分岔小尖
                for fa_ in (a_ice + 0.35, a_ice - 0.35):
                    fx_ = tx_ + math.cos(fa_) * 5
                    fy_ = ty_ + math.sin(fa_) * 5
                    pygame.draw.line(self.screen, (180, 230, 255),
                                     (int(tx_), int(ty_)), (int(fx_), int(fy_)), 1)
            # 十字冰裂纹
            for ca_ in (0, math.pi / 2):
                L1x = cx - math.cos(ca_) * r_draw * 0.8
                L1y = cy - math.sin(ca_) * r_draw * 0.8
                L2x = cx + math.cos(ca_) * r_draw * 0.8
                L2y = cy + math.sin(ca_) * r_draw * 0.8
                pygame.draw.line(self.screen, (255, 255, 255),
                                 (int(L1x), int(L1y)), (int(L2x), int(L2y)), 1)
            # 左上角小冰粒（装饰）
            t_s = pygame.time.get_ticks() * 0.006
            for kk in range(4):
                a_s = t_s + kk * (math.tau / 4)
                px_ = cx + math.cos(a_s) * (r_draw * 0.45)
                py_ = cy + math.sin(a_s) * (r_draw * 0.45)
                pygame.draw.circle(self.screen, (220, 245, 255),
                                   (int(px_), int(py_)), max(1, int(r_draw * 0.12)))
            # 冻结剩余时间文字（仅冻结时间>0.8s时显示）
            if ft > 0.8 and r_draw >= 14:
                self._text(f"{ft:.1f}s", int(cx), int(cy - r_draw - 22),
                           13, (220, 240, 255), center=True, bold=True)
        # 受击闪白
        if getattr(s, "hit_flash", 0) > 0:
            fa = int(180 * (s.hit_flash / 0.18))
            flash = get_glow(r_draw * 1.4, (255, 255, 255), alpha=fa)
            self.screen.blit(flash, flash.get_rect(center=(int(cx), int(cy))),
                             special_flags=pygame.BLEND_RGB_ADD)
        # 生命值条（受过伤才显示）
        if s.danger and s.hp < s.max_hp:
            bw = max(20, int(r_draw * 1.6))
            bh = 4
            bx = int(cx - bw / 2)
            by = int(cy - r_draw - 12)
            pygame.draw.rect(self.screen, (30, 10, 14), (bx, by, bw, bh))
            ratio = max(0.0, s.hp / s.max_hp)
            hc = (90, 255, 120) if ratio > 0.5 else ((255, 200, 60) if ratio > 0.25 else (255, 60, 60))
            pygame.draw.rect(self.screen, hc, (bx, by, int(bw * ratio), bh))
            pygame.draw.rect(self.screen, (200, 200, 200), (bx, by, bw, bh), 1)

    def _draw_powerup(self, pu, ox, oy):
        col = POWERUP_COLORS[pu.ptype]
        cx, cy = pu.x + ox, pu.y + oy
        life_t = clamp(pu.life / pu.max_life, 0, 1)
        blink = 1.0
        if life_t < 0.3:
            blink = 0.5 + 0.5 * (1 if int(pu.life * 10) % 2 == 0 else 0)
        glow = get_glow(pu.r * 2.6, col, alpha=int(160 * blink))
        self.screen.blit(glow, glow.get_rect(center=(int(cx), int(cy))),
                         special_flags=pygame.BLEND_RGB_ADD)
        pts = []
        for i in range(10):
            a = pu.phase + i * math.tau / 10
            rr = pu.r if i % 2 == 0 else pu.r * 0.45
            pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr))
        pygame.draw.polygon(self.screen, col, pts)
        pygame.draw.polygon(self.screen, WHITE, pts, 2)
        letter = POWERUP_LETTER[pu.ptype]
        txt = get_font(13, True).render(letter, True, WHITE)
        self.screen.blit(txt, txt.get_rect(center=(int(cx), int(cy))))

    def _draw_coin(self, c, ox, oy):
        cx, cy = c["x"] + ox, c["y"] + oy
        blink = 1.0
        if c["life"] < 3.0:
            blink = 0.5 + 0.5 * (1 if int(c["life"] * 8) % 2 == 0 else 0)
        g = get_glow(22, NEON_YELLOW, alpha=int(170 * blink))
        self.screen.blit(g, g.get_rect(center=(int(cx), int(cy))),
                         special_flags=pygame.BLEND_RGB_ADD)
        # 金币本体（旋转椭圆模拟翻转）
        w = abs(math.cos(c["phase"])) * 10 + 3
        pygame.draw.ellipse(self.screen, NEON_YELLOW,
                            (int(cx - w), int(cy - 10), int(w * 2), 20))
        pygame.draw.ellipse(self.screen, WHITE,
                            (int(cx - w), int(cy - 10), int(w * 2), 20), 2)
        txt = get_font(12, True).render("$", True, (120, 80, 0))
        self.screen.blit(txt, txt.get_rect(center=(int(cx), int(cy))))

    def _draw_blackhole(self, bh, ox, oy):
        cx, cy = bh["x"] + ox, bh["y"] + oy
        r = bh["r"]
        # 紫色外光环
        for i in range(4):
            rr = r * (1.0 - i * 0.12)
            g = get_glow(rr, NEON_PURPLE, alpha=60 - i * 12)
            self.screen.blit(g, g.get_rect(center=(int(cx), int(cy))),
                             special_flags=pygame.BLEND_RGB_ADD)
        # 黑色核心
        pygame.draw.circle(self.screen, (0, 0, 0), (int(cx), int(cy)), int(r * 0.5))
        pygame.draw.circle(self.screen, NEON_PURPLE, (int(cx), int(cy)), int(r * 0.5), 2)
        # 旋转吸积线
        t = pygame.time.get_ticks() * 0.003
        for i in range(6):
            a = t + i * math.tau / 6
            x1 = cx + math.cos(a) * r * 0.55
            y1 = cy + math.sin(a) * r * 0.55
            x2 = cx + math.cos(a + 0.6) * r * 0.95
            y2 = cy + math.sin(a + 0.6) * r * 0.95
            pygame.draw.line(self.screen, NEON_PURPLE, (x1, y1), (x2, y2), 2)

    # ---- 摄像头预览 ----
    def _draw_preview(self):
        # 仅在手势模式 + 摄像头可用 + 有画面时才弹出至右侧
        if self.control_mode != "hand" or not self.tracker.available:
            return
        if self._cam_frame is None:
            return
        px = WIDTH - PREVIEW_W - 16
        py = 16
        pygame.draw.rect(self.screen, (20, 22, 40),
                         (px - 3, py - 3, PREVIEW_W + 6, PREVIEW_H + 6), border_radius=6)
        if self._cam_frame is not None:
            rgb = cv2.cvtColor(self._cam_frame, cv2.COLOR_BGR2RGB)
            rgb = cv2.resize(rgb, (PREVIEW_W, PREVIEW_H))
            surf = pygame.image.frombuffer(rgb.tobytes(), (PREVIEW_W, PREVIEW_H), 'RGB')
            self.screen.blit(surf, (px, py))
        else:
            pygame.draw.rect(self.screen, (10, 10, 20), (px, py, PREVIEW_W, PREVIEW_H))
            self._text("摄像头未开启", px + PREVIEW_W // 2, py + PREVIEW_H // 2 - 8,
                       14, DIM, center=True)
        if self._last_lms:
            self._draw_hand_landmarks(px, py, self._last_lms)
        # 中心准星（居中、小死区）
        cx = px + PREVIEW_W // 2
        cy = py + PREVIEW_H // 2
        dead_r = int(0.06 * PREVIEW_W)
        pygame.draw.circle(self.screen, HAND_GREEN, (cx, cy), dead_r, 1)
        pygame.draw.line(self.screen, HAND_GREEN, (cx - 8, cy), (cx + 8, cy), 1)
        pygame.draw.line(self.screen, HAND_GREEN, (cx, cy - 8), (cx, cy + 8), 1)
        if self._last_lms:
            hx = int(self._last_lms[8].x * PREVIEW_W) + px
            hy = int(self._last_lms[8].y * PREVIEW_H) + py
            pygame.draw.line(self.screen, NEON_PINK, (cx, cy), (hx, hy), 1)
            pygame.draw.circle(self.screen, NEON_PINK, (hx, hy), 5)
            pygame.draw.circle(self.screen, WHITE, (hx, hy), 5, 1)
        mode_col = NEON_CYAN if self.control_mode == "hand" else DIM
        pygame.draw.rect(self.screen, mode_col,
                         (px - 3, py - 3, PREVIEW_W + 6, PREVIEW_H + 6), 2, border_radius=6)
        if self.control_mode == "hand":
            label = "手势(食指·伸掌加速) [H切换]"
        elif self.control_mode == "arrow":
            label = "方向键模式 [H切换]"
        else:
            label = "鼠标模式 [H切换]"
        self._text(label, px + PREVIEW_W // 2, py + PREVIEW_H + 10, 14, mode_col, center=True)

    def _draw_hand_landmarks(self, ox, oy, lms):
        connections = [(0, 1), (1, 2), (2, 3), (3, 4),
                       (0, 5), (5, 6), (6, 7), (7, 8),
                       (0, 9), (9, 10), (10, 11), (11, 12),
                       (0, 13), (13, 14), (14, 15), (15, 16),
                       (0, 17), (17, 18), (18, 19), (19, 20),
                       (5, 9), (9, 13), (13, 17)]
        pts = [(int(lm.x * PREVIEW_W) + ox, int(lm.y * PREVIEW_H) + oy) for lm in lms]
        for a, b in connections:
            pygame.draw.line(self.screen, HAND_GREEN, pts[a], pts[b], 2)
        for pp in pts:
            pygame.draw.circle(self.screen, HAND_GREEN, pp, 3)
        # 食指尖高亮
        pygame.draw.circle(self.screen, NEON_PINK, pts[8], 5, 2)

    # ---- UI ----
    def _draw_ui(self):
        if getattr(self, "_boss_mode", False):
            # Q9：BOSS模式HUD
            bl = getattr(self, "_boss_level", 1)
            self._text(f"BOSS模式  第{bl}/16关",
                       24, 18, 20, (255, 60, 60), bold=True)
            self._text(f"分数  {self.score}", 24, 52, 18, NEON_YELLOW)
            self._text(f"连击 {self.combo}  ·  剩余敌人 {len(self.stars)}",
                       24, 80, 17, NEON_PINK, bold=True)
        elif getattr(self, "_endless_mode", False):
            self._text(f"无尽模式  波次: {self._endless_wave}  得分: {self._endless_score}",
                       24, 18, 20, NEON_PURPLE, bold=True)
            self._text(f"总分  {self.score}", 24, 52, 18, NEON_YELLOW)
            self._text(f"击败 {int(getattr(self, '_endless_killed', 0))}/{self._endless_wave_target}  ·  连击 {self.combo}",
                       24, 80, 17, NEON_PINK, bold=True)
        else:
            lv = self._get_levels()[self.current_level]
            self._text(f"第 {self.current_level + 1} 关  {lv['name']}", 24, 18, 20, WHITE, bold=True)
            self._text(f"分数  {self.score}", 24, 52, 18, NEON_YELLOW)
            # 吞噬进度（醒目色）
            eat_color = NEON_GREEN if self.level_eaten < lv["goal"] else NEON_PINK
            self._text(f"吞噬 {self.level_eaten}/{lv['goal']}  ·  连击 {self.combo}",
                       24, 80, 17, eat_color, bold=True)
        # 模式 / 控制提示
        if self.num_players == 2:
            self._text("双人  P1:WASD+LShift  P2:↑↓←→+RShift", WIDTH // 2, 20, 15,
                       NEON_PINK, center=True)
        else:
            self._text(self._control_hint(), WIDTH // 2, 20, 15,
                       NEON_CYAN if self.control_mode != "mouse" else DIM, center=True)
        if self.num_players == 1:
            self._draw_preview()
        # Q1/Q2：终极皮肤 - 顶部显示当前元素/炮类型
        for _pp in self.players:
            if not _pp.alive:
                continue
            _sk = getattr(_pp, "skin", None) or self.active_skin
            if _sk == "origin" and hasattr(self, "_origin_elements"):
                _elems = self._origin_elements()
                _idx = _pp._origin_elem_idx % len(_elems)
                _nm, _col, _dmg, _eff = _elems[_idx]
                _tag = f"P{_pp.pid} 下发元素：{_nm}" if self.num_players == 2 else f"下发元素：{_nm}"
                _tx = WIDTH // 2
                _ty = 44
                # 背景框
                _bw = 220
                _rect = pygame.Rect(_tx - _bw // 2, _ty - 4, _bw, 26)
                pygame.draw.rect(self.screen, (20, 20, 40), _rect, border_radius=6)
                pygame.draw.rect(self.screen, _col, _rect, 2, border_radius=6)
                # 元素色点
                pygame.draw.circle(self.screen, _col, (_tx - 86, _ty + 9), 7)
                self._text(_tag, _tx + 6, _ty, 15, _col, bold=True, center=True)
            elif _sk == "paradox" and hasattr(self, "_paradox_cannons"):
                _cans = self._paradox_cannons()
                _idx = _pp._paradox_cannon_idx % len(_cans)
                _nm, _col, _dmg, _eff = _cans[_idx]
                _tag = f"P{_pp.pid} 下发炮型：{_nm}" if self.num_players == 2 else f"下发炮型：{_nm}"
                _tx = WIDTH // 2
                _ty = 44
                _bw = 220
                _rect = pygame.Rect(_tx - _bw // 2, _ty - 4, _bw, 26)
                pygame.draw.rect(self.screen, (25, 15, 30), _rect, border_radius=6)
                pygame.draw.rect(self.screen, _col, _rect, 2, border_radius=6)
                pygame.draw.circle(self.screen, _col, (_tx - 86, _ty + 9), 7)
                self._text(_tag, _tx + 6, _ty, 15, _col, bold=True, center=True)
        # 生命
        for i in range(5):
            cx = 24 + i * 30
            cy = HEIGHT - 30
            col = NEON_CYAN if i < self.lives else (40, 45, 70)
            pygame.draw.circle(self.screen, col, (cx, cy), 10)
            if i < self.lives:
                g = get_glow(16, NEON_CYAN, alpha=120)
                self.screen.blit(g, g.get_rect(center=(cx, cy)),
                                 special_flags=pygame.BLEND_RGB_ADD)
        # 连击倍率
        if self.combo > 0:
            mult = 1 + self.combo // 5
            if self.double_timer > 0:
                mult *= 2
            self._text(f"倍率 x{mult}", 24, HEIGHT - 56, 16, NEON_ORANGE)
        # 能量条（2P 显示两条）：加粗+数值+边框，使用技能时即时可见
        bars = self.players if self.num_players == 2 else [self.player]
        ew = 170 if self.num_players == 2 else 260
        gap = 28
        total_w = len(bars) * ew + (len(bars) - 1) * gap
        ex0 = (WIDTH - total_w) // 2
        ey = HEIGHT - 28
        for i, p in enumerate(bars):
            ex = ex0 + i * (ew + gap)
            eh = 14
            # 背景（带 2px 边框）
            pygame.draw.rect(self.screen, (25, 25, 45), (ex, ey, ew, eh), border_radius=6)
            pygame.draw.rect(self.screen, (90, 90, 140), (ex, ey, ew, eh), 2, border_radius=6)
            fw = max(0, int(ew * p.energy / 100.0))
            ecol = p.color if p.energy > 30 else NEON_RED
            # 能量耗尽后回复中：显示为橙色提示减速
            if p._energy_depleted and p.energy < 100.0:
                ecol = NEON_ORANGE
            if fw > 0:
                # 内填充 + 高亮渐变效果
                fill_rect = pygame.Rect(ex, ey, fw, eh)
                pygame.draw.rect(self.screen, ecol, fill_rect, border_radius=6)
                # 顶部高光
                hl = pygame.Rect(ex + 3, ey + 2, max(0, fw - 6), max(2, eh // 3))
                hl_col = tuple(min(255, int(c * 1.6)) for c in ecol)
                pygame.draw.rect(self.screen, hl_col, hl, border_radius=3)
                # 能量条末端发光
                if fw >= 4:
                    glow = get_glow(20, ecol, alpha=140)
                    self.screen.blit(glow,
                                     glow.get_rect(center=(ex + fw, ey + eh // 2)),
                                     special_flags=pygame.BLEND_RGB_ADD)
            lbl = f"P{p.pid}" if self.num_players == 2 else "能量(加速/技能)"
            if p._energy_depleted and p.energy < 100.0:
                lbl += " [回复慢]"
            self._text(lbl, ex, ey - 26, 15, DIM)
            # 右侧显示具体能量数值（大一些，便于看到瞬时变化）
            pct_text = f"{int(p.energy)} / 100"
            pct_col = ecol if p.energy > 30 else NEON_RED
            self._text(pct_text, ex + ew, ey - 26, 15, pct_col, bold=True, right=True)
        # 技能
        self._draw_skills()
        if self.muted:
            self._text("静音 [F3]", WIDTH - 16, 52, 15, NEON_RED, right=True)

    def _control_hint(self):
        if self.control_mode == "hand":
            return "手势(食指·伸掌加速) [H切换]"
        if self.control_mode == "arrow":
            return "方向键移动 + LShift加速 [H切换]"
        return "鼠标 [H切换 手势/方向键]"

    def _draw_skills(self):
        skills = []
        for p in self.players:
            if not p.alive:
                continue
            if p.shield_timer > 0:
                skills.append((f"P{p.pid}护盾", p.shield_timer, POWERUP_DURATION["SHIELD"], NEON_CYAN))
            if p.magnet_timer > 0:
                skills.append((f"P{p.pid}磁吸", p.magnet_timer, POWERUP_DURATION["MAGNET"], NEON_PURPLE))
            if p.weapon_type is not None:
                skills.append((f"P{p.pid}{POWERUP_NAME[p.weapon_type]}",
                               p.weapon_timer, POWERUP_DURATION[p.weapon_type],
                               POWERUP_COLORS[p.weapon_type]))
        if self.time_slow_timer > 0:
            skills.append(("时停", self.time_slow_timer, POWERUP_DURATION["TIME"], NEON_YELLOW))
        if self.double_timer > 0:
            skills.append(("双倍", self.double_timer, POWERUP_DURATION["DOUBLE"], NEON_ORANGE))
        if self.blackhole is not None:
            skills.append(("黑洞", self.blackhole["life"], 4.0, NEON_PURPLE))
        if not skills:
            return
        item_w = 112 if self.num_players == 2 else 104
        total_w = len(skills) * item_w
        sx = (WIDTH - total_w) // 2
        sy = 50
        for name, t, maxt, col in skills:
            pygame.draw.circle(self.screen, col, (sx + 12, sy + 10), 8)
            g = get_glow(14, col, alpha=110)
            self.screen.blit(g, g.get_rect(center=(sx + 12, sy + 10)),
                             special_flags=pygame.BLEND_RGB_ADD)
            self._text(name, sx + 26, sy + 0, 15, WHITE)
            w = int(68 * clamp(t / maxt, 0, 1))
            pygame.draw.rect(self.screen, (30, 30, 50), (sx + 26, sy + 19, 68, 4))
            pygame.draw.rect(self.screen, col, (sx + 26, sy + 19, w, 4))
            sx += item_w
        # 皮肤技能说明面板（装备皮肤时显示）
        self._draw_skin_skill_info()

    def _draw_skin_skill_info(self):
        """在游戏界面展示当前皮肤的技能说明。"""
        sk = self.active_skin
        if not sk:
            return
        p = self.player
        # 皮肤名称
        name = SKINS[sk][0]
        col = SKINS[sk][2]
        # 根据皮肤生成技能说明
        if sk == "tri":
            mode_names = ["红球", "黄球", "蓝球"]
            mode_skills = [
                "左键：吐炸弹(2s爆炸消灭敌方+回能)",
                "左键：2s护盾",
                "左键：3s加速(+20%速度)"
            ]
            mode = p.tri_mode
            desc = f"{name} [{mode_names[mode]}]  右键切态(需满能)"
            skill = mode_skills[mode]
            energy_ok = "✓" if p.energy >= 100.0 else "✗"
            info = f"{skill}  能量满{energy_ok}"
        elif sk == "moon":
            state = "缩小态" if p.moon_shrunk else "正常态"
            desc = f"{name} [{state}]  右键切换缩小/还原(需满能)"
            info = "左键正常加速  缩小30%更易躲避"
        elif sk == "void":
            desc = f"{name}  左键：螺旋黑洞3s  右键：6向黑洞清屏"
            info = f"左键能量满{'✓' if p.energy >= 100.0 else '✗'}  右键需满能"
        elif sk == "inferno":
            ring = f"灼烧环{p._inferno_ring_timer:.1f}s" if p._inferno_ring_timer > 0 else "待机"
            desc = f"{name} [{ring}]  左键：发射火球(-25能)  右键：灼烧环5s"
            info = f"右键能量满{'✓' if p.energy >= 100.0 else '✗'}  左键:需25能"
        elif sk == "frost":
            ft = f"{self._freeze_timer:.1f}s" if getattr(self, "_freeze_timer", 0) > 0 else "待机"
            desc = f"{name} [{ft}]  左键：冰粒冻结(-15能)  右键：全场冻结"
            info = f"左键:需15能  右键:需30能(按比例时)"
        elif sk == "thunder":
            tf = f"雷电场{self.thunder_field_timer:.1f}s" if self.thunder_field_timer > 0 else "待机"
            desc = f"{name} [{tf}]  左键：追踪电球(-20能)  右键：周围雷电3s"
            info = f"左键:需20能  右键:需60能"
        elif sk == "chaos":
            sw = f"六剑{p._chaos_sword_timer:.1f}s" if p._chaos_sword_timer > 0 else "待机"
            hook = "钩中" if p._chaos_hook and p._chaos_hook["phase"] == 2 else (
                "有钩" if p._chaos_hook else "无钩")
            desc = f"{name} [{sw} 钩:{hook}]  左键：钩子(-30)  右键：六剑(-80)"
            info = f"HP:{p._chaos_hp}/5  钩:吸血+增大  左右键均消耗能量"
        elif sk == "sun":
            glow = "发光中" if p._sun_glow_timer > 0 else "待机"
            desc = f"{name} [{glow}]  左键：发光排斥+加速  右键：全局击退"
            info = f"右键能量满{'✓' if p.energy >= 100.0 else '✗'}  左键:持续2s排斥"
        elif sk == "rainbow":
            idx = getattr(p, "_rb_idx", 0)
            desc = f"{name} [{RAINBOW_NAMES[idx]}]  左键：用道具(30%时长)  右键：切色"
            info = f"右键能量满{'✓' if p.energy >= 100.0 else '✗'}  左键:随时可用"
        else:
            return
        # 绘制面板（右上角）
        px = WIDTH - 16
        py = 80
        self._text(desc, px, py, 14, col, right=True, bold=True)
        self._text(info, px, py + 20, 13, WHITE, right=True)

    def _text(self, text, x, y, size, color, bold=False, right=False, center=False):
        surf = get_font(size, bold).render(text, True, color)
        rect = surf.get_rect()
        if right:
            rect.topright = (x, y)
        elif center:
            rect.midtop = (x, y)
        else:
            rect.topleft = (x, y)
        self.screen.blit(surf, rect)
        return rect

    def _wrap_text(self, text, max_width, size, bold=False):
        """按像素宽度把文字拆成多行（尽量在中文标点或空格处换行）。"""
        font = get_font(size, bold)
        lines = []
        buf = ""
        for ch in text:
            trial = buf + ch
            if font.size(trial)[0] > max_width and buf:
                # 尝试从末尾找标点/空格作为换行点
                split_i = len(buf)
                for i in range(len(buf) - 1, 0, -1):
                    if buf[i] in "，。；、！？,.!?; 、：":
                        split_i = i + 1
                        break
                lines.append(buf[:split_i])
                buf = buf[split_i:] + ch
            else:
                buf = trial
        if buf:
            lines.append(buf)
        return lines

    # ---- 地图 ----
    def _get_levels(self):
        return self.DUNGEON_LEVELS if self.is_dungeon else LEVELS

    def _get_unlocked(self):
        return self.dungeon_unlocked if self.is_dungeon else self.unlocked

    def _set_unlocked(self, val):
        if self.is_dungeon:
            self.dungeon_unlocked = val
        else:
            self.unlocked = val

    def _dungeon_button_rect(self):
        """副本/主线切换按钮：统一放在右侧按钮栏。"""
        return pygame.Rect(WIDTH - 200, 264, 176, 40)

    def _map_positions(self):
        # 4 列蛇形布局，全部容纳在 960×720 窗口内（避开右侧按钮栏 x≥760, y≤410）
        pos = []
        n = len(self._get_levels())
        cols = 4
        rows = (n + cols - 1) // cols
        x0, y0 = 100, 240
        dx, dy = 175, 100
        for i in range(n):
            row = i // cols
            col = i % cols if row % 2 == 0 else cols - 1 - (i % cols)
            x = x0 + col * dx
            y = y0 + row * dy
            pos.append((x, y))
        return pos

    def _mode_button_rect(self):
        return pygame.Rect(WIDTH - 200, 24, 176, 40)

    def _help_button_rect(self):
        return pygame.Rect(WIDTH - 200, 72, 176, 40)

    def _shop_button_rect(self):
        return pygame.Rect(WIDTH - 200, 120, 176, 40)

    def _lottery_button_rect(self):
        return pygame.Rect(WIDTH - 200, 168, 176, 40)

    def _p2skin_button_rect(self):
        """双人模式下 P2 皮肤选择按钮（放在抽奖按钮下面）。"""
        return pygame.Rect(WIDTH - 200, 216, 176, 40)

    # ===== 进度 导入/导出 按钮 =====
    def _export_button_rect(self):
        # 右侧按钮栏，副本按钮下方
        return pygame.Rect(WIDTH - 200, 312, 176, 40)

    def _import_button_rect(self):
        # 右侧按钮栏，导出按钮下方
        return pygame.Rect(WIDTH - 200, 360, 176, 40)

    # ===== Q6/Q7/Q8：新功能按钮 =====
    def _achievement_button_rect(self):
        return pygame.Rect(WIDTH - 200, 408, 176, 40)

    def _endless_button_rect(self):
        return pygame.Rect(WIDTH - 200, 456, 176, 40)

    def _boss_mode_button_rect(self):
        """Q9：BOSS模式按钮（无尽模式下方）。"""
        return pygame.Rect(WIDTH - 200, 504, 176, 40)

    def _settings_button_rect(self):
        # Q9：设置移到右侧最后一个按钮
        return pygame.Rect(WIDTH - 200, 552, 176, 40)

    def _export_file_path(self):
        # 固定放在工作目录下，用户可以直接复制带走
        try:
            base = os.path.dirname(os.path.abspath(__file__))
        except (NameError, Exception):
            base = os.getcwd()
        return os.path.join(base, "stardust_progress_export.json")

    # ===== 8 位短导入码（大小写字母+数字，不含 I/O/0/l 歧义字符）=====
    _SHORT_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ123456789"  # 32 个字符，刚好 5 bit
    _SHORT_LEN = 8

    @classmethod
    def _bits_to_short(cls, bits_list):
        """[0/1...] -> 8 位短编码 (ALPHABET 索引, 5位/字符)"""
        # 不足 40 位补前导 0
        bits = list(bits_list)
        total_bits = cls._SHORT_LEN * 5
        if len(bits) < total_bits:
            bits = [0] * (total_bits - len(bits)) + bits
        bits = bits[:total_bits]
        out = ""
        for ci in range(cls._SHORT_LEN):
            idx = 0
            for bi in range(5):
                idx = (idx << 1) | (1 if bits[ci * 5 + bi] else 0)
            out += cls._SHORT_ALPHABET[idx % 32]
        return out

    @classmethod
    def _short_to_bits(cls, s):
        """8位短编码 -> 40 bit list"""
        s = str(s).strip().upper()
        s_clean = "".join(c for c in s if c in cls._SHORT_ALPHABET)
        if len(s_clean) < cls._SHORT_LEN:
            s_clean = s_clean.rjust(cls._SHORT_LEN, cls._SHORT_ALPHABET[0])
        s_clean = s_clean[:cls._SHORT_LEN]
        bits = []
        for c in s_clean:
            idx = cls._SHORT_ALPHABET.index(c)
            for bi in range(5):
                bits.append(1 if (idx >> (4 - bi)) & 1 else 0)
        return bits

    @classmethod
    def _short_from_data(cls, data):
        """基于数据内容 hash -> 稳定 8 位短码（用户可读、可保存为记事本）"""
        try:
            raw = json.dumps(data, sort_keys=True, ensure_ascii=False).encode("utf-8")
            # SHA256 -> 取前 5 字节 = 40 bit
            import hashlib
            d = hashlib.sha256(raw).digest()[:5]
            bits = []
            for by in d:
                for i in range(8):
                    bits.append(1 if (by >> (7 - i)) & 1 else 0)
            return cls._bits_to_short(bits)
        except Exception:
            # Fallback: 随机生成（不保证可逆）
            return "".join(random.choice(cls._SHORT_ALPHABET) for _ in range(cls._SHORT_LEN))

    def _export_progress(self):
        """Q4：弹出文件保存对话框，把金币/钻石/皮肤/解锁进度保存到用户选择的路径。
        若 tkinter 对话框不可用，则回退到默认路径保存。"""
        try:
            data = {
                "v": 1,
                "coins": int(self.coins),
                "diamonds": int(self.diamonds),
                "skins": sorted(list(self.owned_skins)),
                "active": self.active_skin,
                "active_p2": self.active_skin_p2,
                "unlocked": int(self.unlocked),
                "dungeon_unlocked": int(getattr(self, "dungeon_unlocked", 0)),
                "high_score": int(getattr(self, "high_score", 0)),
                "redeem_used": list(getattr(self, "_redeem_used", set())),
                # Q5：导出签到数据（确保关卡进度/钻石/金币/签到都有存）
                "sign_in_date": getattr(self, "_sign_in_date", None),
                "sign_in_streak": int(getattr(self, "_sign_in_streak", 0)),
                "endless_high_score": int(getattr(self, "_endless_high_score", 0)),
                "endless_high_wave": int(getattr(self, "_endless_high_wave", 0)),
            }
            short = self._short_from_data(data)
            data_with_code = {"_short_code": short, **data}

            save_path = None
            try:
                import tkinter as tk
                from tkinter import filedialog
                root = tk.Tk()
                root.withdraw()
                root.attributes("-topmost", True)
                save_path = filedialog.asksaveasfilename(
                    title="选择保存路径",
                    defaultextension=".json",
                    filetypes=[("JSON 配置文件", "*.json"), ("所有文件", "*.*")],
                    initialfile="stardust_progress.json",
                )
                root.destroy()
            except Exception:
                save_path = None

            if not save_path:
                # 回退：保存到游戏目录
                default_path = self._export_file_path()
                try:
                    with open(default_path, "w", encoding="utf-8") as f:
                        json.dump(data_with_code, f, ensure_ascii=False, indent=2)
                except Exception:
                    pass
                self._modal = {
                    "title": "进度导出成功（默认路径）",
                    "col": NEON_GREEN,
                    "ok_txt": "我知道了",
                    "body_lines": [
                        f"进度已保存到：",
                        f"{default_path}",
                        f"",
                        f"金币 {self.coins}   钻石 {self.diamonds}   皮肤 {len(self.owned_skins)} 个",
                        f"8 位导入码：{short}",
                        f"",
                        f"提示：如需另存为其他位置，可手动复制该文件。",
                    ],
                }
                self._play("coin")
                return True

            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(data_with_code, f, ensure_ascii=False, indent=2)

            # 同时备份到默认路径
            try:
                default_path = self._export_file_path()
                with open(default_path, "w", encoding="utf-8") as f:
                    json.dump(data_with_code, f, ensure_ascii=False, indent=2)
            except Exception:
                pass

            self._modal = {
                "title": "进度导出成功",
                "col": NEON_GREEN,
                "ok_txt": "我知道了",
                "body_lines": [
                    f"进度已保存到：",
                    f"{save_path}",
                    f"",
                    f"金币 {self.coins}   钻石 {self.diamonds}   皮肤 {len(self.owned_skins)} 个",
                    f"主线解锁 第 {self.unlocked} 关   副本解锁 第 {getattr(self, 'dungeon_unlocked', 0)} 关",
                    f"8 位导入码：{short}（也可通过导入码恢复）",
                ],
            }
            self._play("coin")
            return True
        except Exception as e:
            self._modal = {
                "title": "导出失败",
                "col": NEON_RED,
                "ok_txt": "知道了",
                "body_lines": [f"错误信息：{e}"],
            }
            return False

    def _apply_import_data(self, data):
        """实际应用导入数据到游戏状态（共用函数）。"""
        self.coins = max(0, int(data.get("coins", 0)))
        self.diamonds = max(0, int(data.get("diamonds", 0)))
        sks = data.get("skins", [])
        if isinstance(sks, list):
            self.owned_skins = {str(s) for s in sks}
        else:
            self.owned_skins = set()
        act = data.get("active")
        self.active_skin = act if act in self.owned_skins else (
            list(self.owned_skins)[0] if self.owned_skins else None)
        act2 = data.get("active_p2")
        self.active_skin_p2 = act2 if act2 in self.owned_skins else None
        total = len(LEVELS)
        self.unlocked = max(1, min(total, int(data.get("unlocked", 1))))
        du = int(data.get("dungeon_unlocked", 0))
        self.dungeon_unlocked = max(0, du)
        if "high_score" in data:
            self.high_score = int(data["high_score"])
        # Q5：恢复签到数据 + 无尽模式最高记录
        if "sign_in_date" in data:
            self._sign_in_date = data["sign_in_date"]
        if "sign_in_streak" in data:
            try:
                self._sign_in_streak = int(data["sign_in_streak"])
            except (TypeError, ValueError):
                self._sign_in_streak = 0
        if "endless_high_score" in data:
            try:
                self._endless_high_score = int(data["endless_high_score"])
            except (TypeError, ValueError):
                self._endless_high_score = 0
        if "endless_high_wave" in data:
            try:
                self._endless_high_wave = int(data["endless_high_wave"])
            except (TypeError, ValueError):
                self._endless_high_wave = 0
        self.map_cursor = min(self.map_cursor, max(0, self.unlocked - 1))
        self._sync_skin_to_player()
        self._save_game()
        self._play("powerup")

    def _open_import_modal(self):
        """打开输入型导入码弹窗。"""
        self._modal = {
            "title": "导入进度",
            "col": NEON_CYAN,
            "ok_txt": "开始导入",
            "input": "",
            "input_title": "请粘贴或输入 8 位导入码（大小写不区分）：",
            "body_lines": [
                "· 输入/粘贴之前导出时给你的 8 位导入码。",
                "· 若之前保存的是 stardust_progress_export.json 文件，",
                "  也可以直接把文件放在游戏目录下，导入码随意 8 个字符即可自动读取。",
            ],
        }

    def _import_progress(self):
        """Q5：弹出文件选择对话框，让用户选择配置文件导入进度。"""
        # Q5：弹出文件打开对话框
        open_path = None
        try:
            import tkinter as tk
            from tkinter import filedialog
            root = tk.Tk()
            root.withdraw()
            root.attributes("-topmost", True)
            open_path = filedialog.askopenfilename(
                title="选择进度配置文件",
                filetypes=[("JSON 配置文件", "*.json"), ("所有文件", "*.*")],
            )
            root.destroy()
        except Exception:
            open_path = None

        if not open_path:
            # 用户取消了选择，回退到输入 8 位导入码的弹窗
            self._open_import_modal()
            return True

        try:
            with open(open_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            # 兼容短码保存的数据格式
            if "_short_code" in data:
                real_data = {k: v for k, v in data.items() if k != "_short_code"}
            else:
                real_data = data
            self._apply_import_data(real_data)
            sc = data.get("_short_code", "（文件导入）")
            # 恢复兑换码使用记录
            if "redeem_used" in data:
                self._redeem_used = set(data["redeem_used"])
            self._modal = {
                "title": "进度导入成功",
                "col": NEON_CYAN,
                "ok_txt": "好的",
                "body_lines": [
                    f"已从文件恢复进度！",
                    f"文件：{open_path}",
                    f"金币 {self.coins}   钻石 {self.diamonds}   已拥有皮肤 {len(self.owned_skins)} 个",
                    f"主线解锁 第 {self.unlocked} 关，副本解锁 第 {getattr(self, 'dungeon_unlocked', 0)} 关",
                    f"签到状态：连续 {getattr(self, '_sign_in_streak', 0)} 天（{getattr(self, '_sign_in_date', '未签到')}）",
                ],
            }
            self._play("powerup")
        except Exception as e:
            self._modal = {
                "title": "导入失败",
                "col": NEON_RED,
                "ok_txt": "知道了",
                "body_lines": [
                    f"读取文件失败：{open_path}",
                    f"错误：{e}",
                    "请确认选择的是有效的进度配置文件(.json)。",
                ],
            }
        return True

    # ===== 兑换码定义（硬编码 2 组礼包） =====
    REDEEM_CODES = {
        "Zygarden": {
            "name": "新手启程礼包",
            "coins": 300,
            "diamonds": 15,
            "skins": ["frost", "demon"],  # 霜冻冰魄 + 九幽魔君
            "desc": "300 金币 + 15 钻石 + 皮肤【霜冻冰魄】+【九幽魔君】",
        },
        "cbyygyitoh": {
            "name": "开发者专属礼包",
            "coins": 500,
            "diamonds": 50,
            "skins": ["taiji", "buddha"],  # 太上无极 + 不灭尊者
            "desc": "500 金币 + 50 钻石 + 皮肤【太上无极】+【不灭尊者】",
        },
    }

    def _sign_in_button_rect(self):
        """Q8：左上角签到按钮（在兑换码按钮上方）。"""
        return pygame.Rect(16, 16, 156, 42)

    def _redeem_code_button_rect(self):
        """初始界面左上角：兑换码按钮位置（Q8：下移到签到按钮下方）。"""
        return pygame.Rect(16, 64, 156, 42)

    def _do_sign_in(self):
        """Q8：每日签到奖励。连续签到天数越多奖励越好。"""
        today = self._today_str()
        if getattr(self, "_sign_in_date", None) == today:
            self._flash_msg = "今天已签到，明天再来吧！"
            self._flash_timer = 1.5
            self._play("tick")
            return
        # 计算连续签到天数
        yesterday = self._yesterday_str()
        streak = getattr(self, "_sign_in_streak", 0)
        if getattr(self, "_sign_in_date", None) == yesterday:
            streak += 1
        else:
            streak = 1
        self._sign_in_streak = streak
        self._sign_in_date = today
        # 奖励：基础50金+5钻，每连续天+10金+1钻（上限7天循环）
        day_bonus = min(streak, 7)
        reward_coins = 50 + (day_bonus - 1) * 10
        reward_diamonds = 5 + (day_bonus - 1)
        self.coins += reward_coins
        self.diamonds += reward_diamonds
        self._save_game()
        self._play("coin")
        self._flash_msg = f"签到成功（连续{streak}天）！+{reward_coins}金币 +{reward_diamonds}钻石"
        self._flash_timer = 2.5
        self._check_achievements()

    def _yesterday_str(self):
        """返回昨天的日期字符串。"""
        import datetime as _dt
        return (_dt.date.today() - _dt.timedelta(days=1)).isoformat()

    def _open_redeem_modal(self):
        self._modal = {
            "title": "输入兑换码",
            "col": (255, 180, 80),
            "ok_txt": "兑换礼包",
            "input": "",
            "input_title": "兑换码：",
            "body_lines": [
                "· 输入有效的兑换码即可领取对应礼包。",
                "· 兑换码只能使用一次，重复输入相同码无效。",
            ],
            "_used": False,
        }

    def _try_redeem(self, code_raw):
        """尝试使用兑换码，返回 (ok, msg_lines)。"""
        if not hasattr(self, "_redeem_used"):
            self._redeem_used = set()
        code = str(code_raw).strip()
        if not code:
            return False, ["请先输入兑换码！"]
        # 大小写不敏感匹配
        match_key = None
        for k in self.REDEEM_CODES:
            if k.lower() == code.lower():
                match_key = k
                break
        if match_key is None:
            return False, [f"未找到兑换码：{code}", "请检查大小写、首尾空格是否正确。"]
        if match_key in self._redeem_used:
            return False, ["该兑换码已经使用过了，不能重复兑换！", "（每个礼包只能领取 1 次）"]
        info = self.REDEEM_CODES[match_key]
        # 应用奖励
        self.coins = int(self.coins) + int(info.get("coins", 0))
        self.diamonds = int(self.diamonds) + int(info.get("diamonds", 0))
        new_skins = []
        for sid in info.get("skins", []):
            if sid in SKINS and sid not in self.owned_skins:
                self.owned_skins.add(sid)
                new_skins.append(SKINS[sid][0])
            elif sid in SKINS:
                # 已拥有也加入显示名（让玩家知道礼包内容）
                if SKINS[sid][0] not in new_skins:
                    new_skins.append(SKINS[sid][0])
        self._redeem_used.add(match_key)
        self._save_game()
        # Q3：弹窗文案改为「恭喜你获得XXX！」格式
        parts = [f"{info.get('coins', 0)}金",
                 f"{info.get('diamonds', 0)}钻"]
        # 皮肤名按礼包定义顺序输出
        skin_names = []
        for sid in info.get("skins", []):
            if sid in SKINS:
                skin_names.append(SKINS[sid][0])
        if skin_names:
            parts.extend(skin_names)
        msg = [
            f"恭喜你获得{'+'.join(parts)}！",
        ]
        if new_skins:
            newly = [n for n in new_skins if n in skin_names]
            if newly:
                msg.append(f"（新解锁皮肤：{' / '.join(newly)}）")
        self._play("powerup")
        return True, msg

    # ===== 模态弹窗通用点击 / 键盘输入处理 =====
    def _modal_click(self, mx, my):
        """return True if consumed (stop propagation)"""
        m = getattr(self, "_modal", None)
        if m is None:
            return False
        ok_rect = m.get("_ok_rect")
        copy_rect = m.get("_copy_rect")
        inp_rect = m.get("_input_rect")
        close_rect = m.get("_close_rect")
        modal_rect = m.get("_rect")
        # 关闭按钮 (X)
        if close_rect and close_rect.collidepoint(mx, my):
            self._modal = None
            self._play("tick")
            return True
        # 复制
        if copy_rect and copy_rect.collidepoint(mx, my):
            try:
                import subprocess
                txt = str(self._modal_clipboard) if self._modal_clipboard else (str(m.get("input", "")))
                subprocess.run(["clip"], input=txt, text=True, timeout=2, check=False)
                self._flash_msg = "已复制到剪贴板！"
                self._flash_timer = 1.2
            except Exception:
                pass
            self._play("tick")
            return True
        # OK/确定/开始导入/兑换礼包
        if ok_rect and ok_rect.collidepoint(mx, my):
            self._modal_ok_submit()
            return True
        # 输入框：点击即聚焦（无状态，仅提示用户）
        if inp_rect and inp_rect.collidepoint(mx, my):
            self._flash_msg = "直接用键盘输入即可～"
            self._flash_timer = 0.8
            return True
        # 点击弹窗外部区域：关闭弹窗（方便用户放弃操作）
        if modal_rect and not modal_rect.collidepoint(mx, my):
            self._modal = None
            self._play("tick")
            return True
        # 点击弹窗内部其他区域：消费但不关闭
        if modal_rect and modal_rect.collidepoint(mx, my):
            return True
        return True

    def _modal_key_input(self, event):
        """处理弹窗键盘输入（输入文本/退格/回车/ESC）。返回 True 表示已消费。"""
        m = getattr(self, "_modal", None)
        if m is None:
            return False
        key = event.key
        # ESC: 关闭弹窗
        if key == pygame.K_ESCAPE:
            self._modal = None
            self._play("tick")
            return True
        # 回车 = 提交（等同点击OK）
        if key == pygame.K_RETURN or key == pygame.K_KP_ENTER:
            self._modal_ok_submit()
            return True
        # 如果是输入型弹窗，则处理字符输入 / 退格
        if m.get("input") is not None:
            cur = str(m.get("input", ""))
            if key == pygame.K_BACKSPACE:
                m["input"] = cur[:-1]
                self._play("tick")
                return True
            if key == pygame.K_DELETE:
                m["input"] = ""
                return True
            # Ctrl+V：粘贴（尝试）
            if (key == pygame.K_v and (event.mod & pygame.KMOD_CTRL)):
                try:
                    import tkinter as tk
                    rt = tk.Tk(); rt.withdraw()
                    clip = rt.clipboard_get()
                    rt.destroy()
                    m["input"] = cur + str(clip)[:80]
                    self._play("tick")
                    return True
                except Exception:
                    return True
            # 普通字符（event.unicode）：追加（最大 100 字符）
            ch = getattr(event, "unicode", None) or ""
            if ch and ch.isprintable() and len(cur) < 100:
                m["input"] = cur + ch
                return True
        # 非输入键：ESC已处理过；其余键（空格等）默认不消费，交给 _handle_key
        if key in (pygame.K_SPACE, pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT, pygame.K_TAB):
            return False
        return True

    def _modal_ok_submit(self):
        """用户点击弹窗右下角 OK 按钮 / 按回车。"""
        m = getattr(self, "_modal", None)
        if m is None:
            return
        has_input = m.get("input") is not None
        if not has_input:
            # 非输入型弹窗：直接关闭
            self._modal = None
            self._play("tick")
            return
        # ===== 输入型弹窗：根据 context 判定做什么 =====
        title = str(m.get("title", ""))
        code = str(m.get("input", "")).strip()
        # 导入进度（8 位导入码）
        if "导入" in title:
            # 优先尝试自动读取本地导出文件
            path = self._export_file_path()
            try:
                if os.path.isfile(path):
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    if "_short_code" in data:
                        real = {k: v for k, v in data.items() if k != "_short_code"}
                    else:
                        real = data
                    self._apply_import_data(real)
                    sc = data.get("_short_code", "文件读取")
                    self._modal = {
                        "title": "进度导入成功",
                        "col": NEON_CYAN,
                        "ok_txt": "好的",
                        "body_lines": [
                            f"检测到本地导出文件，已恢复进度！",
                            f"8 位导入码：{sc}",
                            f"金币 {self.coins}   钻石 {self.diamonds}   已拥有皮肤 {len(self.owned_skins)} 个",
                            f"主线解锁 {self.unlocked} 关 / 副本解锁 {self.dungeon_unlocked} 关",
                        ],
                    }
                    return
            except Exception as e:
                pass
            # 若 8 位短码：提示用户它只是标识（不是密文），提供手动导入功能
            code_clean = "".join(c for c in code.upper() if c in self._SHORT_ALPHABET)
            if len(code_clean) < self._SHORT_LEN:
                self._modal = {
                    "title": "导入码不足 8 位",
                    "col": NEON_RED,
                    "ok_txt": "好的",
                    "body_lines": [
                        f"您输入的有效字符只有 {len(code_clean)} 位（需 8 位大写字母+数字）。",
                        "请检查：",
                        "· 大写字母 A-H、J-N、P-Z（不含 I / O）",
                        "· 数字 1-9（不含 0）",
                        "当前输入：{code_clean}".format(code_clean=code_clean if code_clean else "(空)"),
                    ],
                }
                return
            code8 = code_clean[:8]
            # 扫一遍本地导出文件匹配；若找不到则提示用户把导出 JSON 放游戏目录
            path = self._export_file_path()
            matched = False
            try:
                if os.path.isfile(path):
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    if "_short_code" in data and str(data["_short_code"]).upper() == code8:
                        real = {k: v for k, v in data.items() if k != "_short_code"}
                        self._apply_import_data(real)
                        matched = True
                        self._modal = {
                            "title": "导入成功（短码匹配）",
                            "col": NEON_CYAN,
                            "ok_txt": "好的",
                            "body_lines": [
                                f"短码 {code8} 已匹配本地导出文件！",
                                f"金币 {self.coins}   钻石 {self.diamonds}   皮肤 {len(self.owned_skins)}",
                            ],
                        }
            except Exception:
                pass
            if not matched:
                self._modal = {
                    "title": "本地未找到该导入码对应的进度",
                    "col": NEON_RED,
                    "ok_txt": "好的",
                    "body_lines": [
                        f"8 位导入码：{code8}",
                        "注意：导入码不是密文，它只是你导出时生成的标识号。",
                        "请确保你本次导出的 stardust_progress_export.json 还在游戏目录！",
                        "（因为它才是真正的进度数据）",
                    ],
                }
            return
        # 兑换礼包（兑换码）
        if "兑换码" in title or "兑换" in title:
            ok, lines = self._try_redeem(code)
            col = (90, 220, 120) if ok else (235, 90, 90)
            self._modal = {
                "title": "兑换成功！" if ok else "兑换失败",
                "col": col,
                "ok_txt": "继续",
                "body_lines": lines,
            }
            return
        # 默认：关弹窗
        self._modal = None
        self._play("tick")

    def _lottery_cost(self):
        """钻石抽奖消耗钻石，金币抽奖消耗金币（F2 作弊时 0）。"""
        if getattr(self, "_lottery_unlocked", False):
            return 0
        if getattr(self, "_diamond_lottery", False):
            return 5  # 钻石抽奖 5 钻 1 抽
        return 30  # 金币抽奖 30 金 1 抽

    def _today_str(self):
        """YYYY-MM-DD 字符串，用于每日刷新抽奖。"""
        import datetime as _dt
        try:
            return _dt.date.today().isoformat()
        except Exception:
            return str(pygame.time.get_ticks() // 86400000)

    def _lottery_pool(self, diamond_mode=False):
        """Q2：按钻石/金币模式返回奖池，且**过滤掉玩家已拥有的皮肤**（只抽没抽到的皮肤）。
        diamond_mode = True  钻石奖池：更偏钻石皮肤+钻石奖励
        diamond_mode = False 金币奖池：更偏金币皮肤+金币奖励
        """
        owned = getattr(self, "owned_skins", set())
        def _skin_ok(sid):
            return sid not in owned
        pool = []
        # Q2：取消"全皮肤+全关卡"大奖，改为至少1个随机皮肤
        if diamond_mode:
            # Q9：钻石抽奖只保留 2 个不重复可抽的钻石页皮肤（从未拥有中随机选 2）
            _diamond_skin_defs = [
                ("judge",   12, "天罚之眼",   (255, 240, 200)),
                ("dragon",  11, "真龙帝皇",   (255, 180, 80)),
                ("demon",   10, "九幽魔君",   (180, 80, 255)),
                ("stellar",  9, "星海主宰",   (150, 220, 255)),
                ("samsara",  8, "六道轮回",   (220, 160, 255)),
                ("寂灭",     7, "寂灭神皇",   (255, 200, 255)),
                ("primal",   6, "鸿蒙之始",   (220, 255, 200)),
                ("taiji",    5, "太上无极",   (200, 200, 255)),
                ("nirvana",  4, "大道涅槃",   (255, 220, 120)),
            ]
            _avail_dskins = [(s, w, n, c) for (s, w, n, c) in _diamond_skin_defs if _skin_ok(s)]
            random.shuffle(_avail_dskins)
            for (s, w, n, c) in _avail_dskins[:2]:
                pool.append((w, f"skin_{s}", s, n, c))
            # 钻石 + 再来一次 + 谢谢参与 + 少量金币
            pool += [
                (14, "diamonds_1",   1,   "1 钻石",   (180, 220, 255)),
                (12, "diamonds_2",   2,   "2 钻石",   (200, 230, 255)),
                (10, "diamonds_3",   3,   "3 钻石",   (220, 230, 255)),
                (8,  "diamonds_5",   5,   "5 钻石",   (230, 240, 255)),
                (5,  "diamonds_10",  10,  "10 钻石",  (255, 240, 255)),
                (6,  "coins_80",     80,  "80 金币",  (255, 220, 90)),
                (4,  "coins_200",    200, "200 金币", (255, 220, 90)),
                (14, "again",        None,"再来一次", (120, 200, 255)),
                (12, "nothing",      None,"谢谢参与", (130, 140, 175)),
            ]
        else:
            # 金币模式奖池
            # 第一页金币 9 皮肤（只抽未拥有）
            if _skin_ok("tri"):      pool.append((12, "skin_tri",      "tri",      "三色灵球",   (255, 120, 120)))
            if _skin_ok("moon"):     pool.append((11, "skin_moon",     "moon",     "月华之球",   (200, 230, 255)))
            if _skin_ok("sun"):      pool.append((10, "skin_sun",      "sun",      "烈阳之球",   (255, 200, 80)))
            if _skin_ok("rainbow"):  pool.append((10, "skin_rainbow",  "rainbow",  "虹光七彩",   (255, 120, 200)))
            if _skin_ok("frost"):    pool.append((8,  "skin_frost",    "frost",    "霜冻冰魄",   (180, 220, 255)))
            if _skin_ok("thunder"):  pool.append((7,  "skin_thunder",  "thunder",  "雷霆战神",   (220, 220, 120)))
            if _skin_ok("void"):     pool.append((6,  "skin_void",     "void",     "深渊黑洞",   (120, 80, 180)))
            if _skin_ok("inferno"):  pool.append((10, "skin_inferno",  "inferno",  "炼狱炎魂",   (255, 120, 40)))
            if _skin_ok("chaos"):    pool.append((5,  "skin_chaos",    "chaos",    "混沌魔神",   (255, 90, 90)))
            # 钻石页 & 第三页（金币抽稀有）
            if _skin_ok("judge"):    pool.append((5, "skin_judge",    "judge",    "天罚之眼",   (255, 240, 200)))
            if _skin_ok("demon"):    pool.append((4, "skin_demon",    "demon",    "九幽魔君",   (180, 80, 255)))
            if _skin_ok("titan"):    pool.append((3, "skin_titan",    "titan",    "裂空雷将",   (120, 180, 255)))
            # 金币 + 少量钻石 + 再来一次 + 谢谢参与
            pool += [
                (10, "coins_30",    30,   "30 金币",   (255, 220, 90)),
                (9,  "coins_50",    50,   "50 金币",   (255, 220, 90)),
                (8,  "coins_80",    80,   "80 金币",   (255, 220, 90)),
                (7,  "coins_120",   120,  "120 金币",  (255, 220, 90)),
                (6,  "coins_200",   200,  "200 金币",  (255, 220, 90)),
                (5,  "coins_300",   300,  "300 金币",  (255, 220, 90)),
                (3,  "coins_500",   500,  "500 金币",  (255, 220, 90)),
                (5,  "diamonds_1",  1,    "1 钻石",    (180, 220, 255)),
                (4,  "diamonds_2",  2,    "2 钻石",    (180, 220, 255)),
                (3,  "diamonds_3",  3,    "3 钻石",    (220, 230, 255)),
                (18, "again",       None, "再来一次",  (120, 200, 255)),
                (16, "nothing",     None, "谢谢参与",  (130, 140, 175)),
            ]
        return pool

    def _reshuffle_lottery(self):
        """Q2：每日刷新 & 只抽未拥有皮肤。按权重随机抽取 12 个奖项并打乱。
        Q2更新：取消"全皮肤+全关卡"，确保12箱中至少1个随机皮肤。"""
        # ===== 每日刷新：若今天和上次不一样，重置箱子为 None（强制重新抽）=====
        today = self._today_str()
        if getattr(self, "_lottery_day", None) != today:
            self._lottery_day = today
            self._lottery_boxes = None
            self._lottery_revealed = {}
            self._lottery_anim = {}
            # 已抽的记录清空（新的一天重新洗牌 & 允许抽新奖）
            setattr(self, "_lottery_boxes_per_day", {})
        diamond_mode = bool(getattr(self, "_diamond_lottery", False))
        pool = self._lottery_pool(diamond_mode=diamond_mode)
        boxes = []
        skin_prize_count = 0
        max_skin_prizes = 2 if diamond_mode else 1
        has_again = False
        has_skin = False
        def _is_skin(k):
            return k.startswith("skin_")
        for _ in range(12):
            candidates = []
            for it in pool:
                k = it[1]
                if _is_skin(k) and skin_prize_count >= max_skin_prizes:
                    continue
                candidates.append(it)
            if not candidates:
                for it in pool:
                    if it[1] == "nothing":
                        candidates = [it]
                        break
            tw = sum(it[0] for it in candidates)
            r = random.uniform(0, tw)
            acc = 0.0
            pick = candidates[-1]
            for it in candidates:
                acc += it[0]
                if r <= acc:
                    pick = it
                    break
            w_, kind, payload, label, color = pick
            if _is_skin(kind):
                skin_prize_count += 1
                has_skin = True
            if kind == "again":
                has_again = True
            boxes.append((kind, payload, label, color))
        # Q2：确保至少1个皮肤奖品
        if not has_skin:
            # 从池中选一个皮肤奖品替换一个非皮肤、非"再来一次"的箱子
            skin_items = [it for it in pool if _is_skin(it[1])]
            if skin_items:
                random.shuffle(skin_items)
                skin_pick = skin_items[0]
                target = -1
                for i, (k, _, _, _) in enumerate(boxes):
                    if not _is_skin(k) and k != "again":
                        target = i
                        break
                if target < 0:
                    target = 0
                boxes[target] = (skin_pick[1], skin_pick[2], skin_pick[3], skin_pick[4])
        if not has_again:
            again_item = (None, "again", None, "再来一次", (120, 200, 255))
            for p in pool:
                if p[1] == "again":
                    again_item = (p[0], p[1], p[2], p[3], p[4])
                    break
            target = -1
            for i, (k, _, _, _) in enumerate(boxes):
                if not _is_skin(k) and k != "again":
                    target = i
                    if k == "nothing":
                        break
            if target < 0:
                target = 0
            boxes[target] = (again_item[1], again_item[2], again_item[3], again_item[4])
        random.shuffle(boxes)
        self._lottery_boxes = boxes

    def _lottery_page_switch_rect(self):
        """金币 / 钻石 抽奖 切换按钮（面板顶部右）。"""
        return pygame.Rect(WIDTH - 260, 78, 160, 38)

    def _lottery_draw(self, mx, my):
        """抽奖面板：12 箱 4×3 网格，点击抽奖。每天刷新 & 只抽未拥有皮肤。"""
        self._dim(200)
        panel = pygame.Rect(80, 70, WIDTH - 160, HEIGHT - 140)
        pygame.draw.rect(self.screen, (10, 12, 26), panel, border_radius=14)
        diamond_mode = bool(getattr(self, "_diamond_lottery", False))
        title_col = (90, 230, 255) if diamond_mode else NEON_PINK
        pygame.draw.rect(self.screen, title_col, panel, 2, border_radius=14)
        self._text("钻石抽奖" if diamond_mode else "星尘抽奖",
                   WIDTH // 2, 90, 28, title_col, bold=True, center=True)
        cost = self._lottery_cost()
        hold = self.diamonds if diamond_mode else self.coins
        unit = "钻石" if diamond_mode else "金币"
        self._text(f"持有{unit}: {hold}    每抽消耗 {cost} {unit}    每日自动刷新奖池(只抽未拥有)",
                   WIDTH // 2, 122, 14, NEON_YELLOW, center=True)
        # ===== 页切换按钮：金币 / 钻石 =====
        psr = self._lottery_page_switch_rect()
        psh = psr.collidepoint(mx, my)
        pygame.draw.rect(self.screen, (16, 18, 36), psr, border_radius=8)
        pygame.draw.rect(self.screen, (NEON_CYAN if diamond_mode else NEON_PINK), psr, 2, border_radius=8)
        self._text("← 切金币抽奖" if diamond_mode else "切钻石抽奖 →",
                   psr.centerx, psr.centery - 11, 15,
                   (NEON_CYAN if diamond_mode else NEON_PINK), bold=True, center=True)

        # 4×3 网格
        cols, rows = 4, 3
        cw, ch = 150, 130
        gx, gy = 14, 14
        grid_w = cols * cw + (cols - 1) * gx
        grid_h = rows * ch + (rows - 1) * gy
        x0 = (WIDTH - grid_w) // 2
        y0 = 150
        # 确保有预生成的箱子列表
        if not hasattr(self, "_lottery_boxes") or self._lottery_boxes is None:
            self._reshuffle_lottery()
        boxes = self._lottery_boxes
        if not hasattr(self, "_lottery_revealed"):
            self._lottery_revealed = {}  # idx -> (kind, payload, label, color)
        if not hasattr(self, "_lottery_anim"):
            self._lottery_anim = {}  # idx -> anim_t
        for i in range(12):
            kind, payload, label, col = boxes[i]
            r = i // cols
            c = i % cols
            rect = pygame.Rect(x0 + c * (cw + gx), y0 + r * (ch + gy), cw, ch)
            hover = rect.collidepoint(mx, my)
            # 箱子背景
            bg = (24, 18, 38) if i not in self._lottery_revealed else (30, 24, 20)
            pygame.draw.rect(self.screen, bg, rect, border_radius=8)
            pygame.draw.rect(self.screen, col if hover else (80, 70, 110), rect, 2, border_radius=8)
            # 箱子图标
            cx = rect.centerx
            cy = rect.centery - 14
            if i in self._lottery_revealed:
                k, pl, lb, cc = self._lottery_revealed[i]
                pygame.draw.rect(self.screen, cc, (cx - 30, cy - 18, 60, 36), border_radius=4)
                # 奖项名称换行
                lb_lines = self._wrap_text(lb, 68, 13, bold=True)
                lby = cy + 24
                for li in lb_lines[:2]:
                    self._text(li, cx, lby, 13, cc, center=True, bold=True)
                    lby += 16
                # 翻开动画
                anim = self._lottery_anim.get(i, 0)
                if anim < 1.0:
                    self._lottery_anim[i] = min(1.0, anim + 0.08)
                    glow_a = int(180 * (1 - anim))
                    g = get_glow(40, cc, alpha=glow_a)
                    self.screen.blit(g, g.get_rect(center=(cx, cy)),
                                     special_flags=pygame.BLEND_RGB_ADD)
            else:
                # 未开箱子：问号
                pygame.draw.rect(self.screen, (60, 50, 90), (cx - 30, cy - 18, 60, 36), border_radius=4)
                pygame.draw.rect(self.screen, (140, 120, 200), (cx - 30, cy - 18, 60, 36), 2, border_radius=4)
                self._text("?", cx, cy - 4, 26, NEON_YELLOW, bold=True, center=True)
                self._text(f"#{i+1}", cx, cy + 40, 13, DIM, center=True)

        # 关闭按钮
        close = pygame.Rect(WIDTH // 2 - 60, HEIGHT - 70, 120, 36)
        chover = close.collidepoint(mx, my)
        pygame.draw.rect(self.screen, (18, 20, 38), close, border_radius=8)
        pygame.draw.rect(self.screen, NEON_PINK, close, 2, border_radius=8)
        self._text("关闭 (ESC)", close.centerx, close.centery - 8, 14,
                   NEON_PINK if chover else WHITE, bold=True, center=True)

    def _lottery_click(self, mx, my):
        """点击抽奖面板：处理关闭/页切换/箱子点击。钻石模式扣钻石，金币模式扣金币。"""
        # 关闭按钮
        close = pygame.Rect(WIDTH // 2 - 60, HEIGHT - 70, 120, 36)
        if close.collidepoint(mx, my):
            self.show_lottery = False
            self._lottery_revealed = {}
            self._lottery_anim = {}
            self._play("tick")
            return
        # ===== 抽奖页切换：金币 ↔ 钻石 =====
        psr = self._lottery_page_switch_rect()
        if psr.collidepoint(mx, my):
            old = bool(getattr(self, "_diamond_lottery", False))
            self._diamond_lottery = not old
            self._lottery_boxes = None  # 强制重新按新模式洗牌
            self._lottery_revealed = {}
            self._lottery_anim = {}
            self._play("tick")
            return
        diamond_mode = bool(getattr(self, "_diamond_lottery", False))
        cost = self._lottery_cost()
        # 检查资源是否足够（F2 作弊不扣）
        if not getattr(self, "_lottery_unlocked", False):
            if diamond_mode:
                if self.diamonds < cost:
                    self._flash_msg = "钻石不足"
                    self._flash_timer = 1.2
                    self._play("hit")
                    return
            else:
                if self.coins < cost:
                    self._flash_msg = "金币不足"
                    self._flash_timer = 1.2
                    self._play("hit")
                    return
        if not hasattr(self, "_lottery_boxes") or self._lottery_boxes is None:
            self._reshuffle_lottery()
        boxes = self._lottery_boxes
        cols = 4
        cw, ch = 150, 130
        gx, gy = 14, 14
        grid_w = cols * cw + (cols - 1) * gx
        x0 = (WIDTH - grid_w) // 2
        y0 = 150
        for i in range(12):
            kind, payload, label, col = boxes[i]
            r = i // cols
            c = i % cols
            rect = pygame.Rect(x0 + c * (cw + gx), y0 + r * (ch + gy), cw, ch)
            if rect.collidepoint(mx, my):
                if i in self._lottery_revealed:
                    self._play("tick")
                    return
                # 扣费（钻石/金币）
                if not getattr(self, "_lottery_unlocked", False):
                    if diamond_mode:
                        self.diamonds -= cost
                    else:
                        self.coins -= cost
                self._lottery_revealed[i] = (kind, payload, label, col)
                self._lottery_anim[i] = 0.0
                self._apply_lottery_prize(kind, payload)
                self._save_game()
                return

    def _apply_lottery_prize(self, kind, payload):
        """应用抽奖奖项到游戏状态。"""
        if kind == "all":
            self.unlocked = len(LEVELS)
            self.dungeon_unlocked = len(self.DUNGEON_LEVELS)
            for sid in SKINS:
                self.owned_skins.add(sid)
            self._flash_msg = "解锁全皮肤 + 全关卡！"
            self._flash_timer = 3.0
            self._play("win")
            self.burst(WIDTH // 2, HEIGHT // 2, (255, 200, 80), 60, 360, size=4.0, life=1.0)
        elif kind.startswith("skin_"):
            sid = kind[len("skin_"):]
            if sid in SKINS:
                self.owned_skins.add(sid)
                self._flash_msg = f"解锁皮肤：{SKINS[sid][0]}"
            else:
                self._flash_msg = "解锁皮肤成功"
            self._flash_timer = 2.4
            self._play("buy")
            self._save_game()
        elif kind.startswith("coins_"):
            n = int(kind.split("_")[1])
            self.coins += n
            self._flash_msg = f"获得 {n} 金币"
            self._flash_timer = 1.6
            self._play("coin")
            self._save_game()
        elif kind.startswith("diamonds_"):
            n = int(kind.split("_")[1])
            self.diamonds += n
            self._flash_msg = f"获得 {n} 钻石"
            self._flash_timer = 1.8
            self._play("buy")
            self._save_game()
        elif kind == "again":
            # 退回本次消耗（钻石抽奖退钻石，金币抽奖退金币）
            diamond_mode = bool(getattr(self, "_diamond_lottery", False))
            refund = self._lottery_cost()
            if diamond_mode:
                self.diamonds += refund
                self._flash_msg = f"再来一次！已退回 {refund} 钻石"
            else:
                self.coins += refund
                self._flash_msg = f"再来一次！已退回 {refund} 金币"
            self._flash_timer = 1.6
            self._play("select")
        else:
            self._flash_msg = "谢谢参与"
            self._flash_timer = 1.2
            self._play("tick")

    def _shop_card_rect(self, idx):
        """商店中每个皮肤卡片的位置。
        Q6：终极页（page=3）改为 3 条横排，1 个武器一条，3 个占满整页。
        其余页保持 3×3 九宫格。"""
        page = getattr(self, "shop_page", 0)
        if page == 3:
            # 终极页：3 个横条卡片，1 个一行
            cw, ch = 800, 150
            gx, gy = 0, 10
            x0 = (WIDTH - cw) // 2
            y0 = 165
            return pygame.Rect(x0, y0 + idx * (ch + gy), cw, ch)
        cols = 3
        cw, ch = 270, 128
        gx, gy = 12, 10
        x0 = (WIDTH - (cols * cw + (cols - 1) * gx)) // 2
        y0 = 150
        r = idx // cols
        c = idx % cols
        return pygame.Rect(x0 + c * (cw + gx), y0 + r * (ch + gy), cw, ch)

    def _shop_ordered_ids(self, page=None):
        """按价格升序返回皮肤ID列表：
        - page=0: 第一页（金币皮肤，按金币升序）
        - page=1: 第二页（钻石皮肤，按钻石数量升序）
        - page=2: 第三页（混合皮肤：金币+钻石，按总价升序）
        - page=3: 第四页（终极皮肤：金币+钻石，3个最强皮肤）
        - page=None: 全部皮肤（金币→钻石→混合→终极）
        """
        gold_items = []
        diamond_items = []
        mix_items = []  # [(sid, 金币, 钻石)]
        for sid in SKINS:
            price = SKINS[sid][1]
            if isinstance(price, tuple) and price:
                if price[0] == "diamond":
                    diamond_items.append((sid, price[1]))
                elif price[0] == "mix" and len(price) >= 3:
                    mix_items.append((sid, int(price[1]), int(price[2])))
                else:
                    gold_items.append((sid, 0))
            else:
                gold_items.append((sid, price))
        gold_items.sort(key=lambda x: x[1])
        diamond_items.sort(key=lambda x: x[1])
        # 混合按"钻石主导+金币辅助"排序（先钻石后金币）
        mix_items.sort(key=lambda x: (x[2], x[1]))
        # Q4：分离终极皮肤（第四页）和普通混合皮肤（第三页）
        _ultimate_ids = {"origin", "paradox", "finality"}
        ultimate_items = [it for it in mix_items if it[0] in _ultimate_ids]
        regular_mix = [it for it in mix_items if it[0] not in _ultimate_ids]
        if page == 0:
            return [sid for sid, _ in gold_items]
        if page == 1:
            return [sid for sid, _ in diamond_items]
        if page == 2:
            return [sid for sid, _, _ in regular_mix]
        if page == 3:
            return [sid for sid, _, _ in ultimate_items]
        return ([sid for sid, _ in gold_items] +
                [sid for sid, _ in diamond_items] +
                [sid for sid, _, _ in regular_mix] +
                [sid for sid, _, _ in ultimate_items])

    def _draw_shop_skin_preview(self, sid, cx, cy, col, **kwargs):
        """商店中已装备皮肤的动态特效预览（半径默认16，终极页可传更大值）。"""
        t = pygame.time.get_ticks() * 0.001
        r = kwargs.get("r", 16)
        # 主体球 + 光晕
        pg = get_glow(int(r * 2.2), col, alpha=180)
        self.screen.blit(pg, pg.get_rect(center=(cx, cy)),
                         special_flags=pygame.BLEND_RGB_ADD)
        pygame.draw.circle(self.screen, col, (cx, cy), r)
        pygame.draw.circle(self.screen, WHITE, (cx, cy), r, 2)
        # 各皮肤特效（精简版）
        if sid == "tri":
            cols = [(255, 70, 90), (90, 130, 255), (255, 220, 80)]
            for i, c in enumerate(cols):
                a0 = t * 2 + i * (math.tau / 3)
                rect = pygame.Rect(0, 0, int(r * 2 + 14), int(r * 2 + 14))
                rect.center = (cx, cy)
                pygame.draw.arc(self.screen, c, rect, a0, a0 + 1.0, 3)
        elif sid == "moon":
            pygame.draw.circle(self.screen, (40, 50, 80),
                               (int(cx + r * 0.4), int(cy - r * 0.2)), int(r * 0.8))
            for i in range(5):
                a = t + i * (math.tau / 5)
                px = cx + math.cos(a) * (r + 8)
                py = cy + math.sin(a) * (r + 8)
                pygame.draw.line(self.screen, (220, 240, 255),
                                 (px, py), (px + math.cos(a) * 4, py + math.sin(a) * 4), 2)
        elif sid == "sun":
            for i in range(12):
                a = t * 1.5 + i * (math.tau / 12)
                L = r + 10 + 6 * math.sin(t * 4 + i)
                pygame.draw.line(self.screen, (255, 200, 80),
                                 (cx + math.cos(a) * r, cy + math.sin(a) * r),
                                 (cx + math.cos(a) * L, cy + math.sin(a) * L), 2)
        elif sid == "rainbow":
            for i in range(7):
                c = RAINBOW_COLORS[i]
                a0 = t * 2 + i * (math.tau / 7)
                rect = pygame.Rect(0, 0, int(r * 2 + 10 + i * 2), int(r * 2 + 10 + i * 2))
                rect.center = (cx, cy)
                pygame.draw.arc(self.screen, c, rect, a0, a0 + 0.5, 2)
        elif sid == "void":
            for i in range(3):
                a = t * 3 + i * (math.tau / 3)
                rr = r + 6 + i * 4
                for k in range(6):
                    aa = a + k * 0.3
                    px = cx + math.cos(aa) * (rr + k * 2)
                    py = cy + math.sin(aa) * (rr + k * 2)
                    pygame.draw.circle(self.screen, (180, 90, 255),
                                       (int(px), int(py)), 1)
        elif sid == "inferno":
            for i in range(14):
                a = t * 4 + i * (math.tau / 14)
                L = r + 8 + 8 * (0.5 + 0.5 * math.sin(t * 8 + i * 1.3))
                fc = (255, 90 + int(80 * math.sin(t * 6 + i)), 30)
                pygame.draw.line(self.screen, fc,
                                 (cx + math.cos(a) * r, cy + math.sin(a) * r),
                                 (cx + math.cos(a) * L, cy + math.sin(a) * L), 3)
        elif sid == "frost":
            for i in range(6):
                a = t * 0.8 + i * (math.tau / 6)
                ex = cx + math.cos(a) * (r + 10)
                ey = cy + math.sin(a) * (r + 10)
                pygame.draw.line(self.screen, (180, 230, 255),
                                 (cx + math.cos(a) * r, cy + math.sin(a) * r), (ex, ey), 2)
        elif sid == "thunder":
            for i in range(8):
                a = t * 5 + i * (math.tau / 8)
                ex = cx + math.cos(a) * (r + 6) + random.uniform(-3, 3)
                ey = cy + math.sin(a) * (r + 6) + random.uniform(-3, 3)
                pygame.draw.line(self.screen, (255, 240, 120),
                                 (cx + math.cos(a) * r, cy + math.sin(a) * r), (ex, ey), 2)
        elif sid == "chaos":
            cols = [(200, 80, 255), (255, 90, 30), (90, 200, 255), (255, 240, 100)]
            for i in range(16):
                a = t * 3 + i * (math.tau / 16)
                L = r + 8 + 6 * math.sin(t * 6 + i)
                c = cols[i % 4]
                pygame.draw.line(self.screen, c,
                                 (cx + math.cos(a) * r, cy + math.sin(a) * r),
                                 (cx + math.cos(a) * L, cy + math.sin(a) * L), 2)
        # ===== 钻石页皮肤预览 =====
        elif sid == "judge":
            # 天罚之眼：天眼金光扫射
            for i in range(8):
                a = t * 4 + i * (math.tau / 8)
                ex = cx + math.cos(a) * (r + 12)
                ey = cy + math.sin(a) * (r + 12)
                pygame.draw.line(self.screen, (255, 240, 200),
                                 (cx, cy), (ex, ey), 2)
            pygame.draw.circle(self.screen, (255, 255, 220), (cx, cy), 4)
        elif sid == "dragon":
            # 真龙帝皇：龙焰环绕
            for i in range(10):
                a = t * 2.5 + i * (math.tau / 10)
                rr = r + 6 + 4 * math.sin(t * 5 + i)
                px = cx + math.cos(a) * rr
                py = cy + math.sin(a) * rr
                pygame.draw.circle(self.screen, (255, 180, 80), (int(px), int(py)), 2)
        elif sid == "demon":
            # 九幽魔君：紫色魔焰
            for i in range(12):
                a = t * 3 + i * (math.tau / 12)
                L = r + 6 + 8 * (0.5 + 0.5 * math.sin(t * 7 + i))
                fc = (120 + int(60 * math.sin(t * 5 + i)), 60, 200)
                pygame.draw.line(self.screen, fc,
                                 (cx + math.cos(a) * r, cy + math.sin(a) * r),
                                 (cx + math.cos(a) * L, cy + math.sin(a) * L), 2)
        elif sid == "stellar":
            # 星海主宰：星辰轨道
            for i in range(3):
                a = t * 2 + i * (math.tau / 3)
                rr = r + 8 + i * 4
                px = cx + math.cos(a) * rr
                py = cy + math.sin(a) * rr
                pygame.draw.circle(self.screen, (150, 220, 255), (int(px), int(py)), 3)
                pygame.draw.circle(self.screen, (200, 240, 255), (int(px), int(py)), 1)
        elif sid == "samsara":
            # 六道轮回：6道轮回环
            for i in range(6):
                a = t * 1.5 + i * (math.tau / 6)
                rr = r + 10
                px = cx + math.cos(a) * rr
                py = cy + math.sin(a) * rr
                pygame.draw.circle(self.screen, (200, 160, 255), (int(px), int(py)), 2)
        elif sid == "寂灭":
            # 寂灭神皇：湮灭光环
            for ring in (r + 6, r + 12):
                rect = pygame.Rect(0, 0, int(ring * 2), int(ring * 2))
                rect.center = (cx, cy)
                pygame.draw.arc(self.screen, (255, 200, 255), rect, t * 2, t * 2 + 2.5, 2)
        elif sid == "primal":
            # 鸿蒙之始：混沌双旋
            for sgn in (-1, 1):
                for i in range(6):
                    a = t * 3 * sgn + i * (math.tau / 6)
                    rr = r + 6 + i * 2
                    px = cx + math.cos(a) * rr
                    py = cy + math.sin(a) * rr
                    pygame.draw.circle(self.screen, (220, 255, 200), (int(px), int(py)), 1)
        elif sid == "taiji":
            # 太上无极：太极阴阳
            for sgn, c in ((-1, (90, 220, 255)), (1, (255, 90, 90))):
                a = t * 2 + sgn * 0.5
                px = cx + math.cos(a) * (r + 8)
                py = cy + math.sin(a) * (r + 8)
                pygame.draw.circle(self.screen, c, (int(px), int(py)), 3)
        elif sid == "nirvana":
            # 大道涅槃：涅槃火环
            for i in range(14):
                a = t * 4 + i * (math.tau / 14)
                L = r + 8 + 6 * math.sin(t * 8 + i)
                pygame.draw.line(self.screen, (255, 220, 120),
                                 (cx + math.cos(a) * r, cy + math.sin(a) * r),
                                 (cx + math.cos(a) * L, cy + math.sin(a) * L), 2)
        # ===== 至高页皮肤预览 =====
        elif sid == "titan":
            # 裂空雷将：双雷环绕
            for i in range(8):
                a = t * 5 + i * (math.tau / 8)
                ex = cx + math.cos(a) * (r + 8) + random.uniform(-2, 2)
                ey = cy + math.sin(a) * (r + 8) + random.uniform(-2, 2)
                pygame.draw.line(self.screen, (120, 180, 255),
                                 (cx + math.cos(a) * r, cy + math.sin(a) * r), (ex, ey), 2)
        elif sid == "qinglong":
            # 沧溟潮君：水波环
            for i in range(3):
                rr = r + 6 + i * 5
                rect = pygame.Rect(0, 0, int(rr * 2), int(rr * 2))
                rect.center = (cx, cy)
                pygame.draw.arc(self.screen, (60, 220, 160), rect, t + i, t + i + 2.0, 2)
        elif sid == "baihu":
            # 碎雪巡使：雪刃闪
            for i in range(6):
                a = t * 4 + i * (math.tau / 6)
                ex = cx + math.cos(a) * (r + 10)
                ey = cy + math.sin(a) * (r + 10)
                pygame.draw.line(self.screen, (240, 250, 255),
                                 (cx + math.cos(a) * r, cy + math.sin(a) * r), (ex, ey), 2)
        elif sid == "zhuque":
            # 燎原武侯：火焰环绕
            for i in range(12):
                a = t * 3 + i * (math.tau / 12)
                L = r + 8 + 6 * math.sin(t * 6 + i)
                pygame.draw.line(self.screen, (255, 120, 60),
                                 (cx + math.cos(a) * r, cy + math.sin(a) * r),
                                 (cx + math.cos(a) * L, cy + math.sin(a) * L), 2)
        elif sid == "xuanwu":
            # 玄冰卫圣：冰晶环
            for i in range(6):
                a = t * 1.5 + i * (math.tau / 6)
                px = cx + math.cos(a) * (r + 8)
                py = cy + math.sin(a) * (r + 8)
                pygame.draw.line(self.screen, (160, 220, 255),
                                 (cx, cy), (px, py), 2)
        elif sid == "stargod":
            # 星陨领主：8星轨道
            for i in range(8):
                a = t * 2 + i * (math.tau / 8)
                px = cx + math.cos(a) * (r + 10)
                py = cy + math.sin(a) * (r + 10)
                pygame.draw.circle(self.screen, (255, 230, 120), (int(px), int(py)), 2)
        elif sid == "chrono":
            # 时空猎手：紫色时空裂隙
            for i in range(3):
                a = t * 3 + i * (math.tau / 3)
                rr = r + 8 + i * 3
                rect = pygame.Rect(0, 0, int(rr * 2), int(rr * 2))
                rect.center = (cx, cy)
                pygame.draw.arc(self.screen, (180, 120, 255), rect, a, a + 1.2, 2)
        elif sid == "buddha":
            # 不灭尊者：金佛光环
            for i in range(9):
                a = t * 2 + i * (math.tau / 9)
                px = cx + math.cos(a) * (r + 10)
                py = cy + math.sin(a) * (r + 10)
                pygame.draw.circle(self.screen, (255, 200, 80), (int(px), int(py)), 2)
        elif sid == "god":
            # 极律虚皇：圣光柱
            for i in range(6):
                a = t * 2 + i * (math.tau / 6)
                ex = cx + math.cos(a) * (r + 12)
                ey = cy + math.sin(a) * (r + 12)
                pygame.draw.line(self.screen, (255, 255, 200),
                                 (cx + math.cos(a) * r, cy + math.sin(a) * r), (ex, ey), 2)
        # ===== 终极武器皮肤预览 =====
        elif sid == "origin":
            # 生命起源：12色元素旋转环 + 创世核脉动
            elems = self._origin_elements() if hasattr(self, "_origin_elements") else None
            pulse = 1.0 + 0.15 * math.sin(t * 4)
            g0 = get_glow(int(r * 2.5 * pulse), (100, 255, 180), alpha=120)
            self.screen.blit(g0, g0.get_rect(center=(cx, cy)),
                             special_flags=pygame.BLEND_RGB_ADD)
            if elems:
                for i, (nm, ec, dmg, eff) in enumerate(elems):
                    a = t * 1.5 + i * (math.tau / 12)
                    orb_r = r + 12 + 3 * math.sin(t * 5 + i)
                    px = cx + math.cos(a) * orb_r
                    py = cy + math.sin(a) * orb_r
                    g_orb = get_glow(10, ec, alpha=150)
                    self.screen.blit(g_orb, g_orb.get_rect(center=(int(px), int(py))),
                                     special_flags=pygame.BLEND_RGB_ADD)
                    pygame.draw.circle(self.screen, ec, (int(px), int(py)), 4)
            # 生命之树放射线
            for i in range(6):
                a = t * 0.5 + i * (math.tau / 6)
                ex = cx + math.cos(a) * (r + 28)
                ey = cy + math.sin(a) * (r + 28)
                pygame.draw.line(self.screen, (120, 255, 180),
                                 (cx, cy), (int(ex), int(ey)), 2)
            # 创世核
            pygame.draw.circle(self.screen, (255, 255, 255), (cx, cy), int(r * 0.4))
            pygame.draw.circle(self.screen, (100, 255, 180), (cx, cy), int(r * 0.25))
        elif sid == "paradox":
            # 逆悖突进：紫黑扭曲漩涡 + 裂隙闪电 + 暗核
            pulse = 1.0 + 0.2 * math.sin(t * 5)
            g0 = get_glow(int(r * 2.8 * pulse), (200, 100, 255), alpha=130)
            self.screen.blit(g0, g0.get_rect(center=(cx, cy)),
                             special_flags=pygame.BLEND_RGB_ADD)
            # 3层扭曲弧
            for li in range(3):
                rr = r + 10 + li * 6
                rect = pygame.Rect(0, 0, int(rr * 2), int(rr * 2))
                rect.center = (cx, cy)
                col_v = [(160, 60, 220), (200, 100, 255), (240, 180, 255)][li]
                pygame.draw.arc(self.screen, col_v, rect,
                                t * (2 + li) + li, t * (2 + li) + li + 3.0, 3)
            # 裂隙闪电
            for i in range(4):
                a = t * 3 + i * (math.tau / 4)
                prev_x, prev_y = float(cx), float(cy)
                for si in range(1, 5):
                    dist = r + 6 + si * 6
                    jitter = random.uniform(-5, 5)
                    px = cx + math.cos(a) * dist + jitter
                    py = cy + math.sin(a) * dist + jitter
                    pygame.draw.line(self.screen, (220, 160, 255),
                                     (int(prev_x), int(prev_y)), (int(px), int(py)), 2)
                    prev_x, prev_y = px, py
            # 暗核
            pygame.draw.circle(self.screen, (60, 20, 80), (cx, cy), int(r * 0.45))
            pygame.draw.circle(self.screen, (200, 100, 255), (cx, cy), int(r * 0.28))
            pygame.draw.circle(self.screen, (255, 220, 255), (cx, cy), int(r * 0.12))
        elif sid == "finality":
            # 终焉：血红黑末日光环 + 死亡镰刀影 + 灭世黑核
            pulse = 1.0 + 0.25 * math.sin(t * 3)
            g0 = get_glow(int(r * 3.0 * pulse), (255, 30, 30), alpha=140)
            self.screen.blit(g0, g0.get_rect(center=(cx, cy)),
                             special_flags=pygame.BLEND_RGB_ADD)
            # 3层血色弧
            for li in range(3):
                rr = r + 8 + li * 8
                rect = pygame.Rect(0, 0, int(rr * 2), int(rr * 2))
                rect.center = (cx, cy)
                col_r = [(180, 20, 20), (220, 40, 40), (255, 80, 80)][li]
                pygame.draw.arc(self.screen, col_r, rect,
                                -t * (1.5 + li * 0.5) + li, -t * (1.5 + li * 0.5) + li + 3.5, 3)
            # 2把旋转镰刀影
            for i in range(2):
                a = t * 1.5 + i * math.pi
                scythe_r = r + 24
                for k in range(5):
                    ka = a + (k - 2) * 0.12
                    kx = cx + math.cos(ka) * (scythe_r + k * 3)
                    ky = cy + math.sin(ka) * (scythe_r + k * 3)
                    pygame.draw.circle(self.screen, (255, 50, 50),
                                       (int(kx), int(ky)), 4 - k // 2)
                pygame.draw.line(self.screen, (120, 20, 20),
                                 (cx, cy),
                                 (int(cx + math.cos(a) * scythe_r),
                                  int(cy + math.sin(a) * scythe_r)), 2)
            # 灭世黑核
            pygame.draw.circle(self.screen, (40, 0, 0), (cx, cy), int(r * 0.5))
            pygame.draw.circle(self.screen, (200, 20, 20), (cx, cy), int(r * 0.32))
            pygame.draw.circle(self.screen, (255, 100, 100), (cx, cy), int(r * 0.15))

    def _shop_prev_page_rect(self):
        # 左翻页：左上（金币皮肤页按钮位置固定）
        return pygame.Rect(80, 88, 112, 34)

    def _shop_next_page_rect(self):
        return pygame.Rect(WIDTH - 80 - 112, 88, 112, 34)

    def _handle_shop_click(self, mx, my):
        # 关闭按钮（与_draw_shop中的新尺寸保持一致）
        if self._shop_close_rect().collidepoint(mx, my):
            self.show_shop = False
            self.shop_page = 0
            self._play("tick")
            return
        # 翻页按钮
        if self._shop_prev_page_rect().collidepoint(mx, my):
            self.shop_page = max(0, self.shop_page - 1)
            self._play("tick")
            return
        if self._shop_next_page_rect().collidepoint(mx, my):
            self.shop_page = min(3, self.shop_page + 1)
            self._play("tick")
            return
        is_p2 = self.show_shop == "p2"
        # P2 商店：跟随 P1 按钮（清除 P2 独立皮肤）
        if is_p2 and self._shop_follow_rect().collidepoint(mx, my):
            self.active_skin_p2 = None
            self._play("select")
            self._save_game()
            return
        skin_ids = self._shop_ordered_ids(page=self.shop_page)
        for i, sid in enumerate(skin_ids):
            if self._shop_card_rect(i).collidepoint(mx, my):
                name, cost, col, desc = SKINS[sid]
                is_diamond = isinstance(cost, tuple) and cost and cost[0] == "diamond"
                is_mix = isinstance(cost, tuple) and cost and cost[0] == "mix" and len(cost) >= 3
                if sid in self.owned_skins:
                    # 切换装备
                    if is_p2:
                        self.active_skin_p2 = None if self.active_skin_p2 == sid else sid
                    else:
                        self.active_skin = None if self.active_skin == sid else sid
                    self._play("select")
                else:
                    infinite_c = getattr(self, "_infinite_coins", False)
                    infinite_d = getattr(self, "_infinite_diamonds", False)
                    paid_ok = False
                    if is_diamond:
                        diamond_amount = cost[1]
                        if self.diamonds >= diamond_amount or infinite_d:
                            if not infinite_d:
                                self.diamonds -= diamond_amount
                            else:
                                self.diamonds = max(self.diamonds, 99999)
                            paid_ok = True
                    elif is_mix:
                        # 混合支付：金币+钻石一起扣（两项都要满足）
                        coin_cost = int(cost[1])
                        diamond_cost = int(cost[2])
                        coin_enough = (self.coins >= coin_cost) or infinite_c
                        diamond_enough = (self.diamonds >= diamond_cost) or infinite_d
                        if coin_enough and diamond_enough:
                            if not infinite_c:
                                self.coins -= coin_cost
                            else:
                                self.coins = max(self.coins, 99999)
                            if not infinite_d:
                                self.diamonds -= diamond_cost
                            else:
                                self.diamonds = max(self.diamonds, 99999)
                            paid_ok = True
                    else:
                        if self.coins >= cost or infinite_c:
                            if not infinite_c:
                                self.coins -= cost
                            else:
                                self.coins = max(self.coins, 99999)
                            paid_ok = True
                    if paid_ok:
                        self.owned_skins.add(sid)
                        # 购买后默认装备：P2商店就装备P2，否则装备P1
                        if is_p2:
                            self.active_skin_p2 = sid
                        else:
                            self.active_skin = sid
                        self._play("buy")
                    else:
                        self._play("hit")
                self._save_game()
                return
        # 点击空白处不关闭（避免误触），仅关闭按钮关闭

    def _draw_help(self):
        self._dim(190)
        x0, y0 = 60, 34
        w, h = WIDTH - 120, HEIGHT - 48
        panel = pygame.Rect(x0, y0, w, h)
        pygame.draw.rect(self.screen, (10, 12, 26), panel, border_radius=12)
        pygame.draw.rect(self.screen, NEON_CYAN, panel, 2, border_radius=12)
        self._text("游戏说明", WIDTH // 2, y0 + 24, 32, NEON_CYAN, bold=True, center=True)

        # 关闭/翻页按钮行（统一放在底部，顶到面板下边缘；内容顶到按钮上一行）
        btn_row_y = y0 + h - 58
        prev = self._help_prev_rect()
        nxt = self._help_next_rect()
        cls = self._help_close_rect()
        # 让按钮垂直对齐到 btn_row_y
        for b in (prev, nxt, cls):
            b.y = btn_row_y
            if False:
                pass
        # 重新计算 rect helper 函数：此处重新定位按钮本身（实际 rect 函数返回时，我们在下面用新定位）

        pages = [
            [
                ("目标", "吞噬比自己小的星体成长，达到本关吞噬数即过关；撞到更大的刺球会扣命。"),
                ("", ""),
                ("操作", ""),
                ("  单人", "鼠标/手势(食指)/方向键控制球；左键·伸掌·V 加速。"),
                ("  ", "右键/握拳/B 触发皮肤专有技能（需穿戴皮肤）。"),
                ("  ", "H 循环切换 鼠标→手势→方向键。"),
                ("  双人", "P1: WASD + V 加速 + B 技能；P2: 方向键 + M 加速 + ] 技能。"),
                ("  通用", "T 切换单/双人  空格/回车/点击 开始"),
                ("  ", "P 暂停  Q 返回地图  R 重开  F3 撤销F2  F4 静音  F11 全屏"),
                ("  ", "ESC: 暂停/返回地图；地图状态下按 ESC 先弹确认窗（Y退出/N或ESC取消），不会直接退出。"),
                ("", ""),
                ("道具（吃到即生效）", ""),
                ("  护盾S", "抵挡一次碰撞，破裂时顺便毁掉碰到的敌人。"),
                ("  磁吸M", "强力吸附附近星体与道具到身边。"),
                ("  时停T", "减慢所有星体速度，获得更久反应窗口。"),
                ("  双倍×", "一段时间内得分翻倍（含吞噬得分）。"),
                ("  炸弹B", "清除场上高威胁的大刺球。"),
                ("  缩小↓", "自身体积缩小 30%，更易穿过密集敌群。"),
                ("  幻影φ", "短暂无敌穿透，可径直穿过敌球不受伤。"),
                ("  加命+ / 加分$", "立即增加 1 条命 / 直接加分。"),
                ("  黑洞◎", "生成一个黑洞：2/3 半径内吞噬，外圈还会持续灼伤。"),
                ("  光枪枪", "数秒内自动连射光弹，对敌球造成生命伤害。"),
                ("  光刃刀", "360° 旋刃持续 4 秒，削减一切触碰敌人的生命。"),
            ],
            [
                ("金币支付 · 9 个皮肤：左键/右键技能说明 + 耗能", ""),
                ("  1 三色灵球 50金", "右键（耗能8）循环切换 红/黄/蓝 三态：黄→获得护盾6秒；蓝→加速×1.6并缩小；红→丢出炸弹。"),
                ("  2 月华之球 80金", "右键（耗能10）缩小30%持续8秒，可穿过更窄缝隙；再按右键还原（不耗能）。"),
                ("  3 烈阳之球 120金", "左键（耗能6）发光排斥敌球+加速；右键（耗能45）一圈光波击退全场敌人。"),
                ("  4 虹光七彩 150金", "右键（耗能12）循环切色；左键（耗能30）激活 红护盾/橙磁吸/黄时停/绿幻影/青加分/蓝缩小/紫黑洞，时长为普通道具30%。"),
                ("  5 霜冻冰魄 300金", "左键（耗能15）冰粒命中敌人冰冻3秒；右键（耗能55）全屏冻结4秒，所有敌人减速+冻结。"),
                ("  6 雷霆战神 500金", "左键（耗能20）追踪电球伤害+击退；右键（耗能75）围绕自身八道雷击3秒周期清场。"),
                ("  7 深渊黑洞 700金", "左键（耗能40）螺旋黑洞3秒前进吞噬；右键（耗能90）六方向黑洞清屏。"),
                ("  8 炼狱炎魂 200金", "左键（耗能14）穿透火球；右键（耗能50）变大+5秒灼烧环持续烧血。"),
                ("  9 混沌魔神 900金", "左键（耗能30）钩锁吸血；右键（耗能80）六把飞剑围绕自身10秒削血。"),
            ],
            [
                ("钻石支付 · 9 个霸气皮肤 · 通关副本获得钻石", ""),
                ("  1 天罚之眼 钻5", "左键（耗能18）穿透审判光弹；右键（耗能95）天眼激光横扫全场。"),
                ("  2 真龙帝皇 钻10", "左键（耗能22）帝皇火球追踪+爆炸范围；右键（耗能100）咆哮龙卷击飞+爆发伤害。"),
                ("  3 九幽魔君 钻15", "左键（耗能16）魔焰弹+毒雾腐蚀；右键（耗能105）骷髅群吸血玩家。"),
                ("  4 星海主宰 钻25", "左键（耗能20）星轨弹弧形切割；右键（耗能120）陨石雨大面积轰炸。"),
                ("  5 六道轮回 钻40", "左键（耗能25）轮回印·敌人死亡返还能量；右键（耗能110）3秒内受伤可自动回退。"),
                ("  6 寂灭神皇 钻60", "左键（耗能30）寂灭射线瞬间湮灭小半径；右键（耗能130）创世莲无敌+回血+爆炸清屏。"),
                ("  7 鸿蒙之始 钻90", "左键（耗能35）鸿蒙一炁吸万物于一点；右键（耗能140）两仪生灭双螺旋黑洞吞噬。"),
                ("  8 太上无极 钻130", "左键（耗能28）青红双剑自动连击；右键（耗能150）太极阵12秒反弹+减速。"),
                ("  9 大道涅槃 钻200", "左键（被动）每局限1次死亡原地复活；右键（耗能200）不灭金身12秒全免伤+反伤。"),
            ],
            [
                ("至高霸气皮肤", ""),
                ("  1 雷霆霸主 500金+钻10", "左键（耗能25）泰坦雷锤追踪电击；右键（耗能120）雷霆领域8秒全场减速+周期雷击。"),
                ("  2 碧海龙王 600金+钻15", "左键（耗能26）青龙吐珠大范围爆炸；右键（耗能130）6条青龙护体10秒清敌。"),
                ("  3 霜风猎王 700金+钻20", "左键（耗能22）三道穿透风刃；右键（耗能125）冲击波+4只白虎分身冲撞5秒。"),
                ("  4 赤焰战神 900金+钻30", "左键（耗能28）天火连射穿透；右键（每局限1次被动）死亡回满血复活+爆炸清屏。"),
                ("  5 玄冰卫圣 1200金+钻40", "左键（耗能30）锥形冰刺冻结路径；右键（耗能140）玄武巨龟护盾10秒无敌+反弹。"),
                ("  6 星陨领主 1500金+钻55", "左键（耗能40）超大陨石群天降5秒；右键（耗能160）8颗恒星围绕自转8秒碰撞爆炸。"),
                ("  7 时空猎手 2000金+钻70", "左键（耗能15）裂空闪瞬移+0.3s无敌；右键（耗能40）巨爪裂空发射巨大爪子击退敌人。"),
                ("  8 不灭尊者 2800金+钻90", "左键（耗能38）金色佛手印击退+大量伤害；右键（耗能200）9座金佛净化光波全屏清屏。"),
                ("  9 九天至尊 4000金+钻150", "左键（耗能50）九道神圣光柱轰炸；右键（耗能260）神皇降世15秒全属性×2无限护盾伤害翻倍。"),
            ],
            [
                ("金币 / 钻石 / 皮肤（续）", ""),
                ("  金币", "通关关卡、拾取金币道具、小概率拾取敌球掉落获得。"),
                ("  钻石", "仅副本关卡通关奖励（越难给越多），用于解锁霸气二、三页皮肤。"),
                ("暂停换皮", "暂停中可直接切换已拥有皮肤（左右键/数字键 立即生效；空格=继续）。"),
                ("双人皮肤", "双人模式下 P1/P2 可各自装备不同皮肤；若 P2 未指定则跟随 P1。"),
                ("能量机制", "每个玩家独立能量条，左右键均消耗；能量随时间回复，空能量释放技能失败（不扣）。"),
                ("", ""),
                ("敌方刺球（拥有生命值，多种形态与种族）", ""),
                ("  尖刺", "常规敌 · 参差尖刺 + 邪眼，体积越大越凶残。"),
                ("  病毒", "绿色蛋白壳突起，生命较高，死亡分裂成两个小球。"),
                ("  三球 / 双球", "多球体旋转复合体，击中其中一节整体受伤。"),
                ("  虫群", "长条形虫子，身段跟随头部，喜欢合围玩家。"),
                ("  长蛇", "多球连节长蛇，击破头部才整体死亡，其余节分裂成独立小蛇。"),
                ("  恐怖种", "血红骷髅头+双牛角+嘴部尖牙，死亡会再分裂两次。"),
                ("  牛魔王", "双巨角+鼻环，生命超高但死亡也会分裂。"),
                ("  幽灵", "半透明可穿墙，中高威胁，带寒气减速。"),
                ("  深渊血魔", "巨敌 · 黑紫外环+血核（出现时警示音）。"),
                ("  霜冻敌人", "被冰系技能命中显示冰蓝色，减速/冻结中更易击败。"),
            ],
            [
                ("终极武器", ""),
                ("  生命起源", "5000金+200钻"),
                ("", "左键（耗能3）元素循环：发射12种元素球自动循环，每次发射不同元素；"),
                ("", "  火·灼烧 | 冰·冻结 | 电·连锁 | 磁·吸引 | 铁·击退 | 暗·吸血"),
                ("", "  黑洞·吞噬 | 光·穿透 | 毒·减速 | 雷·范围 | 风·扩散 | 土·眩晕"),
                ("", "右键（耗能5）万物复苏：召唤12元素球环绕护体8秒+HP加到5。"),
                ("", ""),
                ("  逆悖突进", "8000金+350钻"),
                ("", "左键（耗能4）悖论炮循环：发射4种圆柱炮自动循环，每次发射不同炮型；"),
                ("", "  灭磁炮·吸引 | 毒素炮·减速+毒雾 | 极冻炮·冻结 | 毁灭炮·爆炸震屏"),
                ("", "右键（耗能5）六光柱：展开6根光柱360°旋转6秒击退敌人+HP加到5。"),
                ("", ""),
                ("  终焉", "12000金+500钻"),
                ("", "左键（耗能5）终焉之枪：投掷必中灭世长枪，穿透全屏+即死非Boss+Boss500伤害；"),
                ("", "  同时展开镰刀360°无死角旋转，击中弹开并爆炸。"),
                ("", "右键（耗能8）无敌破坏死光：3秒大范围血红黑激光+无敌3秒+HP加到5。"),
                ("", ""),
                ("终极特性", "终极皮肤能量消耗极低（个位数），外观拥有创世/悖论/毁灭专属霸气光环。"),
            ],
            [
                ("难度与地图", ""),
                ("  主线", "16 关顺序解锁，难度渐升；通过一关才开下一关。"),
                ("  副本", "16 关，难度倍率更高（刺球更多更快），通关奖励钻石。"),
                ("  副本解锁", "主线 16 关全通后自动解锁副本第一关；副本按顺序解锁。"),
                ("  氛围", "部分关卡带 恐怖/混沌/干扰 标签，影响视觉、音效与事件。"),
                ("", ""),
                ("金币 / 钻石 / 皮肤", ""),
                ("  金币", "通关、拾取金币道具、敌球掉落获得。"),
                ("  钻石", "仅副本通关奖励（越难越多），用于解锁霸气皮肤。"),
                ("  换皮", "暂停中可直接切换已拥有皮肤（左右键/数字键）；空格=继续。"),
                ("  双人皮肤", "P1/P2 可各装备不同皮肤；P2 未指定则跟随 P1。"),
                ("  能量", "每玩家独立能量条，左右键消耗，随时间回复，空能量释放失败不扣。"),
                ("", ""),
                ("进度保存 / 导入 / 导出", ""),
                ("  自动保存", "通关、购买皮肤、抽奖后写入 stardust_save.json。"),
                ("  导出/导入", "导出弹 8 位导入码备份；导入粘贴码还原（覆盖当前进度）。"),
                ("", ""),
                ("抽奖", "地图右上12宝箱每日刷新，含随机皮肤。金币30金/次，钻石5钻/次，只抽未拥有。"),
                ("崩溃处理", "闪退时红字显示错误+5秒倒计时，堆栈存 _exception.log。"),
                ("提示", "F2 开启金币/钻石无限+全解锁+抽奖全开（F3 撤销）。"),
                ("", ""),
                ("翻页", "点击下方按钮 或 按 ← / → 键翻页，共 7 页。"),
                ("关闭", "点击下方关闭按钮 或 F1 / ? / ESC 键关闭说明。"),
            ],
        ]
        if not hasattr(self, "_help_page"):
            self._help_page = 0
        self._help_page = max(0, min(len(pages) - 1, self._help_page))
        page = pages[self._help_page]

        # ---- 重定位所有底行按钮（下移到 btn_row_y 并水平排列）----
        button_h = 42
        # 上一页（左）
        prev = pygame.Rect(x0 + 24, btn_row_y, 140, button_h)
        # 页码（中上）
        pager_w = 150
        pager_x = WIDTH // 2 - pager_w // 2 - 90
        # 下一页（中下）
        nxt = pygame.Rect(WIDTH // 2 + 90 - 140 // 2 + 0, btn_row_y, 140, button_h)
        nxt.x = WIDTH // 2 - 70
        # 关闭（右）
        cls = pygame.Rect(x0 + w - 140 - 24, btn_row_y, 140, button_h)
        # 修正 nxt 居中
        nxt.x = (WIDTH - 140) // 2

        # ---- 绘制正文（顶部 y0+56，底部最多到按钮上一行 btn_row_y - 10）----
        y = y0 + 56
        y_max = btn_row_y - 12
        # Q4：皮肤页的「左键/右键技能说明」整体再右移，避免左边标题与正文挤在一起。
        # 终极武器页（索引3）标题更长，需要更大偏移
        is_skin_page = (self._help_page in (1, 2, 3, 4))
        is_ultimate_help = (self._help_page == 3)
        # body 最大宽度相应收缩（整体右移，左边留更大空距给标题）
        body_shift = (100 if is_ultimate_help else (60 if is_skin_page else 0))
        # 非皮肤页正文左移后可用宽度更大
        body_max_w = (w - 300 - body_shift) if is_skin_page else (w - 180)
        head_size = 20
        body_size = 17
        body_gap = 24
        section_gap = 13
        for head, body in page:
            if y > y_max:
                break
            if head and not body:
                self._text(head, x0 + 82, y, head_size, NEON_YELLOW, bold=True)
                y += 26
            elif not head and not body:
                y += section_gap
            else:
                if head:
                    # 非皮肤页绿色标题左移（贴近面板左边缘），皮肤页保持原位
                    if is_ultimate_help:
                        head_x = x0 + 90
                    elif is_skin_page:
                        head_x = x0 + 86
                    else:
                        head_x = x0 + 24
                    self._text(head, head_x, y, 18, NEON_GREEN, bold=True)
                if body:
                    bl = self._wrap_text(body, body_max_w, body_size)
                    yy = y
                    # 终极武器页：标题为空时正文从左侧开始（标题已独占一行）
                    # 皮肤页正文右移，非皮肤页正文左移
                    if is_ultimate_help:
                        if head:
                            body_x = x0 + 300 + body_shift
                        else:
                            body_x = x0 + 90
                    elif is_skin_page:
                        body_x = x0 + 280 + body_shift
                    else:
                        body_x = x0 + 120
                    for line in bl:
                        if yy > y_max:
                            break
                        self._text(line, body_x, yy, body_size, WHITE)
                        yy += 22
                    y = yy - 22
                y += body_gap

        # 上一页按钮（最终定位）
        disabled_prev = self._help_page <= 0
        pcol = (100, 100, 120) if disabled_prev else NEON_CYAN
        pygame.draw.rect(self.screen, (18, 20, 38), prev, border_radius=8)
        pygame.draw.rect(self.screen, pcol, prev, 2, border_radius=8)
        self._text("上一页 <<", prev.centerx, prev.centery - 11, 18, pcol, bold=True, center=True)
        self._help_prev_rect_data = prev

        # 下一页按钮（最终定位）
        disabled_next = self._help_page >= len(pages) - 1
        ncol = (100, 100, 120) if disabled_next else NEON_CYAN
        pygame.draw.rect(self.screen, (18, 20, 38), nxt, border_radius=8)
        pygame.draw.rect(self.screen, ncol, nxt, 2, border_radius=8)
        self._text(">> 下一页", nxt.centerx, nxt.centery - 11, 18, ncol, bold=True, center=True)
        self._help_next_rect_data = nxt

        # 页码指示（移到上一页 / 下一页 两个按钮 的 正中间）
        idx = self._help_page + 1
        total = len(pages)
        mid_x = (prev.centerx + nxt.centerx) // 2
        self._text(f"第{idx}/{total}页", mid_x, prev.centery - 11, 20, NEON_PINK, bold=True, center=True)

        # 关闭按钮（最终定位）
        pygame.draw.rect(self.screen, (18, 20, 38), cls, border_radius=8)
        pygame.draw.rect(self.screen, NEON_PINK, cls, 2, border_radius=8)
        self._text("关闭 (F1)", cls.centerx, cls.centery - 11, 18, NEON_PINK, bold=True, center=True)
        self._help_close_rect_data = cls

    # 覆盖按钮定位函数（优先使用刚才的定位缓存）
    def _help_prev_rect(self):
        if hasattr(self, "_help_prev_rect_data"):
            return self._help_prev_rect_data.copy()
        return pygame.Rect(180, HEIGHT - 106, 140, 42)

    def _help_next_rect(self):
        if hasattr(self, "_help_next_rect_data"):
            return self._help_next_rect_data.copy()
        return pygame.Rect(WIDTH - 180 - 140, HEIGHT - 106, 140, 42)

    def _help_close_rect(self):
        if hasattr(self, "_help_close_rect_data"):
            return self._help_close_rect_data.copy()
        return pygame.Rect(WIDTH - 180 - 140, HEIGHT - 106, 140, 42)

    def _draw_shop(self, mx, my):
        self._dim(200)
        panel = pygame.Rect(60, 80, WIDTH - 120, HEIGHT - 160)
        is_p2 = self.show_shop == "p2"
        title_col = NEON_PURPLE if is_p2 else NEON_ORANGE
        self.shop_page = max(0, min(3, getattr(self, "shop_page", 0)))
        page = self.shop_page
        # 第0页=金币（橙色框）；第1页=钻石（青蓝色边框）；第2页=混合至高（金粉色边框）；第3页=终极（红色边框）
        if page == 0:
            panel_border = NEON_ORANGE
        elif page == 1:
            panel_border = (90, 230, 255)
        elif page == 2:
            panel_border = (255, 160, 220)
        else:
            panel_border = (255, 60, 60)
        pygame.draw.rect(self.screen, (12, 10, 24), panel, border_radius=14)
        pygame.draw.rect(self.screen, panel_border, panel, 2, border_radius=14)
        who = "玩家2" if is_p2 else "玩家1"
        if page == 0:
            page_name = "金币"
        elif page == 1:
            page_name = "钻石"
        elif page == 2:
            page_name = "至高·金币+钻石"
        else:
            page_name = "终极·最强武器"
        self._text(f"皮肤商店 · {who} · {page_name}页", WIDTH // 2, 96, 28, title_col, bold=True, center=True)
        # 顶部同时显示金币+钻石
        diamond_col = (120, 230, 255)
        self._text(f"金币: {self.coins}    钻石: {self.diamonds}",
                   WIDTH // 2, 126, 16, NEON_YELLOW, center=True)
        if page == 1:
            tip_suffix = "（打副本关卡得钻石）"
        elif page == 2:
            tip_suffix = "（金币+钻石一起支付；通关/副本可得）"
        elif page == 3:
            tip_suffix = "（终极皮肤·需大量金币+钻石·最强武器）"
        else:
            tip_suffix = "（通关得金币）"
        tip = f"已拥有可切换，未拥有可购买{tip_suffix}"
        self._text(tip, WIDTH // 2, 148, 15, DIM, center=True)
        # 翻页按钮（左右）
        pprev = self._shop_prev_page_rect()
        pnxt = self._shop_next_page_rect()
        # 上一页文字
        if page == 1:
            pv_text = "<< 金币页"
        elif page == 2:
            pv_text = "<< 钻石页"
        elif page == 3:
            pv_text = "<< 至高页"
        else:
            pv_text = "<< 上一页"
        # 上一页
        pv_hover = pprev.collidepoint(mx, my)
        pv_disabled = (page <= 0)
        pv_col = (80, 80, 110) if pv_disabled else (NEON_CYAN if pv_hover else (120, 180, 255))
        pygame.draw.rect(self.screen, (14, 12, 30) if not pv_disabled else (20, 18, 30), pprev, border_radius=8)
        pygame.draw.rect(self.screen, pv_col, pprev, 2, border_radius=8)
        self._text(pv_text, pprev.centerx, pprev.centery - 10, 14, pv_col, bold=True, center=True)
        # 下一页文字
        if page == 0:
            nv_text = "钻石页 >>"
        elif page == 1:
            nv_text = "至高页 >>"
        elif page == 2:
            nv_text = "终极页 >>"
        else:
            nv_text = "下一页 >>"
        # 下一页
        nv_hover = pnxt.collidepoint(mx, my)
        nv_disabled = (page >= 3)
        if page == 1:
            nv_col_base = (255, 180, 220)
        else:
            nv_col_base = diamond_col
        nv_col = (80, 80, 110) if nv_disabled else (nv_col_base if nv_hover else (150, 210, 255))
        pygame.draw.rect(self.screen, (14, 12, 30) if not nv_disabled else (20, 18, 30), pnxt, border_radius=8)
        pygame.draw.rect(self.screen, nv_col, pnxt, 2, border_radius=8)
        self._text(nv_text, pnxt.centerx, pnxt.centery - 10, 14, nv_col, bold=True, center=True)
        # P1/P2 皮肤选择九宫格
        skin_ids = self._shop_ordered_ids(page=page)
        cur_active = self.active_skin_p2 if is_p2 else self.active_skin
        is_ultimate_page = (page == 3)  # Q6：终极页 3 条横排布局
        for i, sid in enumerate(skin_ids):
            rect = self._shop_card_rect(i)
            name, cost, col, desc = SKINS[sid]
            owned = sid in self.owned_skins
            active = cur_active == sid
            hover = rect.collidepoint(mx, my)
            is_diamond = isinstance(cost, tuple) and cost and cost[0] == "diamond"
            is_mix = isinstance(cost, tuple) and cost and cost[0] == "mix" and len(cost) >= 3
            price_num = cost[1] if is_diamond else (cost if not is_mix else int(cost[1]))
            mix_coin = int(cost[1]) if is_mix else 0
            mix_diamond = int(cost[2]) if is_mix else 0
            # 卡片背景
            bg = (24, 20, 40) if not active else (40, 30, 24)
            if is_diamond:
                bg = (14, 20, 38) if not active else (18, 28, 46)
            elif is_mix:
                bg = (30, 18, 34) if not active else (44, 26, 46)
            pygame.draw.rect(self.screen, bg, rect, border_radius=10)
            border = col if (owned or active) else (70, 70, 90)
            pygame.draw.rect(self.screen, border, rect, 2, border_radius=10)
            if hover:
                pygame.draw.rect(self.screen, WHITE, rect, 1, border_radius=10)
            # 角标
            if is_diamond:
                dm = pygame.Rect(rect.x + 4, rect.y + 4, 24, 18)
                pygame.draw.rect(self.screen, (30, 18, 60), dm, border_radius=4)
                pygame.draw.rect(self.screen, diamond_col, dm, 1, border_radius=4)
                self._text("钻", dm.centerx, dm.centery - 7, 13, diamond_col, bold=True, center=True)
            elif is_mix:
                mm = pygame.Rect(rect.x + 4, rect.y + 4, 28, 18)
                pygame.draw.rect(self.screen, (50, 20, 50), mm, border_radius=4)
                pygame.draw.rect(self.screen, (255, 180, 220), mm, 1, border_radius=4)
                # Q6：终极页角标显示「终」
                mm_txt = "终" if is_ultimate_page else "至"
                self._text(mm_txt, mm.centerx, mm.centery - 7, 12, (255, 190, 220), bold=True, center=True)
            # 皮肤预览球（已装备或悬停时显示动态特效）
            if is_ultimate_page:
                # Q6：终极页 —— 大预览球
                pvx = rect.x + 70
                pvy = rect.y + rect.height // 2
                if active or hover:
                    self._draw_shop_skin_preview(sid, pvx, pvy, col, r=32)
                else:
                    pg = get_glow(70, col, alpha=180)
                    self.screen.blit(pg, pg.get_rect(center=(pvx, pvy)),
                                     special_flags=pygame.BLEND_RGB_ADD)
                    pygame.draw.circle(self.screen, col, (pvx, pvy), 32)
                    pygame.draw.circle(self.screen, WHITE, (pvx, pvy), 32, 3)
            else:
                pvx = rect.x + 36
                pvy = rect.y + 46
                if active or hover:
                    self._draw_shop_skin_preview(sid, pvx, pvy, col)
                else:
                    pg = get_glow(28, col, alpha=160)
                    self.screen.blit(pg, pg.get_rect(center=(pvx, pvy)),
                                     special_flags=pygame.BLEND_RGB_ADD)
                    pygame.draw.circle(self.screen, col, (pvx, pvy), 16)
                    pygame.draw.circle(self.screen, WHITE, (pvx, pvy), 16, 2)
            # 名称（过长自动换行）
            if is_ultimate_page:
                # Q6：终极页 —— 大字体名称 + 描述右侧展开
                name_lines = self._wrap_text(name, 320, 24, bold=True)
                ny = rect.y + 18
                for nl in name_lines[:2]:
                    self._text(nl, rect.x + 130, ny, 24, col if owned else WHITE, bold=True)
                    ny += 28
            else:
                name_lines = self._wrap_text(name, rect.width - 136, 16, bold=True)
                ny = rect.y + 14
                for nl in name_lines[:2]:
                    self._text(nl, rect.x + 64, ny, 16, col if owned else WHITE, bold=True)
                    ny += 19
            # 价格大标签：明显色块 + 大字体（mix 用两个小标签上下叠放或并排）
            infinite_c = getattr(self, "_infinite_coins", False)
            infinite_d = getattr(self, "_infinite_diamonds", False)
            if owned and active:
                # 单标签：已装备
                price_tag = pygame.Rect(rect.right - 72, rect.y + 6, 64, 30)
                pygame.draw.rect(self.screen, (30, 70, 40), price_tag, border_radius=6)
                pygame.draw.rect(self.screen, NEON_GREEN, price_tag, 2, border_radius=6)
                self._text("已装备", price_tag.centerx, price_tag.centery - 9, 15, NEON_GREEN, bold=True, center=True)
            elif owned:
                price_tag = pygame.Rect(rect.right - 72, rect.y + 6, 64, 30)
                pygame.draw.rect(self.screen, (30, 60, 70), price_tag, border_radius=6)
                pygame.draw.rect(self.screen, NEON_CYAN, price_tag, 2, border_radius=6)
                self._text("已拥有", price_tag.centerx, price_tag.centery - 9, 15, NEON_CYAN, bold=True, center=True)
            elif is_mix:
                # 混和：两个标签，左边金币，右边钻石（各自颜色；任一不足都标红）
                coin_ok = (self.coins >= mix_coin or infinite_c)
                diamond_ok = (self.diamonds >= mix_diamond or infinite_d)
                mix_ok = coin_ok and diamond_ok
                # 金币标签（黄/红）
                c_tag = pygame.Rect(rect.right - 142, rect.y + 6, 64, 28)
                if coin_ok:
                    c_bg, c_bd, c_tx = (60, 50, 10), NEON_YELLOW, NEON_YELLOW
                else:
                    c_bg, c_bd, c_tx = (70, 18, 20), NEON_RED, NEON_RED
                pygame.draw.rect(self.screen, c_bg, c_tag, border_radius=6)
                pygame.draw.rect(self.screen, c_bd, c_tag, 2, border_radius=6)
                self._text(f"{mix_coin}金", c_tag.centerx, c_tag.centery - 9, 14, c_tx, bold=True, center=True)
                # 钻石标签（蓝/红）
                d_tag = pygame.Rect(rect.right - 72, rect.y + 6, 64, 28)
                if diamond_ok:
                    d_bg, d_bd, d_tx = (18, 30, 60), diamond_col, diamond_col
                else:
                    d_bg, d_bd, d_tx = (60, 18, 20), NEON_RED, NEON_RED
                pygame.draw.rect(self.screen, d_bg, d_tag, border_radius=6)
                pygame.draw.rect(self.screen, d_bd, d_tag, 2, border_radius=6)
                self._text(f"{mix_diamond}钻", d_tag.centerx, d_tag.centery - 9, 14, d_tx, bold=True, center=True)
                # 状态补充行
                if not mix_ok:
                    miss = []
                    if not coin_ok:
                        miss.append("金币不足")
                    if not diamond_ok:
                        miss.append("钻石不足")
                    # 终极页：放在价格标签下方右侧，避免挡住描述文字
                    if is_ultimate_page:
                        self._text("(" + "/".join(miss) + ")",
                                   rect.right - 142, rect.y + 40, 13, NEON_RED)
                    else:
                        self._text("(" + "/".join(miss) + ")",
                                   rect.x + 64, rect.y + 52, 13, NEON_RED)
            else:
                price_tag = pygame.Rect(rect.right - 72, rect.y + 6, 64, 30)
                if is_diamond:
                    affordable = self.diamonds >= price_num or infinite_d
                    if affordable:
                        pt_bg, pt_bd, pt_tx = (18, 30, 60), diamond_col, diamond_col
                    else:
                        pt_bg, pt_bd, pt_tx = (60, 18, 20), NEON_RED, NEON_RED
                    pt_txt = f"{price_num}钻"
                else:
                    affordable = self.coins >= price_num or infinite_c
                    if affordable:
                        pt_bg, pt_bd, pt_tx = (60, 50, 10), NEON_YELLOW, NEON_YELLOW
                    else:
                        pt_bg, pt_bd, pt_tx = (70, 18, 20), NEON_RED, NEON_RED
                    pt_txt = f"{price_num}金"
                pygame.draw.rect(self.screen, pt_bg, price_tag, border_radius=6)
                pygame.draw.rect(self.screen, pt_bd, price_tag, 2, border_radius=6)
                self._text(pt_txt, price_tag.centerx, price_tag.centery - 9, 15, pt_tx, bold=True, center=True)
                # 状态补充行
                if is_diamond:
                    ok = (self.diamonds >= price_num or infinite_d)
                    if not ok:
                        if is_ultimate_page:
                            self._text("(钻石不足)",
                                       rect.right - 72, rect.y + 40, 14, NEON_RED)
                        else:
                            self._text("(钻石不足)",
                                       rect.x + 64, rect.y + 52, 14, NEON_RED)
                else:
                    ok = (self.coins >= price_num or infinite_c)
                    if not ok:
                        if is_ultimate_page:
                            self._text("(金币不足)",
                                       rect.right - 72, rect.y + 40, 14, NEON_RED)
                        else:
                            self._text("(金币不足)",
                                       rect.x + 64, rect.y + 52, 14, NEON_RED)
            # 能力描述（换行，高度留给描述更多空间）
            if is_ultimate_page:
                # Q6：终极页 —— 描述放右侧大区域，更大字体
                desc_lines = self._wrap_text(desc, 360, 16)
                dy = rect.y + 60
                for dl in desc_lines[:4]:
                    self._text(dl, rect.x + 130, dy, 16, WHITE)
                    dy += 20
            else:
                desc_lines = self._wrap_text(desc, rect.width - 28, 13)
                dy = rect.y + 76
                for dl in desc_lines[:3]:
                    self._text(dl, rect.x + 14, dy, 14, WHITE)
                    dy += 15
        # P2 商店：额外提供"跟随 P1"按钮（可取消 P2 独立皮肤）
        if is_p2:
            follow_rect = self._shop_follow_rect()
            fhover = follow_rect.collidepoint(mx, my)
            fcol_active = (self.active_skin_p2 is None)
            fbg = (30, 20, 46) if fcol_active else (22, 20, 34)
            fbd = NEON_GREEN if fcol_active else (NEON_CYAN if fhover else (120, 130, 160))
            pygame.draw.rect(self.screen, fbg, follow_rect, border_radius=9)
            pygame.draw.rect(self.screen, fbd, follow_rect, 3, border_radius=9)
            flabel = "跟随 P1 皮肤 ✓" if fcol_active else "跟随 P1 皮肤"
            self._text(flabel, follow_rect.centerx, follow_rect.centery - 10, 16,
                       fbd, bold=True, center=True)
        # 关闭按钮（明显，放大到 180×44 居中）
        close = pygame.Rect(WIDTH // 2 - 90, HEIGHT - 82, 180, 44)
        chover = close.collidepoint(mx, my)
        pygame.draw.rect(self.screen, (30, 16, 32) if chover else (22, 18, 36), close, border_radius=10)
        pygame.draw.rect(self.screen, NEON_PINK if chover else (200, 120, 200), close, 3, border_radius=10)
        self._text("关闭商店 (ESC)", close.centerx, close.centery - 12, 18,
                   NEON_PINK if chover else WHITE, bold=True, center=True)

    def _shop_close_rect(self):
        return pygame.Rect(WIDTH // 2 - 90, HEIGHT - 82, 180, 44)

    def _shop_follow_rect(self):
        """P2 商店内"跟随 P1 皮肤"按钮位置。"""
        return pygame.Rect(80, 150, 180, 44)

    # ===== Q8：设置面板 =====
    def _settings_panel_rect(self):
        return pygame.Rect(WIDTH // 2 - 220, 120, 440, 460)

    def _settings_sound_rect(self):
        # Q7：音效按钮在上（原语言位置）
        return pygame.Rect(WIDTH // 2 - 120, 220, 240, 44)

    def _settings_about_rect(self):
        # Q7：关于我们按钮在下（原音效位置）
        return pygame.Rect(WIDTH // 2 - 120, 280, 240, 44)

    def _settings_close_rect(self):
        return pygame.Rect(WIDTH // 2 - 80, HEIGHT - 80, 160, 40)

    def _draw_settings(self, mx, my):
        self._dim(190)
        panel = self._settings_panel_rect()
        pygame.draw.rect(self.screen, (10, 12, 26), panel, border_radius=12)
        pygame.draw.rect(self.screen, (100, 200, 180), panel, 2, border_radius=12)
        self._text("设置 / Settings", WIDTH // 2, panel.y + 24, 30, (100, 200, 180),
                   bold=True, center=True)
        # Q7：音效切换按钮（在上）
        snd_btn = self._settings_sound_rect()
        shover = snd_btn.collidepoint(mx, my)
        snd_txt = "音效: 开" if self._sound_on else "音效: 关"
        snd_col = NEON_GREEN if self._sound_on else (160, 160, 160)
        pygame.draw.rect(self.screen, (18, 20, 38), snd_btn, border_radius=8)
        pygame.draw.rect(self.screen, snd_col, snd_btn, 2, border_radius=8)
        if shover:
            pygame.draw.rect(self.screen, WHITE, snd_btn, 1, border_radius=8)
        self._text(snd_txt, snd_btn.centerx, snd_btn.centery - 10, 18,
                   snd_col if shover else WHITE, bold=True, center=True)
        # Q7：关于我们按钮（在下）
        about_btn = self._settings_about_rect()
        ahover = about_btn.collidepoint(mx, my)
        pygame.draw.rect(self.screen, (18, 20, 38), about_btn, border_radius=8)
        pygame.draw.rect(self.screen, NEON_CYAN, about_btn, 2, border_radius=8)
        if ahover:
            pygame.draw.rect(self.screen, WHITE, about_btn, 1, border_radius=8)
        self._text("关于我们", about_btn.centerx, about_btn.centery - 10, 18,
                   NEON_CYAN if ahover else WHITE, bold=True, center=True)
        # 说明文字
        self._text("点击按钮可切换音效 / 查看关于信息", WIDTH // 2, 352, 15, DIM, center=True)
        # GitHub 链接（仅显示，不可点击）
        self._text("GitHub: https://github.com/cbyygyitoh/stardust-devourer", WIDTH // 2,
                   panel.y + panel.h - 96, 16, NEON_YELLOW, center=True)
        self._text("ESC 返回地图", WIDTH // 2, panel.y + panel.h - 64, 14, DIM, center=True)
        # 关闭按钮
        cls = self._settings_close_rect()
        chover = cls.collidepoint(mx, my)
        pygame.draw.rect(self.screen, (18, 20, 38), cls, border_radius=8)
        pygame.draw.rect(self.screen, NEON_PINK, cls, 2, border_radius=8)
        if chover:
            pygame.draw.rect(self.screen, WHITE, cls, 1, border_radius=8)
        self._text("关闭", cls.centerx, cls.centery - 9, 17,
                   NEON_PINK if chover else WHITE, bold=True, center=True)

    def _handle_settings_click(self, mx, my):
        # Q7：音效按钮
        if self._settings_sound_rect().collidepoint(mx, my):
            self._sound_on = not self._sound_on
            self.muted = not self._sound_on
            if self._sound_on:
                self._play("tick")
            return
        # Q7：关于我们按钮 → 弹出关于弹窗
        if self._settings_about_rect().collidepoint(mx, my):
            self._modal = {
                "title": "关于我们",
                "col": NEON_CYAN,
                "ok_txt": "关闭",
                "body_lines": [
                    "",
                    "游戏名称：星尘吞噬者(Stardust Devourer)",
                    "游戏版本：V1.0.0",
                    "",
                    "制作：独立开发者",
                    "",
                    "游戏简介：",
                    "  一款支持双人游玩的闯关小游戏，",
                    "  包含副本、无尽、抽奖收集皮肤等玩法。",
                    "",
                    "  · 16关主线 + 16关副本 + 无尽模式 + BOSS模式",
                    "  · 30+种华丽皮肤技能，300个成就",
                    "  · 支持单人/双人、手势/键鼠操控",
                    "  · 兑换码礼包 + 每日签到 + 成就奖励",
                    "",
                    "温馨提示：",
                    "  本游戏为娱乐作品，请勿过度沉迷游戏。",
                    "",
                    "版权 © 2026 保留所有权利",
                ],
            }
            self._play("tick")
            return
        # 关闭按钮或点击面板外关闭
        if self._settings_close_rect().collidepoint(mx, my) or not self._settings_panel_rect().collidepoint(mx, my):
            self.show_settings = False
            self._play("tick")
            return

    # ===== Q6：成就系统 =====
    @classmethod
    def _build_achievements(cls):
        """生成 300 个成就（5 类：进度/战斗/收集/特殊/里程碑）。"""
        lst = []
        counter = [0]

        def add(name, desc, cat, check=None):
            counter[0] += 1
            lst.append({"id": counter[0], "name": name, "desc": desc,
                        "category": cat, "unlocked": False, "check": check})

        def fill(cat, target, prefix):
            """不足 target 个时用占位成就补齐到该类目指定数量。"""
            cur = sum(1 for a in lst if a["category"] == cat)
            i = cur
            while cur < target:
                i += 1
                add(f"{prefix} {i}", f"{prefix}里程碑 {i}", cat, None)
                cur += 1

        # ---- 进度（1-50）----
        for n in range(1, 17):
            add(f"通关第{n}关", f"完成主线第 {n} 关", "进度", ("level", n))
        for n in range(1, 17):
            add(f"通关副本第{n}关", f"完成副本第 {n} 关", "进度", ("dungeon", n))
        for n in (5, 10, 15, 20, 25, 27):
            add(f"解锁{ n }个皮肤", f"拥有 {n} 个皮肤", "进度", ("skins", n))
        for nm, ds, chk in [
            ("首次通关", "完成第一关", ("level", 1)),
            ("无伤通关", "无伤完成一关", None),
            ("速通新手", "快速完成一关", None),
            ("主线全通关", "通关全部 16 关主线", ("level", 16)),
            ("副本全通关", "通关全部 16 关副本", ("dungeon", 16)),
            ("初入副本", "解锁副本模式", ("dungeon", 1)),
            ("首次购买皮肤", "拥有第一件皮肤", ("skins", 1)),
            ("首次获得钻石", "获得第一颗钻石", ("diamonds", 1)),
            ("首次获得金币", "获得第一枚金币", ("coins", 1)),
            ("解锁全部皮肤", "拥有全部 27 个皮肤", ("skins", 27)),
            ("累计游玩10局", "累计游玩 10 局", ("games", 10)),
            ("累计游玩50局", "累计游玩 50 局", ("games", 50)),
        ]:
            add(nm, ds, "进度", chk)
        fill("进度", 50, "进度")  # 进度类目标 50 个
        # ---- 战斗（51-120）----
        for n in (10, 25, 50, 100, 200, 500, 1000, 2000, 5000, 10000):
            add(f"击败{ n }个敌人", f"累计击败 {n} 个敌人", "战斗", ("kills", n))
        for n in (5, 10, 15, 25, 50, 75, 100, 150, 200, 300):
            add(f"连击{ n }次", f"单局连击 {n} 次", "战斗", ("combo", n))
        for n in (500, 1000, 2000, 5000, 10000, 20000, 50000, 100000, 200000, 500000):
            add(f"单局得分{ n }", f"单局得分达到 {n}", "战斗", ("score", n))
        for n in (10, 20, 50, 100, 200, 500, 1000, 2000):
            add(f"单局吞噬{ n }", f"单局吞噬 {n} 个星体", "战斗", ("eaten", n))
        for n in (1, 3, 5, 9, 13, 18, 22, 27):
            add(f"使用{ n }种皮肤", f"累计使用 {n} 种皮肤", "战斗", ("skins", n))
        for n in (10000, 50000, 100000, 200000, 500000, 1000000):
            add(f"累计得分{ n }", f"累计得分达到 {n}", "战斗", ("score", n))
        for nm, ds, chk in [
            ("首次击败敌人", "击败第一个敌人", ("kills", 1)),
            ("首次击败Boss", "击败第一个 Boss", ("kills", 5)),
            ("击败Boss10次", "累计击败 10 个强敌", ("kills", 50)),
            ("击败Boss50次", "累计击败 50 个强敌", ("kills", 200)),
            ("连击达人", "连击达到 500", ("combo", 500)),
            ("单局击败100敌", "单局击败 100 个敌人", ("kills", 100)),
            ("完美一局", "单局得分 100 万", ("score", 1000000)),
            ("吞噬之王", "单局吞噬 5000", ("eaten", 5000)),
            ("皮肤大师", "使用全部 27 种皮肤", ("skins", 27)),
            ("战斗专家", "累计击败 50000 敌人", ("kills", 50000)),
            ("得分狂人", "累计得分 500 万", ("score", 5000000)),
            ("连击巅峰", "连击 1000", ("combo", 1000)),
            ("百连斩", "连击 100 次", ("combo", 100)),
            ("千军万马", "击败 100000 敌人", ("kills", 100000)),
            ("富可敌国", "单局得分 500 万", ("score", 5000000)),
            ("吞噬万星", "单局吞噬 10000", ("eaten", 10000)),
            ("全能战士", "使用 20 种皮肤", ("skins", 20)),
            ("战神", "累计击败 100 万敌人", ("kills", 1000000)),
        ]:
            add(nm, ds, "战斗", chk)
        fill("战斗", 70, "战斗")  # 战斗类目标 70 个
        # ---- 收集（121-200）----
        for n in (100, 500, 1000, 2000, 5000, 10000, 20000, 50000, 100000, 500000, 1000000):
            add(f"获得{ n }金币", f"累计获得 {n} 金币", "收集", ("coins", n))
        for n in (1, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000):
            add(f"获得{ n }钻石", f"累计获得 {n} 钻石", "收集", ("diamonds", n))
        for n in (1, 2, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 25, 27):
            add(f"拥有{ n }个皮肤", f"拥有 {n} 个皮肤", "收集", ("skins", n))
        for n in (1, 3, 5, 7, 9):
            add(f"拥有{ n }个金币皮肤", f"拥有 {n} 个金币皮肤", "收集", ("skins", n))
        for n in (1, 3, 5, 7, 9):
            add(f"拥有{ n }个钻石皮肤", f"拥有 {n} 个钻石皮肤", "收集", ("skins", n + 9))
        for n in (1, 3, 5, 7, 9):
            add(f"拥有{ n }个至高皮肤", f"拥有 {n} 个至高皮肤", "收集", ("skins", n + 18))
        for nm, ds, chk in [
            ("拥有全部皮肤", "集齐全部 27 个皮肤", ("skins", 27)),
            ("集齐金币皮肤", "集齐 9 个金币皮肤", ("skins", 9)),
            ("集齐钻石皮肤", "集齐钻石皮肤", ("skins", 18)),
            ("集齐至高皮肤", "集齐至高皮肤", ("skins", 27)),
            ("首次购买皮肤", "拥有第一件皮肤", ("skins", 1)),
            ("金币之王", "拥有 100 万金币", ("coins", 1000000)),
            ("钻石之王", "拥有 1 万钻石", ("diamonds", 10000)),
            ("皮肤收藏大师", "拥有全部皮肤", ("skins", 27)),
            ("富翁", "拥有 10 万金币", ("coins", 100000)),
            ("钻石大亨", "拥有 1000 钻石", ("diamonds", 1000)),
            ("财富自由", "拥有 5 万金币", ("coins", 50000)),
            ("宝藏猎人", "拥有 15 个皮肤", ("skins", 15)),
            ("收藏家", "拥有 20 个皮肤", ("skins", 20)),
            ("万贯家财", "拥有 50 万金币", ("coins", 500000)),
            ("钻石之路", "拥有 500 钻石", ("diamonds", 500)),
            ("初露锋芒", "拥有 1 个皮肤", ("skins", 1)),
            ("渐入佳境", "拥有 5 个皮肤", ("skins", 5)),
            ("收获颇丰", "拥有 10 个皮肤", ("skins", 10)),
            ("满载而归", "拥有 20 个皮肤", ("skins", 20)),
            ("大收藏家", "拥有 25 个皮肤", ("skins", 25)),
            ("富甲一方", "拥有 20 万金币", ("coins", 200000)),
            ("钻石满仓", "拥有 2000 钻石", ("diamonds", 2000)),
            ("金银满屋", "拥有 30 万金币", ("coins", 300000)),
            ("钻石恒久", "拥有 5000 钻石", ("diamonds", 5000)),
            ("腰缠万贯", "拥有 40 万金币", ("coins", 400000)),
        ]:
            add(nm, ds, "收集", chk)
        fill("收集", 80, "收集")  # 收集类目标 80 个
        # ---- 特殊（201-280）----
        for n in (5, 10, 20, 50, 100, 200, 500, 1000):
            add(f"无尽波次{ n }", f"无尽模式到达第 {n} 波", "特殊", ("endless_wave", n))
        for n in (1000, 5000, 10000, 50000, 100000, 200000, 500000):
            add(f"无尽得分{ n }", f"无尽模式得分 {n}", "特殊", ("endless", n))
        for nm, ds, chk in [
            ("首次抽奖", "完成第一次抽奖", None),
            ("抽奖10次", "累计抽奖 10 次", None),
            ("抽奖50次", "累计抽奖 50 次", None),
            ("抽奖100次", "累计抽奖 100 次", None),
            ("首次兑换码", "首次使用兑换码", None),
            ("使用10个道具", "累计使用 10 个道具", None),
            ("使用50个道具", "累计使用 50 个道具", None),
            ("使用100个道具", "累计使用 100 个道具", None),
            ("双人模式游玩", "在双人模式下完成一关", None),
            ("切换5次皮肤", "累计切换 5 次皮肤", None),
            ("切换10次皮肤", "累计切换 10 次皮肤", None),
            ("切换20次皮肤", "累计切换 20 次皮肤", None),
            ("首次进入副本", "首次进入副本模式", ("dungeon", 1)),
            ("首次无尽模式", "首次进入无尽模式", ("endless_wave", 1)),
            ("无尽波次10", "无尽模式到达第 10 波", ("endless_wave", 10)),
            ("无尽波次25", "无尽模式到达第 25 波", ("endless_wave", 25)),
            ("无尽波次50", "无尽模式到达第 50 波", ("endless_wave", 50)),
            ("无尽波次100", "无尽模式到达第 100 波", ("endless_wave", 100)),
            ("无尽首胜", "无尽模式得分破 1000", ("endless", 1000)),
            ("无尽高手", "无尽模式得分破 10000", ("endless", 10000)),
            ("无尽大师", "无尽模式得分破 50000", ("endless", 50000)),
            ("无尽之神", "无尽模式得分破 100000", ("endless", 100000)),
            ("Boss终结者", "击败首个 Boss", ("kills", 5)),
            ("连抽之王", "累计抽奖 200 次", None),
            ("道具达人", "使用 200 个道具", None),
            ("换装狂魔", "切换 50 次皮肤", None),
            ("社交玩家", "双人模式游玩 10 次", None),
            ("探险家", "进入副本 10 次", None),
            ("无尽挑战者", "无尽模式到达第 5 波", ("endless_wave", 5)),
            ("无尽老兵", "无尽模式到达第 20 波", ("endless_wave", 20)),
            ("无尽传奇", "无尽模式到达第 75 波", ("endless_wave", 75)),
            ("无尽神话", "无尽模式到达第 150 波", ("endless_wave", 150)),
        ]:
            add(nm, ds, "特殊", chk)
        fill("特殊", 80, "特殊")  # 特殊类目标 80 个
        # ---- 里程碑（281-300）----
        for n in (1, 5, 10, 20, 50):
            add(f"游玩{ n }小时", f"累计游玩 {n} 小时", "里程碑", ("games", n * 30))
        for n in (10, 50, 100, 500, 1000):
            add(f"总游玩{ n }局", f"累计游玩 {n} 局", "里程碑", ("games", n))
        for nm, ds, chk in [
            ("成就达人(50)", "解锁 50 个成就", None),
            ("成就达人(100)", "解锁 100 个成就", None),
            ("成就达人(200)", "解锁 200 个成就", None),
            ("全成就达成", "解锁全部 300 个成就", None),
            ("初出茅庐", "解锁第 1 个成就", None),
            ("渐有所成", "解锁 10 个成就", None),
            ("小有名气", "解锁 25 个成就", None),
            ("名声大噪", "解锁 150 个成就", None),
            ("成就宗师", "解锁 250 个成就", None),
            ("完美主义者", "解锁 280 个成就", None),
        ]:
            add(nm, ds, "里程碑", chk)
        fill("里程碑", 20, "里程碑")  # 里程碑类目标 20 个
        return lst[:300]

    def _ensure_achievements(self):
        """懒加载成就列表，并从存档恢复解锁状态。"""
        if self._achievements_list is None:
            self._achievements_list = self._build_achievements()
            for ach in self._achievements_list:
                if ach["id"] in self._achievements_unlocked:
                    ach["unlocked"] = True

    def _ach_panel_rect(self):
        return pygame.Rect(40, 50, WIDTH - 80, HEIGHT - 100)

    def _ach_prev_rect(self):
        return pygame.Rect(60, HEIGHT - 78, 130, 40)

    def _ach_next_rect(self):
        return pygame.Rect(WIDTH - 190, HEIGHT - 78, 130, 40)

    def _ach_close_rect(self):
        return pygame.Rect(WIDTH // 2 - 80, HEIGHT - 78, 160, 40)

    def _draw_achievements(self, mx, my):
        self._ensure_achievements()
        self._dim(195)
        panel = self._ach_panel_rect()
        pygame.draw.rect(self.screen, (10, 12, 26), panel, border_radius=12)
        pygame.draw.rect(self.screen, (255, 215, 0), panel, 2, border_radius=12)
        # 标题
        unlocked_cnt = len(self._achievements_unlocked)
        total_cnt = len(self._achievements_list)
        self._text("成就殿堂", WIDTH // 2, panel.y + 16, 30, (255, 215, 0),
                   bold=True, center=True)
        # 进度条
        bar_w = 420
        bar_x = WIDTH // 2 - bar_w // 2
        bar_y = panel.y + 56
        pygame.draw.rect(self.screen, (30, 30, 50), (bar_x, bar_y, bar_w, 16), border_radius=6)
        fill_w = int(bar_w * unlocked_cnt / max(1, total_cnt))
        if fill_w > 0:
            pygame.draw.rect(self.screen, (255, 215, 0), (bar_x, bar_y, fill_w, 16), border_radius=6)
        pygame.draw.rect(self.screen, (255, 215, 0), (bar_x, bar_y, bar_w, 16), 1, border_radius=6)
        self._text(f"{unlocked_cnt} / {total_cnt}", WIDTH // 2, bar_y + 22, 16, WHITE,
                   bold=True, center=True)
        # 分页：每页 12 条
        per_page = 12
        total_pages = (total_cnt + per_page - 1) // per_page
        if not hasattr(self, "_ach_page"):
            self._ach_page = 0
        self._ach_page = max(0, min(total_pages - 1, self._ach_page))
        start = self._ach_page * per_page
        page_items = self._achievements_list[start:start + per_page]
        # 列表
        row_y = panel.y + 110
        row_h = 40
        for ach in page_items:
            row_rect = pygame.Rect(panel.x + 20, row_y, panel.w - 40, row_h - 4)
            if ach["unlocked"]:
                pygame.draw.rect(self.screen, (40, 36, 12), row_rect, border_radius=6)
                pygame.draw.rect(self.screen, (255, 215, 0), row_rect, 1, border_radius=6)
                icon = "★"
                name_col = (255, 215, 0)
                desc_col = (220, 200, 120)
            else:
                pygame.draw.rect(self.screen, (22, 24, 40), row_rect, border_radius=6)
                pygame.draw.rect(self.screen, (70, 70, 90), row_rect, 1, border_radius=6)
                icon = "☆"
                name_col = (150, 150, 170)
                desc_col = (110, 110, 130)
            self._text(icon, panel.x + 38, row_y + 8, 20, name_col, bold=True)
            self._text(ach["name"], panel.x + 66, row_y + 6, 16, name_col, bold=True)
            self._text(ach["desc"], panel.x + 66, row_y + 22, 13, desc_col)
            self._text(f"[{ach['category']}]", panel.x + panel.w - 110, row_y + 8, 12, desc_col)
            row_y += row_h
        # 翻页按钮
        prev = self._ach_prev_rect()
        nxt = self._ach_next_rect()
        cls = self._ach_close_rect()
        phover = prev.collidepoint(mx, my)
        nhover = nxt.collidepoint(mx, my)
        chover = cls.collidepoint(mx, my)
        pcol = (100, 100, 120) if self._ach_page <= 0 else NEON_CYAN
        ncol = (100, 100, 120) if self._ach_page >= total_pages - 1 else NEON_CYAN
        pygame.draw.rect(self.screen, (18, 20, 38), prev, border_radius=8)
        pygame.draw.rect(self.screen, pcol, prev, 2, border_radius=8)
        if phover:
            pygame.draw.rect(self.screen, WHITE, prev, 1, border_radius=8)
        self._text("← 上一页", prev.centerx, prev.centery - 9, 15, pcol, bold=True, center=True)
        pygame.draw.rect(self.screen, (18, 20, 38), nxt, border_radius=8)
        pygame.draw.rect(self.screen, ncol, nxt, 2, border_radius=8)
        if nhover:
            pygame.draw.rect(self.screen, WHITE, nxt, 1, border_radius=8)
        self._text("下一页 →", nxt.centerx, nxt.centery - 9, 15, ncol, bold=True, center=True)
        self._text(f"第 {self._ach_page + 1} / {total_pages} 页",
                   WIDTH // 2, HEIGHT - 70, 16, NEON_PINK, bold=True, center=True)
        pygame.draw.rect(self.screen, (18, 20, 38), cls, border_radius=8)
        pygame.draw.rect(self.screen, NEON_PINK, cls, 2, border_radius=8)
        if chover:
            pygame.draw.rect(self.screen, WHITE, cls, 1, border_radius=8)
        self._text("关闭 (ESC)", cls.centerx, cls.centery - 9, 16,
                   NEON_PINK if chover else WHITE, bold=True, center=True)

    def _handle_achievements_click(self, mx, my):
        self._ensure_achievements()
        total_cnt = len(self._achievements_list)
        per_page = 12
        total_pages = (total_cnt + per_page - 1) // per_page
        if self._ach_prev_rect().collidepoint(mx, my):
            if self._ach_page > 0:
                self._ach_page -= 1
                self._play("tick")
            return
        if self._ach_next_rect().collidepoint(mx, my):
            if self._ach_page < total_pages - 1:
                self._ach_page += 1
                self._play("tick")
            return
        # 关闭按钮或点击面板外关闭
        if self._ach_close_rect().collidepoint(mx, my) or not self._ach_panel_rect().collidepoint(mx, my):
            self.show_achievements = False
            self._play("tick")
            return

    def _ach_reward(self, ach):
        """Q6：根据成就类别计算奖励（金币, 钻石）。"""
        cat = ach.get("category", "")
        aid = ach.get("id", 0)
        if cat == "进度":
            return (80 + aid * 3, max(1, aid // 10))
        elif cat == "战斗":
            return (50 + aid * 2, max(1, aid // 15))
        elif cat == "收集":
            return (120 + aid * 4, max(2, aid // 8))
        elif cat == "特殊":
            return (200 + aid * 5, max(3, aid // 6))
        elif cat == "里程碑":
            return (500 + aid * 10, max(5, aid // 3))
        return (50, 1)

    def _check_achievements(self):
        """根据游戏状态检测并解锁成就。Q6：解锁时奖励金币+钻石。"""
        self._ensure_achievements()
        changed = False
        unlocked_cnt = len(self._achievements_unlocked)
        newly_unlocked = []
        total_reward_coins = 0
        total_reward_diamonds = 0
        for ach in self._achievements_list:
            if ach["unlocked"]:
                continue
            chk = ach.get("check")
            if chk is None:
                continue
            ct = chk[0]
            val = chk[1] if len(chk) > 1 else 0
            done = False
            if ct == "level":
                done = self.unlocked > val or (val >= len(LEVELS) and self.unlocked >= len(LEVELS))
            elif ct == "dungeon":
                done = (self.dungeon_unlocked > val
                        or (val >= len(DUNGEON_LEVELS) and self.dungeon_unlocked >= len(DUNGEON_LEVELS)))
            elif ct == "skins":
                done = len(self.owned_skins) >= val
            elif ct == "coins":
                done = self.coins >= val
            elif ct == "diamonds":
                done = self.diamonds >= val
            elif ct == "score":
                done = self.score >= val or self.best >= val
            elif ct == "kills":
                done = getattr(self, "_total_kills", 0) >= val
            elif ct == "combo":
                done = getattr(self, "_max_combo", 0) >= val
            elif ct == "eaten":
                done = getattr(self, "_max_eaten", 0) >= val
            elif ct == "games":
                done = getattr(self, "_games_played", 0) >= val
            elif ct == "endless":
                done = getattr(self, "_endless_high_score", 0) >= val
            elif ct == "endless_wave":
                done = getattr(self, "_endless_high_wave", 0) >= val
            if done:
                ach["unlocked"] = True
                self._achievements_unlocked.add(ach["id"])
                changed = True
                nm = ach.get("name", ach["id"])
                newly_unlocked.append(nm)
                # Q6：发放奖励
                rc, rd = self._ach_reward(ach)
                total_reward_coins += rc
                total_reward_diamonds += rd
        if changed:
            new_cnt = len(self._achievements_unlocked)
            # Q6：发放奖励金币和钻石
            if total_reward_coins > 0:
                self.coins += total_reward_coins
            if total_reward_diamonds > 0:
                self.diamonds += total_reward_diamonds
            self._save_game()
            # 解锁里程碑类成就：成就达人数
            for ach in self._achievements_list:
                if ach["unlocked"]:
                    continue
                nm = ach.get("name", "")
                milestone_done = False
                if nm == "初出茅庐" and new_cnt >= 1:
                    milestone_done = True
                elif nm == "渐有所成" and new_cnt >= 10:
                    milestone_done = True
                elif nm == "小有名气" and new_cnt >= 25:
                    milestone_done = True
                elif nm == "成就达人(50)" and new_cnt >= 50:
                    milestone_done = True
                elif nm == "成就达人(100)" and new_cnt >= 100:
                    milestone_done = True
                elif nm == "名声大噪" and new_cnt >= 150:
                    milestone_done = True
                elif nm == "成就达人(200)" and new_cnt >= 200:
                    milestone_done = True
                elif nm == "成就宗师" and new_cnt >= 250:
                    milestone_done = True
                elif nm == "完美主义者" and new_cnt >= 280:
                    milestone_done = True
                elif nm == "全成就达成" and new_cnt >= 300:
                    milestone_done = True
                if milestone_done:
                    ach["unlocked"] = True
                    self._achievements_unlocked.add(ach["id"])
                    newly_unlocked.append(nm)
                    # Q6：里程碑奖励
                    rc, rd = self._ach_reward(ach)
                    self.coins += rc
                    self.diamonds += rd
                    total_reward_coins += rc
                    total_reward_diamonds += rd
            # Q7：添加成就解锁提示到队列（含奖励信息）
            for nm in newly_unlocked:
                self._ach_toasts.append({"name": nm, "timer": 3.5})
            # Q6：显示奖励提示
            if total_reward_coins > 0 or total_reward_diamonds > 0:
                msg_parts = []
                if total_reward_coins > 0:
                    msg_parts.append(f"+{total_reward_coins}金币")
                if total_reward_diamonds > 0:
                    msg_parts.append(f"+{total_reward_diamonds}钻石")
                self._flash_msg = f"成就奖励：{' / '.join(msg_parts)}"
                self._flash_timer = max(self._flash_timer, 2.5)

    # ===== Q7：无尽模式 =====
    def _start_endless(self):
        self._endless_mode = True
        self._endless_wave = 1
        self._endless_score = 0
        self.is_dungeon = False
        self.current_level = 0
        self.reset_level()
        self.state = self.PLAYING
        self._flash_msg = "无尽模式开始！波次 1"
        self._flash_timer = 2.0
        self._play("start")

    # ===== Q9：BOSS模式 =====
    BOSS_MODE_LEVELS = 16

    def _start_boss_mode(self):
        """Q9：BOSS模式 - 16关连续Boss挑战，每关难度递增。"""
        self._boss_mode = True
        self._endless_mode = False
        self._boss_level = 1
        self.is_dungeon = True
        self.current_level = 0
        # 使用副本背景但加强
        self.reset_level()
        self.state = self.PLAYING
        self._flash_msg = f"BOSS模式 第{self._boss_level}关！"
        self._flash_timer = 2.0
        self._play("start")

    def _boss_spawn(self):
        """Q7：生成当前关卡的Boss（基于已有小怪种族，高血量大体积，持续存在直至被击败）。"""
        bl = getattr(self, "_boss_level", 1)
        # Boss血量随关卡递增（16关：从易到难）
        boss_hp = 150 + bl * 60
        boss_r = 38 + bl * 2
        # Boss颜色随关卡变化
        boss_cols = [
            (255, 60, 60), (255, 120, 40), (255, 200, 50), (120, 255, 80),
            (60, 200, 255), (100, 100, 255), (200, 80, 255), (255, 80, 200),
            (255, 100, 100), (255, 160, 60), (255, 220, 80), (140, 255, 120),
            (80, 220, 255), (120, 140, 255), (220, 100, 255), (255, 100, 255),
        ]
        col = boss_cols[(bl - 1) % len(boss_cols)]
        # Q7：Boss使用已有的种族形态，按关卡轮换
        boss_kinds = ["horror", "oxdemon", "ghost", "spider", "centipede",
                      "turtle", "fangshe", "tri", "dual", "virus",
                      "horror", "oxdemon", "ghost", "spider", "centipede", "fangshe"]
        boss_kind = boss_kinds[(bl - 1) % len(boss_kinds)]
        # 生成Boss（使用正确的 Star 构造签名）
        angle = random.uniform(0, math.tau)
        bx = WIDTH / 2 + math.cos(angle) * 200
        by = HEIGHT / 2 + math.sin(angle) * 150
        spd = 60 + bl * 4
        vx = math.cos(angle) * spd
        vy = math.sin(angle) * spd
        boss = Star(bx, by, vx, vy, boss_r, col, True, tier=3, kind=boss_kind)
        boss.hp = boss_hp
        boss.max_hp = boss_hp
        boss.is_boss = True
        boss.boss_level = bl
        self.stars.append(boss)
        # 同时生成少量小怪干扰（使用已有种族）
        small_kinds = ["spike", "virus", "tri", "dual", "worm",
                       "spider", "centipede", "ghost", "oxdemon", "fangshe"]
        for _ in range(3 + min(8, bl)):
            sa = random.uniform(0, math.tau)
            sr = random.uniform(18, 32)
            sx = WIDTH / 2 + math.cos(sa) * random.uniform(100, 300)
            sy = HEIGHT / 2 + math.sin(sa) * random.uniform(80, 200)
            svx = math.cos(sa) * random.uniform(50, 100)
            svy = math.sin(sa) * random.uniform(50, 100)
            skind = random.choice(small_kinds[:max(3, bl // 2 + 3)])
            scol = random.choice([(200, 50, 70), (180, 60, 30), (120, 40, 160), (90, 10, 25)])
            small = Star(sx, sy, svx, svy, sr, scol, True, tier=1, kind=skind)
            small.hp = 20 + bl * 4
            small.max_hp = small.hp
            self.stars.append(small)

    def _boss_advance_level(self):
        """Q9：通关当前Boss关，推进下一关。"""
        bl = getattr(self, "_boss_level", 1)
        reward_coins = 100 + bl * 30
        reward_diamonds = max(1, bl // 2)
        self.coins += reward_coins
        self.diamonds += reward_diamonds
        self.score += 2000
        self.best = max(self.best, self.score)
        self._total_kills = getattr(self, "_total_kills", 0) + 1
        self._save_game()
        if bl >= self.BOSS_MODE_LEVELS:
            # 通关全部BOSS关
            self._boss_mode = False
            self.state = self.MAP
            self._flash_msg = f"BOSS模式全通关！奖励 {reward_coins}金 {reward_diamonds}钻"
            self._flash_timer = 3.0
            self._play("win")
            self._check_achievements()
        else:
            self._boss_level = bl + 1
            self.reset_level()
            self._flash_msg = f"BOSS第{bl}关通关！+{reward_coins}金 +{reward_diamonds}钻 → 第{self._boss_level}关"
            self._flash_timer = 2.5
            self._play("win")
            self._check_achievements()

    def _endless_advance_wave(self):
        """本波次击败目标后推进下一波，并刷新敌人+发放奖励。"""
        self._endless_wave += 1
        w = self._endless_wave
        # Q2：每轮奖励 —— 金币+钻石+能量，随波次递增
        bonus_score = 500
        reward_coins = 80 + w * 30          # 金币奖励
        reward_diamonds = max(1, w // 3)     # 钻石奖励（每3波+1）
        self._endless_score = getattr(self, "_endless_score", 0) + bonus_score
        self.score += bonus_score
        self.coins = int(self.coins) + reward_coins
        self.diamonds = int(self.diamonds) + reward_diamonds
        self.best = max(self.best, self.score)
        # 能量恢复
        for p in self.players:
            if p.alive:
                p.energy = min(100, p.energy + 40)
        self._endless_spawned = 0
        self._endless_killed = 0
        # Q2：难度递增但不过分 —— 目标数温和增长
        self._endless_wave_target = 3 + int(w * 1.2)
        # 每 5 波：Boss 波
        if w % 5 == 0:
            self._endless_spawn_boss()
            reward_diamonds += 3              # Boss波额外钻石
            self.diamonds = int(self.diamonds) + 3
        self._flash_msg = f"第{w}波通关！+{reward_coins}金 +{reward_diamonds}钻 能量恢复"
        self._flash_timer = 2.0
        self._play("win")

    def _endless_spawn_boss(self):
        """生成一个高血量大体积 Boss。"""
        pr = max((p.r for p in self.players if p.alive), default=18.0)
        r = pr * 2.4
        side = random.randint(0, 3)
        if side == 0:
            x, y = random.uniform(0, WIDTH), -40
        elif side == 1:
            x, y = random.uniform(0, WIDTH), HEIGHT + 40
        elif side == 2:
            x, y = -40, random.uniform(0, HEIGHT)
        else:
            x, y = WIDTH + 40, random.uniform(0, HEIGHT)
        tx = random.uniform(WIDTH * 0.3, WIDTH * 0.7)
        ty = random.uniform(HEIGHT * 0.3, HEIGHT * 0.7)
        ang = math.atan2(ty - y, tx - x)
        speed = 70.0 + self._endless_wave * 2.0
        vx = math.cos(ang) * speed
        vy = math.sin(ang) * speed
        col = (120, 0, 30)
        boss = Star(x, y, vx, vy, r, col, True, tier=3, kind="horror")
        hp_scale = 1.0 + self._endless_wave * 0.3
        boss.hp = int(boss.hp * hp_scale * 3)
        boss.max_hp = boss.hp
        boss._endless_boss = True
        self.stars.append(boss)
        self._flash_msg = "⚠ Boss 波次！"
        self._flash_timer = 1.8
        self._play("warn")

    def _endless_end(self):
        """无尽模式玩家死亡：保存高分并返回地图。"""
        if self._endless_score > getattr(self, "_endless_high_score", 0):
            self._endless_high_score = self._endless_score
        # 记录最高波次用于成就检测
        self._endless_high_wave = max(getattr(self, "_endless_high_wave", 0), self._endless_wave)
        self._flash_msg = (f"无尽模式结束！波次 {self._endless_wave} "
                           f"得分 {self._endless_score}")
        self._flash_timer = 3.0
        self._endless_mode = False
        self._save_game()
        self._check_achievements()
        self._goto_map()

    def _draw_map(self, mx, my):
        # Q10：副本地图背景升级为「血月 + 暗紫黑迷雾 + 随机闪电 + 飘浮眼球/尸骨粒子」，后期更惊悚
        if self.is_dungeon:
            # 更深的血黑底（比之前更暗更厚重）
            self.screen.fill((10, 2, 6))
            tt = pygame.time.get_ticks()
            # ===== 黑雾团：多个大小不一的暗紫/黑径向光晕 =====
            # 水平居中对称雾（(cy, color, r, alpha)）
            for (gy, gc, gr, ga) in [
                (int(HEIGHT * 0.28), (70, 4, 10), 540, 58),
                (int(HEIGHT * 0.62), (40, 0, 40), 640, 48),
                (120,                 (160, 10, 40), 260, 42),
                (HEIGHT - 140,        (50, 0, 55),  300, 42),
            ]:
                cx = WIDTH // 2
                cy = gy
                cc = gc
                cr = gr
                ca = ga
                try:
                    gv = get_glow(cr * 2, cc, alpha=ca)
                    self.screen.blit(gv, gv.get_rect(center=(cx, cy)),
                                     special_flags=pygame.BLEND_RGB_ADD)
                except Exception:
                    pass
            # 额外紫黑雾（按 x,y 定位）
            for (cx, cy, cc, cr, ca) in [
                (int(WIDTH * 0.22), 180, (70, 20, 120), 220, 28),
                (int(WIDTH * 0.78), HEIGHT - 200, (90, 10, 80), 260, 24),
                (int(WIDTH * 0.5),  90,  (120, 0, 20),  180, 34),
                (int(WIDTH * 0.18), int(HEIGHT * 0.78), (30, 0, 60), 220, 30),
                (int(WIDTH * 0.82), int(HEIGHT * 0.32), (20, 0, 30), 260, 30),
            ]:
                try:
                    gv = get_glow(cr * 2, cc, alpha=ca)
                    self.screen.blit(gv, gv.get_rect(center=(cx, cy)),
                                     special_flags=pygame.BLEND_RGB_ADD)
                except Exception:
                    pass
            # ===== 角落随机闪电（暗红紫）=====
            lightning_prob = (tt // 80) % 60
            if lightning_prob < 3:
                # 白色偏紫闪光叠层 + 折线
                flash_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                flash_a = 50 if lightning_prob == 0 else 22
                flash_surf.fill((180, 160, 255, flash_a))
                self.screen.blit(flash_surf, (0, 0))
                # 折线绘制（左右各一条）
                t_seed = (tt // 80)
                for side in (-1, 1):
                    sx = WIDTH // 2 + side * (WIDTH // 3)
                    sy = 0
                    segs = 8
                    lx, ly = sx, sy
                    for i in range(segs):
                        ny = sy + int((i + 1) * HEIGHT / segs)
                        nx = lx + random.Random(t_seed * 131 + side * 17 + i * 19).randint(-60, 60)
                        pygame.draw.line(self.screen, (220, 180, 255),
                                         (lx, ly), (nx, ny), 2)
                        lx, ly = nx, ny
            # ===== 飘浮尸骨 / 眼球粒子（确定性伪随机，不突变）=====
            for k in range(80):
                rnd = (k * 211 + tt // 60)
                x = ((rnd * 233) % (WIDTH - 60)) + 30
                y = ((rnd * 701 + (tt // 2)) % (HEIGHT - 160)) + 80
                tp = k % 4
                if tp == 0:
                    # 小血点
                    sz = 1 + (k % 3)
                    self.screen.fill(((120 + (k % 6) * 18), 8, 10 + (k % 5) * 8),
                                     (int(x), int(y), sz, sz + (k % 2)))
                elif tp == 1:
                    # 漂浮白骨点（灰白）
                    sz = 2 + (k % 2)
                    if (k + (tt // 250)) % 9 == 0:
                        self.screen.fill((230, 230, 220), (int(x), int(y), sz, sz))
                elif tp == 2:
                    # 血丝小线
                    if (k % 11) < 2:
                        pygame.draw.line(self.screen, (160, 10, 20),
                                         (x, y), (x + 8 + (k % 6), y - 4 - (k % 4)), 1)
                else:
                    # 红眼珠：周期性睁开
                    if ((tt // 500) + k) % 7 == 0:
                        rr = 3
                        pygame.draw.circle(self.screen, (180, 20, 20),
                                           (int(x), int(y)), rr)
                        pygame.draw.circle(self.screen, (255, 240, 0),
                                           (int(x), int(y)), 1)
            # ===== 背景星（暗沉血红 + 少量闪金）=====
            si = 0
            for stars, _ in self.bg_stars:
                mul_col = (150, 40, 40) if si == 0 else ((90, 60, 110) if si == 1 else (255, 230, 120))
                for s in stars:
                    self.screen.fill(mul_col, (int(s[0]), int(s[1]),
                                               max(1, int(s[2])), max(1, int(s[2]))))
                si += 1
            # ===== 顶部血月（大光晕 + 遮挡缺口）=====
            moon_cx, moon_cy, moon_r = 128, 118, 54
            try:
                moon_glow = get_glow(moon_r * 5, (120, 10, 14), alpha=70)
                self.screen.blit(moon_glow, moon_glow.get_rect(center=(moon_cx, moon_cy)),
                                 special_flags=pygame.BLEND_RGB_ADD)
            except Exception:
                pass
            pygame.draw.circle(self.screen, (210, 40, 45), (moon_cx, moon_cy), moon_r)
            # 月亮表面暗斑（让它更像邪月）
            for (ox, oy, rr) in [(-15, -8, 10), (12, 14, 8), (20, -18, 6), (-6, 22, 5)]:
                pygame.draw.circle(self.screen, (120, 10, 20),
                                   (moon_cx + ox, moon_cy + oy), rr)
            # 右上角邪眼图腾（盯视玩家）
            e_cx, e_cy = WIDTH - 120, 108
            eye_pulse = 1 + 0.06 * math.sin(tt * 0.004)
            pygame.draw.circle(self.screen, (255, 220, 255),
                               (e_cx, e_cy), int(20 * eye_pulse), 2)
            pygame.draw.circle(self.screen, (230, 20, 30),
                               (e_cx, e_cy), int(12 * eye_pulse))
            pygame.draw.circle(self.screen, (255, 255, 120),
                               (e_cx - 3, e_cy - 3), 3)
            self._text("★ 蚀狱副本 · 惊悚地图 ★", WIDTH // 2, 36, 34, (255, 60, 70), bold=True, center=True)
        else:
            self.screen.fill((6, 6, 18))
            # 背景星
            for stars, _ in self.bg_stars:
                for s in stars:
                    self.screen.fill((50, 50, 70), (int(s[0]), int(s[1]),
                                                    max(1, int(s[2])), max(1, int(s[2]))))
            self._text("星尘吞噬者 · 关卡地图", WIDTH // 2, 36, 36, NEON_CYAN, bold=True, center=True)
        # Q6: 皮肤行独立显示（换行+居中），不与分数行挤在一起
        p1_skin_name = SKINS[self.active_skin][0] if self.active_skin else "无"
        p2_skin_name = ""
        if self.num_players == 2:
            p2_sk_show = self.active_skin_p2 if self.active_skin_p2 else (self.active_skin if self.active_skin else None)
            if p2_sk_show:
                p2_skin_name = SKINS[p2_sk_show][0]
            else:
                p2_skin_name = "跟随P1"
        total = len(self._get_levels())
        unlock = self._get_unlocked()
        mode_txt = "·副本地图·" if self.is_dungeon else "·主线地图·"
        hud_text = (f"总分  {self.score}    最高  {self.best}    金币  {self.coins}    "
                    f"钻石  {self.diamonds}    {mode_txt}")
        hud_size = 20
        # 预留右侧按钮宽度，超宽自动降字号
        try:
            if get_font(hud_size, True).size(hud_text)[0] > 720:
                hud_size = 18
        except Exception:
            pass
        self._text(hud_text, WIDTH // 2, 118, hud_size, NEON_YELLOW, bold=True, center=True)
        # ===== Q8：左上角「签到」按钮绘制（在兑换码上方）=====
        sbtn = self._sign_in_button_rect()
        shover = sbtn.collidepoint(mx, my)
        today = self._today_str()
        signed_today = getattr(self, "_sign_in_date", None) == today
        sign_col = (120, 200, 120) if not signed_today else (100, 100, 110)
        pygame.draw.rect(self.screen, (14, 18, 14), sbtn, border_radius=10)
        pygame.draw.rect(self.screen, sign_col, sbtn, 2, border_radius=10)
        if shover and not signed_today:
            pygame.draw.rect(self.screen, (255, 255, 255, 80), sbtn, 1, border_radius=10)
        sign_txt = "已签到" if signed_today else "签到"
        self._text(sign_txt, sbtn.centerx, sbtn.centery - 10, 16,
                   (140, 220, 140) if not signed_today else (120, 120, 130),
                   bold=True, center=True)
        # ===== Q5：初始界面左上角「兑换码」按钮绘制（Q8：下移）=====
        rbtn = self._redeem_code_button_rect()
        rhover = rbtn.collidepoint(mx, my)
        pygame.draw.rect(self.screen, (18, 14, 26), rbtn, border_radius=10)
        pygame.draw.rect(self.screen, (255, 200, 90) if rhover else (255, 170, 60),
                         rbtn, 2, border_radius=10)
        if rhover:
            pygame.draw.rect(self.screen, (255, 255, 255, 80), rbtn, 1, border_radius=10)
        self._text("礼包 兑换码", rbtn.centerx, rbtn.centery - 10, 16,
                   (255, 220, 120) if rhover else (255, 240, 200),
                   bold=True, center=True)
        # Q6：P1 皮肤（及双人下 P2 皮肤）在 P 前换行后居中，双行显示更清晰
        if self.num_players == 1:
            self._text("P1 皮肤：", WIDTH // 2, 146, 17, NEON_CYAN, bold=True, center=True)
            self._text(p1_skin_name, WIDTH // 2, 168, 19, NEON_CYAN, bold=True, center=True)
        else:
            # 双人：P1 / P2 各占两行（前缀一行 + 皮肤名一行），保持上下对齐居中
            p1_y = 140
            self._text("P1 皮肤：", WIDTH // 2 - 140, p1_y, 16, NEON_CYAN, bold=True, center=True)
            self._text(p1_skin_name, WIDTH // 2 - 140, p1_y + 22, 18, NEON_CYAN, bold=True, center=True)
            self._text("P2 皮肤：", WIDTH // 2 + 140, p1_y, 16, NEON_PURPLE, bold=True, center=True)
            self._text(p2_skin_name, WIDTH // 2 + 140, p1_y + 22, 18, NEON_PURPLE, bold=True, center=True)
        # 模式切换按钮
        btn = self._mode_button_rect()
        hover = btn.collidepoint(mx, my)
        mode_txt = "双人模式 >>" if self.num_players == 1 else "单人模式 >>"
        bcol = NEON_PINK if self.num_players == 2 else NEON_CYAN
        pygame.draw.rect(self.screen, (18, 20, 38), btn, border_radius=8)
        pygame.draw.rect(self.screen, bcol, btn, 2, border_radius=8)
        if hover:
            pygame.draw.rect(self.screen, (255, 255, 255, 80), btn, 1, border_radius=8)
        self._text(mode_txt, btn.centerx, btn.centery - 9, 16, bcol, bold=True, center=True)
        # 游戏说明按钮
        hbtn = self._help_button_rect()
        hhover = hbtn.collidepoint(mx, my)
        pygame.draw.rect(self.screen, (18, 20, 38), hbtn, border_radius=8)
        pygame.draw.rect(self.screen, NEON_YELLOW, hbtn, 2, border_radius=8)
        if hhover:
            pygame.draw.rect(self.screen, WHITE, hbtn, 1, border_radius=8)
        self._text("游戏说明 ?", hbtn.centerx, hbtn.centery - 9, 16, NEON_YELLOW,
                   bold=True, center=True)
        # 商店按钮
        sbtn = self._shop_button_rect()
        shover = sbtn.collidepoint(mx, my)
        pygame.draw.rect(self.screen, (18, 20, 38), sbtn, border_radius=8)
        pygame.draw.rect(self.screen, NEON_ORANGE, sbtn, 2, border_radius=8)
        if shover:
            pygame.draw.rect(self.screen, WHITE, sbtn, 1, border_radius=8)
        self._text(f"商店  ${self.coins}", sbtn.centerx, sbtn.centery - 9, 16, NEON_ORANGE,
                   bold=True, center=True)
        # 抽奖按钮
        lbtn = self._lottery_button_rect()
        lhover = lbtn.collidepoint(mx, my)
        pygame.draw.rect(self.screen, (18, 20, 38), lbtn, border_radius=8)
        pygame.draw.rect(self.screen, NEON_PINK, lbtn, 2, border_radius=8)
        if lhover:
            pygame.draw.rect(self.screen, WHITE, lbtn, 1, border_radius=8)
        self._text(f"抽奖  ${self._lottery_cost()}", lbtn.centerx, lbtn.centery - 9, 16, NEON_PINK,
                   bold=True, center=True)
        # P2 皮肤按钮
        p2btn = self._p2skin_button_rect()
        p2hover = p2btn.collidepoint(mx, my)
        p2col = NEON_PURPLE if self.num_players == 2 else (90, 90, 120)
        pygame.draw.rect(self.screen, (18, 20, 38), p2btn, border_radius=8)
        pygame.draw.rect(self.screen, p2col, p2btn, 2, border_radius=8)
        if p2hover:
            pygame.draw.rect(self.screen, WHITE, p2btn, 1, border_radius=8)
        if self.num_players == 2:
            show = self.active_skin_p2 if (self.active_skin_p2 and self.active_skin_p2 in self.owned_skins) else (self.active_skin or None)
            name = SKINS[show][0] if show else "跟随P1"
            head = f"P2皮肤: {name}"
            if len(head) > 14:
                head = f"P2皮肤: {name[:8]}.."
        else:
            head = "P2皮肤(双人)"
        self._text(head, p2btn.centerx, p2btn.centery - 9, 15, p2col, bold=True, center=True)
        # 副本切换按钮（右栏）
        db = self._dungeon_button_rect()
        dhover = db.collidepoint(mx, my)
        dun_enabled = self.is_dungeon or self.unlocked >= len(LEVELS)
        dcol = (NEON_PINK if dun_enabled else (60, 60, 90))
        pygame.draw.rect(self.screen, (18, 14, 30), db, border_radius=8)
        pygame.draw.rect(self.screen, dcol, db, 2, border_radius=8)
        if dhover:
            pygame.draw.rect(self.screen, WHITE, db, 1, border_radius=8)
        if self.is_dungeon:
            self._text("返回主线", db.centerx, db.centery - 10, 16,
                       NEON_CYAN if dhover else WHITE, bold=True, center=True)
        else:
            self._text(("副本 16关" if dun_enabled else "副本 未解锁"),
                       db.centerx, db.centery - 10, 16,
                       dcol if dhover else WHITE, bold=True, center=True)
        # ===== 进度 导入 / 导出 按钮（右栏，无下方小字）=====
        for (btn_fn, title, col) in [
            (self._export_button_rect(), "导出进度", NEON_GREEN),
            (self._import_button_rect(), "导入进度", NEON_CYAN),
        ]:
            btn = btn_fn
            bhover = btn.collidepoint(mx, my)
            pygame.draw.rect(self.screen, (14, 18, 30), btn, border_radius=8)
            pygame.draw.rect(self.screen, col, btn, 2, border_radius=8)
            if bhover:
                pygame.draw.rect(self.screen, WHITE, btn, 1, border_radius=8)
            self._text(title, btn.centerx, btn.centery - 10, 17,
                       col if bhover else WHITE, bold=True, center=True)
        # ===== Q6/Q7/Q8/Q9：新功能按钮 =====
        for (btn, title, col) in [
            (self._achievement_button_rect(), "成就", (255, 215, 0)),
            (self._endless_button_rect(),  "无尽模式", (180, 100, 255)),
            (self._boss_mode_button_rect(), "BOSS模式", (255, 60, 60)),
            (self._settings_button_rect(), "设置", (100, 200, 180)),
        ]:
            bhover = btn.collidepoint(mx, my)
            pygame.draw.rect(self.screen, (14, 18, 30), btn, border_radius=8)
            pygame.draw.rect(self.screen, col, btn, 2, border_radius=8)
            if bhover:
                pygame.draw.rect(self.screen, WHITE, btn, 1, border_radius=8)
            self._text(title, btn.centerx, btn.centery - 10, 17,
                       col if bhover else WHITE, bold=True, center=True)
        # 连线
        pos = self._map_positions()
        levels = self._get_levels()
        unlock = self._get_unlocked()
        path_col = NEON_PINK if self.is_dungeon else NEON_CYAN
        for i in range(len(pos) - 1):
            c1 = path_col if i < unlock - 1 else (50, 55, 80)
            pygame.draw.line(self.screen, c1, pos[i], pos[i + 1], 3)
        # 节点
        for i, (nx, ny) in enumerate(pos):
            lv = levels[i]
            unlocked = i < unlock
            is_cur = i == self.map_cursor
            node_col = lv["node"] if unlocked else (45, 48, 70)
            # 光晕
            if unlocked:
                g = get_glow(54, node_col, alpha=110)
                self.screen.blit(g, g.get_rect(center=(nx, ny)),
                                 special_flags=pygame.BLEND_RGB_ADD)
            pygame.draw.circle(self.screen, node_col, (nx, ny), 38)
            pygame.draw.circle(self.screen, (20, 22, 40), (nx, ny), 38, 3)
            # 编号
            self._text(str(i + 1), nx, ny - 10, 26, WHITE if unlocked else DIM,
                       bold=True, center=True)
            # 名称：相对节点圆下方显示，上移一些避免与下方详情行重叠或与下排挤压
            self._text(lv["name"], nx, ny + 44, 15, node_col if unlocked else DIM, center=True)
            # 副本：去掉每关节点下「钻X」标注（不显示，通关再给奖励）
            # 当前选中
            if is_cur:
                pulse = 42 + int(math.sin(pygame.time.get_ticks() * 0.006) * 4)
                pygame.draw.circle(self.screen, NEON_YELLOW, (nx, ny), pulse, 3)
        # 详情：整体下移，避免「【主线】第X关 名字」盖到第 13/14/15/16 关节点名
        cur = levels[self.map_cursor]
        header = "副本" if self.is_dungeon else "主线"
        self._text(f"【{header}】第 {self.map_cursor + 1} 关  {cur['name']}",
                   WIDTH // 2, HEIGHT - 90, 22, WHITE, bold=True, center=True)
        if self.is_dungeon:
            dr = cur.get("diamond_reward", 0)
            diff = cur.get("difficulty", 1.0)
            extra_desc = f"难度 x{diff:.2f}    通关奖励  钻石 +{dr}"
            self._text(extra_desc, WIDTH // 2, HEIGHT - 65, 14, (220, 220, 255), center=True)
            self._text(cur["desc"], WIDTH // 2, HEIGHT - 42, 14, NEON_GREEN, center=True)
        else:
            self._text(cur["desc"], WIDTH // 2, HEIGHT - 63, 14, NEON_GREEN, center=True)
        # Q3：初始界面最下一行去掉 F1/F2/F3 字样，只保留常用操作提示
        self._text("← → 切换关卡    空格/回车/点击 开始    T 单/双人    H 控制    F11 全屏    ? 说明    右键/B 皮肤技能    ESC 确认窗",
                   WIDTH // 2, HEIGHT - 22, 14, DIM, center=True)
        # 说明面板
        if self.show_help:
            self._draw_help()
        # 商店面板
        if self.show_shop:
            self._draw_shop(mx, my)
        # 抽奖面板
        if self.show_lottery:
            self._lottery_draw(mx, my)
        # Q6：成就面板
        if getattr(self, "show_achievements", False):
            self._draw_achievements(mx, my)
        # Q8：设置面板
        if getattr(self, "show_settings", False):
            self._draw_settings(mx, my)

    # ---- 覆盖层 ----
    def _dim(self, alpha=160):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((4, 4, 14, alpha))
        self.screen.blit(overlay, (0, 0))

    def _overlay_pause(self):
        self._dim(120)
        self._text("已暂停", WIDTH // 2, HEIGHT // 2 - 170, 60, WHITE, bold=True, center=True)
        # Q8：P/ESC/空格 继续 再向下移 50 像素（距「已暂停」> 140px，避免遮挡标题）
        self._text("P/ESC/空格 继续    R 重开本关", WIDTH // 2, HEIGHT // 2 - 40, 22, DIM, center=True, bold=True)
        # ===== Q2：皮肤切换（暂停时直接切换，无需空格确认）=====
        owned = [sid for sid in ALL_SKIN_ORDER if sid in self.owned_skins]
        if not owned:
            owned = [None]
        # 直接显示当前 active_skin（不再有 pending 预览态）
        preview_sid = self.active_skin
        try:
            cur_idx = owned.index(preview_sid)
        except ValueError:
            cur_idx = 0
        # 当前皮肤信息
        cur_sid = owned[cur_idx]
        if cur_sid is not None and cur_sid in SKINS:
            cur_name = SKINS[cur_sid][0]
            cur_col = SKINS[cur_sid][2]
        else:
            cur_name = "默认星辰"
            cur_col = NEON_CYAN
        # 左右按钮 + 中间皮肤名
        prev_btn = pygame.Rect(WIDTH // 2 - 210, HEIGHT // 2 + 20, 80, 48)
        next_btn = pygame.Rect(WIDTH // 2 + 130, HEIGHT // 2 + 20, 80, 48)
        mid_box = pygame.Rect(WIDTH // 2 - 120, HEIGHT // 2 - 30, 240, 98)
        mx, my = pygame.mouse.get_pos()
        # 中间皮肤面板
        pygame.draw.rect(self.screen, (16, 18, 36), mid_box, border_radius=14)
        pygame.draw.rect(self.screen, cur_col, mid_box, 2, border_radius=14)
        # 皮肤色预览球
        pxc = mid_box.centerx
        pyc = mid_box.centery - 22
        g = get_glow(50, cur_col, alpha=180)
        self.screen.blit(g, g.get_rect(center=(int(pxc), int(pyc))),
                         special_flags=pygame.BLEND_RGB_ADD)
        pygame.draw.circle(self.screen, cur_col, (int(pxc), int(pyc)), 22)
        pygame.draw.circle(self.screen, WHITE, (int(pxc), int(pyc)), 22, 2)
        # 皮肤名字
        self._text(f"{cur_idx + 1} / {len(owned)}  {cur_name}",
                   pxc, mid_box.centery + 22, 16, WHITE, center=True, bold=True)
        # 左右按钮
        for b, txt in ((prev_btn, "< 上一"), (next_btn, "下一 >")):
            hover = b.collidepoint(mx, my)
            pygame.draw.rect(self.screen, (18, 22, 42), b, border_radius=10)
            pygame.draw.rect(self.screen, NEON_GREEN if hover else DIM, b, 2, border_radius=10)
            self._text(txt, b.centerx, b.centery - 10, 17,
                       NEON_GREEN if hover else WHITE, bold=True, center=True)
        # Q1：空格已改为暂停/继续切换，皮肤切换通过左右键/数字键
        self._text("左右键/数字键 直接切换皮肤",
                   WIDTH // 2, mid_box.bottom + 12, 15, NEON_YELLOW, center=True, bold=True)
        # 返回地图按钮
        btn_back = pygame.Rect(WIDTH // 2 - 130, HEIGHT // 2 + 150, 260, 52)
        hover = btn_back.collidepoint(mx, my)
        pygame.draw.rect(self.screen, (18, 20, 38), btn_back, border_radius=10)
        pygame.draw.rect(self.screen, NEON_PINK, btn_back, 2, border_radius=10)
        self._text("返回地图选关 (Q)", btn_back.centerx, btn_back.centery - 10, 22,
                   NEON_PINK if hover else WHITE, bold=True, center=True)

    def _overlay_level_complete(self):
        self._dim(150)
        lv = self._get_levels()[self.current_level]
        self._text("关卡完成!", WIDTH // 2, HEIGHT // 2 - 110, 54, NEON_YELLOW,
                   bold=True, center=True)
        self._text(f"第 {self.current_level + 1} 关  {lv['name']}", WIDTH // 2, HEIGHT // 2 - 56,
                   24, WHITE, center=True)
        # 星级
        stars = 3 if self.combo_peak >= 15 else (2 if self.combo_peak >= 8 else 1)
        star_txt = "*" * stars + "." * (3 - stars)
        self._text(star_txt, WIDTH // 2, HEIGHT // 2 - 16, 42, NEON_YELLOW, bold=True, center=True)
        self._text(f"本关吞噬 {self.level_eaten}  ·  最高连击 {self.combo_peak}  ·  总分 {self.score}",
                   WIDTH // 2, HEIGHT // 2 + 36, 18, DIM, center=True)
        if self.lc_timer > 0.4 and int(pygame.time.get_ticks() / 400) % 2 == 0:
            lvs = self._get_levels()
            nxt = "挑战最终关" if self.current_level >= len(lvs) - 1 else f"下一关：{lvs[self.current_level + 1]['name']}"
            self._text(f"空格/点击  {nxt}", WIDTH // 2, HEIGHT // 2 + 90, 22, NEON_CYAN,
                       bold=True, center=True)

    def _overlay_victory(self):
        self._dim(170)
        self._text("通  关", WIDTH // 2, HEIGHT // 2 - 90, 64, NEON_YELLOW,
                   bold=True, center=True)
        self._text("你吞噬了整个宇宙!", WIDTH // 2, HEIGHT // 2 - 20, 28, WHITE,
                   bold=True, center=True)
        self._text(f"最终分数  {self.score}", WIDTH // 2, HEIGHT // 2 + 24, 24, NEON_CYAN,
                   bold=True, center=True)
        if int(pygame.time.get_ticks() / 400) % 2 == 0:
            self._text("空格/R/点击  返回地图", WIDTH // 2, HEIGHT // 2 + 90, 22, NEON_PINK,
                       bold=True, center=True)

    def _overlay_over(self):
        self._dim(170)
        self._text("游戏结束", WIDTH // 2, HEIGHT // 2 - 90, 64, NEON_RED, bold=True, center=True)
        self._text(f"第 {self.current_level + 1} 关  {self._get_levels()[self.current_level]['name']}",
                   WIDTH // 2, HEIGHT // 2 - 30, 22, DIM, center=True)
        self._text(f"分数  {self.score}", WIDTH // 2, HEIGHT // 2 + 6, 30, WHITE,
                   bold=True, center=True)
        self._text(f"吞噬 {self.level_eaten}/{self._get_levels()[self.current_level]['goal']}  ·  存活 {int(self.time_alive)}s",
                   WIDTH // 2, HEIGHT // 2 + 46, 17, DIM, center=True)
        if self.over_timer > 0.6 and int(pygame.time.get_ticks() / 400) % 2 == 0:
            self._text("R/点击 重开本关    ESC/Q 返回地图", WIDTH // 2, HEIGHT // 2 + 100, 20,
                       NEON_CYAN, bold=True, center=True)


# ================ 入口 ================
if __name__ == "__main__":
    Game().run()