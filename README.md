# BYD investment-hypothesis prototype

一个最小、可复算的主观投资研究框架。案例问题：BYD 的闪充等资本投入，能否在 2027–2030 年形成可持续的超额经济回报？信息截止 **2026-11-15**。

**[阅读中文分析报告](reports/BYD_OUTLOOK_ZH.md)** · [公开来源](cases/byd/sources.json) · [实际计算结果](outputs/byd/results.json)

## 一分钟运行

Python 3.10+，无第三方依赖，不需要 API key，也不会发起网络请求。

```sh
python prototype.py
python -m unittest discover -s tests -v
```

第一条命令输出证据包、情景结果、结构化反馈和供模型使用的提示文件。默认不填充任何语义结论。

导入本项目的示范分析（保持仓库中示范输出一致）：

```sh
python prototype.py --review examples/byd_review.json
```

`examples/byd_review.json` 是本次研究中由 AI 助手编写的分析示例，**不是独立 Agent 实验结果，也不是参考真值**。运行脚本不会调用模型。它仅验证命题完整性和引用 ID/时间有效性，不验证语义正确性。

## 最小工作流

```text
case.json + sources.json + financials.csv
                 |
                 v
      日期过滤 / 来源记录 / 财务与情景计算
                 |
                 v
      evidence_packet.json + review_prompt.md
                 |
        交给任意 LLM 或研究员审阅
                 |
                 v
      导入 review.json -> 结构检查 -> feedback.json
```

1. 执行 `python prototype.py`。
2. 将 `outputs/byd/review_prompt.md` 交给任意模型或研究员。提示中包含本轮已筛选证据、假设和计算。不要同时提供示范答案。
3. 把返回的 JSON 保存到 `local_runs/review.json`。
4. 执行 `python prototype.py --review local_runs/review.json --out local_runs/reviewed`。

外部模型只看人工整理的证据包，尚不具备自主检索。未来可以接一个模型适配器；首版有意保留文件接口，避免引入模型账户、框架和部署依赖。

## 可运行的诊断

```sh
# 源文件发布日期截止检查；这是来源可得性回放，不是完整的历史投资模拟。
python prototype.py --as-of 2026-04-01 --out local_runs/early
# 移除竞争对手证据后重新生成研究输入，再让模型重新判断。
python prototype.py --drop-source catl2026 --out local_runs/no_competitor
```

日期过滤不自动重建历史信息全集；研究问题、情景和代理设计是在 2026-11-15 编写的。不得把这些回放标记为当时的真实预测。

## 文件

| 路径 | 内容 |
|---|---|
| `prototype.py` | 唯一运行程序；计算、日期门控、提示导出、结论导入 |
| `cases/byd/` | 假设、来源清单、人工核对的财务输入、示意参数 |
| `prompts/research.md` | 通用研究流程与输出格式 |
| `examples/byd_review.json` | 明确标记作者来源的示范分析 |
| `outputs/byd/` | 已执行的结果、48 行情景网格、输入哈希和反馈 |
| `reports/` | 中文研究报告及运行范围 |
| `tests/` | 10 项实现测试，不是投资假设验证成功率 |

## 结果与边界

- “集团购建长期资产现金支出”不等于“闪充资本开支”；现金流残差不等于股东自由现金流。
- 公司公布的累计充电量不能除以期末站数就作为成熟站利用率。
- 场景中的投资、留存边际收益、年限和资本成本是**示意输入**，不是 BYD 已披露数据，不分配概率。
- 同源文件不视为独立复制。6 个文件属于 BYD 和 CATL 两个上游来源家族，后者也是供应商自述。
- 未独立复核的语义反馈 `mask=0`，不自动投入训练。
- 尚未进行模型比较、微调、因果估计或股票回测。本报告讨论经营假设，不给出目标价或交易建议。

本仓库只保存原创代码、分析、必要的数据点与来源链接，不转载完整报告、图片、私人笔记或账户凭据。代码采用 MIT 许可；原始第三方材料的权利归其所有者。
