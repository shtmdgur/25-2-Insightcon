import pandas as pd
import os

# ---------------------------------------------------------
# 0. 경로 및 설정
# ---------------------------------------------------------
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))

# 기본 경로
raw_path = os.path.join(project_root, 'data', 'raw')
save_path = os.path.join(project_root, 'data', 'processed')

# 하위 폴더 경로 (states만 사용)
states_path = os.path.join(raw_path, 'states')

# 저장 폴더가 없으면 생성
if not os.path.exists(save_path):
    os.makedirs(save_path)

print(f"🚀 전처리 시작...")
print(f"📂 원본 데이터 경로 (raw): {raw_path}")
print(f"   ㄴ states 폴더: {states_path}")
print(f"📂 저장 경로: {save_path}")
print("-" * 50)


# ---------------------------------------------------------
# 1. companies.csv (기업 기본 정보)
# ---------------------------------------------------------
# 위치: data/raw/states/companies.csv
try:
    print("[1/2] companies.csv 처리 중...")
    comp_df = pd.read_csv(os.path.join(states_path, 'companies.csv'))
    
    # 남길 컬럼 정의
    target_cols = ['corp_name', 'ceo_nm', 'est_dt', 'adres']
    
    # 실제 데이터에 존재하는 컬럼만 선택
    valid_cols = [c for c in target_cols if c in comp_df.columns]
    comp_processed = comp_df[valid_cols]
    
    comp_processed.to_csv(os.path.join(save_path, 'companies_clean.csv'), index=False)
    print("  ✅ 완료")
except FileNotFoundError:
    print("  ❌ companies.csv 파일을 'states' 폴더에서 찾을 수 없습니다.")
except Exception as e:
    print(f"  ❌ 에러 발생: {e}")


# ---------------------------------------------------------
# 2. financial_states.csv (재무 데이터)
# ---------------------------------------------------------
# 위치: data/raw/states/financial_states.csv
try:
    print("[2/2] financial_states.csv 처리 중...")
    file_name = 'financial_states.csv'
    fin_df = pd.read_csv(os.path.join(states_path, file_name))
    
    # ★ 수정됨: ticker 추가 (tiker 오타와 ticker 둘 다 포함하여 안전하게 삭제)
    drop_cols = ['symbol', 'margin_level', 'tiker', 'ticker']
    
    # 데이터에 존재하는 컬럼만 골라서 삭제
    cols_to_drop = [c for c in drop_cols if c in fin_df.columns]
    fin_df.drop(columns=cols_to_drop, inplace=True)
    
    fin_df.to_csv(os.path.join(save_path, 'financial_clean.csv'), index=False)
    print("  ✅ 완료")
except FileNotFoundError:
    print(f"  ❌ {file_name} 파일을 'states' 폴더에서 찾을 수 없습니다.")
except Exception as e:
    print(f"  ❌ 에러 발생: {e}")

# global 부분은 요청하신 대로 삭제했습니다.

print("-" * 50)
print("🎉 전처리 작업 종료")