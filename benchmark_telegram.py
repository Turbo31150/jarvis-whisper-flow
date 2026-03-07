#!/usr/bin/env python3
"""
JARVIS Benchmark — Test multi-question pipeline via cluster (M1/OL1).
Simule des requetes Telegram et mesure vitesse + qualite.

Usage:
    python benchmark_telegram.py              # 50 cycles
    python benchmark_telegram.py --cycles 200 # 200 cycles
    python benchmark_telegram.py --telegram   # Envoie vraiment via Telegram
"""

import asyncio
import json
import time
import sys
import os
import argparse
from pathlib import Path

# Fix Windows console encoding
if sys.platform == "win32":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from whisperflow.jarvis.cluster_bridge import cluster_race, query_m1, query_ol1
from whisperflow.jarvis.commander import Commander

# === TEST PROMPTS ===
TEST_PROMPTS = {
    "voice_commands": [
        "ouvre chrome",
        "volume a 50",
        "quelle heure est-il",
        "capture d'ecran",
        "cherche rapport pdf",
        "mode dictee",
        "minuteur 5 minutes",
        "note acheter du pain",
        "google intelligence artificielle",
        "batterie",
    ],
    "llm_questions": [
        "Explique le machine learning en 2 phrases",
        "Quelle est la capitale de l'Australie",
        "Comment fonctionne un GPU",
        "Donne moi une recette rapide de pates",
        "Quel temps fait-il en general a Paris en mars",
        "C'est quoi le deep learning",
        "Explique Docker simplement",
        "Qui a invente Internet",
        "Combien de planetes dans le systeme solaire",
        "Quel langage pour le web frontend",
    ],
    "mixed_actions": [
        "lance le terminal",
        "monte le volume",
        "youtube tutoriel python",
        "cree un fichier test.txt",
        "liste les processus",
        "traduis en anglais bonjour le monde",
        "calcule 42 fois 13",
        "pile ou face",
        "agenda ajoute reunion demain 10h",
        "genere un mot de passe",
    ],
    "edge_cases": [
        "euh... ouvre truc la",
        "jarviss aide moi",
        "fais un truc cool",
        "repete",
        "",
        "a",
        "merci beaucoup jarvis",
    ],
}


def score_response(prompt: str, response: str, latency: float) -> dict:
    """Score une reponse: qualite + vitesse."""
    score = 0
    issues = []

    if not response:
        return {"score": 0, "issues": ["empty_response"], "latency": latency}

    # French markers
    fr_markers = ["je", "le", "la", "de", "du", "un", "est", "les", "des", "en", "pour"]
    fr_count = sum(1 for m in fr_markers if f" {m} " in f" {response.lower()} ")
    if fr_count >= 2:
        score += 25
    elif fr_count >= 1:
        score += 15
    else:
        issues.append("not_french")

    # Length check (2-200 words ideal)
    words = len(response.split())
    if 5 <= words <= 200:
        score += 25
    elif 2 <= words <= 300:
        score += 15
    else:
        issues.append(f"length_{words}w")

    # No thinking tokens leaked
    if "<think>" in response or "</think>" in response:
        issues.append("thinking_leak")
    else:
        score += 15

    # No prompt regurgitation
    if "Tu es JARVIS" in response or "/nothink" in response:
        issues.append("prompt_leak")
    else:
        score += 10

    # Speed bonus
    if latency < 2.0:
        score += 25
    elif latency < 5.0:
        score += 15
    elif latency < 10.0:
        score += 5
    else:
        issues.append(f"slow_{latency:.1f}s")

    return {"score": min(score, 100), "issues": issues, "latency": latency}


async def run_benchmark(cycles: int = 50, verbose: bool = False):
    """Run benchmark cycles."""
    commander = Commander()

    # Collect all prompts
    all_prompts = []
    for category, prompts in TEST_PROMPTS.items():
        for p in prompts:
            all_prompts.append((category, p))

    results = {
        "total": 0,
        "success": 0,
        "errors": 0,
        "scores": [],
        "latencies": [],
        "by_category": {},
        "by_agent": {"M1": 0, "OL1": 0, "NONE": 0, "commander": 0},
    }

    prompt_idx = 0
    for cycle in range(cycles):
        category, prompt = all_prompts[prompt_idx % len(all_prompts)]
        prompt_idx += 1
        results["total"] += 1

        if category not in results["by_category"]:
            results["by_category"][category] = {"total": 0, "success": 0, "avg_score": 0, "scores": []}
        results["by_category"][category]["total"] += 1

        try:
            # Step 1: Try Commander (local regex parsing)
            t0 = time.time()
            cmd = commander.parse(prompt) if prompt else None

            if cmd and cmd.intent != "unknown":
                latency = time.time() - t0
                results["success"] += 1
                results["by_agent"]["commander"] += 1
                sc = {"score": 95, "issues": [], "latency": latency}
                results["scores"].append(sc["score"])
                results["latencies"].append(latency)
                results["by_category"][category]["success"] += 1
                results["by_category"][category]["scores"].append(sc["score"])
                if verbose:
                    print(f"  [{cycle+1:3d}] CMD  {latency:.2f}s | {cmd.intent:25s} | {prompt[:40]}")
                continue

            # Step 2: Cluster race for unknown commands
            t0 = time.time()
            reply, agent = await cluster_race(prompt)
            latency = time.time() - t0

            if reply:
                results["success"] += 1
                results["by_agent"][agent] += 1
                sc = score_response(prompt, reply, latency)
                results["scores"].append(sc["score"])
                results["latencies"].append(latency)
                results["by_category"][category]["success"] += 1
                results["by_category"][category]["scores"].append(sc["score"])
                if verbose:
                    print(f"  [{cycle+1:3d}] [{agent:3s}] {latency:.2f}s | {sc['score']:3d}/100 | {prompt[:30]:30s} → {reply[:50]}")
            else:
                results["errors"] += 1
                results["by_agent"]["NONE"] += 1
                if verbose:
                    print(f"  [{cycle+1:3d}] FAIL {prompt[:40]}")

        except Exception as e:
            results["errors"] += 1
            if verbose:
                print(f"  [{cycle+1:3d}] ERR  {e}")

        # Progress
        if (cycle + 1) % 10 == 0 and not verbose:
            avg_lat = sum(results["latencies"][-10:]) / max(len(results["latencies"][-10:]), 1)
            print(f"  Cycle {cycle+1}/{cycles} | Success: {results['success']}/{results['total']} | Avg latency: {avg_lat:.2f}s")

    # Final report
    avg_score = sum(results["scores"]) / max(len(results["scores"]), 1)
    avg_lat = sum(results["latencies"]) / max(len(results["latencies"]), 1)
    min_lat = min(results["latencies"]) if results["latencies"] else 0
    max_lat = max(results["latencies"]) if results["latencies"] else 0

    print("\n" + "=" * 60)
    print(f"  JARVIS BENCHMARK — {cycles} cycles")
    print("=" * 60)
    print(f"  Total: {results['total']} | Success: {results['success']} | Errors: {results['errors']}")
    print(f"  Avg Score: {avg_score:.1f}/100 | Avg Latency: {avg_lat:.2f}s")
    print(f"  Min Latency: {min_lat:.2f}s | Max Latency: {max_lat:.2f}s")
    print(f"\n  Agents: Commander={results['by_agent']['commander']} | M1={results['by_agent']['M1']} | OL1={results['by_agent']['OL1']} | FAIL={results['by_agent']['NONE']}")

    print("\n  Par categorie:")
    for cat, data in results["by_category"].items():
        cat_avg = sum(data["scores"]) / max(len(data["scores"]), 1)
        print(f"    {cat:20s}: {data['success']}/{data['total']} | Avg: {cat_avg:.1f}/100")

    print("=" * 60)

    return results


def main():
    parser = argparse.ArgumentParser(description="JARVIS Benchmark")
    parser.add_argument("--cycles", type=int, default=50, help="Number of test cycles")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()

    print(f"\nJARVIS Benchmark — {args.cycles} cycles")
    print("-" * 40)
    asyncio.run(run_benchmark(args.cycles, args.verbose))


if __name__ == "__main__":
    main()
