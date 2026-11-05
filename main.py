import re
from collections import Counter
from itertools import combinations
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="급식 연관규칙 분석", layout="wide")

st.title("🍚 송탄고 급식 연관규칙(Apriori) 분석 앱")


# 데이터 로드 및 전처리
@st.cache_data
def load_and_preprocess_data():
    url = "https://raw.githubusercontent.com/it-teacher-go/data-share-/main/songtan_meals_184.csv"
    df = pd.read_csv(url, encoding="utf-8")

    transactions = []
    all_items = set()

    for raw_menu in df["메뉴"].dropna():
        items = raw_menu.split("|")
        cleaned_items = set()
        for item in items:
            cleaned = re.sub(r"\(.*?\)", "", item).strip()
            if cleaned:
                cleaned_items.add(cleaned)
                all_items.add(cleaned)
        if cleaned_items:
            transactions.append(cleaned_items)

    return transactions, sorted(list(all_items))


transactions, all_items = load_and_preprocess_data()
total_days = len(transactions)


# 연관규칙 생성
@st.cache_data
def generate_association_rules(transactions, total_days):
    pair_counts = Counter()
    item_counts = Counter()

    for itemset in transactions:
        for item in itemset:
            item_counts[item] += 1
        for pair in combinations(sorted(itemset), 2):
            pair_counts[pair] += 1

    rules = []
    for (item_a, item_b), count in pair_counts.items():
        supp_ab = count / total_days
        supp_a = item_counts[item_a] / total_days
        supp_b = item_counts[item_b] / total_days

        conf_a_to_b = count / item_counts[item_a]
        lift_a_to_b = conf_a_to_b / supp_b

        conf_b_to_a = count / item_counts[item_b]
        lift_b_to_a = conf_b_to_a / supp_a

        rules.append(
            {
                "조건": item_a,
                "결과": item_b,
                "동시": count,
                "지지도": supp_ab,
                "신뢰도": conf_a_to_b,
                "향상도": lift_a_to_b,
            }
        )

        rules.append(
            {
                "조건": item_b,
                "결과": item_a,
                "동시": count,
                "지지도": supp_ab,
                "신뢰도": conf_b_to_a,
                "향상도": lift_b_to_a,
            }
        )

    rules_df = pd.DataFrame(rules)
    unique_pairs_count = len(pair_counts)
    return rules_df, unique_pairs_count


rules_df, unique_pairs_count = generate_association_rules(
    transactions, total_days
)

# 사이드바 설정 및 필터
st.sidebar.header("설정 및 필터")

selected_menu = st.sidebar.selectbox(
    "메뉴 선택 (전체 보기 또는 특정 메뉴 선택)", options=["전체"] + all_items
)

sort_by = st.sidebar.radio(
    "정렬 기준 선택",
    options=["향상도", "신뢰도", "동시"],
    format_func=lambda x: f"{x} 순",
)

# 요약 정보 표시
total_menu_types = len(all_items)
st.markdown(
    f"**급식 일수:** {total_days}일 | **메뉴 종류 수:** {total_menu_types}개 | **함께 나온 적이 있는 메뉴 쌍의 수:** {unique_pairs_count}쌍"
)

# 규칙 필터링
if selected_menu != "전체":
    filtered_df = rules_df[
        (rules_df["조건"] == selected_menu)
        | (rules_df["결과"] == selected_menu)
    ].copy()
else:
    filtered_df = rules_df.copy()

# 정렬
filtered_df = filtered_df.sort_values(by=sort_by, ascending=False).reset_index(
    drop=True
)

# Plotly 가로 막대그래프 (상위 10개)
st.subheader("📊 향상도 상위 10개 규칙")
if not filtered_df.empty:
    top10_df = filtered_df.sort_values(by="향상도", ascending=False).head(10)
    top10_df["규칙"] = top10_df["조건"] + " ➔ " + top10_df["결과"]

    fig = px.bar(
        top10_df.sort_values(by="향상도", ascending=True),
        x="향상도",
        y="규칙",
        orientation="h",
        text=top10_df.sort_values(by="향상도", ascending=True)[
            "향상도"
        ].round(2),
        labels={"향상도": "향상도 (Lift)", "규칙": "메뉴 규칙 (조건 ➔ 결과)"},
        color="향상도",
        color_continuous_scale="Blues",
    )
    fig.update_layout(height=400, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("해당 메뉴가 포함된 규칙이 없습니다.")

# 데이터 표 출력
st.subheader("📋 메뉴 연관규칙 목록")
st.dataframe(
    filtered_df.style.format(
        {"지지도": "{:.4f}", "신뢰도": "{:.4f}", "향상도": "{:.4f}"}
    ),
    use_container_width=True,
)
