import re

def extract_product_name(original_name):
    # 괄호 안에 있는 정보를 제거하고, 대괄호로 감싸진 텍스트도 제거합니다.
    cleaned_name = re.sub(r"\[.*?\]|\(.*?\)", "", original_name)

    # 불필요한 공백 제거
    cleaned_name = cleaned_name.strip()

    return cleaned_name
