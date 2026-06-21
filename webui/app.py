"""
A-Stock-Skills Web UI
====================
基于 Streamlit 的可视化仪表板

启动: streamlit run webui/app.py
"""

import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta


# ============================================================
# 页面配置
# ============================================================
st.set_page_config(
    page_title="A-Stock-Skills",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# 侧边栏 - Skill 选择
# ============================================================
st.sidebar.title("📈 A-Stock-Skills")
st.sidebar.markdown("**41 个 A 股分析 Skill**")

CATEGORIES = {
    "🏠 首页": ["首页"],
    "📡 数据采集": [
        "实时行情", "新闻情绪", "公司公告", "大盘数据", "板块数据",
        "个股信息", "政策资讯", "自选股监控",
    ],
    "🌊 市场分析": [
        "大盘分析", "板块轮动", "资金流向", "龙虎榜",
        "北向资金", "两融分析",
    ],
    "🎯 个股分析": [
        "涨停板", "技术面", "基本面", "估值", "财报",
        "个股资金流", "股东分析", "同业对比",
    ],
    "📊 量化策略": [
        "多因子", "回测", "信号筛选", "风控", "组合优化",
        "自定义筛选", "多策略", "事件驱动", "专业回测", "择时",
    ],
    "🤖 ML 量化": [
        "涨跌分类", "价格预测", "ML 因子", "LSTM 预测",
    ],
    "📝 报告": [
        "每日复盘", "个股研报", "持仓报告",
    ],
    "🛠️ 工具": [
        "告警推送", "持仓模拟器",
    ],
}

category = st.sidebar.selectbox("选择分类", list(CATEGORIES.keys()))
skill = st.sidebar.selectbox("选择 Skill", CATEGORIES[category])

st.sidebar.markdown("---")
st.sidebar.markdown(f"""
**当前 Skill**: `{skill}`

📖 [项目主页](https://github.com/ZICXR/A-Stock-Skills)
""")


# ============================================================
# 主页面 - 首页
# ============================================================
if category == "🏠 首页" or skill == "首页":
    st.title("📈 A-Stock-Skills Dashboard")
    st.markdown("""
    欢迎使用 **A-Stock-Skills** Web UI!

    这是一个集成 41 个 A 股分析 Skill 的可视化仪表板, 覆盖:
    - 📡 数据采集 (8 个)
    - 🌊 市场分析 (6 个)
    - 🎯 个股分析 (8 个)
    - 📊 量化策略 (10 个)
    - 🤖 ML 量化 (4 个)
    - 📝 报告 (3 个)
    - 🛠️ 工具 (2 个)
    """)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Skill 总数", "41", "+4")
    with col2:
        st.metric("支持数据源", "3", "akshare/tushare/东财")
    with col3:
        st.metric("支持渠道", "6", "钉钉/微信/飞书/Slack/Telegram/Server酱")
    with col4:
        st.metric("GitHub Stars", "⭐", "欢迎 Star")

    st.markdown("---")

    # 快捷入口
    st.subheader("🚀 快速入口")
    quick_cols = st.columns(3)
    with quick_cols[0]:
        if st.button("📊 今日复盘", use_container_width=True):
            st.session_state["skill"] = "每日复盘"
    with quick_cols[1]:
        if st.button("🔥 涨停板追踪", use_container_width=True):
            st.session_state["skill"] = "涨停板"
    with quick_cols[2]:
        if st.button("💰 资金流向", use_container_width=True):
            st.session_state["skill"] = "资金流向")


# ============================================================
# Skill 页面实现
# ============================================================
def render_realtime():
    """实时行情"""
    st.header("📊 实时行情")
    code = st.text_input("股票代码", value="000001")
    if st.button("查询"):
        with st.spinner("加载中..."):
            from skills.02-data-collection.stock-basic-info.stock_basic_info import get_realtime
            rt = get_realtime(code)
            if rt:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("股票名称", rt.get("name", ""))
                    st.metric("现价", f"{rt.get('price', 0):.2f}")
                with col2:
                    st.metric("涨跌幅", f"{rt.get('pct_change', 0):+.2f}%")
                    st.metric("换手率", f"{rt.get('turnover', 0):.2f}%")
                with col3:
                    st.metric("总市值", f"{rt.get('total_mv', 0)/1e8:.2f}亿")
                    st.metric("PE", f"{rt.get('pe', 0):.2f}")
            else:
                st.error("未找到数据")


def render_zt_pool():
    """涨停板追踪"""
    st.header("🚀 涨停板追踪")
    if st.button("刷新涨停板"):
        with st.spinner("加载中..."):
            from skills.04-stock-analysis.limit-up-tracker.limit_up_tracker import get_zt_pool
            df = get_zt_pool()
            if not df.empty:
                st.metric("涨停数", len(df))
                cols = [c for c in ["code", "name", "pct_change", "consecutive", "reason"] if c in df.columns]
                st.dataframe(df[cols].head(30), use_container_width=True)
            else:
                st.warning("今日无涨停数据")


def render_technical():
    """技术面分析"""
    st.header("📈 技术面分析")
    code = st.text_input("股票代码", value="000001", key="tech_code")
    if st.button("分析"):
        with st.spinner("分析中..."):
            from skills.04-stock-analysis.stock-technical-analysis.stock_technical_analysis import full_technical_analysis
            result = full_technical_analysis(code)
            if result:
                # K线图
                from skills.02-data-collection.stock-basic-info.stock_basic_info import get_realtime
                from skills.04-stock-analysis.stock-technical-analysis.stock_technical_analysis import get_kline
                df = get_kline(code, days=60)
                if not df.empty:
                    fig = go.Figure()
                    fig.add_trace(go.Candlestick(
                        x=df["date"] if "date" in df.columns else df.index,
                        open=df["open"], high=df["high"],
                        low=df["low"], close=df["close"],
                        name="K线"
                    ))
                    fig.update_layout(title=f"{code} K线图", xaxis_rangeslider_visible=False)
                    st.plotly_chart(fig, use_container_width=True)

                # 交易信号
                st.subheader("📊 交易信号")
                signal = result.get("trading_signal", {})
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("信号", signal.get("signal", "-"))
                with col2:
                    st.metric("强度", signal.get("strength", "-"))
                with col3:
                    st.metric("评分", signal.get("score", 0))

                # 趋势信号
                st.subheader("趋势信号")
                for s in result.get("trend", {}).get("signals", []):
                    st.write(f"- {s.get('name')}: {s.get('desc')}")


def render_daily_report():
    """每日复盘"""
    st.header("📝 每日复盘报告")
    if st.button("生成今日报告"):
        with st.spinner("生成中... (可能需要 10-30 秒)"):
            from skills.05-reports.daily-market-report.daily_market_report import generate_daily_report
            report = generate_daily_report()
            st.markdown(report)


def render_research_report():
    """个股研报"""
    st.header("🔬 个股深度研报")
    code = st.text_input("股票代码", value="000001", key="research_code")
    if st.button("生成研报"):
        with st.spinner("生成中..."):
            from skills.05-reports.stock-research-report.stock_research_report import generate_research
            report = generate_research(code)
            st.markdown(report)


def render_watchlist():
    """自选股监控"""
    st.header("🔔 自选股监控")
    codes_input = st.text_input("股票代码 (逗号分隔)", value="000001,600519,300750")
    if st.button("查询"):
        codes = [c.strip() for c in codes_input.split(",")]
        with st.spinner("查询中..."):
            from skills.02-data-collection.watchlist-monitor.watchlist_monitor import get_realtime_quotes
            quotes = get_realtime_quotes(codes)
            if quotes:
                # 转为 DataFrame
                rows = []
                for q in quotes:
                    rows.append({
                        "代码": q["code"],
                        "名称": q.get("name", ""),
                        "现价": q.get("price", 0),
                        "涨跌幅": f"{q.get('pct_change', 0):+.2f}%",
                        "换手率": f"{q.get('turnover', 0):.2f}%",
                    })
                df = pd.DataFrame(rows)
                st.dataframe(df, use_container_width=True)


def render_market():
    """大盘分析"""
    st.header("📊 大盘分析")
    if st.button("分析大盘"):
        with st.spinner("分析中..."):
            from skills.03-market-analysis.market-analysis.market_analysis import full_market_analysis
            result = full_market_analysis("000001", days=60)
            if result:
                st.subheader(f"上证指数分析")
                st.write(f"**建议**: {result.get('advice', '-')}")

                # 主要指数
                from skills.02-data-collection.market-data-collector.market_data_collector import get_major_indices
                df = get_major_indices()
                if not df.empty:
                    st.subheader("主要指数")
                    cols = [c for c in ["code", "name", "price", "pct_change"] if c in df.columns]
                    st.dataframe(df[cols], use_container_width=True)

                # 市场广度
                from skills.02-data-collection.market-data-collector.market_data_collector import get_market_breadth
                breadth = get_market_breadth()
                if breadth:
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("上涨", breadth.get("up", 0))
                    with col2:
                        st.metric("下跌", breadth.get("down", 0))
                    with col3:
                        st.metric("涨停", breadth.get("limit_up", 0))
                    with col4:
                        st.metric("跌停", breadth.get("limit_down", 0))


# ============================================================
# Skill 路由
# ============================================================
SKILL_RENDERERS = {
    "实时行情": render_realtime,
    "涨停板": render_zt_pool,
    "技术面": render_technical,
    "每日复盘": render_daily_report,
    "个股研报": render_research_report,
    "自选股监控": render_watchlist,
    "大盘分析": render_market,
}

if skill in SKILL_RENDERERS:
    SKILL_RENDERERS[skill]()
elif skill == "首页":
    pass
else:
    st.info(f"💡 **{skill}** Skill 的 Web UI 尚未实现")
    st.markdown(f"""
    ### 📖 使用方式

    **命令行**:
    ```bash
    python skills/XX/main.py
    ```

    **Claude Code**:
    > @Claude 使用 {skill} Skill

    **Python API**:
    ```python
    from skills.XX.main import func
    result = func()
    ```
    """)

# 页脚
st.sidebar.markdown("---")
st.sidebar.markdown("""
<div style="font-size: 0.8em; color: gray;">
A-Stock-Skills v1.0<br>
41 Skills | Claude Agent Native<br>
<a href="https://github.com/ZICXR/A-Stock-Skills">GitHub</a>
</div>
""", unsafe_allow_html=True)
