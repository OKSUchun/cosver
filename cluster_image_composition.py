"""
비슷한 구도의 사진을 클러스터링하는 스크립트

이미지의 구도(composition)를 분석하여 유사한 구도의 이미지들을 그룹화합니다.
구도 특징: 엣지 분포, 공간적 레이아웃, 색상 분포, OCR 텍스트 등을 고려합니다.
"""
import shutil
import re
from pathlib import Path
import numpy as np
from PIL import Image
import cv2
from sklearn.cluster import DBSCAN, KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
from collections import defaultdict

# 평가 모듈 import (선택적)
try:
    from tests.evaluate_clustering import (
        convert_cluster_result_to_list,
        evaluate_clustering,
        print_evaluation_report,
        generate_ground_truth_template,
    )
    EVALUATION_AVAILABLE = True
except ImportError:
    EVALUATION_AVAILABLE = False
    print("⚠️  평가 모듈을 찾을 수 없습니다. 평가 기능을 사용하려면 tests/evaluate_clustering.py가 필요합니다.")

# OCR 라이브러리 import (선택적)
try:
    import easyocr
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    print("⚠️  easyocr이 설치되지 않았습니다. OCR 기능을 사용하려면 'pip install easyocr'을 실행하세요.")

# 이미지 해시 라이브러리 import (선택적)
try:
    import imagehash
    IMAGEHASH_AVAILABLE = True
except ImportError:
    IMAGEHASH_AVAILABLE = False
    print("⚠️  imagehash가 설치되지 않았습니다. 이미지 해시 기능을 사용하려면 'pip install imagehash'을 실행하세요.")


def load_image(image_path: Path) -> np.ndarray:
    """이미지를 로드하고 numpy 배열로 변환"""
    try:
        img = Image.open(image_path)
        # RGB로 변환 (RGBA나 다른 형식 처리)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        return np.array(img)
    except Exception as e:
        print(f"⚠️  이미지 로드 실패 {image_path.name}: {e}")
        return None


def preprocess_image_for_ocr(image: np.ndarray) -> np.ndarray:
    """OCR 정확도를 높이기 위한 이미지 전처리"""
    # 그레이스케일 변환
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    else:
        gray = image
    
    # 이미지 크기 조정 (너무 작으면 확대)
    h, w = gray.shape
    if h < 300 or w < 300:
        scale = max(300 / h, 300 / w)
        new_h, new_w = int(h * scale), int(w * scale)
        gray = cv2.resize(gray, (new_w, new_h), interpolation=cv2.INTER_CUBIC)
    
    # 대비 향상 (CLAHE)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    gray = clahe.apply(gray)
    
    # 가우시안 블러로 노이즈 제거
    gray = cv2.GaussianBlur(gray, (3, 3), 0)
    
    # 이진화 (Otsu's method)
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    return binary


def correct_ocr_typos(text: str) -> str:
    """OCR 오타를 보정합니다 (예: "3oml" -> "30ml", "5oml" -> "50ml")"""
    # 일반적인 OCR 오타 패턴 보정
    corrections = {
        r'(\d+)o\s*ml': r'\g<1>0ml',  # "3oml" -> "30ml", "5oml" -> "50ml"
        r'(\d+)o\s*ML': r'\g<1>0ml',
        r'(\d+)O\s*ml': r'\g<1>0ml',
        r'(\d+)O\s*ML': r'\g<1>0ml',
    }
    
    corrected_text = text
    for pattern, replacement in corrections.items():
        corrected_text = re.sub(pattern, replacement, corrected_text, flags=re.IGNORECASE)
    
    return corrected_text


def extract_text_from_image(image: np.ndarray, reader=None) -> dict:
    """
    이미지에서 OCR을 사용하여 텍스트를 추출합니다.
    
    Returns:
        추출된 텍스트 정보 딕셔너리 (숫자, 단위 등)
    """
    if not OCR_AVAILABLE or reader is None:
        return {
            "has_text": 0.0,
            "volume_ml": 0.0,  # ml 단위 숫자
            "has_ml": 0.0,  # ml 텍스트 존재 여부
            "numbers": [],  # 발견된 모든 숫자
        }
    
    try:
        # 이미지 전처리
        processed_image = preprocess_image_for_ocr(image)
        
        # OCR 수행
        results = reader.readtext(processed_image)
        
        # 추출된 텍스트 합치기
        all_text = " ".join([result[1] for result in results]).lower()
        
        # OCR 오타 보정
        corrected_text = correct_ocr_typos(all_text)
        
        # ml 단위 찾기 (예: "30ml", "50ml", "30 ml", "50 ml")
        ml_pattern = r'(\d+)\s*ml'
        ml_matches = re.findall(ml_pattern, corrected_text)
        
        volume_ml = 0.0
        if ml_matches:
            # 가장 큰 숫자를 선택 (여러 개 있을 경우)
            volume_ml = float(max([int(m) for m in ml_matches], key=int))
        
        # 모든 숫자 찾기
        number_pattern = r'\d+'
        numbers = [int(n) for n in re.findall(number_pattern, corrected_text)]
        
        return {
            "has_text": 1.0 if corrected_text.strip() else 0.0,
            "volume_ml": volume_ml,
            "has_ml": 1.0 if ml_matches else 0.0,
            "numbers": numbers,
            "text": corrected_text,  # 디버깅용
            "original_text": all_text,  # 원본 텍스트
        }
    except Exception as e:
        print(f"⚠️  OCR 오류: {e}")
        return {
            "has_text": 0.0,
            "volume_ml": 0.0,
            "has_ml": 0.0,
            "numbers": [],
        }


def extract_image_hash(image: np.ndarray) -> np.ndarray:
    """이미지 해시 특징을 추출합니다 (perceptual hashing)"""
    if not IMAGEHASH_AVAILABLE:
        return np.zeros(64)  # 해시가 없으면 0으로 채움 (8x8 = 64)
    
    try:
        pil_image = Image.fromarray(image)
        # dHash (difference hash) 사용
        hash_value = imagehash.dhash(pil_image, hash_size=8)
        # 해시를 숫자 배열로 변환 (8x8 = 64비트)
        hash_str = str(hash_value)
        # 16진수 문자열을 64비트 배열로 변환
        hash_int = int(hash_str, 16)
        hash_array = np.array([(hash_int >> i) & 1 for i in range(64)], dtype=float)
        return hash_array
    except Exception:
        return np.zeros(64)


def extract_composition_features(image: np.ndarray, ocr_features: dict = None) -> np.ndarray:
    """
    이미지의 구도 특징을 추출합니다.
    
    특징:
    1. 엣지 분포 (9개 영역으로 나눈 엣지 밀도)
    2. 색상 분포 (9개 영역의 평균 색상)
    3. 전체 엣지 히스토그램
    4. 공간적 레이아웃 (중심, 대칭성 등)
    """
    if image is None:
        return None
    
    h, w = image.shape[:2]
    features = []
    
    # 1. 엣지 검출
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    edges = cv2.Canny(gray, 50, 150)
    
    # 2. 3x3 그리드로 이미지를 나눠서 각 영역의 특징 추출
    grid_size = 3
    cell_h, cell_w = h // grid_size, w // grid_size
    
    for i in range(grid_size):
        for j in range(grid_size):
            y1, y2 = i * cell_h, (i + 1) * cell_h
            x1, x2 = j * cell_w, (j + 1) * cell_w
            
            # 엣지 밀도
            cell_edges = edges[y1:y2, x1:x2]
            edge_density = np.sum(cell_edges > 0) / (cell_h * cell_w)
            features.append(edge_density)
            
            # 평균 색상 (RGB)
            cell_image = image[y1:y2, x1:x2]
            avg_color = np.mean(cell_image, axis=(0, 1))
            features.extend(avg_color)
    
    # 3. 전체 엣지 히스토그램 (8개 bin)
    edge_hist = np.histogram(edges[edges > 0], bins=8, range=(0, 255))[0]
    edge_hist = edge_hist / (np.sum(edge_hist) + 1e-6)  # 정규화
    features.extend(edge_hist)
    
    # 4. 중심 영역의 특징 (중앙 1/3 영역)
    center_y1, center_y2 = h // 3, 2 * h // 3
    center_x1, center_x2 = w // 3, 2 * w // 3
    center_region = image[center_y1:center_y2, center_x1:center_x2]
    center_avg_color = np.mean(center_region, axis=(0, 1))
    features.extend(center_avg_color)
    
    # 5. 수평/수직 대칭성 점수
    # 수평 대칭성: 상단과 하단의 유사도
    top_half = gray[:h//2, :]
    bottom_half = cv2.flip(gray[h//2:, :], 0)
    if top_half.shape == bottom_half.shape:
        horizontal_symmetry = 1.0 - np.mean(np.abs(top_half.astype(float) - bottom_half.astype(float))) / 255.0
    else:
        horizontal_symmetry = 0.0
    
    # 수직 대칭성: 좌측과 우측의 유사도
    left_half = gray[:, :w//2]
    right_half = cv2.flip(gray[:, w//2:], 1)
    if left_half.shape == right_half.shape:
        vertical_symmetry = 1.0 - np.mean(np.abs(left_half.astype(float) - right_half.astype(float))) / 255.0
    else:
        vertical_symmetry = 0.0
    
    features.extend([horizontal_symmetry, vertical_symmetry])
    
    # 6. OCR 특징 추가 (텍스트 정보)
    if ocr_features:
        features.append(ocr_features.get("has_text", 0.0))
        features.append(ocr_features.get("volume_ml", 0.0))
        features.append(ocr_features.get("has_ml", 0.0))
        # 숫자가 여러 개 있을 경우, 가장 큰 숫자와 평균 추가
        numbers = ocr_features.get("numbers", [])
        if numbers:
            features.append(float(max(numbers)))
            features.append(float(np.mean(numbers)))
        else:
            features.extend([0.0, 0.0])
    else:
        # OCR 특징이 없으면 0으로 채움
        features.extend([0.0, 0.0, 0.0, 0.0, 0.0])
    
    # 7. 이미지 해시 특징 추가 (perceptual hashing)
    hash_features = extract_image_hash(image)
    features.extend(hash_features)
    
    return np.array(features)


def cluster_images(
    image_dir: str,
    output_dir: str = None,
    method: str = "dbscan",
    n_clusters: int = None,
    eps: float = 0.5,
    min_samples: int = 2,
    use_ocr: bool = True,
) -> dict:
    """
    이미지들을 구도에 따라 클러스터링합니다.
    
    Args:
        image_dir: 이미지가 있는 디렉토리 경로
        output_dir: 클러스터별로 이미지를 복사할 출력 디렉토리 (None이면 복사 안 함)
        method: 클러스터링 방법 ("dbscan" 또는 "kmeans")
        n_clusters: KMeans 사용 시 클러스터 개수
        eps: DBSCAN의 eps 파라미터
        min_samples: DBSCAN의 min_samples 파라미터
        use_ocr: OCR을 사용하여 텍스트 특징 추출 여부
    
    Returns:
        클러스터링 결과 딕셔너리
    """
    image_path = Path(image_dir)
    if not image_path.exists():
        print(f"❌ 디렉토리를 찾을 수 없습니다: {image_path}")
        return {}
    
    # 이미지 파일 찾기
    image_files = []
    for ext in ['*.jpg', '*.jpeg', '*.png', '*.webp', '*.JPG', '*.JPEG', '*.PNG', '*.WEBP']:
        image_files.extend(image_path.glob(ext))
    
    if not image_files:
        print(f"❌ 이미지 파일을 찾을 수 없습니다: {image_path}")
        return {}
    
    print(f"📸 {len(image_files)}개의 이미지를 찾았습니다.\n")
    
    # OCR 리더 초기화
    ocr_reader = None
    if use_ocr and OCR_AVAILABLE:
        print("📝 OCR 리더 초기화 중... (처음 실행 시 모델 다운로드로 시간이 걸릴 수 있습니다)")
        try:
            ocr_reader = easyocr.Reader(['en', 'ko'], gpu=False)  # 영어와 한국어 지원
            print("✅ OCR 리더 준비 완료\n")
        except Exception as e:
            print(f"⚠️  OCR 리더 초기화 실패: {e}. OCR 없이 진행합니다.\n")
            ocr_reader = None
    elif use_ocr and not OCR_AVAILABLE:
        print("⚠️  OCR을 사용하려면 'pip install easyocr'을 실행하세요. OCR 없이 진행합니다.\n")
    
    # 이미지 로드 및 특징 추출
    print("🔍 이미지 특징 추출 중...")
    images_data = []
    valid_files = []
    ocr_results = {}  # 디버깅용
    
    for img_file in sorted(image_files):
        img = load_image(img_file)
        if img is None:
            continue
        
        # OCR 특징 추출
        ocr_features = None
        if ocr_reader:
            ocr_features = extract_text_from_image(img, ocr_reader)
            ocr_results[img_file.name] = ocr_features
            if ocr_features.get("volume_ml", 0) > 0:
                print(f"   📝 {img_file.name}: {ocr_features.get('volume_ml', 0)}ml 감지")
        
        features = extract_composition_features(img, ocr_features)
        if features is not None:
            images_data.append(features)
            valid_files.append(img_file)
    
    if len(images_data) < 2:
        print("❌ 클러스터링을 위해 최소 2개 이상의 이미지가 필요합니다.")
        return {}
    
    print(f"✅ {len(images_data)}개의 이미지 특징 추출 완료\n")
    
    # 특징 벡터 정규화
    X = np.array(images_data)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # OCR ml 값에 가중치 적용 (ml 값이 있는 경우 해당 특징에 더 큰 가중치)
    # ml 값 특징의 인덱스 찾기 (OCR 특징은 뒤쪽에 있음)
    # 구조: [구도 특징들...] + [has_text, volume_ml, has_ml, max_num, avg_num] + [해시 64개]
    if use_ocr and ocr_results:
        # volume_ml 특징의 인덱스는 대략 구도 특징 개수 + 1 위치
        # 정확한 인덱스 계산: 구도 특징 개수 확인
        base_features_count = len(images_data[0]) - 5 - 64  # 전체 - OCR 5개 - 해시 64개
        volume_ml_idx = base_features_count + 1  # has_text 다음이 volume_ml
        
        # ml 값이 있는 이미지들에 대해 가중치 적용
        for i, img_file in enumerate(valid_files):
            ocr_data = ocr_results.get(img_file.name, {})
            volume_ml = ocr_data.get("volume_ml", 0)
            if volume_ml > 0:
                # ml 값에 큰 가중치 적용 (정규화된 값에 추가)
                X_scaled[i, volume_ml_idx] *= 10.0  # ml 값 특징에 10배 가중치
    
    # PCA로 차원 축소 (선택적, 시각화 및 성능 향상)
    if X_scaled.shape[1] > 50:
        n_components = min(50, X_scaled.shape[0] - 1, X_scaled.shape[1])
        if n_components > 0:
            pca = PCA(n_components=n_components)
            X_scaled = pca.fit_transform(X_scaled)
            print(f"📊 PCA로 차원 축소: {X_scaled.shape[1]}차원\n")
    
    # 클러스터링
    print(f"🎯 {method.upper()} 클러스터링 수행 중...")
    if method.lower() == "dbscan":
        clustering = DBSCAN(eps=eps, min_samples=min_samples)
        labels = clustering.fit_predict(X_scaled)
        n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
        n_noise = list(labels).count(-1)
        print(f"✅ {n_clusters}개의 클러스터 발견 (노이즈: {n_noise}개)\n")
    else:  # kmeans
        if n_clusters is None:
            n_clusters = min(5, len(valid_files) // 2)
        clustering = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        labels = clustering.fit_predict(X_scaled)
        print(f"✅ {n_clusters}개의 클러스터 생성\n")
    
    # 결과 정리
    clusters = defaultdict(list)
    for img_file, label in zip(valid_files, labels):
        clusters[label].append(img_file)
    
    # 결과 출력
    print("=" * 70)
    print("클러스터링 결과")
    print("=" * 70)
    for cluster_id in sorted(clusters.keys()):
        if cluster_id == -1:
            print(f"\n🔸 노이즈 (클러스터 없음): {len(clusters[cluster_id])}개")
        else:
            print(f"\n📁 클러스터 {cluster_id}: {len(clusters[cluster_id])}개")
        for img_file in clusters[cluster_id]:
            print(f"   - {img_file.name}")
    
    # 출력 디렉토리에 복사
    if output_dir:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        print(f"\n📂 클러스터별 이미지를 {output_path}에 복사 중...")
        for cluster_id, img_files in clusters.items():
            if cluster_id == -1:
                cluster_dir = output_path / "noise"
            else:
                cluster_dir = output_path / f"cluster_{cluster_id}"
            cluster_dir.mkdir(exist_ok=True)
            
            for img_file in img_files:
                shutil.copy2(img_file, cluster_dir / img_file.name)
        
        print(f"✅ 복사 완료!\n")
    
    return {
        "clusters": dict(clusters),
        "labels": labels,
        "n_clusters": n_clusters,
        "features": X_scaled,
        "ocr_results": ocr_results,
    }


def visualize_clusters(result: dict, output_path: str = "cluster_visualization.png"):
    """클러스터링 결과를 시각화합니다."""
    if not result or "features" not in result:
        print("❌ 시각화할 데이터가 없습니다.")
        return
    
    features = result["features"]
    labels = result["labels"]
    
    # 2D로 차원 축소
    pca_2d = PCA(n_components=2)
    features_2d = pca_2d.fit_transform(features)
    
    # 플롯
    plt.figure(figsize=(12, 8))
    unique_labels = set(labels)
    colors = plt.cm.Spectral(np.linspace(0, 1, len(unique_labels)))
    
    for k, col in zip(unique_labels, colors):
        if k == -1:
            col = 'black'  # 노이즈는 검은색
            marker = 'x'
            label = 'Noise'
        else:
            marker = 'o'
            label = f'Cluster {k}'
        
        class_member_mask = labels == k
        xy = features_2d[class_member_mask]
        plt.scatter(xy[:, 0], xy[:, 1], c=[col], marker=marker, s=50, label=label, alpha=0.6)
    
    plt.title('Image Composition Clustering Results', fontsize=14, fontweight='bold')
    plt.xlabel('PCA Component 1')
    plt.ylabel('PCA Component 2')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"📊 시각화 결과를 {output_path}에 저장했습니다.")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="비슷한 구도의 이미지를 클러스터링합니다.")
    parser.add_argument(
        "--input",
        type=str,
        default="/Users/admin/Downloads/sulwhasoo",
        help="이미지가 있는 디렉토리 경로",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="클러스터별 이미지를 저장할 디렉토리 (지정하지 않으면 복사 안 함)",
    )
    parser.add_argument(
        "--method",
        type=str,
        choices=["dbscan", "kmeans"],
        default="dbscan",
        help="클러스터링 방법 (dbscan 또는 kmeans)",
    )
    parser.add_argument(
        "--n-clusters",
        type=int,
        default=None,
        help="KMeans 사용 시 클러스터 개수 (지정하지 않으면 자동 결정)",
    )
    parser.add_argument(
        "--eps",
        type=float,
        default=0.45,
        help="DBSCAN의 eps 파라미터 (클러스터 간 거리 임계값)",
    )
    parser.add_argument(
        "--min-samples",
        type=int,
        default=2,
        help="DBSCAN의 min_samples 파라미터 (최소 샘플 수)",
    )
    parser.add_argument(
        "--visualize",
        action="store_true",
        help="클러스터링 결과를 시각화합니다.",
    )
    parser.add_argument(
        "--no-ocr",
        action="store_true",
        help="OCR 기능을 사용하지 않습니다.",
    )
    parser.add_argument(
        "--ground-truth",
        type=str,
        default=None,
        help="정답 데이터 파일 경로 (CSV 형식: image_path,cluster_id) 또는 평가를 건너뛰려면 지정하지 않음",
    )
    parser.add_argument(
        "--generate-template",
        type=str,
        default=None,
        help="정답 데이터 템플릿 CSV 파일을 생성합니다. 파일 경로를 지정하세요.",
    )
    
    args = parser.parse_args()
    
    # 클러스터링 수행
    result = cluster_images(
        image_dir=args.input,
        output_dir=args.output,
        method=args.method,
        n_clusters=args.n_clusters,
        eps=args.eps,
        min_samples=args.min_samples,
        use_ocr=not args.no_ocr,
    )
    
    # OCR 결과 출력
    if result and "ocr_results" in result and result["ocr_results"]:
        print("\n" + "=" * 70)
        print("OCR 텍스트 추출 결과")
        print("=" * 70)
        has_ml = False
        for img_name, ocr_data in result["ocr_results"].items():
            volume_ml = ocr_data.get("volume_ml", 0)
            if volume_ml > 0:
                print(f"  {img_name}: {volume_ml}ml")
                has_ml = True
            elif ocr_data.get("has_text", 0) > 0:
                # 텍스트는 있지만 ml을 찾지 못한 경우
                text = ocr_data.get("text", "")
                if text:
                    print(f"  {img_name}: 텍스트 발견 (ml 없음) - '{text[:50]}...'")
        if not has_ml:
            print("  (ml 단위를 찾지 못했습니다)")
        print()
    
    # 정답 데이터 템플릿 생성
    if args.generate_template and result:
        if not EVALUATION_AVAILABLE:
            print("❌ 평가 모듈을 사용할 수 없습니다. tests/evaluate_clustering.py를 확인하세요.")
        else:
            generate_ground_truth_template(result, args.generate_template)
    
    # 정답 데이터와 비교 평가
    if args.ground_truth and result:
        if not EVALUATION_AVAILABLE:
            print("❌ 평가 모듈을 사용할 수 없습니다. tests/evaluate_clustering.py를 확인하세요.")
        else:
            print("\n" + "=" * 70)
            print("정답 데이터와 비교 평가")
            print("=" * 70)
            predicted_clusters = convert_cluster_result_to_list(result)
            evaluation_result = evaluate_clustering(predicted_clusters, args.ground_truth)
            print_evaluation_report(evaluation_result)
    
    # 시각화
    if args.visualize and result:
        visualize_clusters(result)

