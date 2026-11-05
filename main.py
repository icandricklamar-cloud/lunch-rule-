import re
from collections import Counter
from itertools import combinations
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="급식 연관규칙 분석", layout="wide")

st.title("🍚 송탄고 급식 연관규칙(Apriori) 분석 앱")


# Data Loading & Preprocessing
@st.cache_data
def load_and_preprocess_data():
    url = "https://raw.githubusercontent.com/it-teacher-go/data-share-/main/songtan_meals_184.csv"
    df = pd.read_csv(url, encoding="utf-8")

    transactions = []
    all_items = set()

    for raw_menu in df["메뉴"].dropna():
        # 세로줄(|)로 분할
        items = raw_menu.split("|")
        cleaned_items = set()
        for item in items:
            # 괄호 및 괄호 내부 문자열 제거 후 앞뒤 공백 제거
            cleaned = re.sub(r"\(.*?\)", "", item).strip()
            if cleaned:
                cleaned_items.add(cleaned)
                all_items.add(cleaned)
        if cleaned_items:
            transactions.append(cleaned_items)

    return transactions, sorted(list(all_items))


transactions, all_items = load_and_preprocess_data()
total_days = len(transactions)


# Generate Association Rules
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
        # 지지도, 신뢰도, 향상도 계산
        supp_ab = count / total_days
        supp_a = item_counts[item_a] / total_days
        supp_b = item_counts[item_b] / total_days

        conf_a_to_b = count / item_counts[item_a]
        lift_a_to_b = conf_a_to_b / supp_b

        conf_b_to_a = count / item_counts[item_b]
        lift_b_to_a = conf_b_to_a / supp_a

        # A -> B
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

        # B -> A
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

# Sidebar Options
st.sidebar.header("설정 및 필터")

selected_menu = st.sidebar.selectbox(
    "메뉴 선택 (전체 보기 또는 특정 메뉴 선택)", options=["전체"] + all_items
)

sort_by = st.sidebar.radio(
    "정렬 기준 선택",
    options=["향상도", "신뢰도", "동시"],
