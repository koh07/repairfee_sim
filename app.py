import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import matplotlib.ticker as ticker
import matplotlib.ticker as mticker
import platform

# **診断ボタンの状態を管理**
if "run_simulation" not in st.session_state:
    st.session_state.run_simulation = False

# **フォントのパスを直接指定**
font_path = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"

# **matplotlib に適用**
font_prop = fm.FontProperties(fname=font_path)
plt.rcParams["font.family"] = font_prop.get_name()

# **現在の設定を確認**
print(f"✅ 設定されたフォント: {plt.rcParams['font.family']}")

# **タイトル**
st.markdown("## 中古マンションの財政状態を簡単診断！<br>修繕積立金シミュレーション", unsafe_allow_html=True)

# **ユーザー入力（基本情報）**
total_units = st.number_input("総戸数", min_value=1, value=39)
years_old = st.number_input("築年数", min_value=0, value=22)
current_balance = st.text_input("現在の修繕積立金残高（円）", value="46383000")
monthly_fee = st.text_input("1戸あたりの修繕積立金（月額）", value="19321")

# **バリデーションエラー管理**
validation_errors = []

# **金額入力のバリデーション**
def validate_number(value, field_name):
    try:
        return int(value.replace(",", ""))  # カンマを削除して整数変換
    except ValueError:
        validation_errors.append(f"❌ エラー: {field_name} に数値を入力してください。")
        return None

# **バリデーション実行**
current_balance = validate_number(current_balance, "現在の修繕積立金残高")
monthly_fee = validate_number(monthly_fee, "1戸あたりの修繕積立金（月額）")

# **バリデーションエラーがある場合、計算を中止**
if current_balance is None or monthly_fee is None:
    st.error("❌ 入力された金額が正しくありません。数値を入力してください。")
    st.stop()

# **築年数による年間設備修繕費の変動**
base_annual_equipment_repair_cost = total_units * 120000  # 1戸あたり12万円
if years_old <= 10:
    annual_equipment_repair_cost = base_annual_equipment_repair_cost * 0.8  # 80%に減少（築浅）
elif 11 <= years_old <= 20:
    annual_equipment_repair_cost = base_annual_equipment_repair_cost  # 100%（標準）
else:
    annual_equipment_repair_cost = base_annual_equipment_repair_cost * 1.2  # 120%（築古）

# **築30年以上なら特別修繕費（突発修繕リスク増）**
if years_old >= 30:
    annual_equipment_repair_cost += 2000000  # +200万円

st.info(f"💡 築年数に応じた年間設備修繕費: {annual_equipment_repair_cost:,.0f} 円")

# **大規模修繕の入力**
st.subheader("大規模修繕の年と費用")

# **セッションステートで修繕リストを管理**
if "repairs" not in st.session_state:
    st.session_state.repairs = []

# 「大規模修繕を追加」ボタンで新しい入力グループを追加
if st.button("大規模修繕を追加"):
    st.session_state.repairs.append({"year": 2028, "cost": "100000000"})  # 初期値を設定

# **入力グループの表示**
to_remove = None
for i, repair in enumerate(st.session_state.repairs):
    st.markdown(f"**大規模修繕 {i+1}**")

    col1, col2, col3 = st.columns([2, 2, 1])  # 年と費用の2フィールド＋削除ボタン
    with col1:
        repair["year"] = st.number_input(f"修繕年 {i+1}", min_value=2024, value=repair["year"], key=f"year_{i}")
    with col2:
        repair["cost"] = st.text_input(f"修繕費 {i+1}（円）", value=repair["cost"], key=f"cost_{i}")
    with col3:
        if st.button(f"削除", key=f"remove_{i}"):
            to_remove = i

# **入力グループを削除**
if to_remove is not None:
    st.session_state.repairs.pop(to_remove)

# **試算対象年を最後に移動**
st.subheader("いつ時点での残高を試算しますか？")
future_year = st.number_input("試算対象年（西暦）", min_value=2024, value=2040)

# **診断ボタン**
if st.button("診断を実行"):
    st.session_state.run_simulation = True

if st.session_state.run_simulation:
    # **積立金のシミュレーション**
    annual_contribution = total_units * monthly_fee * 12
    balance = current_balance
    insufficient_year = None

    # **グラフ用データ**
    years = []
    balances = []
    increased_balances = None

    for year in range(2024, future_year + 1):
        years.append(year)
        balances.append(balance)
        
        balance += annual_contribution
        balance -= annual_equipment_repair_cost  

        # **大規模修繕の費用を差し引く**
        for repair in st.session_state.repairs:
            if repair["year"] == year:
                repair_cost = validate_number(repair["cost"], f"{repair['year']}年の修繕費")
                if repair_cost is not None:
                    balance -= repair_cost

        if balance < 0 and insufficient_year is None:
            insufficient_year = year

    # **シミュレーション結果の表示**
    st.subheader("診断結果")
    st.write(f"【{future_year}年時点の積立残高】 {balance:,.0f} 円")

    if balance >= 0:
        st.success(f"{future_year}年時点で残高はプラスです。")
    else:
        st.error(f"{future_year}年時点で不足が発生します。")
        if insufficient_year:
            st.warning(f"⚠️ {insufficient_year}年で赤字になります。")

        # **不足分の積立増額計算**
        missing_amount = abs(balance)
        remaining_years = future_year - 2024
        required_increase = missing_amount / (remaining_years * 12 * total_units)
        st.warning(f"💰 毎月の積立金を **{required_increase:,.0f} 円** 増額すると不足を回避できます。")
        
        # **増額後のシミュレーション**
        increased_balance = current_balance
        increased_balances = []

        for year in years:
            increased_balances.append(increased_balance)
            increased_balance += (annual_contribution + (required_increase * total_units * 12))
            increased_balance -= annual_equipment_repair_cost
            # **大規模修繕の費用を差し引く**
            for repair in st.session_state.repairs:
                if repair["year"] == year:
                    repair_cost = validate_number(repair["cost"], f"{repair['year']}年の修繕費")
                    if repair_cost is not None:
                        increased_balance -= repair_cost

    # **グラフの作成**
    fig, ax = plt.subplots()
    ax.plot(years, balances, marker="o", linestyle="-", color="b", label="積立金残高")

    # **残高不足時のみ増額後の積立金をプロット**
    if increased_balances:
        ax.plot(years, increased_balances, marker="o", linestyle="--", color="orange", label="増額後の積立金残高")

    ax.set_title("積立金の推移シミュレーション")
    ax.legend()
    ax.grid()

    # **X軸のラベルを整数（西暦）にする**
    ax.set_xlabel("年")
    ax.xaxis.set_major_locator(mticker.MaxNLocator(integer=True))
    
    # **Y軸の単位を「円」にする**
    ax.set_ylabel("積立金残高（円）")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, pos: f"{int(x):,} 円"))

    # **Streamlit にグラフを表示**
    st.pyplot(fig)
