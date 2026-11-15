# Evidence-Grounded Verification for Investment Hypotheses

一个面向主观投资研究的通用 **agent skill + 最小离线证据工具**。将自然语言假设拆解为可审查的命题，通过公开数据、代理变量和多条证据路径形成有来源、有边界、可修订的判断。BYD 是其中一个案例，不是工具预设的研究对象。

## 使用方式

将 [`skills/investment-hypothesis-verification`](skills/investment-hypothesis-verification) 整个目录复制到支持 `SKILL.md` 的 agent 的 skills 目录。例如 Codex 的 `~/.codex/skills/`。该目录包含独立运行需要的全部脚本和说明，不依赖本仓库的 BYD 文件。

在 agent 中调用：

> 使用 $investment-hypothesis-verification 分析这个投资假设：某零售商增加自动化仓储投入，会通过提高周转效率，在未来三年产生超过资本成本的增量回报。限定使用截至指定日期可获取的公开证据；审查代理效度，比较多条路径，并输出冲突解释、缺失证据和结构化反馈。

请给出研究对象、假设、信息截止日期和预测期限。它也适用于定价权、用户留存、渠道扩张、研发投入、行业供需等命题；具体数据和估计方法由研究问题决定。

## 工作流程

1. **假设形式化**：明确对象、期限、隐含条件和模糊构念，区分描述、预测与因果命题。
2. **证据与代理审查**：寻找公开来源，记录发布时间、口径及来源家族；检查代理是否衡量目标构念。
3. **多路径验证**：组织经营、财务、竞争、客户或其他适用路径；检查共同来源、共同偏差和识别条件。
4. **冲突与修订**：区分口径差异和实质矛盾；提出可区分解释的下一步取证；代理失效时追踪受影响节点。
5. **分层反馈**：分别输出可执行检查、带来源的分析判断、未识别部分及下一步行动。未来投资结论不自动作为正确性奖励。

完整规范见 [SKILL.md](skills/investment-hypothesis-verification/SKILL.md)，数据约定见 [schema](skills/investment-hypothesis-verification/references/schema.md)，研究检查见 [research checks](skills/investment-hypothesis-verification/references/research-checks.md)。

## 最小工具：Python 3.10+，无第三方依赖

从仓库根目录创建独立案例：

```sh
python prototype.py init local_runs/retail --id RETAIL_AUTOMATION --as-of 2026-11-15 --horizon "2027-2029" --hypothesis "Warehouse automation creates incremental returns above the cost of capital."
```

这只生成待填写模板，不会自动完成假设拆解。由 agent 或研究员补全 `case.json`、`sources.json`、`observations.json` 后运行：

```sh
python prototype.py run --case local_runs/retail --out local_runs/retail-run
```

需要计算时，在案例目录编写并单独执行计算脚本，再通过 `--calculations calculations.json` 传入带来源的结果。工具不会自动执行案例中的代码。审查 `review_prompt.md` 后，可以将结构化分析保存为 `review.json`，使用 `--review review.json` 检查格式和引用资格。

每次运行生成：

| 文件 | 内容 |
|---|---|
| `evidence_packet.json` | 截止日期内的来源、观测、计算、代理、路径与依赖关系 |
| `review_prompt.md` | 通用审查指令及证据包，供 agent/研究员使用 |
| `results.json` | 输入指纹、来源筛选、失效节点与可选审查记录 |
| `feedback.json` | 可执行检查与语义候选标签分开；未校准语义标签的训练 mask 为 0 |

受控诊断支持 `--as-of YYYY-MM-DD`、`--drop-source SOURCE_ID`、`--invalidate NODE_ID`，可重复传入后两项。失效传播仅沿已声明的依赖图进行；它标记“需要重审”，不自动判定下游命题为假。删除来源后不能继续提交引用该来源的旧 review，应重新审查。

## 案例：BYD 资本投入与未来超额回报

[案例说明](cases/byd/README.md) · [中文研究报告](cases/byd/report.md) · [公开来源清单](cases/byd/sources.json)

```sh
python cases/byd/calculate.py
python prototype.py run --case cases/byd --calculations cases/byd/outputs/calculations.json --review cases/byd/review.example.json --out cases/byd/outputs/verification
```

BYD 的财务转录、充电站经济性假设、48 个情景和报告均放在 `cases/byd/`。它演示“网络规模并不直接证明利润归属或未来超额回报”等代理审查。案例结论是特定截止日期的研究记录，本次架构改造不等于更新其原始数据。

## 验证与范围

```sh
python -m unittest discover -s tests -v
```

测试使用不涉及汽车或充电的合成零售案例，检查任意命题 ID、日期门控、来源依赖、局部失效、反馈隔离及 skill 独立复制运行，并对 BYD 原有数值做回归检查。合成数据仅用于软件测试，不是零售投资的实证结果。

**能力边界**：skill 指导宿主 agent 检索与推理；Python 工具只做离线结构、来源资格和依赖检查，不调用 LLM、不自动抓取网页、不验证引用蕴含，也不提供经过校准的因果估计或收益预测。不同路径或来源家族的数量不能当作统计独立性。详见 [RUN_SCOPE](reports/RUN_SCOPE.md)。

许可证：[MIT](LICENSE)。
