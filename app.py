import streamlit as st
import pandas as pd
from datetime import datetime
import io

# ============================================================================
# 页面配置
# ============================================================================
st.set_page_config(
    page_title="大学生绩点管理与目标规划",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("📚 大学生绩点管理与目标规划")
st.markdown("---")

# ============================================================================
# 初始化会话状态
# ============================================================================
if 'courses' not in st.session_state:
    st.session_state.courses = pd.DataFrame({
        '课程名称': ['示例课程'],
        '学分': [3.0],
        '成绩': [85.0]
    })

if 'target_gpa' not in st.session_state:
    st.session_state.target_gpa = 85.0

# ============================================================================
# 辅助函数：计算加权平均分
# ============================================================================
def calculate_weighted_average(df):
    """
    计算课程的加权平均分
    公式：(∑ 成绩 × 学分) / (∑ 学分)
    
    参数：
        df (DataFrame): 包含 '成绩' 和 '学分' 列的数据框
    
    返回：
        float: 加权平均分，若无课程返回 0
    """
    if df.empty or df['学分'].sum() == 0:
        return 0.0
    
    # 过滤有效数据（成绩和学分都不为空）
    valid_df = df.dropna(subset=['成绩', '学分'])
    if valid_df.empty:
        return 0.0
    
    weighted_sum = (valid_df['成绩'] * valid_df['学分']).sum()
    total_credits = valid_df['学分'].sum()
    
    return round(weighted_sum / total_credits, 1)

# ============================================================================
# 辅助函数：根据目标倒推所需平均分
# ============================================================================
def calculate_required_average(current_gpa, completed_credits, remaining_credits, target_gpa):
    """
    根据目标分数反向计算剩余学分所需的平均分
    
    参数：
        current_gpa (float): 当前加权平均分（已完成课程）
        completed_credits (float): 已完成课程的总学分
        remaining_credits (float): 剩余课程的总学分
        target_gpa (float): 目标加权平均分
    
    返回：
        dict: 包含计算结果的字典
    """
    total_credits = completed_credits + remaining_credits
    
    if total_credits == 0:
        return {
            'feasible': False,
            'message': '❌ 总学分为 0，无法计算',
            'required_avg': 0
        }
    
    # 当前已获得的总分数
    current_points = current_gpa * completed_credits
    
    # 目标所需的总分数
    required_points = target_gpa * total_credits
    
    # 剩余需要的分数
    needed_points = required_points - current_points
    
    # 若剩余学分为 0，无法进一步提升
    if remaining_credits == 0:
        if current_gpa >= target_gpa:
            return {
                'feasible': True,
                'message': f'✅ 已达成目标！当前绩点：{current_gpa:.1f}',
                'required_avg': current_gpa
            }
        else:
            return {
                'feasible': False,
                'message': f'❌ 无剩余课程，无法达成目标（当前：{current_gpa:.1f} < 目标：{target_gpa:.1f}）',
                'required_avg': 0
            }
    
    # 计算剩余课程所需的平均分
    required_avg = needed_points / remaining_credits
    required_avg = round(required_avg, 1)
    
    # 判断是否可行（剩余平均分不超过 100）
    feasible = required_avg <= 100
    
    if feasible:
        if required_avg < 0:
            message = f'✅ 无需努力！当前成绩已足以达成目标'
            required_avg = 0
        else:
            message = f'✅ 可行！剩余课程需要平均 {required_avg:.1f} 分'
    else:
        message = f'❌ 目标不可达！需要 {required_avg:.1f} 分（超过 100 分上限）'
    
    return {
        'feasible': feasible,
        'message': message,
        'required_avg': max(0, required_avg)
    }

# ============================================================================
# 主界面布局
# ============================================================================
col1, col2 = st.columns([3, 1])

with col1:
    st.subheader("📋 课程成绩表")
    st.markdown("**说明**：可直接在表格中编辑课程信息。支持自动添加和删除行。")
    
    # 使用 data_editor 实现动态编辑表格
    edited_df = st.data_editor(
        st.session_state.courses,
        num_rows='dynamic',
        column_config={
            '课程名称': st.column_config.TextColumn(
                '课程名称',
                help='输入课程名称',
                width='medium'
            ),
            '学分': st.column_config.NumberColumn(
                '学分',
                help='输入课程学分（正数）',
                step=0.5,
                min_value=0,
                width='small'
            ),
            '成绩': st.column_config.NumberColumn(
                '成绩',
                help='输入课程成绩（0-100）',
                step=1,
                min_value=0,
                max_value=100,
                width='small'
            )
        },
        use_container_width=True,
        height=300
    )
    
    # 更新会话状态
    st.session_state.courses = edited_df

with col2:
    st.subheader("📊 当前绩点")
    current_gpa = calculate_weighted_average(st.session_state.courses)
    
    # 使用 metric 突出显示绩点
    st.metric(
        label='加权平均分',
        value=f'{current_gpa:.1f}',
        delta=None
    )
    
    # 显示统计信息
    completed_credits = st.session_state.courses['学分'].sum()
    course_count = len(st.session_state.courses.dropna(subset=['成绩', '学分']))
    
    st.markdown(f"""
    ---
    **📈 统计信息**
    - 已添加课程数：{course_count} 门
    - 总学分：{completed_credits:.1f}
    """)

st.markdown("---")

# ============================================================================
# 目标倒推功能
# ============================================================================
st.subheader("🎯 目标倒推规划")
st.markdown("**说明**：设定目标绩点，计算剩余课程所需的平均分。")

col1, col2, col3 = st.columns([1.5, 1.5, 1])

with col1:
    target_gpa = st.number_input(
        '目标绩点',
        min_value=0.0,
        max_value=100.0,
        value=st.session_state.target_gpa,
        step=0.1,
        help='设定你想要达成的目标绩点（0-100）'
    )
    st.session_state.target_gpa = target_gpa

with col2:
    remaining_credits = st.number_input(
        '剩余学分',
        min_value=0.0,
        value=0.0,
        step=0.5,
        help='输入还需要修读的课程总学分'
    )

with col3:
    st.write('')  # 占位符用于对齐按钮
    if st.button('📊 计算所需分数', use_container_width=True):
        current_gpa = calculate_weighted_average(st.session_state.courses)
        completed_credits = st.session_state.courses['学分'].sum()
        
        result = calculate_required_average(
            current_gpa=current_gpa,
            completed_credits=completed_credits,
            remaining_credits=remaining_credits,
            target_gpa=target_gpa
        )
        
        # 显示计算结果
        st.markdown("---")
        st.markdown(f"#### {result['message']}")
        
        if remaining_credits > 0:
            st.markdown(f"""
            **计算详情**：
            - 当前绩点：{current_gpa:.1f}（已修 {completed_credits:.1f} 学分）
            - 目标绩点：{target_gpa:.1f}
            - 剩余学分：{remaining_credits:.1f}
            - 所需平均分：{result['required_avg']:.1f}
            """)

st.markdown("---")

# ============================================================================
# 数据导入导出功能
# ============================================================================
st.subheader("💾 数据管理")

col1, col2 = st.columns(2)

with col1:
    st.markdown("**📥 导出数据**")
    
    # 生成 CSV 文件
    csv = st.session_state.courses.to_csv(index=False).encode('utf-8-sig')
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    st.download_button(
        label='📥 下载为 CSV',
        data=csv,
        file_name=f'绩点管理_{timestamp}.csv',
        mime='text/csv',
        help='将课程成绩数据下载为 CSV 文件'
    )

with col2:
    st.markdown("**📤 导入数据**")
    
    uploaded_file = st.file_uploader(
        '选择 CSV 文件',
        type='csv',
        help='导入之前保存的 CSV 文件'
    )
    
    if uploaded_file is not None:
        try:
            imported_df = pd.read_csv(uploaded_file)
            
            # 验证导入的 DataFrame 有正确的列
            required_cols = {'课程名称', '学分', '成绩'}
            if set(imported_df.columns) == required_cols:
                st.session_state.courses = imported_df
                st.success('✅ 数据导入成功！')
            else:
                st.error(f'❌ CSV 文件格式不正确。应包含列：{required_cols}')
        except Exception as e:
            st.error(f'❌ 导入失败：{str(e)}')

st.markdown("---")

# ============================================================================
# 说明和使用指南
# ============================================================================
with st.expander("❓ 使用说明和常见问题"):
    st.markdown("""
    ### 📖 功能说明
    
    **1. 课程成绩表**
    - 在表格中输入课程名称、学分和成绩
    - 支持动态添加和删除行
    - 表格下方点击 `+` 可添加新行，行末的 `×` 可删除该行
    
    **2. 当前绩点**
    - 实时显示加权平均分
    - 计算公式：(∑ 成绩 × 学分) / (∑ 学分)
    - 包含课程统计信息
    
    **3. 目标倒推规划**
    - 设定目标绩点后，输入剩余学分
    - 点击"计算所需分数"按钮，得出剩余课程的所需平均分
    - 若所需分数超过 100，表示目标不可达
    
    **4. 数据管理**
    - 支持导出为 CSV 文件备份
    - 支持导入之前保存的 CSV 文件恢复数据
    
    ### ❓ 常见问题
    
    **Q: 新增课程后绩点没有更新？**
    A: 绩点会自动计算。确保课程的"成绩"和"学分"字段都已填写。
    
    **Q: 如何快速添加多个课程？**
    A: 在表格下方点击 `+` 快速添加新行。也可以使用CSV导入功能批量导入。
    
    **Q: 目标倒推计算出的分数超过 100 是什么意思？**
    A: 表示当前成绩太低，即使剩余课程全部 100 分也无法达成目标。
    
    **Q: 数据会被保存吗？**
    A: 数据保存在浏览器会话中。刷新页面时会重置。可使用 CSV 导出功能保存数据。
    """)

st.markdown("---")

# ============================================================================
# 页脚
# ============================================================================
st.markdown("""
<div style='text-align: center; color: gray; font-size: 0.8em;'>
由 Streamlit 驱动 | 大学生绩点管理系统 v1.0
</div>
""", unsafe_allow_html=True)
