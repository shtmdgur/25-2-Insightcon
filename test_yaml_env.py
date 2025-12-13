"""
YAML 환경 테스트 스크립트
"""
import yaml
from pathlib import Path

def test_yaml_loading():
    """prompts.yaml 파일 로딩 테스트"""
    
    yaml_path = Path("src/templates/prompts.yaml")
    
    if not yaml_path.exists():
        print(f"❌ YAML 파일을 찾을 수 없습니다: {yaml_path}")
        return False
    
    try:
        with open(yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        print("✅ YAML 파일 로딩 성공!")
        print(f"\n📋 최상위 키: {list(data.keys())}")
        
        # Analysts 섹션 확인
        if 'analysts' in data:
            print(f"\n👥 Analysts: {list(data['analysts'].keys())}")
        
        # Debate 섹션 확인
        if 'debate' in data:
            print(f"\n💬 Debate: {list(data['debate'].keys())}")
        
        # Synthesizer 섹션 확인
        if 'synthesizer' in data:
            print(f"\n🧠 Synthesizer: {list(data['synthesizer'].keys())}")
        
        return True
        
    except yaml.YAMLError as e:
        print(f"❌ YAML 파싱 오류: {e}")
        return False
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return False

if __name__ == "__main__":
    print("🧪 YAML 환경 테스트 시작...\n")
    success = test_yaml_loading()
    
    if success:
        print("\n✅ YAML 환경이 정상적으로 구축되어 있습니다!")
    else:
        print("\n❌ YAML 환경 설정에 문제가 있습니다.")
        print("   'poetry install' 또는 'pip install PyYAML'을 실행하세요.")
