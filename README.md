# 🌌  Stardust Devourer（星尘吞噬者）

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Pygame](https://img.shields.io/badge/Pygame-2.6.1-green.svg)](https://www.pygame.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Release](https://img.shields.io/badge/Release-V1.0.0-orange.svg)](https://github.com/cbyygyitoh/stardust-devourer/releases)

> 🚀 霓虹风格吞噬成长闯关游戏 — 16关主线 + 16关副本 · 双人同屏 · 30款皮肤 · 300个成就

---

## 🎮 游戏简介

《星尘吞噬者》是一款霓虹风格的**吞噬成长闯关游戏**。你将成为一颗星际星球，在绚丽的星尘中吞噬小星体不断成长，挑战越来越强的敌方刺球，解锁全新关卡和炫酷皮肤！

<img width="1442" height="1134" alt="image" src="https://github.com/user-attachments/assets/d3d0b8bd-d325-46d9-91d4-5daede342f75" />

支持**单人模式**（鼠标/键盘/方向键）与**双人同屏模式**，内置**30款特色皮肤**、**12种道具**、**300个成就**及**无尽/BOSS模式**。

---

## ✨ 核心特色

| 特性 | 说明 |
|------|------|
| 🗺️ **32个关卡** | 16关主线 + 16关副本，顺序解锁，难度逐级递增 |
| 👥 **双人模式** | 支持双人同屏合作/对战，P1(WASD)，P2(↑↓←→) |
| 🎨 **30款皮肤** | 金币/钻石/至高/终极四阶，每款拥有专属技能与霸气外观 |
| 🛠️ **12种道具** | 护盾、磁吸、时停、炸弹、光枪、光刃等丰富战术选择 |
| 👾 **13种敌人** | 尖刺、病毒、三球、长蛇、恐怖种、牛魔王、幽灵等，各有独特AI |
| 🏆 **300个成就** | 进度/战斗/收集/特殊/里程碑五类，解锁获得奖励 |
| ♾️ **无尽模式** | 无限波次生存挑战，每波奖励递增 |
| 👹 **BOSS模式** | 连续挑战16关强力Boss，难度逐步攀升 |
| 💾 **进度管理** | 自动存档 + 手动导入/导出（含8位导入码） |

---

## 🎯 游戏玩法

### 核心机制

1. **吞噬成长** — 控制星球吞噬比自己小的星体，体积不断增大
2. **敌方战斗** — 刺球拥有独立生命值，需通过武器或技能削减至零
3. **连击倍率** — 连续吞噬获得倍率加成，最高可叠加
4. **能量管理** — 加速冲刺和皮肤技能消耗能量，随时间自动回复
<img width="1442" height="1134" alt="image" src="https://github.com/user-attachments/assets/1bb6a1cd-8495-4081-989d-afa1b5afe9c3" />


### 敌方种族

游戏内置13种敌方种族，每种拥有独特的AI行为：

| 种族 | 说明 |
|------|------|
| 尖刺 | 基础敌人，直线移动 |
| 病毒 | 死亡分裂为两个小球 |
| 三球 | 3颗卫星球体旋转 |
| 双球 | 2颗球体旋转 |
| 虫群 | 长条形虫身，合围玩家 |
| 长蛇 | 多球连节，断头后分裂 |
| 恐怖种 | 血红骷髅脸，死亡分裂两次 |
| 牛魔王 | 双巨角，生命极高 |
| 幽灵 | 半透明可穿墙 |
| 蜘蛛 | 8条长腿，近战威胁 |
| 蜈蚣 | 12节长身，群体移动 |
| 毒蛇 | 暗绿鳞片，毒雾持续伤害 |
| 玄武龟 | 六边形甲壳，移动缓慢但生命极高 |

---

## 🎮 操作指南

### 单人模式

| 操作 | 键位 |
|------|------|
| 移动 | 鼠标 / 方向键 |
| 加速冲刺 | 鼠标左键 / V |
| 皮肤技能 | 鼠标右键 / B |
| 切换控制方式 | H（鼠标 ↔ 方向键） |

### 双人模式

| 玩家 | 移动 | 加速 | 技能 |
|------|------|------|------|
| P1 | WASD | V | B |
| P2 | ↑↓←→ | [ | ] |

### 通用操作

| 功能 | 键位 |
|------|------|
| 切换关卡（地图界面） | ← / → |
| 切换单/双人模式（地图界面） | T |
| 游戏说明 | ? / F1 |
| 开始 / 下一关 | 空格 / 回车 / 点击 |
| 暂停 | P |
| 返回地图（暂停/结束时） | Q |
| 静音 | F3 |
| 重开当前关 | R |
| 全屏切换 | F11 |
| 返回地图 / 暂停 / 退出 | ESC |

---
## 🎬 演示示例


---

## 🖥️ 安装与运行

### 方式一：直接运行（推荐）

1. 从 [Releases](https://github.com/cbyygyitoh/stardust-devourer/releases) 下载 `StardustDevourer.exe`
2. 双击运行即可，无需安装任何环境

### 方式二：源码运行

```bash
# 克隆仓库
git clone https://github.com/cbyygyitoh/stardust-devourer.git
cd stardust-devourer

# 安装依赖
pip install -r requirements.txt

# 运行游戏
python stardust_devourer.py
```

## 📦 依赖库

| 库 | 版本 | 用途 |
|----|------|------|
| pygame | 2.6.1 | 游戏引擎 |
| numpy | 1.24+ | 数值计算 / 粒子特效 |
| opencv-python | 4.8+ | 图像处理（可选，仅手势控制需要） |

---

## 🏷️ 版本历史

### V1.0.0（当前版本）

- ✅ 16个主线关卡 + 16个副本关卡
- ✅ 单人/双人模式
- ✅ 30款皮肤（金币/钻石/至高/终极）
- ✅ 12种道具
- ✅ 13种敌方种族
- ✅ 300个成就
- ✅ 无尽模式 + BOSS模式
- ✅ 进度导入/导出
- ✅ 兑换码系统

## ⚠️ 当前版本说明

### 手势控制暂不可用

由于 `MediaPipe` 和 `TensorFlow` 依赖库体积过大（约 **1-2GB**），打包后严重影响下载和启动效率，当前 Windows 发行版**暂不支持手势控制功能**。

**推荐使用以下方式游玩：**

- ✅ 鼠标控制（推荐）
- ✅ 键盘方向键控制
- ✅ 双人模式（P1: WASD / P2: 方向键）

> 手势控制将在后续版本重新评估优化方案后择机恢复。
---

## 📄 开源协议

本项目采用 [MIT License](LICENSE) 开源协议，欢迎 Fork 和 PR！

---

## 🙏 致谢

- [Pygame](https://www.pygame.org/) — 强大的游戏开发框架
- [Python](https://www.python.org/) — 优雅的编程语言

---

## 📧 联系方式

- GitHub: [@cbyygyitoh](https://github.com/cbyygyitoh)
- 项目地址: [https://github.com/cbyygyitoh/stardust-devourer](https://github.com/cbyygyitoh/stardust-devourer)

---

**如果觉得这个项目不错，别忘了给个 ⭐ Star 支持一下！**
