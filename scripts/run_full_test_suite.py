#!/usr/bin/env python3
"""
Script d'Exécution de la Suite Complète de Tests FinAgent

Ce script exécute l'ensemble de la suite de tests avec différents
niveaux de profondeur et génère un rapport complet des résultats.
"""

import os
import sys
import subprocess
import time
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import argparse


@dataclass
class TestSuiteResult:
    """Résultat d'exécution d'une suite de tests"""
    suite_name: str
    total_tests: int
    passed_tests: int
    failed_tests: int
    skipped_tests: int
    execution_time: float
    success_rate: float
    errors: List[str]


@dataclass
class FullTestReport:
    """Rapport complet d'exécution de tests"""
    execution_start: datetime
    execution_end: datetime
    total_duration: float
    suites_results: List[TestSuiteResult]
    overall_success_rate: float
    coverage_percentage: Optional[float]
    compliance_status: str
    recommendations: List[str]


class FinAgentTestRunner:
    """Runner pour la suite complète de tests FinAgent"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.test_configurations = {
            'unit': {
                'path': 'tests/unit',
                'markers': 'unit',
                'timeout': 300,  # 5 minutes
                'description': 'Tests unitaires'
            },
            'integration': {
                'path': 'tests/integration',
                'markers': 'integration',
                'timeout': 600,  # 10 minutes
                'description': 'Tests d\'intégration'
            },
            'performance': {
                'path': 'tests/performance',
                'markers': 'performance and not slowest',
                'timeout': 900,  # 15 minutes
                'description': 'Tests de performance'
            },
            'robustness': {
                'path': 'tests/robustness',
                'markers': 'robustness and not slow',
                'timeout': 600,  # 10 minutes
                'description': 'Tests de robustesse'
            },
            'security': {
                'path': 'tests/security',
                'markers': 'security and not slow',
                'timeout': 600,  # 10 minutes
                'description': 'Tests de sécurité'
            }
        }
    
    def run_test_suite(self, suite_name: str, config: Dict[str, Any], 
                      verbose: bool = False) -> TestSuiteResult:
        """Exécute une suite de tests spécifique"""
        print(f"\n🧪 Exécution: {config['description']}")
        print("-" * 50)
        
        # Préparer commande pytest
        cmd = [
            sys.executable, "-m", "pytest",
            config['path'],
            "-m", config['markers'],
            "--tb=short",
            "--junit-xml", f"test-results-{suite_name}.xml",
            "--json-report", f"--json-report-file=test-report-{suite_name}.json"
        ]
        
        if verbose:
            cmd.append("-v")
        else:
            cmd.append("-q")
        
        # Exécuter tests
        start_time = time.time()
        errors = []
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=config['timeout']
            )
            
            execution_time = time.time() - start_time
            
            # Parser résultats depuis JSON si disponible
            json_report_path = self.project_root / f"test-report-{suite_name}.json"
            
            if json_report_path.exists():
                with open(json_report_path, 'r') as f:
                    json_data = json.load(f)
                
                summary = json_data.get('summary', {})
                total_tests = summary.get('total', 0)
                passed_tests = summary.get('passed', 0)
                failed_tests = summary.get('failed', 0)
                skipped_tests = summary.get('skipped', 0)
                
            else:
                # Parser depuis stdout si JSON non disponible
                total_tests, passed_tests, failed_tests, skipped_tests = self._parse_pytest_output(result.stdout)
            
            # Collecter erreurs
            if result.returncode != 0:
                if result.stderr:
                    errors.append(f"Stderr: {result.stderr}")
                # Extraire erreurs importantes du stdout
                error_lines = [
                    line for line in result.stdout.split('\n')
                    if any(keyword in line.lower() for keyword in ['error', 'failed', 'exception'])
                ]
                if error_lines:
                    errors.extend(error_lines[:5])  # Limiter à 5 erreurs
            
            # Calculer taux de succès
            success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
            
            # Afficher résultats
            print(f"   Tests total: {total_tests}")
            print(f"   Réussis: {passed_tests} ({success_rate:.1f}%)")
            print(f"   Échoués: {failed_tests}")
            print(f"   Ignorés: {skipped_tests}")
            print(f"   Temps: {execution_time:.1f}s")
            
            if errors:
                print(f"   Erreurs: {len(errors)}")
                for error in errors[:2]:  # Afficher 2 premières erreurs
                    print(f"      {error[:100]}...")
            
            return TestSuiteResult(
                suite_name=suite_name,
                total_tests=total_tests,
                passed_tests=passed_tests,
                failed_tests=failed_tests,
                skipped_tests=skipped_tests,
                execution_time=execution_time,
                success_rate=success_rate,
                errors=errors
            )
            
        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            error_msg = f"Timeout après {config['timeout']}s"
            print(f"   ❌ {error_msg}")
            
            return TestSuiteResult(
                suite_name=suite_name,
                total_tests=0,
                passed_tests=0,
                failed_tests=1,
                skipped_tests=0,
                execution_time=execution_time,
                success_rate=0.0,
                errors=[error_msg]
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Erreur exécution: {e}"
            print(f"   ❌ {error_msg}")
            
            return TestSuiteResult(
                suite_name=suite_name,
                total_tests=0,
                passed_tests=0,
                failed_tests=1,
                skipped_tests=0,
                execution_time=execution_time,
                success_rate=0.0,
                errors=[error_msg]
            )
    
    def _parse_pytest_output(self, stdout: str) -> tuple:
        """Parse la sortie pytest pour extraire les statistiques"""
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        skipped_tests = 0
        
        # Chercher ligne de résumé
        for line in stdout.split('\n'):
            if 'passed' in line or 'failed' in line or 'error' in line:
                # Format typique: "5 passed, 2 failed, 1 skipped in 10.23s"
                if ' passed' in line:
                    passed_tests = int(line.split(' passed')[0].split()[-1])
                if ' failed' in line:
                    failed_tests = int(line.split(' failed')[0].split()[-1])
                if ' skipped' in line:
                    skipped_tests = int(line.split(' skipped')[0].split()[-1])
                
                total_tests = passed_tests + failed_tests + skipped_tests
                break
        
        return total_tests, passed_tests, failed_tests, skipped_tests
    
    def run_coverage_analysis(self) -> Optional[float]:
        """Exécute l'analyse de couverture"""
        print(f"\n📊 Analyse de couverture")
        print("-" * 50)
        
        try:
            # Utiliser le script de validation de couverture
            coverage_script = self.project_root / "scripts" / "validate_test_coverage.py"
            
            if coverage_script.exists():
                result = subprocess.run(
                    [sys.executable, str(coverage_script)],
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                    timeout=600  # 10 minutes
                )
                
                # Extraire pourcentage de couverture depuis la sortie
                for line in result.stdout.split('\n'):
                    if 'Couverture globale:' in line:
                        # Format: "Couverture globale: 87.5%"
                        percentage_str = line.split(':')[1].strip().rstrip('%')
                        return float(percentage_str)
                
                print("   ⚠️  Pourcentage de couverture non trouvé dans la sortie")
                return None
            else:
                print("   ⚠️  Script de validation de couverture non trouvé")
                return None
                
        except Exception as e:
            print(f"   ❌ Erreur analyse couverture: {e}")
            return None
    
    def generate_recommendations(self, results: List[TestSuiteResult], 
                               coverage: Optional[float]) -> List[str]:
        """Génère des recommandations basées sur les résultats"""
        recommendations = []
        
        # Analyser taux de succès global
        total_tests = sum(r.total_tests for r in results)
        total_passed = sum(r.passed_tests for r in results)
        overall_success = (total_passed / total_tests * 100) if total_tests > 0 else 0
        
        if overall_success < 90:
            recommendations.append(
                f"Taux de succès global ({overall_success:.1f}%) insuffisant - "
                "investiguer et corriger les tests échoués"
            )
        
        # Analyser par suite
        for result in results:
            if result.success_rate < 80:
                recommendations.append(
                    f"Suite {result.suite_name} ({result.success_rate:.1f}%) nécessite attention"
                )
            
            if result.execution_time > 600:  # Plus de 10 minutes
                recommendations.append(
                    f"Suite {result.suite_name} trop lente ({result.execution_time:.1f}s) - "
                    "optimiser les tests"
                )
        
        # Analyser couverture
        if coverage is not None:
            if coverage < 85:
                recommendations.append(
                    f"Couverture ({coverage:.1f}%) sous l'objectif 85% - "
                    "ajouter tests pour code non couvert"
                )
            elif coverage >= 90:
                recommendations.append(
                    "Excellente couverture de code - maintenir la qualité"
                )
        
        # Recommandations générales
        if not recommendations:
            recommendations.append("Excellents résultats de tests - continuer le bon travail!")
        
        return recommendations
    
    def generate_full_report(self, execution_start: datetime, execution_end: datetime,
                           results: List[TestSuiteResult], coverage: Optional[float]) -> FullTestReport:
        """Génère le rapport complet"""
        total_duration = (execution_end - execution_start).total_seconds()
        
        # Calculer taux de succès global
        total_tests = sum(r.total_tests for r in results)
        total_passed = sum(r.passed_tests for r in results)
        overall_success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        
        # Déterminer statut de conformité
        compliance_status = "CONFORME"
        if overall_success_rate < 90:
            compliance_status = "NON CONFORME - Taux succès insuffisant"
        elif coverage is not None and coverage < 85:
            compliance_status = "NON CONFORME - Couverture insuffisante"
        elif any(r.success_rate < 80 for r in results):
            compliance_status = "PARTIELLEMENT CONFORME - Certaines suites problématiques"
        
        # Générer recommandations
        recommendations = self.generate_recommendations(results, coverage)
        
        return FullTestReport(
            execution_start=execution_start,
            execution_end=execution_end,
            total_duration=total_duration,
            suites_results=results,
            overall_success_rate=overall_success_rate,
            coverage_percentage=coverage,
            compliance_status=compliance_status,
            recommendations=recommendations
        )
    
    def print_final_report(self, report: FullTestReport):
        """Affiche le rapport final"""
        print("\n" + "=" * 80)
        print("🎯 RAPPORT FINAL - SUITE DE TESTS FINAGENT")
        print("=" * 80)
        
        # Résumé exécution
        print(f"\n⏱️  RÉSUMÉ EXÉCUTION")
        print(f"   Début: {report.execution_start.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   Fin: {report.execution_end.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   Durée totale: {report.total_duration/60:.1f} minutes")
        
        # Résultats globaux
        total_tests = sum(r.total_tests for r in report.suites_results)
        total_passed = sum(r.passed_tests for r in report.suites_results)
        total_failed = sum(r.failed_tests for r in report.suites_results)
        total_skipped = sum(r.skipped_tests for r in report.suites_results)
        
        print(f"\n📊 RÉSULTATS GLOBAUX")
        print(f"   Tests total: {total_tests}")
        print(f"   Réussis: {total_passed} ({report.overall_success_rate:.1f}%)")
        print(f"   Échoués: {total_failed}")
        print(f"   Ignorés: {total_skipped}")
        
        if report.coverage_percentage is not None:
            print(f"   Couverture: {report.coverage_percentage:.1f}%")
        
        # Détail par suite
        print(f"\n🧪 DÉTAIL PAR SUITE")
        for result in report.suites_results:
            status = "✅" if result.success_rate >= 80 else "❌"
            print(f"   {status} {result.suite_name}: {result.success_rate:.1f}% "
                  f"({result.passed_tests}/{result.total_tests}) "
                  f"- {result.execution_time:.1f}s")
        
        # Statut conformité
        print(f"\n🎯 CONFORMITÉ")
        print(f"   Statut: {report.compliance_status}")
        
        # Recommandations
        print(f"\n💡 RECOMMANDATIONS")
        for i, rec in enumerate(report.recommendations, 1):
            print(f"   {i}. {rec}")
        
        print("\n" + "=" * 80)
    
    def save_report_json(self, report: FullTestReport, filename: str = "test_report.json"):
        """Sauvegarde le rapport en JSON"""
        report_path = self.project_root / filename
        
        try:
            # Convertir en dict avec sérialisation des dates
            report_dict = asdict(report)
            report_dict['execution_start'] = report.execution_start.isoformat()
            report_dict['execution_end'] = report.execution_end.isoformat()
            
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report_dict, f, indent=2, ensure_ascii=False)
            
            print(f"📄 Rapport JSON sauvegardé: {report_path}")
            
        except Exception as e:
            print(f"❌ Erreur sauvegarde rapport JSON: {e}")
    
    def run_full_suite(self, suites: List[str] = None, verbose: bool = False,
                      with_coverage: bool = True) -> FullTestReport:
        """Exécute la suite complète de tests"""
        print("🚀 DÉMARRAGE SUITE COMPLÈTE DE TESTS FINAGENT")
        print("=" * 80)
        
        execution_start = datetime.now()
        
        # Déterminer suites à exécuter
        if suites is None:
            suites = list(self.test_configurations.keys())
        
        # Valider suites demandées
        invalid_suites = [s for s in suites if s not in self.test_configurations]
        if invalid_suites:
            print(f"❌ Suites invalides: {invalid_suites}")
            print(f"   Suites disponibles: {list(self.test_configurations.keys())}")
            sys.exit(1)
        
        print(f"📋 Suites à exécuter: {', '.join(suites)}")
        
        # Exécuter chaque suite
        results = []
        for suite_name in suites:
            config = self.test_configurations[suite_name]
            result = self.run_test_suite(suite_name, config, verbose)
            results.append(result)
        
        # Analyse de couverture
        coverage = None
        if with_coverage:
            coverage = self.run_coverage_analysis()
        
        execution_end = datetime.now()
        
        # Générer rapport final
        report = self.generate_full_report(execution_start, execution_end, results, coverage)
        
        return report


def main():
    """Point d'entrée principal"""
    parser = argparse.ArgumentParser(description="Exécute la suite complète de tests FinAgent")
    parser.add_argument(
        "--suites",
        nargs="+",
        choices=["unit", "integration", "performance", "robustness", "security"],
        help="Suites à exécuter (défaut: toutes)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Mode verbose"
    )
    parser.add_argument(
        "--no-coverage",
        action="store_true",
        help="Skip analyse de couverture"
    )
    parser.add_argument(
        "--save-json",
        action="store_true",
        help="Sauvegarder rapport en JSON"
    )
    
    args = parser.parse_args()
    
    runner = FinAgentTestRunner()
    
    try:
        report = runner.run_full_suite(
            suites=args.suites,
            verbose=args.verbose,
            with_coverage=not args.no_coverage
        )
        
        # Afficher rapport final
        runner.print_final_report(report)
        
        # Sauvegarder en JSON si demandé
        if args.save_json:
            runner.save_report_json(report)
        
        # Code de sortie basé sur conformité
        if "NON CONFORME" in report.compliance_status:
            print(f"\n❌ Tests non conformes")
            sys.exit(1)
        else:
            print(f"\n✅ Tests conformes")
            sys.exit(0)
            
    except KeyboardInterrupt:
        print(f"\n⚠️  Exécution interrompue par l'utilisateur")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Erreur critique: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()