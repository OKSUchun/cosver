import pandas as pd
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import AgglomerativeClustering


# ---------------------------
# 1) Light Normalization Rule
# ---------------------------
def normalize(s):
    if pd.isna(s):
        return ""

    # 괄호 제거
    s = re.sub(r"\(.*?\)|\[.*?\]|\{.*?\}", " ", s)

    # 이모지 및 특수문자 제거
    s = re.sub(r"[^0-9a-zA-Z가-힣\s]", " ", s)

    # 숫자 + 단위 붙이기 (15 g → 15g)
    s = re.sub(r"(\d+)\s*(g|ml|ML|G)", lambda m: m.group(1) + m.group(2).lower(), s)

    # 중복 공백 제거
    s = re.sub(r"\s+", " ", s)

    return s.strip().lower()


# ---------------------------
# 2) 데이터 로드 & Normalize
# ---------------------------
df = pd.read_csv("/mnt/data/scraper_data.csv")

df["normalized"] = df["name"].apply(normalize)


# ---------------------------
# 3) TF-IDF 벡터화
# ---------------------------
vectorizer = TfidfVectorizer()
X = vectorizer.fit_transform(df["normalized"])


# ---------------------------
# 4) Agglomerative Clustering
# ---------------------------
clustering = AgglomerativeClustering(
    n_clusters=None,
    distance_threshold=0.6,  # ← threshold 조정 가능
    affinity="euclidean",
    linkage="ward",
)

labels = clustering.fit_predict(X.toarray())
df["cluster"] = labels


# ---------------------------
# 5) 결과 출력
# ---------------------------
df[["name", "normalized", "cluster"]].head(50)
