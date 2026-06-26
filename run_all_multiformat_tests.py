import os
import sys
import time
import json
import subprocess
from pathlib import Path
from datetime import datetime

print("="*80)
print("TESTS MULTIFORMAT - 4 SOLUTIONS OCR")
print("="*80)

results_dir = Path("test_results")
results_dir.mkdir(exist_ok=True)

test_files = [
    {"name": "Docling", "file": "test_docling_multiformat.py"},
    {"name": "PaddleOCR", "file": "test_paddleocr_multiformat.py"},
    {"name": "EasyOCR", "file": "test_easyocr_multiformat.py"},
    {"name": "TrOCR", "file": "test_trocr_multiformat.py"}
]

available_tests = [t for t in test_files if Path(t["file"]).exists()]

if not available_tests:
    print("Aucun fichier de test trouve")
    sys.exit(1)

print(f"\nTests disponibles: {len(available_tests)}/4")
print("Temps estime: 15-35 minutes\n")

test_results = []
global_start = time.time()

for i, test in enumerate(available_tests, 1):
    print(f"\n[{i}/{len(available_tests)}] {test['name']}...")
    test_start = time.time()
    
    try:
        result = subprocess.run(
            [sys.executable, test["file"]],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        
        duration = time.time() - test_start
        status = "success" if result.returncode == 0 else "failed"
        
        test_results.append({
            "name": test["name"],
            "file": test["file"],
            "status": status,
            "duration": round(duration, 2),
            "returncode": result.returncode
        })
        
        print(f"  {status.upper()} en {duration:.0f}s")
        
    except Exception as e:
        duration = time.time() - test_start
        test_results.append({
            "name": test["name"],
            "file": test["file"],
            "status": "error",
            "duration": round(duration, 2),
            "error": str(e)
        })
        print(f"  ERROR: {e}")
    
    if i < len(available_tests):
        time.sleep(2)

global_duration = time.time() - global_start

print("\n" + "="*80)
print("RESULTATS")
print("="*80)

successful = [r for r in test_results if r["status"] == "success"]
print(f"\nTemps total: {global_duration:.0f}s")
print(f"Tests reussis: {len(successful)}/{len(test_results)}")
print(f"Taux de reussite: {len(successful)/len(test_results)*100:.1f}%\n")

for test in test_results:
    icon = "✓" if test["status"] == "success" else "✗"
    print(f"{icon} {test['name']}: {test['status']} ({test['duration']:.0f}s)")

result_files = list(results_dir.glob("*_multiformat_results.json"))
detailed_results = []

for result_file in result_files:
    try:
        with open(result_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        detailed_results.append({
            "tool": data.get("tool", "Unknown"),
            "success_rate": data.get("success_rate", 0),
            "total_tests": data.get("total_tests", 0)
        })
    except:
        pass

if detailed_results:
    print("\nPerformances:")
    detailed_results.sort(key=lambda x: x["success_rate"], reverse=True)
    for i, r in enumerate(detailed_results, 1):
        print(f"{i}. {r['tool']}: {r['success_rate']:.1f}%")

global_report = {
    "report_date": datetime.now().isoformat(),
    "total_time": global_duration,
    "tests_executed": len(test_results),
    "successful": len(successful),
    "success_rate": len(successful)/len(test_results)*100 if test_results else 0,
    "results": test_results,
    "detailed": detailed_results
}

report_file = results_dir / "global_multiformat_report.json"
with open(report_file, 'w', encoding='utf-8') as f:
    json.dump(global_report, f, indent=2, ensure_ascii=False)

print(f"\nRapport sauvegarde: {report_file}")
print("\n" + "="*80)
