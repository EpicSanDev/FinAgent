#!/usr/bin/env python3
"""
Script de Test Rapide FinAgent

Script pour exécution rapide des tests les plus critiques
pour validation durant le développement.
"""

import subprocess
import sys
import time
from pathlib import Path


def run_quick_tests():
    """Exécute les tests critiques rapidement"""
    project_root = Path(__file__).parent.parent
    
    print("🚀 Tests Rapides FinAgent")
    print("=" * 40)
    
    # Configuration des tests rapides
    quick_tests = [
        {
            'name': 'Modèles Core',
            'path': 'tests/unit/test_models.py',
            'markers': 'unit and critical',
            'timeout': 30
        },
        {
            'name': 'Configuration',
            'path': 'tests/unit/test_config.py',
            'markers': 'unit and not slow',
            'timeout': 20
        },
        {
            'name': 'Workflow Principal',
            'path': 'tests/integration/test_workflow.py::test_basic_analysis_workflow',
            'markers': 'integration and critical',
            'timeout': 60
        },
        {
            'name': 'Sécurité API',
            'path': 'tests/security/test_api_security.py::test_api_key_protection',
            'markers': 'security and critical',
            'timeout': 30
        }
    ]
    
    total_tests = 0
    passed_tests = 0
    failed_tests = 0
    
    for test_config in quick_tests:
        print(f"\n🧪 {test_config['name']}")
        print("-" * 30)
        
        cmd = [
            sys.executable, "-m", "pytest",
            test_config['path'],
            "-v", "--tb=short", "-q"
        ]
        
        if 'markers' in test_config:
            cmd.extend(["-m", test_config['markers']])
        
        start_time = time.time()
        
        try:
            result = subprocess.run(
                cmd,
                cwd=project_root,
                capture_output=True,
                text=True,
                timeout=test_config['timeout']
            )
            
            duration = time.time() - start_time
            
            # Parse résultats
            output_lines = result.stdout.split('\n')
            
            test_passed = 0
            test_failed = 0
            
            for line in output_lines:
                if ' PASSED' in line:
                    test_passed += 1
                elif ' FAILED' in line or ' ERROR' in line:
                    test_failed += 1
            
            total_tests += test_passed + test_failed
            passed_tests += test_passed
            failed_tests += test_failed
            
            # Afficher résultat
            if result.returncode == 0:
                print(f"   ✅ Réussi: {test_passed} tests ({duration:.1f}s)")
            else:
                print(f"   ❌ Échoué: {test_failed} échecs, {test_passed} réussis ({duration:.1f}s)")
                
                # Afficher première erreur
                for line in output_lines:
                    if 'FAILED' in line:
                        print(f"      {line}")
                        break
        
        except subprocess.TimeoutExpired:
            print(f"   ⏱️  Timeout après {test_config['timeout']}s")
            failed_tests += 1
            total_tests += 1
        
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
            failed_tests += 1
            total_tests += 1
    
    # Résumé final
    print(f"\n" + "=" * 40)
    print(f"📊 RÉSUMÉ TESTS RAPIDES")
    print(f"   Total: {total_tests}")
    print(f"   Réussis: {passed_tests}")
    print(f"   Échoués: {failed_tests}")
    
    if failed_tests == 0:
        print(f"   ✅ Tous les tests critiques passent!")
        return True
    else:
        print(f"   ❌ {failed_tests} tests critiques échouent")
        return False


def run_coverage_check():
    """Vérifie rapidement la couverture"""
    print(f"\n📊 Vérification Couverture")
    print("-" * 30)
    
    project_root = Path(__file__).parent.parent
    
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/unit/",
        "--cov=finagent",
        "--cov-report=term-missing",
        "-q"
    ]
    
    try:
        result = subprocess.run(
            cmd,
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=120
        )
        
        # Extraire pourcentage de couverture
        for line in result.stdout.split('\n'):
            if 'TOTAL' in line and '%' in line:
                coverage_match = line.split()[-1]
                if coverage_match.endswith('%'):
                    coverage = int(coverage_match.rstrip('%'))
                    print(f"   Couverture actuelle: {coverage}%")
                    
                    if coverage >= 85:
                        print(f"   ✅ Objectif 85% atteint!")
                        return True
                    else:
                        print(f"   ⚠️  Sous l'objectif 85%")
                        return False
        
        print(f"   ⚠️  Couverture non déterminée")
        return False
        
    except Exception as e:
        print(f"   ❌ Erreur vérification: {e}")
        return False


def main():
    """Point d'entrée principal"""
    print("🎯 VALIDATION RAPIDE FINAGENT")
    print("=" * 50)
    
    # Tests critiques
    tests_ok = run_quick_tests()
    
    # Vérification couverture
    coverage_ok = run_coverage_check()
    
    # Résultat final
    print(f"\n" + "=" * 50)
    print(f"🎯 VALIDATION FINALE")
    
    if tests_ok and coverage_ok:
        print(f"✅ Projet prêt pour production!")
        print(f"   - Tests critiques: ✅")
        print(f"   - Couverture: ✅")
        sys.exit(0)
    else:
        print(f"❌ Validation échouée:")
        print(f"   - Tests critiques: {'✅' if tests_ok else '❌'}")
        print(f"   - Couverture: {'✅' if coverage_ok else '❌'}")
        print(f"\nExecuter la suite complète:")
        print(f"python scripts/run_full_test_suite.py")
        sys.exit(1)


if __name__ == "__main__":
    main()