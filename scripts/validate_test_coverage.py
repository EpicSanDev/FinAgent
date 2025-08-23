#!/usr/bin/env python3
"""
Script de Validation de Couverture de Tests

Ce script valide que la couverture de code atteint les objectifs
requis (minimum 85%) et génère un rapport détaillé de la couverture.
"""

import os
import sys
import subprocess
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
import argparse


@dataclass
class CoverageResult:
    """Résultat de couverture pour un module"""
    module_name: str
    line_coverage: float
    branch_coverage: float
    missing_lines: List[int]
    total_lines: int
    covered_lines: int


@dataclass
class CoverageSummary:
    """Résumé global de couverture"""
    overall_coverage: float
    total_modules: int
    modules_above_threshold: int
    modules_below_threshold: List[str]
    target_coverage: float
    compliance: bool


class TestCoverageValidator:
    """Validateur de couverture de tests"""
    
    def __init__(self, target_coverage: float = 0.85):
        self.target_coverage = target_coverage
        self.project_root = Path(__file__).parent.parent
        self.finagent_dir = self.project_root / "finagent"
        self.tests_dir = self.project_root / "tests"
        
        # Vérifier que les répertoires existent
        if not self.finagent_dir.exists():
            print(f"⚠️  Répertoire finagent non trouvé: {self.finagent_dir}")
        if not self.tests_dir.exists():
            print(f"⚠️  Répertoire tests non trouvé: {self.tests_dir}")
    
    def run_coverage_analysis(self) -> Dict[str, Any]:
        """Exécute l'analyse de couverture avec pytest-cov"""
        print("🔍 Exécution de l'analyse de couverture...")
        
        # Commande pour exécuter les tests avec couverture
        cmd = [
            sys.executable, "-m", "pytest",
            "--cov=finagent",
            "--cov-report=xml:coverage.xml",
            "--cov-report=json:coverage.json",
            "--cov-report=html:htmlcov",
            "--cov-report=term-missing",
            "--cov-fail-under=85",
            "tests/",
            "-v"
        ]
        
        try:
            # Exécuter depuis le répertoire du projet
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes max
            )
            
            print(f"   Code de retour: {result.returncode}")
            
            if result.stdout:
                print("📊 Sortie coverage:")
                # Filtrer les lignes de couverture importantes
                coverage_lines = [
                    line for line in result.stdout.split('\n')
                    if any(keyword in line for keyword in [
                        'TOTAL', 'finagent/', '====', 'coverage'
                    ])
                ]
                for line in coverage_lines[-20:]:  # Dernières 20 lignes pertinentes
                    print(f"   {line}")
            
            if result.stderr:
                print("⚠️  Erreurs:")
                for line in result.stderr.split('\n')[-10:]:  # Dernières 10 lignes d'erreur
                    if line.strip():
                        print(f"   {line}")
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
            
        except subprocess.TimeoutExpired:
            print("❌ Timeout lors de l'exécution des tests")
            return {
                "success": False,
                "error": "Timeout après 5 minutes"
            }
        except Exception as e:
            print(f"❌ Erreur lors de l'exécution: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def parse_coverage_json(self) -> Dict[str, CoverageResult]:
        """Parse le fichier JSON de couverture"""
        coverage_file = self.project_root / "coverage.json"
        
        if not coverage_file.exists():
            print(f"⚠️  Fichier coverage.json non trouvé: {coverage_file}")
            return {}
        
        try:
            with open(coverage_file, 'r') as f:
                coverage_data = json.load(f)
            
            results = {}
            files_data = coverage_data.get("files", {})
            
            for file_path, file_data in files_data.items():
                # Ne prendre que les fichiers finagent
                if "finagent" not in file_path:
                    continue
                
                # Extraire nom du module
                module_name = file_path.replace(str(self.project_root) + "/", "")
                
                # Calculer métriques
                executed_lines = file_data.get("executed_lines", [])
                missing_lines = file_data.get("missing_lines", [])
                total_lines = len(executed_lines) + len(missing_lines)
                covered_lines = len(executed_lines)
                
                line_coverage = (covered_lines / total_lines * 100) if total_lines > 0 else 0
                
                # Coverage de branche (si disponible)
                branch_coverage = 0.0
                if "executed_branches" in file_data and "missing_branches" in file_data:
                    exec_branches = len(file_data["executed_branches"])
                    miss_branches = len(file_data["missing_branches"])
                    total_branches = exec_branches + miss_branches
                    branch_coverage = (exec_branches / total_branches * 100) if total_branches > 0 else 0
                
                results[module_name] = CoverageResult(
                    module_name=module_name,
                    line_coverage=line_coverage,
                    branch_coverage=branch_coverage,
                    missing_lines=missing_lines,
                    total_lines=total_lines,
                    covered_lines=covered_lines
                )
            
            return results
            
        except Exception as e:
            print(f"❌ Erreur parsing coverage.json: {e}")
            return {}
    
    def analyze_coverage_results(self, coverage_results: Dict[str, CoverageResult]) -> CoverageSummary:
        """Analyse les résultats de couverture"""
        if not coverage_results:
            return CoverageSummary(
                overall_coverage=0.0,
                total_modules=0,
                modules_above_threshold=0,
                modules_below_threshold=[],
                target_coverage=self.target_coverage,
                compliance=False
            )
        
        # Calculer couverture globale
        total_lines = sum(r.total_lines for r in coverage_results.values())
        covered_lines = sum(r.covered_lines for r in coverage_results.values())
        overall_coverage = (covered_lines / total_lines * 100) if total_lines > 0 else 0
        
        # Analyser conformité par module
        modules_above = 0
        modules_below = []
        threshold_percent = self.target_coverage * 100
        
        for module_name, result in coverage_results.items():
            if result.line_coverage >= threshold_percent:
                modules_above += 1
            else:
                modules_below.append(module_name)
        
        return CoverageSummary(
            overall_coverage=overall_coverage,
            total_modules=len(coverage_results),
            modules_above_threshold=modules_above,
            modules_below_threshold=modules_below,
            target_coverage=self.target_coverage,
            compliance=overall_coverage >= threshold_percent
        )
    
    def generate_detailed_report(self, coverage_results: Dict[str, CoverageResult], 
                               summary: CoverageSummary) -> str:
        """Génère un rapport détaillé"""
        report = []
        report.append("=" * 80)
        report.append("🧪 RAPPORT DE COUVERTURE DE TESTS - FINAGENT")
        report.append("=" * 80)
        report.append("")
        
        # Résumé global
        report.append("📊 RÉSUMÉ GLOBAL")
        report.append("-" * 40)
        report.append(f"Couverture globale: {summary.overall_coverage:.1f}%")
        report.append(f"Objectif: {summary.target_coverage:.1%}")
        report.append(f"Conformité: {'✅ OUI' if summary.compliance else '❌ NON'}")
        report.append(f"Modules totaux: {summary.total_modules}")
        report.append(f"Modules conformes: {summary.modules_above_threshold}")
        report.append(f"Modules non conformes: {len(summary.modules_below_threshold)}")
        report.append("")
        
        # Détail par module
        if coverage_results:
            report.append("📋 DÉTAIL PAR MODULE")
            report.append("-" * 40)
            
            # Trier par couverture (du plus faible au plus élevé)
            sorted_modules = sorted(
                coverage_results.items(),
                key=lambda x: x[1].line_coverage
            )
            
            for module_name, result in sorted_modules:
                status = "✅" if result.line_coverage >= self.target_coverage * 100 else "❌"
                report.append(f"{status} {module_name}")
                report.append(f"   Couverture lignes: {result.line_coverage:.1f}%")
                report.append(f"   Lignes totales: {result.total_lines}")
                report.append(f"   Lignes couvertes: {result.covered_lines}")
                
                if result.missing_lines:
                    missing_ranges = self._compress_line_ranges(result.missing_lines)
                    report.append(f"   Lignes manquantes: {missing_ranges}")
                
                if result.branch_coverage > 0:
                    report.append(f"   Couverture branches: {result.branch_coverage:.1f}%")
                
                report.append("")
        
        # Modules non conformes
        if summary.modules_below_threshold:
            report.append("⚠️  MODULES NÉCESSITANT ATTENTION")
            report.append("-" * 40)
            for module in summary.modules_below_threshold:
                if module in coverage_results:
                    result = coverage_results[module]
                    gap = self.target_coverage * 100 - result.line_coverage
                    report.append(f"• {module}: {result.line_coverage:.1f}% (manque {gap:.1f}%)")
            report.append("")
        
        # Recommandations
        report.append("💡 RECOMMANDATIONS")
        report.append("-" * 40)
        
        if summary.compliance:
            report.append("✅ Couverture globale conforme!")
            report.append("• Maintenir la qualité des tests existants")
            report.append("• Ajouter des tests pour nouveaux développements")
        else:
            gap = self.target_coverage * 100 - summary.overall_coverage
            report.append(f"❌ Couverture insuffisante (manque {gap:.1f}%)")
            report.append("• Prioriser les modules avec faible couverture")
            report.append("• Ajouter tests unitaires pour code non couvert")
            report.append("• Réviser et améliorer tests existants")
        
        if len(summary.modules_below_threshold) > summary.total_modules * 0.3:
            report.append("• Plus de 30% des modules non conformes - révision générale recommandée")
        
        report.append("")
        report.append("=" * 80)
        
        return "\n".join(report)
    
    def _compress_line_ranges(self, lines: List[int]) -> str:
        """Compresse une liste de lignes en ranges"""
        if not lines:
            return ""
        
        sorted_lines = sorted(lines)
        ranges = []
        start = sorted_lines[0]
        end = sorted_lines[0]
        
        for i in range(1, len(sorted_lines)):
            if sorted_lines[i] == end + 1:
                end = sorted_lines[i]
            else:
                if start == end:
                    ranges.append(str(start))
                else:
                    ranges.append(f"{start}-{end}")
                start = end = sorted_lines[i]
        
        # Ajouter dernier range
        if start == end:
            ranges.append(str(start))
        else:
            ranges.append(f"{start}-{end}")
        
        return ", ".join(ranges)
    
    def save_report(self, report: str, filename: str = "coverage_report.txt"):
        """Sauvegarde le rapport"""
        report_path = self.project_root / filename
        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"📄 Rapport sauvegardé: {report_path}")
        except Exception as e:
            print(f"❌ Erreur sauvegarde rapport: {e}")
    
    def validate_coverage(self) -> bool:
        """Validation complète de la couverture"""
        print("🧪 VALIDATION DE LA COUVERTURE DE TESTS")
        print("=" * 60)
        
        # 1. Exécuter analyse couverture
        coverage_run = self.run_coverage_analysis()
        
        if not coverage_run.get("success", False):
            print("❌ Échec de l'analyse de couverture")
            return False
        
        # 2. Parser résultats
        print("\n📊 Parsing des résultats...")
        coverage_results = self.parse_coverage_json()
        
        if not coverage_results:
            print("⚠️  Aucun résultat de couverture trouvé")
            return False
        
        # 3. Analyser conformité
        print("🔍 Analyse de conformité...")
        summary = self.analyze_coverage_results(coverage_results)
        
        # 4. Générer rapport
        print("📄 Génération du rapport...")
        report = self.generate_detailed_report(coverage_results, summary)
        
        # 5. Afficher résultats
        print("\n" + report)
        
        # 6. Sauvegarder rapport
        self.save_report(report)
        
        # 7. Retourner conformité
        return summary.compliance


def main():
    """Point d'entrée principal"""
    parser = argparse.ArgumentParser(description="Valide la couverture de tests FinAgent")
    parser.add_argument(
        "--target", 
        type=float, 
        default=0.85,
        help="Couverture cible (défaut: 0.85)"
    )
    parser.add_argument(
        "--fail-under",
        action="store_true",
        help="Échouer si couverture insuffisante"
    )
    
    args = parser.parse_args()
    
    validator = TestCoverageValidator(target_coverage=args.target)
    is_compliant = validator.validate_coverage()
    
    if args.fail_under and not is_compliant:
        print(f"\n❌ ÉCHEC: Couverture inférieure à {args.target:.1%}")
        sys.exit(1)
    elif is_compliant:
        print(f"\n✅ SUCCÈS: Couverture conforme à {args.target:.1%}")
        sys.exit(0)
    else:
        print(f"\n⚠️  ATTENTION: Couverture inférieure à {args.target:.1%}")
        sys.exit(0)


if __name__ == "__main__":
    main()