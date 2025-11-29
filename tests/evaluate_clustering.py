"""
클러스터링 결과를 평가하는 모듈

클러스터링 결과를 정답 데이터와 비교하여 평가합니다.
"""
import os
import csv
from typing import List, Dict, Union


def convert_cluster_result_to_list(result: dict) -> List[List[str]]:
    """
    cluster_images의 결과를 evaluate_clustering이 기대하는 형식으로 변환합니다.
    
    Args:
        result: cluster_images 함수의 반환값 ({"clusters": {cluster_id: [Path, ...]}})
    
    Returns:
        List[List[str]] 형식의 클러스터 리스트
    """
    clusters_dict = result.get("clusters", {})
    clusters_list = []
    
    # 노이즈(-1)를 제외하고 정렬된 클러스터 ID로 처리
    sorted_cluster_ids = sorted([cid for cid in clusters_dict.keys() if cid != -1])
    
    # 노이즈가 있으면 마지막에 추가
    for cluster_id in sorted_cluster_ids:
        # Path 객체를 문자열로 변환
        cluster_paths = [str(path) for path in clusters_dict[cluster_id]]
        clusters_list.append(cluster_paths)
    
    # 노이즈 클러스터 추가 (있는 경우)
    if -1 in clusters_dict:
        noise_paths = [str(path) for path in clusters_dict[-1]]
        clusters_list.append(noise_paths)
    
    return clusters_list


def load_ground_truth(ground_truth: Union[str, Dict, List]) -> Dict[str, int]:
    """
    정답 데이터를 로드합니다.
    
    Args:
        ground_truth: 정답 데이터. 다음 형식 중 하나:
            - CSV 파일 경로: 'image_path,cluster_id' 형식
            - 딕셔너리: {cluster_id: [image_paths]}
            - 리스트의 리스트: [[image_paths], [image_paths]]
    
    Returns:
        {image_path: cluster_id} 형식의 딕셔너리
    """
    ground_truth_dict = {}
    
    if isinstance(ground_truth, str):
        # CSV 파일인 경우
        with open(ground_truth, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                image_path = row.get('image_path', '').strip()
                cluster_id_str = row.get('cluster_id', '').strip()
                # cluster_id가 비어있거나 숫자가 아닌 경우 건너뛰기
                if image_path and cluster_id_str and cluster_id_str.isdigit():
                    ground_truth_dict[image_path] = int(cluster_id_str)
    elif isinstance(ground_truth, dict):
        # 딕셔너리 형식: {cluster_id: [image_paths]}
        for cluster_id, image_paths in ground_truth.items():
            for image_path in image_paths:
                ground_truth_dict[image_path] = cluster_id
    elif isinstance(ground_truth, list):
        # 리스트의 리스트 형식: [[image_paths], [image_paths]]
        for cluster_id, image_paths in enumerate(ground_truth):
            for image_path in image_paths:
                ground_truth_dict[image_path] = cluster_id
    
    return ground_truth_dict


def evaluate_clustering(
    predicted_clusters: List[List[str]],
    ground_truth: Union[str, Dict, List],
    normalize_paths: bool = True
) -> Dict:
    """
    클러스터링 결과를 평가합니다.
    
    Args:
        predicted_clusters: 예측된 클러스터 리스트
        ground_truth: 정답 데이터
        normalize_paths: 경로를 정규화할지 여부 (대소문자, 슬래시 등)
    
    Returns:
        평가 결과 딕셔너리
    """
    # 정답 데이터 로드
    gt_dict = load_ground_truth(ground_truth)
    
    # 경로 정규화 함수
    def normalize_path(path):
        if normalize_paths:
            return os.path.normpath(path).lower()
        return os.path.normpath(path)
    
    # 정답 데이터 경로 정규화
    gt_dict_normalized = {normalize_path(k): v for k, v in gt_dict.items()}
    
    # 예측 클러스터를 딕셔너리로 변환: {image_path: cluster_id}
    pred_dict = {}
    for cluster_id, cluster in enumerate(predicted_clusters):
        for image_path in cluster:
            normalized_path = normalize_path(image_path)
            pred_dict[normalized_path] = cluster_id
    
    # 평가할 이미지 쌍 생성 (정답에 있는 이미지들만)
    true_positives = 0  # 같은 클러스터에 있어야 하고, 실제로 같은 클러스터에 있음
    true_negatives = 0  # 다른 클러스터에 있어야 하고, 실제로 다른 클러스터에 있음
    false_positives = 0  # 다른 클러스터에 있어야 하는데, 같은 클러스터에 있음
    false_negatives = 0  # 같은 클러스터에 있어야 하는데, 다른 클러스터에 있음
    
    wrong_cases = {
        'false_positives': [],  # 잘못 묶인 케이스
        'false_negatives': [],  # 잘못 분리된 케이스
        'missing_images': [],  # 정답에는 있지만 예측에 없는 이미지
        'extra_images': []  # 예측에는 있지만 정답에 없는 이미지
    }
    
    # 정답에 있는 이미지들만 평가
    gt_images = list(gt_dict_normalized.keys())
    
    for i in range(len(gt_images)):
        img1 = gt_images[i]
        gt_cluster1 = gt_dict_normalized.get(img1)
        
        # 정답에 있지만 예측에 없는 경우
        if img1 not in pred_dict:
            wrong_cases['missing_images'].append(img1)
            continue
        
        pred_cluster1 = pred_dict.get(img1)
        
        for j in range(i + 1, len(gt_images)):
            img2 = gt_images[j]
            gt_cluster2 = gt_dict_normalized.get(img2)
            
            # 정답에 있지만 예측에 없는 경우
            if img2 not in pred_dict:
                continue
            
            pred_cluster2 = pred_dict.get(img2)
            
            # 정답에서 같은 클러스터인지 확인
            same_in_gt = (gt_cluster1 == gt_cluster2)
            # 예측에서 같은 클러스터인지 확인
            same_in_pred = (pred_cluster1 == pred_cluster2)
            
            if same_in_gt and same_in_pred:
                true_positives += 1
            elif not same_in_gt and not same_in_pred:
                true_negatives += 1
            elif not same_in_gt and same_in_pred:
                # 다른 클러스터에 있어야 하는데 같은 클러스터에 있음 (잘못 묶임)
                false_positives += 1
                wrong_cases['false_positives'].append((img1, img2, pred_cluster1))
            elif same_in_gt and not same_in_pred:
                # 같은 클러스터에 있어야 하는데 다른 클러스터에 있음 (잘못 분리됨)
                false_negatives += 1
                wrong_cases['false_negatives'].append((img1, img2, gt_cluster1))
    
    # 예측에는 있지만 정답에 없는 이미지
    for img in pred_dict:
        if img not in gt_dict_normalized:
            wrong_cases['extra_images'].append(img)
    
    # 메트릭 계산
    total_pairs = true_positives + true_negatives + false_positives + false_negatives
    
    if total_pairs == 0:
        accuracy = 0.0
        precision = 0.0
        recall = 0.0
        f1_score = 0.0
    else:
        accuracy = (true_positives + true_negatives) / total_pairs
        
        # Precision: 같은 클러스터로 예측한 것 중 실제로 같은 클러스터인 비율
        if (true_positives + false_positives) == 0:
            precision = 0.0
        else:
            precision = true_positives / (true_positives + false_positives)
        
        # Recall: 실제로 같은 클러스터인 것 중 같은 클러스터로 예측한 비율
        if (true_positives + false_negatives) == 0:
            recall = 0.0
        else:
            recall = true_positives / (true_positives + false_negatives)
        
        # F1 Score
        if (precision + recall) == 0:
            f1_score = 0.0
        else:
            f1_score = 2 * (precision * recall) / (precision + recall)
    
    return {
        'accuracy': accuracy,
        'precision': precision,
        'recall': recall,
        'f1_score': f1_score,
        'true_positives': true_positives,
        'true_negatives': true_negatives,
        'false_positives': false_positives,
        'false_negatives': false_negatives,
        'total_pairs': total_pairs,
        'wrong_cases': wrong_cases,
        'n_predicted_clusters': len(predicted_clusters),
        'n_ground_truth_clusters': len(set(gt_dict_normalized.values())),
    }


def print_evaluation_report(evaluation_result: Dict):
    """평가 결과를 보기 좋게 출력합니다."""
    print("\n" + "=" * 80)
    print("클러스터링 평가 결과")
    print("=" * 80)
    
    print("\n📊 메트릭:")
    print(f"  정확도 (Accuracy): {evaluation_result['accuracy']:.4f} ({evaluation_result['accuracy']*100:.2f}%)")
    print(f"  정밀도 (Precision): {evaluation_result['precision']:.4f} ({evaluation_result['precision']*100:.2f}%)")
    print(f"  재현율 (Recall): {evaluation_result['recall']:.4f} ({evaluation_result['recall']*100:.2f}%)")
    print(f"  F1 점수: {evaluation_result['f1_score']:.4f} ({evaluation_result['f1_score']*100:.2f}%)")
    
    print("\n📈 상세 통계:")
    print(f"  True Positives (TP): {evaluation_result['true_positives']}")
    print(f"  True Negatives (TN): {evaluation_result['true_negatives']}")
    print(f"  False Positives (FP): {evaluation_result['false_positives']} (잘못 묶인 케이스)")
    print(f"  False Negatives (FN): {evaluation_result['false_negatives']} (잘못 분리된 케이스)")
    print(f"  총 이미지 쌍 수: {evaluation_result['total_pairs']}")
    
    print("\n📁 클러스터 수:")
    print(f"  예측된 클러스터 수: {evaluation_result['n_predicted_clusters']}")
    print(f"  정답 클러스터 수: {evaluation_result['n_ground_truth_clusters']}")
    
    wrong_cases = evaluation_result['wrong_cases']
    
    if wrong_cases['false_positives']:
        print(f"\n❌ 잘못 묶인 케이스 (False Positives) - {len(wrong_cases['false_positives'])}개:")
        for img1, img2, cluster_id in wrong_cases['false_positives'][:10]:  # 최대 10개만 출력
            print(f"  클러스터 {cluster_id}:")
            print(f"    - {img1}")
            print(f"    - {img2}")
        if len(wrong_cases['false_positives']) > 10:
            print(f"  ... 외 {len(wrong_cases['false_positives']) - 10}개 더")
    
    if wrong_cases['false_negatives']:
        print(f"\n❌ 잘못 분리된 케이스 (False Negatives) - {len(wrong_cases['false_negatives'])}개:")
        for img1, img2, gt_cluster in wrong_cases['false_negatives'][:10]:  # 최대 10개만 출력
            print(f"  정답 클러스터 {gt_cluster}에 있어야 하는데 분리됨:")
            print(f"    - {img1}")
            print(f"    - {img2}")
        if len(wrong_cases['false_negatives']) > 10:
            print(f"  ... 외 {len(wrong_cases['false_negatives']) - 10}개 더")
    
    if wrong_cases['missing_images']:
        print(f"\n⚠️  정답에는 있지만 예측에 없는 이미지 - {len(wrong_cases['missing_images'])}개:")
        for img in wrong_cases['missing_images'][:10]:
            print(f"  - {img}")
        if len(wrong_cases['missing_images']) > 10:
            print(f"  ... 외 {len(wrong_cases['missing_images']) - 10}개 더")
    
    if wrong_cases['extra_images']:
        print(f"\n⚠️  예측에는 있지만 정답에 없는 이미지 - {len(wrong_cases['extra_images'])}개:")
        for img in wrong_cases['extra_images'][:10]:
            print(f"  - {img}")
        if len(wrong_cases['extra_images']) > 10:
            print(f"  ... 외 {len(wrong_cases['extra_images']) - 10}개 더")
    
    print("\n" + "=" * 80)


def generate_ground_truth_template(result: dict, output_file: str = "ground_truth_template.csv"):
    """
    클러스터링 결과를 기반으로 정답 데이터 템플릿 CSV 파일을 생성합니다.
    
    Args:
        result: cluster_images 함수의 반환값
        output_file: 출력할 CSV 파일 경로
    
    Returns:
        생성된 파일 경로
    """
    clusters_list = convert_cluster_result_to_list(result)
    
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        # 헤더 작성
        writer.writerow(['image_path', 'cluster_id', 'note'])
        
        # 각 클러스터의 이미지들을 작성 (단일 이미지 클러스터도 포함)
        for cluster_id, cluster in enumerate(clusters_list):
            for image_path in cluster:
                # 현재 예측된 cluster_id를 기본값으로 설정
                # 사용자가 이를 수정하여 정답을 작성할 수 있음
                note = f'현재 예측: 클러스터 {cluster_id}'
                if len(cluster) == 1:
                    note += ' (단일 이미지)'
                writer.writerow([image_path, cluster_id, note])
    
    total_images = sum(len(cluster) for cluster in clusters_list)
    multi_image_clusters = sum(1 for cluster in clusters_list if len(cluster) > 1)
    
    print(f"✅ 정답 데이터 템플릿이 생성되었습니다: {output_file}")
    print(f"   - 총 {total_images}개 이미지, {len(clusters_list)}개 클러스터 (다중 이미지 클러스터: {multi_image_clusters}개)")
    print(f"   - 각 이미지의 cluster_id를 정답에 맞게 수정하세요.")
    print(f"   - 같은 클러스터에 있어야 하는 이미지들은 같은 cluster_id를 가져야 합니다.")
    print(f"   - note 컬럼은 참고용이며, 수정할 필요 없습니다.")
    print(f"   - 수정 후 --ground-truth 옵션으로 평가하세요.")
    
    return output_file

