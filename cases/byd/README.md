# BYD case: capital investment and prospective excess returns

这是通用 [investment-hypothesis-verification skill](../../skills/investment-hypothesis-verification/SKILL.md) 的一个研究案例。原始假设是：当前大规模资本投入，尤其闪充基础设施，可能在短期表现疲弱时仍创造未来可持续的超额回报。

## 文件

- `case.json`：命题、代理、路径、缺失证据与示范性依赖图。
- `sources.json` / `observations.json`：有日期和来源家族的证据目录；计划与已报告观测分开。
- `financials.csv`：公开财务数据的手工转录，缺失值保留为空。
- `scenario.json` / `calculate.py`：仅适用于本案例的充电经济性假设与计算。
- `review.example.json`：既有人工/助手分析记录，不是新调用模型产生的验证结果。
- [report.md](report.md)：中文分析、证据冲突解释与后续可检验条件。

## 复现

在仓库根目录执行：

```sh
python cases/byd/calculate.py
python prototype.py run --case cases/byd --calculations cases/byd/outputs/calculations.json --review cases/byd/review.example.json --out cases/byd/outputs/verification
```

第一个命令计算财务变化、三组示例情景和 48 行敏感性网格；第二个命令用通用工具检查来源资格及 review 结构。若只需要准备待分析证据包，省略 `--review`。

输出位于 `outputs/`；通用证据包和反馈位于 `outputs/verification/`。所有情景都是显式假设下的成熟期经济性测算，不是已观测收益，也不是股价预测。集团资产购置现金支出不等于闪充专项资本支出。

示例：检查“品牌站点数代表资本所有权和利润捕获”这一代理失效的影响：

```sh
python prototype.py run --case cases/byd --calculations cases/byd/outputs/calculations.json --invalidate M_owned_network --out local_runs/byd-proxy-challenge
```

工具将标记 `M_owned_network`、`P3`、`P4` 需要重审，不会把它们自动改为假，也不会标记图中不依赖该代理的其他命题。依赖图只演示一条重要关系，并非完整因果图。

调整截止日期时，计算记录只有在其全部来源均符合日期要求时才会进入通用证据包。计算文件本身仍包含完整输入，因此历史回测应只消费筛选后的证据包，并另外核对数据修订版本、观测时间和当时可获得性。
