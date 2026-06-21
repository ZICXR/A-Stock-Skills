# Web UI (Streamlit)

> A-Stock-Skills 的可视化 Web 界面

## 启动

```bash
# 安装依赖
pip install streamlit plotly

# 启动
streamlit run webui/app.py
```

默认在 http://localhost:8501 打开

## 功能

| 页面 | 功能 |
|------|------|
| 实时行情 | 单股实时数据 |
| 涨停板 | 当日涨停追踪 |
| 技术面 | K线 + 买卖信号 |
| 大盘分析 | 主要指数 + 广度 |
| 每日复盘 | 一键生成报告 |
| 个股研报 | 深度研究报告 |
| 自选股监控 | 多股实时 |

## 截图

(启动后可见)

## 添加新页面

编辑 `webui/app.py`, 在 `SKILL_RENDERERS` 字典中添加新 Skill 的渲染函数。
