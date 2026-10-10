import streamlit as st
import numpy as np

# ---------------------------------------------------------
# 1. 頁面基本設定 (Page Configuration)
# ---------------------------------------------------------
st.set_page_config(
    page_title="IE QC Simulation | 工工系品管抽樣與監控模擬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------------------------------------
# 2. 標題與簡介 (Header & Introduction)
# ---------------------------------------------------------
st.title("工工系品管課程｜抽樣與製程穩定性模擬")
st.subheader("IE Quality Control Course | Sampling & Process Stability Simulation")
st.markdown(
    """
    - **Phase 1**: 練習常態抽樣與檢驗成本計算 (Practice normal distribution sampling & baseline inspection cost)
    - **Phase 2**: 線上動態監控與異常決策 (Online dynamic monitoring & out-of-control decision making)
    """
)

# ---------------------------------------------------------
# 3. 輔助常數與函式 (Helper Constants & Functions)
# ---------------------------------------------------------
MU_NORMAL = 50.0
SIGMA_NORMAL = 1.5
MU_SHIFT = 53.0  # +2.0 sigma shift (50 + 2 * 1.5 = 53.0)
UNIT_INSPECTION_COST = 10.0
COST_TYPE_1 = 1000.0  # 假警報成本 (False alarm cost)
COST_TYPE_2 = 10000.0 # 漏判成本 (Escape cost per unnotified unstable step)

# 生成 08:00 至 17:00 (每 10 分鐘一步，共 55 個時間點：08:00 到 17:00 包含首尾)
TIME_SLOTS = []
for h in range(8, 18):
    for m in range(0, 60, 10):
        TIME_SLOTS.append(f"{h:02d}:{m:02d}")
        if h == 17 and m == 0:
            break
TOTAL_STEPS = len(TIME_SLOTS)  # 55 個時間步 (08:00 為第 0 步，17:00 為最後一步)

def initialize_phase2_state(n_val=5):
    """初始化或重置 Phase 2 模擬狀態 (Initialize or Reset Phase 2 State)"""
    st.session_state.p2_step = 0
    st.session_state.p2_n = n_val
    st.session_state.p2_history = []
    st.session_state.p2_cost_inspection = 0.0
    st.session_state.p2_type1_count = 0
    st.session_state.p2_type1_cost = 0.0
    st.session_state.p2_type2_count = 0
    st.session_state.p2_type2_cost = 0.0
    st.session_state.p2_feedback_msg = None
    st.session_state.p2_feedback_type = "info"
    st.session_state.p2_reported_this_step = False

    # 抽取 08:30 到 16:30 之間 3 個互不連續的異常時段 (indices)
    # 08:30 對應 index 3；16:30 對應 index 51
    eligible_indices = list(range(3, 52))
    chosen_indices = []
    # 隨機抽取互不相鄰的 3 個點
    while len(chosen_indices) < 3:
        cand = int(np.random.choice(eligible_indices))
        # 檢查是否與已選取的點相鄰或重複
        if all(abs(cand - c) > 1 for c in chosen_indices):
            chosen_indices.append(cand)
    chosen_indices.sort()
    st.session_state.p2_true_unstable_steps = chosen_indices
    # 追蹤每個時段是否仍處於異常狀態（回報成功後該點會恢復為穩定）
    st.session_state.p2_current_unstable_active = {step: True for step in chosen_indices}

# ---------------------------------------------------------
# 4. Session State 全局初始化 (Global Session State Init)
# ---------------------------------------------------------
if "p1_cost" not in st.session_state:
    st.session_state.p1_cost = 0.0
if "p1_data" not in st.session_state:
    st.session_state.p1_data = None
if "p1_n" not in st.session_state:
    st.session_state.p1_n = 5
if "p1_m" not in st.session_state:
    st.session_state.p1_m = 20

if "p2_step" not in st.session_state:
    initialize_phase2_state(st.session_state.p1_n)

# ---------------------------------------------------------
# 5. 介面分頁 (Interface Tabs)
# ---------------------------------------------------------
tab1, tab2 = st.tabs([
    "分頁 1: Phase 1 | 基準界限抽樣 (Phase 1 | Baseline Limit Sampling)",
    "分頁 2: Phase 2 | 線上動態監控 (Phase 2 | Online Dynamic Monitoring)"
])

# =========================================================
# 分頁 1: Phase 1 基準界限抽樣
# =========================================================
with tab1:
    st.markdown("### 階段一：建立基準管制界限 (Phase 1: Establishing Baseline Control Limits)")
    st.info(
        "**母體設定 (Population Parameters):** 常態分配 Normal Distribution $N(\\mu=50.0, \\sigma=1.5)$，"
        "檢驗成本 Inspection Cost: $10 / 件 (unit)。"
    )

    col1, col2 = st.columns(2)
    with col1:
        p1_n_input = st.slider(
            "每組樣本數 n (Subgroup Size n):",
            min_value=1,
            max_value=20,
            value=st.session_state.p1_n,
            step=1,
            help="每組抽取的件數 / Number of inspected parts per subgroup."
        )
    with col2:
        p1_m_input = st.slider(
            "樣本組數 m (Number of Subgroups m):",
            min_value=1,
            max_value=30,
            value=st.session_state.p1_m,
            step=1,
            help="抽樣的總組數 / Total number of subgroups to sample."
        )

    if st.button("開始抽樣 (Start Sampling)", type="primary"):
        st.session_state.p1_n = p1_n_input
        st.session_state.p1_m = p1_m_input
        
        # 產生 m 組常態分佈樣本，每組 n 個數據
        raw_samples = np.random.normal(loc=MU_NORMAL, scale=SIGMA_NORMAL, size=(p1_m_input, p1_n_input))
        raw_samples = np.round(raw_samples, 3)

        # 組成字典方便轉為 DataFrame 呈現
        table_dict = {"Subgroup": [f"Group_{i+1}" for i in range(p1_m_input)]}
        for j in range(p1_n_input):
            table_dict[f"X{j+1}"] = raw_samples[:, j].tolist()

        st.session_state.p1_data = table_dict
        st.session_state.p1_cost = float(p1_n_input * p1_m_input * UNIT_INSPECTION_COST)

    # 顯示抽樣結果與成本
    if st.session_state.p1_data is not None:
        metric_col1, metric_col2 = st.columns([1, 2])
        with metric_col1:
            st.metric(
                label="Phase 1 總檢驗成本 (Phase 1 Total Inspection Cost)",
                value=f"${st.session_state.p1_cost:,.0f}",
                delta=f"{st.session_state.p1_n * st.session_state.p1_m} 件總抽樣數 (Total Units)"
            )
        with metric_col2:
            st.markdown(
                """
                **提示 (Tips):** 您可以將下方表格數據複製並貼入 **Minitab** 或 **Excel** 
                進行常態性檢定與試算 $\\bar{X}-R$ 或 $\\bar{X}-s$ 基準管制界限。
                """
            )

        st.dataframe(
            st.session_state.p1_data,
            use_container_width=True,
            hide_index=True
        )

# =========================================================
# 分頁 2: Phase 2 線上動態監控
# =========================================================
with tab2:
    st.markdown("### 階段二：線上即時監控與決策 (Phase 2: Online Monitoring & Decision Making)")
    st.caption(
        "產線排程為 08:00 至 17:00，每 10 分鐘抽樣一次。請利用 Phase 1 建立之管制原則判斷製程是否失控。"
    )

    # 頂部控制列
    ctrl_col1, ctrl_col2, ctrl_col3 = st.columns([2, 1, 1])
    with ctrl_col1:
        p2_n_select = st.number_input(
            "Phase 2 抽樣樣本數 n (Phase 2 Subgroup Size n):",
            min_value=1,
            max_value=20,
            value=st.session_state.p1_n,
            step=1,
            help="預設承接 Phase 1 之設定值，亦可手動微調。"
        )
    with ctrl_col2:
        st.write("")
        st.write("")
        if st.button("重置模擬 (Reset Simulation)", type="secondary"):
            initialize_phase2_state(p2_n_select)
            st.rerun()

    # 當前狀態檢視
    current_idx = st.session_state.p2_step
    is_completed = (current_idx >= TOTAL_STEPS - 1)
    current_time_str = TIME_SLOTS[min(current_idx, TOTAL_STEPS - 1)]

    # 成本總覽看板 (Cost Dashboard)
    total_cost = (
        st.session_state.p1_cost
        + st.session_state.p2_cost_inspection
        + st.session_state.p2_type1_cost
        + st.session_state.p2_type2_cost
    )

    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
    kpi1.metric("當前時間 (Current Time)", current_time_str)
    kpi2.metric("Phase 1 成本 (P1 Cost)", f"${st.session_state.p1_cost:,.0f}")
    kpi3.metric("Phase 2 抽樣成本 (Sampling Cost)", f"${st.session_state.p2_cost_inspection:,.0f}")
    kpi4.metric(
        "型一假警報成本 (Type I Cost)",
        f"${st.session_state.p2_type1_cost:,.0f}",
        f"{st.session_state.p2_type1_count} 次 (Times)"
    )
    kpi5.metric(
        "型二漏判成本 (Type II Cost)",
        f"${st.session_state.p2_type2_cost:,.0f}",
        f"{st.session_state.p2_type2_count} 次 (Times)"
    )

    st.markdown(f"#### 累計總營運成本 (Cumulative Total Cost): **${total_cost:,.0f}**")

    # 操作按鈕區
    btn_col1, btn_col2 = st.columns(2)

    with btn_col1:
        step_btn = st.button(
            "抽取下一時段樣本 (Next Time Step)",
            type="primary",
            use_container_width=True,
            disabled=is_completed
        )

    with btn_col2:
        report_btn = st.button(
            "回報製程異常！(I Think the Process is Unstable!)",
            type="secondary",
            use_container_width=True,
            disabled=is_completed or (len(st.session_state.p2_history) == 0)
        )

    # 邏輯 1：抽取下一時段樣本
    if step_btn and not is_completed:
        # 1. 推進時間步
        st.session_state.p2_step += 1
        new_step = st.session_state.p2_step
        new_time = TIME_SLOTS[new_step]

        # 2. 判斷前一步長是否有漏判的異常（如果前一步是異常且未被通報修復）
        prev_step = new_step - 1
        if prev_step in st.session_state.p2_true_unstable_steps:
            if st.session_state.p2_current_unstable_active.get(prev_step, False):
                # 未通報 -> 發生型二誤差 (Type II Error)
                st.session_state.p2_type2_count += 1
                st.session_state.p2_type2_cost += COST_TYPE_2

        # 3. 判斷新時間步是否為異常時段，並生成對應樣本
        is_unstable_now = (new_step in st.session_state.p2_true_unstable_steps)
        if is_unstable_now and st.session_state.p2_current_unstable_active.get(new_step, False):
            # 引入 +2.0 sigma 偏移 (mu=53.0)
            sample_data = np.random.normal(loc=MU_SHIFT, scale=SIGMA_NORMAL, size=st.session_state.p2_n)
        else:
            # 正常時段 (mu=50.0, sigma=1.5)
            sample_data = np.random.normal(loc=MU_NORMAL, scale=SIGMA_NORMAL, size=st.session_state.p2_n)

        sample_data = np.round(sample_data, 3)

        # 4. 累計抽樣成本
        st.session_state.p2_cost_inspection += float(st.session_state.p2_n * UNIT_INSPECTION_COST)

        # 5. 紀錄至歷史列表
        history_record = {
            "Step": new_step,
            "Time": new_time,
            "Subgroup Mean (X-bar)": round(float(np.mean(sample_data)), 3),
            "Subgroup Std (s)": round(float(np.std(sample_data, ddof=1)) if st.session_state.p2_n > 1 else 0.0, 3)
        }
        for idx_val, val in enumerate(sample_data):
            history_record[f"X{idx_val+1}"] = val

        st.session_state.p2_history.append(history_record)
        st.session_state.p2_reported_this_step = False
        st.session_state.p2_feedback_msg = None
        st.rerun()

    # 邏輯 2：回報異常
    if report_btn:
        curr_step = st.session_state.p2_step
        # 檢查當前是否處於真實異常時段，且尚未修復
        if (curr_step in st.session_state.p2_true_unstable_steps) and st.session_state.p2_current_unstable_active.get(curr_step, False):
            # 判定成功：即時排除異常
            st.session_state.p2_current_unstable_active[curr_step] = False
            st.session_state.p2_feedback_msg = "正確！製程已成功排除異常並恢復穩定 (Correct! Process adjusted back to in-control.)"
            st.session_state.p2_feedback_type = "success"
        else:
            # 誤判：型一誤差 (Type I Error)
            st.session_state.p2_type1_count += 1
            st.session_state.p2_type1_cost += COST_TYPE_1
            st.session_state.p2_feedback_msg = "誤判！此為型一誤差/假警報，增加 $1,000 成本 (Wrong! Type I Error / False Alarm cost added: +$1,000.)"
            st.session_state.p2_feedback_type = "error"
        st.rerun()

    # 顯示回報訊息回饋
    if st.session_state.p2_feedback_msg:
        if st.session_state.p2_feedback_type == "success":
            st.success(st.session_state.p2_feedback_msg)
        else:
            st.error(st.session_state.p2_feedback_msg)

    # 歷史抽樣監控數據表
    if len(st.session_state.p2_history) > 0:
        st.markdown("##### 即時抽樣數據流水帳 (Real-Time Inspection Log):")
        # 建立倒序檢視（最新抽樣排在最上方方便學生查閱）
        reversed_history = list(reversed(st.session_state.p2_history))
        st.dataframe(reversed_history, use_container_width=True)

    # 結束時段揭示與結算 (Session Debriefing)
    if is_completed:
        st.warning("全天監控時程已結束 (17:00 Reached. Daily dynamic monitoring completed.)")
        st.markdown("### 真實異常時段揭示 (Actual Unstable Time Periods Reveal)")
        actual_unstable_times = [TIME_SLOTS[idx] for idx in st.session_state.p2_true_unstable_steps]
        
        st.write(
            f"- **當日真實異常時段 (True Disturbance Times):** `{'`, `'.join(actual_unstable_times)}`"
        )
        st.markdown(
            """
            > **課後檢討作業 (Debriefing Assignment):**  
            > 請將歷史抽樣數據匯出至 Minitab，檢驗西電法則（WECO Rules / Run Rules）在哪些時段出現警訊，並比較您的決策時機點與成本損耗。
            """
        )
