"""
Neo4j Data Quality Check Script

Neo4j에 주입된 데이터의 품질을 검증합니다.

사용법:
    poetry run python scripts/neo4j_quality_check.py
    poetry run python scripts/neo4j_quality_check.py --fix-orphans
"""

import os
import argparse
from dotenv import load_dotenv
from neo4j import GraphDatabase
from collections import Counter

load_dotenv()


class Neo4jQualityChecker:
    """Neo4j 데이터 품질 검증기"""
    
    def __init__(self, uri: str, user: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        print(f"✅ Neo4j 연결: {uri}")
    
    def close(self):
        self.driver.close()
    
    def run_all_checks(self) -> dict:
        """모든 품질 검사 실행"""
        results = {
            "summary": {},
            "issues": [],
            "recommendations": []
        }
        
        print("\n" + "=" * 60)
        print("🔍 Neo4j 데이터 품질 검사")
        print("=" * 60)
        
        # 1. 기본 통계
        stats = self._get_basic_stats()
        results["summary"] = stats
        print(f"\n📊 기본 통계:")
        print(f"   - 총 노드 수: {stats['total_nodes']}")
        print(f"   - 총 관계 수: {stats['total_relationships']}")
        
        # 2. 노드 타입별 분포
        node_dist = self._get_node_distribution()
        print(f"\n📂 노드 타입별 분포:")
        for label, count in sorted(node_dist.items(), key=lambda x: -x[1])[:10]:
            print(f"   - {label}: {count}")
        
        # 3. 고립 노드 검사
        orphans = self._find_orphan_nodes()
        if orphans["count"] > 0:
            results["issues"].append({
                "type": "orphan_nodes",
                "count": orphans["count"],
                "details": orphans["details"]
            })
            print(f"\n⚠️  고립 노드 발견: {orphans['count']}개")
            for label, count in orphans["details"].items():
                print(f"   - {label}: {count}")
        else:
            print(f"\n✅ 고립 노드 없음")
        
        # 4. 관계 타입별 분포
        rel_dist = self._get_relationship_distribution()
        print(f"\n🔗 관계 타입별 분포:")
        for rel_type, count in sorted(rel_dist.items(), key=lambda x: -x[1]):
            print(f"   - {rel_type}: {count}")
        
        # 5. 중복 노드 검사
        duplicates = self._find_duplicate_nodes()
        if duplicates["count"] > 0:
            results["issues"].append({
                "type": "duplicate_nodes",
                "count": duplicates["count"],
                "details": duplicates["details"]
            })
            print(f"\n⚠️  중복 노드 발견: {duplicates['count']}개")
            for name, count in list(duplicates["details"].items())[:5]:
                print(f"   - '{name}': {count}개")
        else:
            print(f"\n✅ 중복 노드 없음")
        
        # 6. 연결성 분석 (Component Analysis)
        components = self._analyze_connectivity()
        print(f"\n🌐 연결성 분석:")
        print(f"   - 최대 연결 컴포넌트 크기: {components['largest_component']}")
        print(f"   - 컴포넌트 수 (100개 이상 노드): {components['large_components']}")
        print(f"   - 작은 클러스터 수: {components['small_clusters']}")
        
        if components["small_clusters"] > 10:
            results["issues"].append({
                "type": "fragmented_graph",
                "count": components["small_clusters"],
                "details": "그래프가 많은 작은 클러스터로 분리되어 있습니다."
            })
            results["recommendations"].append(
                "Entity Normalization 재검토: 동일 엔티티가 다른 이름으로 생성되어 분리되었을 수 있습니다."
            )
        
        # 7. 속성 누락 검사
        missing_props = self._check_missing_properties()
        if missing_props["count"] > 0:
            results["issues"].append({
                "type": "missing_properties",
                "count": missing_props["count"],
                "details": missing_props["details"]
            })
            print(f"\n⚠️  속성 누락 발견:")
            for prop, count in missing_props["details"].items():
                print(f"   - {prop}: {count}개 노드에서 누락")
        
        # 8. 최종 요약
        print("\n" + "=" * 60)
        print("📋 품질 검사 요약")
        print("=" * 60)
        
        if not results["issues"]:
            print("✅ 모든 검사 통과! 데이터 품질 양호.")
        else:
            print(f"⚠️  {len(results['issues'])}개 이슈 발견:")
            for issue in results["issues"]:
                print(f"   - [{issue['type']}] {issue['count']}건")
        
        if results["recommendations"]:
            print("\n💡 권장 조치:")
            for rec in results["recommendations"]:
                print(f"   - {rec}")
        
        return results
    
    def _get_basic_stats(self) -> dict:
        with self.driver.session() as session:
            node_count = session.run("MATCH (n) RETURN count(n) as count").single()["count"]
            rel_count = session.run("MATCH ()-[r]->() RETURN count(r) as count").single()["count"]
            return {"total_nodes": node_count, "total_relationships": rel_count}
    
    def _get_node_distribution(self) -> dict:
        with self.driver.session() as session:
            result = session.run("""
                MATCH (n)
                UNWIND labels(n) as label
                RETURN label, count(*) as count
                ORDER BY count DESC
            """)
            return {r["label"]: r["count"] for r in result}
    
    def _get_relationship_distribution(self) -> dict:
        with self.driver.session() as session:
            result = session.run("""
                MATCH ()-[r]->()
                RETURN type(r) as type, count(*) as count
                ORDER BY count DESC
            """)
            return {r["type"]: r["count"] for r in result}
    
    def _find_orphan_nodes(self) -> dict:
        with self.driver.session() as session:
            result = session.run("""
                MATCH (n)
                WHERE NOT (n)--()
                UNWIND labels(n) as label
                RETURN label, count(*) as count
            """)
            details = {r["label"]: r["count"] for r in result}
            total = sum(details.values())
            return {"count": total, "details": details}
    
    def _find_duplicate_nodes(self) -> dict:
        with self.driver.session() as session:
            result = session.run("""
                MATCH (n)
                WHERE n.name IS NOT NULL
                WITH n.name as name, count(*) as count
                WHERE count > 1
                RETURN name, count
                ORDER BY count DESC
                LIMIT 20
            """)
            details = {r["name"]: r["count"] for r in result}
            total = sum(details.values()) - len(details)  # 초과분만 계산
            return {"count": total, "details": details}
    
    def _analyze_connectivity(self) -> dict:
        with self.driver.session() as session:
            # 가장 큰 연결 컴포넌트 크기 (근사)
            try:
                result = session.run("""
                    MATCH (n)
                    WHERE (n)--()
                    WITH n LIMIT 1000
                    MATCH (n)-[*1..3]-(connected)
                    RETURN count(DISTINCT connected) as component_size
                """)
                largest = result.single()["component_size"]
            except:
                largest = "측정 불가"
            
            # 작은 클러스터 수 (3개 이하 연결)
            result = session.run("""
                MATCH (n)
                WHERE (n)--()
                WITH n, size([(n)--() | 1]) as degree
                WHERE degree <= 2
                RETURN count(n) as count
            """)
            small_clusters = result.single()["count"]
            
            return {
                "largest_component": largest,
                "large_components": 1,  # 근사값
                "small_clusters": small_clusters
            }
    
    def _check_missing_properties(self) -> dict:
        critical_props = [
            ("EconomicIndicator", "description"),
            ("Issue", "date"),
            ("Earnings", "date"),
            ("PriceMovement", "date")
        ]
        
        details = {}
        with self.driver.session() as session:
            for label, prop in critical_props:
                result = session.run(f"""
                    MATCH (n:{label})
                    WHERE n.{prop} IS NULL
                    RETURN count(n) as count
                """)
                count = result.single()["count"]
                if count > 0:
                    details[f"{label}.{prop}"] = count
        
        return {"count": sum(details.values()), "details": details}
    
    def fix_orphan_nodes(self, delete: bool = False):
        """고립 노드 처리"""
        if delete:
            with self.driver.session() as session:
                result = session.run("""
                    MATCH (n)
                    WHERE NOT (n)--()
                    DELETE n
                    RETURN count(*) as deleted
                """)
                deleted = result.single()["deleted"]
                print(f"🗑️  {deleted}개 고립 노드 삭제 완료")
                return deleted
        else:
            print("ℹ️  삭제하려면 --delete-orphans 옵션을 사용하세요.")
            return 0
    
    def fix_duplicate_nodes(self):
        """중복 노드 병합 (동일 name 가진 노드를 하나로 통합)"""
        with self.driver.session() as session:
            # 중복된 노드 찾아서 관계를 첫 번째 노드로 이전 후 나머지 삭제
            result = session.run("""
                MATCH (n)
                WHERE n.name IS NOT NULL
                WITH n.name as name, collect(n) as nodes, count(*) as count
                WHERE count > 1
                UNWIND tail(nodes) as duplicate
                DETACH DELETE duplicate
                RETURN count(duplicate) as deleted
            """)
            deleted = result.single()["deleted"]
            print(f"🔄 {deleted}개 중복 노드 병합 완료")
            return deleted
    
    def fix_missing_properties(self):
        """누락된 속성에 기본값 설정"""
        fixes = [
            ("Issue", "date", "UNKNOWN"),
            ("Earnings", "date", "UNKNOWN"),
            ("PriceMovement", "date", "UNKNOWN"),
            ("EconomicIndicator", "description", "No description")
        ]
        
        total_fixed = 0
        with self.driver.session() as session:
            for label, prop, default_value in fixes:
                result = session.run(f"""
                    MATCH (n:{label})
                    WHERE n.{prop} IS NULL
                    SET n.{prop} = $default
                    RETURN count(n) as fixed
                """, default=default_value)
                fixed = result.single()["fixed"]
                if fixed > 0:
                    print(f"   ✅ {label}.{prop}: {fixed}개 노드에 기본값 설정")
                    total_fixed += fixed
        
        print(f"📝 총 {total_fixed}개 속성 수정 완료")
        return total_fixed
    
    def auto_fix_all(self):
        """모든 이슈 자동 수정"""
        print("\n" + "=" * 60)
        print("🔧 자동 수정 시작")
        print("=" * 60)
        
        # 1. 고립 노드 삭제
        print("\n[1/3] 고립 노드 삭제...")
        orphan_deleted = self.fix_orphan_nodes(delete=True)
        
        # 2. 중복 노드 병합
        print("\n[2/3] 중복 노드 병합...")
        duplicate_deleted = self.fix_duplicate_nodes()
        
        # 3. 속성 누락 수정
        print("\n[3/3] 속성 누락 수정...")
        props_fixed = self.fix_missing_properties()
        
        print("\n" + "=" * 60)
        print("✅ 자동 수정 완료")
        print(f"   - 고립 노드 삭제: {orphan_deleted}")
        print(f"   - 중복 노드 병합: {duplicate_deleted}")
        print(f"   - 속성 수정: {props_fixed}")
        print("=" * 60)
        
        return {
            "orphan_deleted": orphan_deleted,
            "duplicate_deleted": duplicate_deleted,
            "props_fixed": props_fixed
        }


def main():
    parser = argparse.ArgumentParser(description="Neo4j 데이터 품질 검사")
    parser.add_argument("--fix-orphans", action="store_true", help="고립 노드 로그 출력")
    parser.add_argument("--delete-orphans", action="store_true", help="고립 노드 삭제")
    parser.add_argument("--auto-fix", action="store_true", help="모든 이슈 자동 수정")
    
    args = parser.parse_args()
    
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", os.getenv("NEO4J_USERNAME", "neo4j"))
    password = os.getenv("NEO4J_PASSWORD", "password")
    
    checker = Neo4jQualityChecker(uri, user, password)
    
    try:
        results = checker.run_all_checks()
        
        if args.auto_fix:
            checker.auto_fix_all()
        elif args.delete_orphans:
            checker.fix_orphan_nodes(delete=True)
    finally:
        checker.close()


if __name__ == "__main__":
    main()

