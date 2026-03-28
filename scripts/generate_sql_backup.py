"""Generate SQL backup of the JARVIS system."""
import re as re_mod
from datetime import datetime

from whisperflow.jarvis.commander import COMMAND_PATTERNS
from whisperflow.jarvis.jarvis_core import Jarvis
from whisperflow.jarvis.skills.abbreviations import _ABBREVIATIONS

j = Jarvis()

lines = []
now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Header
lines.append("-- ============================================")
lines.append("-- JARVIS Voice Assistant - SQL Backup")
lines.append(f"-- Date: {now}")
lines.append(f"-- Patterns: {len(COMMAND_PATTERNS)}")
lines.append(f"-- Handlers: {len(j.commander._handlers)}")
lines.append("-- Cycles: 1-250 (complete)")
lines.append("-- ============================================")
lines.append("")

# Drop
for t in ["training_cycles", "handlers", "patterns", "skills", "abbreviations"]:
    lines.append(f"DROP TABLE IF EXISTS {t};")
lines.append("")

# Schema
lines.append("""CREATE TABLE skills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    class_name TEXT NOT NULL UNIQUE,
    skill_type TEXT NOT NULL DEFAULT 'skill',
    created_at TEXT NOT NULL
);""")
lines.append("")

lines.append("""CREATE TABLE patterns (
    id INTEGER PRIMARY KEY,
    regex TEXT NOT NULL,
    intent TEXT NOT NULL,
    section TEXT,
    priority_order INTEGER NOT NULL
);""")
lines.append("")

lines.append("""CREATE TABLE handlers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    intent TEXT NOT NULL UNIQUE,
    method_name TEXT NOT NULL,
    skill_class TEXT NOT NULL
);""")
lines.append("")

lines.append("""CREATE TABLE training_cycles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cycle_range TEXT NOT NULL,
    test_file TEXT NOT NULL,
    test_count INTEGER NOT NULL,
    skills_added TEXT,
    commit_hash TEXT,
    created_at TEXT NOT NULL
);""")
lines.append("")

lines.append("""CREATE TABLE abbreviations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    abbr TEXT NOT NULL UNIQUE,
    definition TEXT NOT NULL,
    category TEXT
);""")
lines.append("")

# Indexes
lines.append("CREATE INDEX idx_patterns_intent ON patterns(intent);")
lines.append("CREATE INDEX idx_handlers_intent ON handlers(intent);")
lines.append("CREATE INDEX idx_handlers_skill ON handlers(skill_class);")
lines.append("CREATE INDEX idx_abbreviations_abbr ON abbreviations(abbr);")
lines.append("")

# Skills data
lines.append("-- === SKILLS DATA ===")
skill_classes = set()
for intent, handler in j.commander._handlers.items():
    if hasattr(handler, "__self__"):
        cls = handler.__self__.__class__.__name__
        if cls != "Jarvis":
            skill_classes.add(cls)

for cls in sorted(skill_classes):
    stype = "agent" if "Agent" in cls else "skill"
    esc = cls.replace("'", "''")
    lines.append(f"INSERT INTO skills (class_name, skill_type, created_at) VALUES ('{esc}', '{stype}', '{now}');")
lines.append("")

# Section mapping
def get_section(intent):
    prefix_map = {
        "dictation_": "DICTEE", "vdesktop_": "BUREAUX VIRTUELS",
        "media_": "MEDIA", "process_": "PROCESSUS",
        "network_": "RESEAU", "power_": "ALIMENTATION",
        "display_": "AFFICHAGE", "audio_": "AUDIO",
        "software_": "LOGICIELS", "clipboard_": "PRESSE-PAPIERS",
        "navigate_": "NAVIGATION", "web_": "WEB",
        "timer_": "MINUTEURS", "note_": "NOTES",
        "unit_": "CONVERSION", "calc_": "CALCULATRICE",
        "translate_": "TRADUCTION", "pomodoro_": "POMODORO",
        "snapshot_": "SNAPSHOT", "password_": "MOT DE PASSE",
        "date_": "DATES", "text_": "OUTILS TEXTE",
        "fav_": "FAVORIS", "stopwatch_": "CHRONOMETRE",
        "agenda_": "AGENDA", "random_": "ALEATOIRE",
        "abbrev_": "ABREVIATIONS", "automation_": "AUTOMATISATION",
        "app_": "APPLICATIONS", "file_": "FICHIERS",
        "window_": "FENETRES", "jarvis_": "JARVIS",
    }
    for prefix, section in prefix_map.items():
        if intent.startswith(prefix):
            return section
    if intent.startswith("system_"):
        sys_map = {
            "system_resources": "PROCESSUS", "system_top_cpu": "PROCESSUS",
            "system_disk": "PROCESSUS", "system_uptime": "PROCESSUS",
            "system_gpu": "PROCESSUS", "system_hardware": "PROCESSUS",
        }
        return sys_map.get(intent, "SYSTEME")
    return "GENERAL"

# Patterns data
lines.append("-- === PATTERNS DATA ===")
for i, (regex, intent) in enumerate(COMMAND_PATTERNS):
    esc_regex = regex.replace("'", "''")
    section = get_section(intent)
    lines.append(
        f"INSERT INTO patterns (id, regex, intent, section, priority_order) "
        f"VALUES ({i+1}, '{esc_regex}', '{intent}', '{section}', {i+1});"
    )
lines.append("")

# Handlers data
lines.append("-- === HANDLERS DATA ===")
for intent, handler in j.commander._handlers.items():
    name = handler.__name__ if hasattr(handler, "__name__") else str(handler)
    if hasattr(handler, "__self__"):
        cls = handler.__self__.__class__.__name__
    else:
        cls = "function"
    esc_i = intent.replace("'", "''")
    esc_n = name.replace("'", "''")
    esc_c = cls.replace("'", "''")
    lines.append(
        f"INSERT INTO handlers (intent, method_name, skill_class) "
        f"VALUES ('{esc_i}', '{esc_n}', '{esc_c}');"
    )
lines.append("")

# Training cycles
lines.append("-- === TRAINING CYCLES ===")
cycles = [
    ("1-50", "test_jarvis_simulation + test_jarvis_full_training + test_jarvis_50_cycles", 583,
     "AppLauncher, SystemControl, WindowManager, FileManager, WebBrowser, MediaControl, ClipboardManager, ProcessManager, NetworkControl, PowerDisplay, SoftwareManager",
     "a3aae3c"),
    ("51-100", "test_jarvis_100_cycles", 251,
     "DictationAgent, VirtualDesktop, TimerReminder, QuickNotes, Calculator, Translator, UnitConverter",
     "eefff6e"),
    ("101-150", "test_jarvis_150_cycles", 148,
     "PomodoroSkill, SystemSnapshotSkill",
     "b4fcc82"),
    ("151-200", "test_jarvis_200_cycles", 150,
     "PasswordGenerator, DateCalculator, TextTools, Favorites",
     "837a236"),
    ("201-250", "test_jarvis_250_cycles", 127,
     "Stopwatch, Agenda, RandomPicker, Abbreviations",
     "2bb924a"),
]
for cr, tf, tc, sa, ch in cycles:
    lines.append(
        f"INSERT INTO training_cycles (cycle_range, test_file, test_count, skills_added, commit_hash, created_at) "
        f"VALUES ('{cr}', '{tf}', {tc}, '{sa}', '{ch}', '{now}');"
    )
lines.append("")

# Abbreviations
lines.append("-- === ABBREVIATIONS DATA ===")
cat_map = {}
for a in ["ia","api","cpu","gpu","ram","ssd","hdd","usb","html","css","sql","url","ip","http","https","dns","vpn","pdf","json","xml","ide","cli","gui","os","iot","ml","llm","nlp"]:
    cat_map[a] = "Informatique"
for a in ["rh","pme","tva","smic","bac","bts","dut","cdi","cdd","cv","rsa","sncf","ratp"]:
    cat_map[a] = "General FR"
for a in ["onu","ue","otan","nasa","oms","fmi"]:
    cat_map[a] = "Organisations"
for a in ["km","kg","mb","gb","tb"]:
    cat_map[a] = "Unites"

for abbr, defn in _ABBREVIATIONS.items():
    esc_a = abbr.replace("'", "''")
    esc_d = defn.replace("'", "''")
    cat = cat_map.get(abbr, "Autre")
    lines.append(
        f"INSERT INTO abbreviations (abbr, definition, category) "
        f"VALUES ('{esc_a}', '{esc_d}', '{cat}');"
    )
lines.append("")

# Stats
lines.append(f"-- Total patterns: {len(COMMAND_PATTERNS)}")
lines.append(f"-- Total handlers: {len(j.commander._handlers)}")
lines.append(f"-- Total skill classes: {len(skill_classes)}")
lines.append(f"-- Total abbreviations: {len(_ABBREVIATIONS)}")
lines.append("-- Total tests: 1259")
lines.append("-- Training cycles: 250")
lines.append("-- END OF BACKUP")

output = "\n".join(lines)
with open("jarvis_backup.sql", "w", encoding="utf-8") as f:
    f.write(output)

print(f"SQL backup: jarvis_backup.sql")
print(f"  {len(COMMAND_PATTERNS)} patterns")
print(f"  {len(j.commander._handlers)} handlers")
print(f"  {len(skill_classes)} skill classes")
print(f"  {len(_ABBREVIATIONS)} abbreviations")
print(f"  5 training cycles (250 total)")
print(f"  {len(lines)} lines SQL")
