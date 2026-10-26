<p align="center"><img src="assets/banner.svg" alt="像樊登一样讲书" width="860"></p>

<h3 align="center">先报书再讲理 · 观点永远挂着故事 · 随时把「他」换成「你」</h3>

<p align="center">简体中文 | <a href="README.en.md">English</a></p>

<p align="center">
<a href="CHANGELOG.md"><img src="https://img.shields.io/badge/version-v2.0-blue" alt="Version"></a>
<a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green" alt="License"></a>
<a href=".github/workflows/ci.yml"><img src="https://img.shields.io/badge/CI-示例AI味%3C20-brightgreen" alt="CI"></a>
<a href="tools/"><img src="https://img.shields.io/badge/python-3.8%2B-blue?logo=python" alt="Python"></a>
<a href="corpus/README.md"><img src="https://img.shields.io/badge/语料-60样本·30小时·39万字-8b5cf6" alt="Corpus"></a>
<a href="research/统计结果.md"><img src="https://img.shields.io/badge/编码-786单元·kappa披露-c0392b" alt="Coding"></a>
<a href="CONTRIBUTING.md"><img src="https://img.shields.io/badge/PRs-welcome-brightgreen" alt="PRs Welcome"></a>
</p>

---

一句话：把一本书、一个道理，讲成樊登那样。这是一个装进 AI 工具的 skill——你说一句话，它按樊登讲书的方法产出内容。**像不像不由感觉说了算**：方法全部来自 30 小时公开语料的逐单元编码统计，每条规则都能回放核对。

## 30 秒上手（零依赖）

```bash
git clone 本仓库 && cd think-like-fandeng
python3 tools/ai_flavor_check.py tools/demo/AI味对照稿.txt    # AI 味 54/100
python3 tools/ai_flavor_check.py tools/demo/本仓库示例稿节选.txt # AI 味 4/100
```

同一个检测器、同一套基准（樊登 19 万字实测频次），AI 腔的稿子和按本 skill 写的稿子，分数差出一个量级。检测逻辑全部可数、完全透明，见 `tools/ai_flavor_check.py`。

## 最直观的看效果：真人 vs 生成版正面对照

同一本书《我可能错了》，skill 生成版（未看语料）与樊登真人讲书的实际开场、正文、收尾，逐段并排对照——开场走的是同一条路（书名+定性+作者来头），观点后面挂的都是场景，收尾都是一句总结不列清单：

→ **[examples/13-对照案例-我可能错了.md](examples/13-对照案例-我可能错了.md)**

被尖锐追问时呢？skill 应答与鲁豫真实访谈的同类应答对照——都先接招给立场，没有一个绕圈子：

→ **[examples/14-对照案例-被追问时.md](examples/14-对照案例-被追问时.md)**

更多示例（12 个，覆盖讲书 / 分析 / 口播 / 对谈 / 改稿五种用法）→ [examples/](examples/)

## 它能带来什么

你说「给我讲讲这本书」，多数 AI 给你的是一份内容摘要：观点一、观点二、观点三，最后祝你学有所成。听着全对，就是没人记得住。

这个 skill 给你的是讲法。同一个观点，它会先立住，然后马上给你一个有人的场景——你半夜嚼着白天那句话的样子、你把鞋擦好放在门口等孩子的样子。你会发现，书里的道理落到你身上，从来不是「我认为」，是「你有没有过」。讲完不催你行动，一句总结把整期收拢，书推给你，路留给你。

一句话：它不替你读书，它替你把书讲成「人话」。

## 怎么用

把 [SKILL.md](SKILL.md) 装进你的 AI 工具（支持 Claude Skills / ZCode skill 的工具直接安装），然后：

| 你说 | 你得到 |
|---|---|
| 用樊登的方式，给我讲讲《XXX》这本书 / 这一章 | 5 分钟可直接念的讲书稿 |
| 用樊登 skill 帮我分析一下 XXX | 可转发的分析短文 |
| 用樊登的方式写一篇 2 分钟口播 | 可直接念的稿子 |
| 我想和樊登聊聊 XXX，你来当樊登 | 一来一回的对话（第一轮声明：按他的思路聊，不是本人） |
| 这是我的讲稿，樊登帮我改改 | 最要紧的问题 + 改好的全文 + 改动说明 |

没有 skill 机制的工具，直接把 SKILL.md 全文粘给 AI 当系统提示词。想深入每种做法的细则与出处，SKILL.md 尾部有 10 个专题文件的「按需再读」索引。

## 这套方法是从哪来的

不是「感觉像」，是数出来的：

- **样本**：60 个公开样本分层随机抽取（讲书 12 期 / 官方短视频 28 条 / 演讲 6 场 / 访谈 6 场 / 第三方切片 8 条），约 30 小时、39 万字转写；
- **编码**：786 个单元逐一带时间戳编码，每个数字可由 `research/scripts/` 一键复算；
- **复核**：169 个单元由 44 个独立复核员重编，一致率与 kappa 全部披露——**未过信度检验的结论如实降级为「探索性观察」，不冒充强结论**；
- **几个反直觉的发现**：开场 75% 先介绍书和作者（不是先抛问题）；被追问 61–84% 第一句直接给答案（不是先讲故事）；收尾行动清单只占 17%；第三方切片 5/7 把金句剪到片头——「他先抛金句」是剪辑制造的错觉。

完整方法 → [METHODOLOGY.md](METHODOLOGY.md)；每条结论的原文出处与反例 → [references/thinking-思维运转.md](references/thinking-思维运转.md)；全部数字一处汇总 → [references/data-量化复盘.md](references/data-量化复盘.md)。

## 仓库结构

```
SKILL.md                  skill 本体：五种用法 + 讲书十步 + 交付前自检（自足可用）
references/               专题库：生成前检验 / 十步细则 / 对谈手册 / 改稿审查 /
                          禁用清单（带实测频次）/ 句法气口 / 标杆拆解 / 金句库 /
                          量化复盘 + 研究层主文档
examples/                 14 个示例：12 个用法示例 + 2 个真人对照案例
tools/ai_flavor_check.py  「AI 味」检测器（基准为樊登语料实测，附 demo 对照稿）
research/                 抽样记录、编码表、统计脚本（一键复算）、复核报告
corpus/                   语料说明（音频与转写全文受版权约束不入库）
assets/                   横幅与标识
```

## 版权与伦理

- 研究只用公开免费内容；转写全文与音频不公开（`git ls-files` 可验证零泄露）。
- 产出为**风格学习**，不冒充樊登本人；对谈用法第一轮即声明。
- 讲书稿只概括和讲解，不大段复述原书；书中事实无把握时标注【待核实】。
- 不使用其声音与肖像；不攻击任何作者。

## 社区

- 报问题、提建议：开 issue，附你的输入、输出和检测器分数。
- 贡献规则与示例：见 [CONTRIBUTING.md](CONTRIBUTING.md)——改规则要带语料证据。
- 更新记录：[CHANGELOG.md](CHANGELOG.md)。

## License

见 [LICENSE](LICENSE)。
