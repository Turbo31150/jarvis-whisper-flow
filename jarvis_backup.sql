-- ============================================
-- JARVIS Voice Assistant - SQL Backup
-- Date: 2026-02-17 12:58:54
-- Patterns: 147
-- Handlers: 140
-- Cycles: 1-250 (complete)
-- ============================================

DROP TABLE IF EXISTS training_cycles;
DROP TABLE IF EXISTS handlers;
DROP TABLE IF EXISTS patterns;
DROP TABLE IF EXISTS skills;
DROP TABLE IF EXISTS abbreviations;

CREATE TABLE skills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    class_name TEXT NOT NULL UNIQUE,
    skill_type TEXT NOT NULL DEFAULT 'skill',
    created_at TEXT NOT NULL
);

CREATE TABLE patterns (
    id INTEGER PRIMARY KEY,
    regex TEXT NOT NULL,
    intent TEXT NOT NULL,
    section TEXT,
    priority_order INTEGER NOT NULL
);

CREATE TABLE handlers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    intent TEXT NOT NULL UNIQUE,
    method_name TEXT NOT NULL,
    skill_class TEXT NOT NULL
);

CREATE TABLE training_cycles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cycle_range TEXT NOT NULL,
    test_file TEXT NOT NULL,
    test_count INTEGER NOT NULL,
    skills_added TEXT,
    commit_hash TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE abbreviations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    abbr TEXT NOT NULL UNIQUE,
    definition TEXT NOT NULL,
    category TEXT
);

CREATE INDEX idx_patterns_intent ON patterns(intent);
CREATE INDEX idx_handlers_intent ON handlers(intent);
CREATE INDEX idx_handlers_skill ON handlers(skill_class);
CREATE INDEX idx_abbreviations_abbr ON abbreviations(abbr);

-- === SKILLS DATA ===
INSERT INTO skills (class_name, skill_type, created_at) VALUES ('AbbreviationsSkill', 'skill', '2026-02-17 12:58:54');
INSERT INTO skills (class_name, skill_type, created_at) VALUES ('AgendaSkill', 'skill', '2026-02-17 12:58:54');
INSERT INTO skills (class_name, skill_type, created_at) VALUES ('AppLauncherSkill', 'skill', '2026-02-17 12:58:54');
INSERT INTO skills (class_name, skill_type, created_at) VALUES ('AutomationAgent', 'agent', '2026-02-17 12:58:54');
INSERT INTO skills (class_name, skill_type, created_at) VALUES ('CalculatorSkill', 'skill', '2026-02-17 12:58:54');
INSERT INTO skills (class_name, skill_type, created_at) VALUES ('ClipboardManagerSkill', 'skill', '2026-02-17 12:58:54');
INSERT INTO skills (class_name, skill_type, created_at) VALUES ('DateCalculatorSkill', 'skill', '2026-02-17 12:58:54');
INSERT INTO skills (class_name, skill_type, created_at) VALUES ('DictationAgent', 'agent', '2026-02-17 12:58:54');
INSERT INTO skills (class_name, skill_type, created_at) VALUES ('FavoritesSkill', 'skill', '2026-02-17 12:58:54');
INSERT INTO skills (class_name, skill_type, created_at) VALUES ('FileManagerSkill', 'skill', '2026-02-17 12:58:54');
INSERT INTO skills (class_name, skill_type, created_at) VALUES ('MediaControlSkill', 'skill', '2026-02-17 12:58:54');
INSERT INTO skills (class_name, skill_type, created_at) VALUES ('NavigationAgent', 'agent', '2026-02-17 12:58:54');
INSERT INTO skills (class_name, skill_type, created_at) VALUES ('NetworkControlSkill', 'skill', '2026-02-17 12:58:54');
INSERT INTO skills (class_name, skill_type, created_at) VALUES ('PasswordGeneratorSkill', 'skill', '2026-02-17 12:58:54');
INSERT INTO skills (class_name, skill_type, created_at) VALUES ('PomodoroSkill', 'skill', '2026-02-17 12:58:54');
INSERT INTO skills (class_name, skill_type, created_at) VALUES ('PowerDisplaySkill', 'skill', '2026-02-17 12:58:54');
INSERT INTO skills (class_name, skill_type, created_at) VALUES ('ProcessManagerSkill', 'skill', '2026-02-17 12:58:54');
INSERT INTO skills (class_name, skill_type, created_at) VALUES ('QuickNotesSkill', 'skill', '2026-02-17 12:58:54');
INSERT INTO skills (class_name, skill_type, created_at) VALUES ('RandomPickerSkill', 'skill', '2026-02-17 12:58:54');
INSERT INTO skills (class_name, skill_type, created_at) VALUES ('SoftwareManagerSkill', 'skill', '2026-02-17 12:58:54');
INSERT INTO skills (class_name, skill_type, created_at) VALUES ('StopwatchSkill', 'skill', '2026-02-17 12:58:54');
INSERT INTO skills (class_name, skill_type, created_at) VALUES ('SystemControlSkill', 'skill', '2026-02-17 12:58:54');
INSERT INTO skills (class_name, skill_type, created_at) VALUES ('SystemSnapshotSkill', 'skill', '2026-02-17 12:58:54');
INSERT INTO skills (class_name, skill_type, created_at) VALUES ('TextToolsSkill', 'skill', '2026-02-17 12:58:54');
INSERT INTO skills (class_name, skill_type, created_at) VALUES ('TimerReminderSkill', 'skill', '2026-02-17 12:58:54');
INSERT INTO skills (class_name, skill_type, created_at) VALUES ('TranslatorSkill', 'skill', '2026-02-17 12:58:54');
INSERT INTO skills (class_name, skill_type, created_at) VALUES ('UnitConverterSkill', 'skill', '2026-02-17 12:58:54');
INSERT INTO skills (class_name, skill_type, created_at) VALUES ('VirtualDesktopSkill', 'skill', '2026-02-17 12:58:54');
INSERT INTO skills (class_name, skill_type, created_at) VALUES ('WebBrowserSkill', 'skill', '2026-02-17 12:58:54');
INSERT INTO skills (class_name, skill_type, created_at) VALUES ('WindowManagerSkill', 'skill', '2026-02-17 12:58:54');

-- === PATTERNS DATA ===
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (1, '(?:mode\s+dictée|dictation\s+mode|commence\s+à\s+écrire|écris)', 'dictation_start', 'DICTEE', 1);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (2, '(?:arrête\s+la\s+dictée|stop\s+dictation|fin\s+de\s+dictée|arrête\s+d''écrire)', 'dictation_stop', 'DICTEE', 2);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (3, '(?:nouvelle\s+ligne|new\s+line|à\s+la\s+ligne|retour\s+à\s+la\s+ligne)', 'dictation_newline', 'DICTEE', 3);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (4, '(?:\bpoint\s+final\b|\bpoint\s*$)', 'dictation_period', 'DICTEE', 4);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (5, '(?:nouveau\s+bureau\s+virtuel|new\s+desktop|cr[ée]+\s+un\s+bureau)', 'vdesktop_new', 'BUREAUX VIRTUELS', 5);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (6, '(?:ferme\s+(?:le\s+)?bureau\s+virtuel|close\s+desktop)', 'vdesktop_close', 'BUREAUX VIRTUELS', 6);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (7, '(?:bureau\s+virtuel\s+(?:pr[ée]c[ée]dent|gauche)|desktop\s+left)', 'vdesktop_left', 'BUREAUX VIRTUELS', 7);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (8, '(?:bureau\s+virtuel\s+(?:suivant|droite)|desktop\s+right)', 'vdesktop_right', 'BUREAUX VIRTUELS', 8);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (9, '(?:vue\s+des?\s+t[âa]ches|task\s+view)', 'vdesktop_task_view', 'BUREAUX VIRTUELS', 9);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (10, '(?:arrête\s+la\s+musique|arrête\s+la\s+lecture)', 'media_pause', 'MEDIA', 10);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (11, '(?:play|lecture|joue|jouer)', 'media_play', 'MEDIA', 11);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (12, '(?:pause)', 'media_pause', 'MEDIA', 12);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (13, '(?:suivant|next|piste\s+suivante|chanson\s+suivante)', 'media_next', 'MEDIA', 13);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (14, '(?:\bprécédent\b|previous|piste\s+précédente|chanson\s+précédente)', 'media_previous', 'MEDIA', 14);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (15, '(?:liste|lister|list)\s+(?:les\s+)?(?:processus|process|tâches)', 'process_list', 'PROCESSUS', 15);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (16, '(?:tue|tuer|kill)\s+(?:le\s+)?(?:processus|process)\s+(.+)', 'process_kill', 'PROCESSUS', 16);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (17, '(?:ressources|resources|\bcharge\b|utilisation)\s*(?:système|system)?', 'system_resources', 'PROCESSUS', 17);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (18, '(?:utilisation\s+(?:cpu|ram|système|system))', 'system_resources', 'PROCESSUS', 18);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (19, '(?:cpu|processeur)\s*(?:usage|utilisation)?', 'system_top_cpu', 'PROCESSUS', 19);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (20, '(?:\bram\b|mémoire|memory)\s*(?:usage|utilisation)?', 'system_resources', 'PROCESSUS', 20);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (21, '(?:espace\s+disque|disk\s+space|stockage|disque\s+dur)', 'system_disk', 'PROCESSUS', 21);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (22, '(?:uptime|durée\s+de\s+fonctionnement|allumé\s+depuis)', 'system_uptime', 'PROCESSUS', 22);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (23, '(?:gpu|carte\s+graphique)', 'system_gpu', 'PROCESSUS', 23);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (24, '(?:matériel|hardware|specs|configuration\s+matérielle|info(?:rmation)?s?\s+(?:matériel(?:les?)?|système)|system\s+info)', 'system_hardware', 'PROCESSUS', 24);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (25, '(?:état\s+(?:du\s+)?réseau|network\s+status|interfaces?\s+réseau)', 'network_status', 'RESEAU', 25);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (26, '(?:(?:adresse\s+)?ip\s+publique|public\s+ip|ip\s+externe)', 'network_ip_public', 'RESEAU', 26);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (27, '(?:adresse\s+ip|ip\s+locale|mon\s+ip|ip\s+address)', 'network_ip', 'RESEAU', 27);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (28, '(?:ping)\s+(.+)', 'network_ping', 'RESEAU', 28);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (29, '(?:teste?\s+(?:la\s+)?connexion|connection\s+test)', 'network_ping', 'RESEAU', 29);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (30, '(?:réseaux?\s+wifi|wifi\s+(?:disponibles?|list)|scan\s+wifi)', 'network_wifi_list', 'RESEAU', 30);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (31, '(?:test\s+(?:de\s+)?débit|speed\s*test|vitesse\s+internet)', 'network_speed', 'RESEAU', 31);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (32, '(?:plan\s+(?:d'')?alimentation|power\s+plan)', 'power_plan', 'ALIMENTATION', 32);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (33, '(?:haute\s+performance|high\s+performance|mode\s+performance)', 'power_high_perf', 'ALIMENTATION', 33);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (34, '(?:mode\s+équilibré|balanced)', 'power_balanced', 'ALIMENTATION', 34);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (35, '(?:économie\s+d''énergie|power\s+saver|mode\s+éco)', 'power_saver', 'ALIMENTATION', 35);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (36, '(?:hibernation|hiberne|hibernate)', 'power_hibernate', 'ALIMENTATION', 36);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (37, '(?:résolution)\s*(?:d''écran)?', 'display_resolution', 'AFFICHAGE', 37);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (38, '(?:mode\s+nuit|night\s+(?:mode|light)|lumière\s+bleue|filtre\s+bleu)', 'display_night', 'AFFICHAGE', 38);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (39, '(?:paramètres?\s+(?:d'')?affichage|display\s+settings)', 'display_settings', 'AFFICHAGE', 39);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (40, '(?:paramètres?\s+(?:du?\s+)?son|audio\s+settings|paramètres?\s+audio)', 'audio_settings', 'AUDIO', 40);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (41, '(?:désinstalle|désinstaller|uninstall)\s+(?:le\s+)?(?:logiciel|programme)?\s*(.+)', 'software_uninstall', 'LOGICIELS', 41);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (42, '(?:installe|installer|install)\s+(?:le\s+)?(?:logiciel|programme|package)?\s*(.+)', 'software_install', 'LOGICIELS', 42);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (43, '(?:mets?\s+à\s+jour\s+tout|update\s+all|mise\s+à\s+jour\s+(?:de\s+)?tout)', 'software_update_all', 'LOGICIELS', 43);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (44, '(?:liste\s+(?:les\s+)?(?:logiciels|programmes)|installed\s+software|programmes?\s+installés?)', 'software_list', 'LOGICIELS', 44);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (45, '(?:mises?\s+à\s+jour|updates?\s+disponibles?|vérifi(?:e|er)\s+(?:les\s+)?mises?\s+à\s+jour)', 'software_check_updates', 'LOGICIELS', 45);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (46, '(?:lis\s+le\s+presse-papiers|read\s+clipboard|contenu\s+(?:du\s+)?presse-papiers)', 'clipboard_read', 'PRESSE-PAPIERS', 46);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (47, '(?:coupe\s+le\s+son)', 'system_mute', 'SYSTEME', 47);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (48, '(?:coupe|couper|\bcut\b)\s*(?:la\s+)?(?:sélection)?', 'clipboard_cut', 'PRESSE-PAPIERS', 48);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (49, '(?:sélectionne\s+tout|select\s+all|tout\s+sélectionner)', 'clipboard_select_all', 'PRESSE-PAPIERS', 49);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (50, '(?:ouvre|ouvrir)\s+(?:le\s+)?(?:dossier|répertoire|folder)\s+(.+)', 'navigate_folder', 'NAVIGATION', 50);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (51, '(?:ouvre|ouvrir)\s+(?:les\s+)?(?:t[ée]l[ée]chargements|downloads)', 'navigate_downloads', 'NAVIGATION', 51);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (52, '(?:ouvre|ouvrir)\s+(?:les\s+)?(?:documents)', 'navigate_documents', 'NAVIGATION', 52);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (53, '(?:ouvre|ouvrir)\s+(?:le\s+)?(?:bureau|desktop)', 'navigate_desktop', 'NAVIGATION', 53);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (54, '(?:google|recherche\s+sur\s+google|cherche\s+sur\s+google)\s+(.+)', 'web_google', 'WEB', 54);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (55, '(?:youtube)\s+(.+)', 'web_youtube', 'WEB', 55);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (56, '(?:wikipedia|wiki)\s+(.+)', 'web_wikipedia', 'WEB', 56);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (57, '(?:va\s+sur|ouvre\s+le\s+site|navigate|go\s+to)\s+(.+)', 'web_navigate', 'WEB', 57);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (58, '(?:météo|weather|temps\s+qu''il\s+fait)', 'web_weather', 'WEB', 58);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (59, '(?:minuteur|timer|chrono(?:m[èe]tre)?)\s+(.+)', 'timer_set', 'MINUTEURS', 59);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (60, '(?:rappelle[\s-]moi|reminder|rappel)\s+(?:dans\s+)?(.+)', 'timer_reminder', 'MINUTEURS', 60);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (61, '(?:annule|cancel)\s+(?:le\s+)?(?:minuteur|timer|chrono|rappel)', 'timer_cancel', 'MINUTEURS', 61);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (62, '(?:liste\s+(?:les\s+)?(?:minuteurs|timers|rappels)|timers?\s+actifs?)', 'timer_list', 'MINUTEURS', 62);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (63, '(?:note|noter|prends?\s+(?:en\s+)?note)\s+(.+)', 'note_add', 'NOTES', 63);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (64, '(?:lis|lire)\s+(?:les\s+)?notes', 'note_read', 'NOTES', 64);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (65, '(?:efface|supprime|clear)\s+(?:les\s+)?notes', 'note_clear', 'NOTES', 65);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (66, '(?:cherche|search)\s+(?:dans\s+)?(?:les\s+)?notes\s+(.+)', 'note_search', 'NOTES', 66);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (67, '(?:convertis?|conversion?|convert)\s+(\d+(?:[.,]\d+)?)\s*([a-zéèêàâôûïü-]+)\s+(?:en|to|vers)\s+([a-zéèêàâôûïü-]+)', 'unit_convert', 'CONVERSION', 67);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (68, '(?:calcule|calculer|calculate|combien\s+fait)\s+(.+)', 'calc_compute', 'CALCULATRICE', 68);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (69, '(\d+)\s*(?:pourcent|%|percent)\s+(?:de|of)\s+(\d+)', 'calc_percentage', 'CALCULATRICE', 69);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (70, '(?:convertis?|conversion?|convert)\s+(.+)', 'calc_convert', 'CALCULATRICE', 70);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (71, '(?:traduis?|traduire|translate)\s+en\s+anglais\s+(.+)', 'translate_fr_en', 'TRADUCTION', 71);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (72, '(?:traduis?|traduire|translate)\s+en\s+fran[çc]ais\s+(.+)', 'translate_en_fr', 'TRADUCTION', 72);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (73, '(?:traduis?|traduire|translate)\s+(.+)\s+en\s+anglais', 'translate_fr_en', 'TRADUCTION', 73);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (74, '(?:traduis?|traduire|translate)\s+(.+)\s+en\s+fran[çc]ais', 'translate_en_fr', 'TRADUCTION', 74);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (75, '(?:traduction|translation)\s+(?:de\s+)?(.+)', 'translate_lookup', 'TRADUCTION', 75);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (76, '(?:arr[êe]te\s+(?:le\s+)?pomodoro|stop\s+pomodoro|fin\s+(?:du\s+)?pomodoro)', 'pomodoro_stop', 'POMODORO', 76);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (77, '(?:[ée]tat\s+(?:du\s+)?pomodoro|pomodoro\s+status|o[ùu]\s+en\s+est\s+le\s+pomodoro|status\s+pomodoro)', 'pomodoro_status', 'POMODORO', 77);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (78, '(?:pomodoro|lance\s+(?:un\s+)?pomodoro|technique\s+pomodoro|mode\s+travail)', 'pomodoro_start', 'POMODORO', 78);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (79, '(?:snapshot\s+(?:du\s+)?syst[èe]me|capture\s+(?:du\s+)?syst[èe]me|[ée]tat\s+complet|system\s+snapshot|bilan\s+syst[èe]me)', 'snapshot_take', 'SNAPSHOT', 79);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (80, '(?:compare\s+(?:les\s+)?snapshots?|comparaison\s+syst[èe]me|diff\s+syst[èe]me)', 'snapshot_compare', 'SNAPSHOT', 80);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (81, '(?:historique\s+(?:des\s+)?snapshots?|snapshots?\s+pr[ée]c[ée]dents?)', 'snapshot_history', 'SNAPSHOT', 81);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (82, '(?:g[ée]n[èe]re|g[ée]n[ée]rer|generate)\s+(?:un\s+)?(?:mot\s+de\s+passe|password|mdp)\s*(.*)', 'password_generate', 'MOT DE PASSE', 82);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (83, '(?:force|strength)\s+(?:du\s+)?(?:mot\s+de\s+passe|password)\s+(.+)', 'password_strength', 'MOT DE PASSE', 83);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (84, '(?:dans\s+combien\s+de\s+jours?|combien\s+de\s+jours?\s+(?:avant|jusqu''[àa]))\s+(.+)', 'date_days_until', 'DATES', 84);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (85, '(?:quel\s+jour)\s+(?:sera|serons-nous|dans)\s+(.+)', 'date_add_days', 'DATES', 85);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (86, '(?:dans\s+(\d+)\s+jours?)', 'date_add_days', 'DATES', 86);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (87, '(?:quel\s+jour\s+(?:[ée]tait|est)\s+le|jour\s+de\s+la\s+semaine)\s+(.+)', 'date_day_of_week', 'DATES', 87);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (88, '(?:compte\s+(?:les\s+)?mots?|word\s+count)\s+(?:dans\s+|de\s+)?(.+)', 'text_count', 'OUTILS TEXTE', 88);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (89, '(?:en\s+majuscules?|uppercase|majuscule)\s+(.+)', 'text_uppercase', 'OUTILS TEXTE', 89);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (90, '(?:en\s+minuscules?|lowercase|minuscule)\s+(.+)', 'text_lowercase', 'OUTILS TEXTE', 90);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (91, '(?:acronyme|acronym)\s+(?:de\s+)?(.+)', 'text_acronym', 'OUTILS TEXTE', 91);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (92, '(?:[ée]pelle|[ée]peler|spell)\s+(.+)', 'text_spell', 'OUTILS TEXTE', 92);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (93, '(?:ajoute\s+(?:en|aux?)\s+favoris?|favori\s+ajout(?:e|er))\s+(.+)', 'fav_add', 'FAVORIS', 93);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (94, '(?:liste\s+(?:les\s+)?favoris?|mes\s+favoris?|favoris?\s+list)', 'fav_list', 'FAVORIS', 94);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (95, '(?:supprime\s+(?:le\s+)?favori|retire\s+(?:le\s+)?favori|favori\s+supprim(?:e|er))\s+(.+)', 'fav_remove', 'FAVORIS', 95);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (96, '(?:lance\s+(?:le\s+)?favori|favori)\s+(\d+|.+)', 'fav_run', 'FAVORIS', 96);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (97, '(?:chrono(?:m[èe]tre)?\s+(?:d[ée]marre|start|lance)|d[ée]marre\s+(?:le\s+)?chrono(?:m[èe]tre)?|start\s+stopwatch)', 'stopwatch_start', 'CHRONOMETRE', 97);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (98, '(?:arr[êe]te\s+(?:le\s+)?chrono(?:m[èe]tre)?|stop\s+(?:le\s+)?chrono(?:m[èe]tre)?|chrono\s+stop)', 'stopwatch_stop', 'CHRONOMETRE', 98);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (99, '(?:tour|lap)\s*(?:du\s+)?(?:chrono(?:m[èe]tre)?)?', 'stopwatch_lap', 'CHRONOMETRE', 99);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (100, '(?:r[ée]initialise|reset)\s+(?:le\s+)?chrono(?:m[èe]tre)?', 'stopwatch_reset', 'CHRONOMETRE', 100);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (101, '(?:temps\s+(?:du\s+)?chrono(?:m[èe]tre)?|chrono\s+status)', 'stopwatch_status', 'CHRONOMETRE', 101);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (102, '(?:agenda\s+ajoute|ajoute\s+(?:[àa])\s+l''agenda|[ée]v[ée]nement)\s+(.+)', 'agenda_add', 'AGENDA', 102);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (103, '(?:vide\s+(?:l'')?agenda|efface\s+(?:l'')?agenda|clear\s+agenda)', 'agenda_clear', 'AGENDA', 103);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (104, '(?:prochain\s+[ée]v[ée]nement|next\s+event|qu''est-ce\s+(?:que\s+)?(?:j''ai\s+)?(?:apr[èe]s|ensuite))', 'agenda_next', 'AGENDA', 104);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (105, '(?:agenda|(?:mon|l'')\s*agenda|planning|[ée]v[ée]nements?\s+(?:du\s+jour|pr[ée]vus?))', 'agenda_list', 'AGENDA', 105);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (106, '(?:pile\s+ou\s+face|coin\s+flip|lance\s+(?:une\s+)?pi[èe]ce)', 'random_coin', 'ALEATOIRE', 106);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (107, '(?:lance\s+(?:un\s+)?d[ée]|d[ée]\s+[àa]\s+(\d+)|roll\s+dice|jet\s+de\s+d[ée])', 'random_dice', 'ALEATOIRE', 107);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (108, '(?:choisis?\s+(?:entre|parmi)|pick|random\s+choice)\s+(.+)', 'random_pick', 'ALEATOIRE', 108);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (109, '(?:nombre\s+al[ée]atoire|random\s+number|nombre\s+au\s+hasard)\s*(.*)', 'random_number', 'ALEATOIRE', 109);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (110, '(?:liste\s+(?:des?\s+)?abr[ée]viations?|abr[ée]viations?\s+(?:disponibles?|connues?))', 'abbrev_list', 'ABREVIATIONS', 110);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (111, '(?:(?:que\s+)?(?:signifie|veut\s+dire)|d[ée]finition\s+(?:de\s+)?|abr[ée]viation)\s*([A-Za-zÀ-ÿ]+)', 'abbrev_define', 'ABREVIATIONS', 111);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (112, '(?:exécute|exécuter|run|lance)\s+(?:l[ea]\s+)?(?:macro|automatisation|script)\s+(.+)', 'automation_run', 'AUTOMATISATION', 112);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (113, '(?:automatise|automatiser|automate|macro)\s+(.+)', 'automation_create', 'AUTOMATISATION', 113);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (114, '(?:ouvre|ouvrir|lance|lancer|démarre|démarrer|start|open|launch)\s+(.+)', 'app_launch', 'APPLICATIONS', 114);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (115, '(?:ferme|fermer|quitte|quitter|close|kill|arrête|arrêter)\s+(.+)', 'app_close', 'APPLICATIONS', 115);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (116, '(?:crée|créer|nouveau|nouvelle)\s+(?:un\s+)?(?:fichier|dossier|répertoire)\s+(.+)', 'file_create', 'FICHIERS', 116);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (117, '(?:supprime|supprimer|efface|effacer|delete)\s+(?:le\s+)?(?:fichier|dossier)?\s*(.+)', 'file_delete', 'FICHIERS', 117);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (118, '(?:cherche|chercher|recherche(?:r)?|trouve|trouver|find|search)\s+(?:le\s+fichier\s+)?(.+)', 'file_search', 'FICHIERS', 118);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (119, '(?:renomme|renommer|rename)\s+(.+)\s+en\s+(.+)', 'file_rename', 'FICHIERS', 119);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (120, '(?:copie|copier|copy)\s+(.+)', 'clipboard_copy', 'PRESSE-PAPIERS', 120);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (121, '(?:colle|coller|paste)', 'clipboard_paste', 'PRESSE-PAPIERS', 121);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (122, '(?:minimise|minimiser|minimize)\s*(?:la\s+)?(?:fenêtre)?', 'window_minimize', 'FENETRES', 122);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (123, '(?:maximise|maximiser|maximize)\s*(?:la\s+)?(?:fenêtre)?', 'window_maximize', 'FENETRES', 123);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (124, '(?:restaure|restaurer|restore)\s*(?:la\s+)?(?:fenêtre)?', 'window_restore', 'FENETRES', 124);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (125, '(?:bascule|basculer|switch|alt.?tab)', 'window_switch', 'FENETRES', 125);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (126, '(?:bureau|show\s+desktop|affiche\s+le\s+bureau)', 'window_desktop', 'FENETRES', 126);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (127, '(?:capture|screenshot|écran)\s*(?:d''écran)?', 'window_screenshot', 'FENETRES', 127);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (128, '(?:volume)\s+(?:à|a|au)?\s*(\d+)', 'system_volume_set', 'SYSTEME', 128);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (129, '(?:monte|augmente|plus\s+fort|volume\s+up|up\s+volume)\s*(?:le\s+)?(?:volume|son)?', 'system_volume_up', 'SYSTEME', 129);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (130, '(?:baisse|diminue|moins\s+fort|volume\s+down|down\s+volume)\s*(?:le\s+)?(?:volume|son)?', 'system_volume_down', 'SYSTEME', 130);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (131, '(?:muet|mute|coupe\s+le\s+son|silence)', 'system_mute', 'SYSTEME', 131);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (132, '(?:luminosité|brightness)\s+(?:à|a|au)?\s*(\d+)', 'system_brightness', 'SYSTEME', 132);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (133, '(?:wifi)\s+(on|off|active|désactive)', 'system_wifi', 'SYSTEME', 133);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (134, '(?:bluetooth)\s+(on|off|active|désactive)', 'system_bluetooth', 'SYSTEME', 134);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (135, '(?:éteins|éteindre|shutdown|arrête\s+l''ordinateur)', 'system_shutdown', 'SYSTEME', 135);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (136, '(?:redémarre|redémarrer|restart|reboot)', 'system_restart', 'SYSTEME', 136);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (137, '(?:veille|sleep|mise\s+en\s+veille|verrouille|lock)', 'system_sleep', 'SYSTEME', 137);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (138, '(?:batterie|battery|autonomie)', 'system_battery', 'SYSTEME', 138);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (139, '(?:heure|quelle\s+heure|time)', 'system_time', 'SYSTEME', 139);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (140, '(?:date|quel\s+jour|today)', 'system_date', 'SYSTEME', 140);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (141, '(?:aide|help|qu''est-ce\s+que\s+tu\s+(?:sais|peux)\s+faire|commandes)', 'jarvis_help', 'JARVIS', 141);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (142, '(?:statut|status|état|state)', 'jarvis_status', 'JARVIS', 142);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (143, '(?:au\s+revoir|goodbye|bye|à\s+plus|bonne\s+nuit|stop\s+jarvis|quitte\s+jarvis)', 'jarvis_quit', 'JARVIS', 143);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (144, '(?:merci|thanks|thank\s+you)', 'jarvis_thanks', 'JARVIS', 144);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (145, '(?:répète|repeat|redis)', 'jarvis_repeat', 'JARVIS', 145);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (146, '(?:annule|cancel|undo|annuler)', 'jarvis_cancel', 'JARVIS', 146);
INSERT INTO patterns (id, regex, intent, section, priority_order) VALUES (147, '(?:paramètres|settings|configuration|config)\s*(?:de\s+)?(?:jarvis)?', 'jarvis_settings', 'JARVIS', 147);

-- === HANDLERS DATA ===
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('app_launch', 'launch', 'AppLauncherSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('app_close', 'close', 'AppLauncherSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('system_volume_set', 'volume_set', 'SystemControlSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('system_volume_up', 'volume_up', 'SystemControlSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('system_volume_down', 'volume_down', 'SystemControlSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('system_mute', 'mute', 'SystemControlSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('system_brightness', 'brightness', 'SystemControlSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('system_wifi', 'wifi', 'SystemControlSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('system_bluetooth', 'bluetooth', 'SystemControlSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('system_shutdown', 'shutdown', 'SystemControlSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('system_restart', 'restart', 'SystemControlSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('system_sleep', 'sleep', 'SystemControlSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('system_battery', 'battery', 'SystemControlSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('system_time', 'time', 'SystemControlSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('system_date', 'date', 'SystemControlSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('window_minimize', 'minimize', 'WindowManagerSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('window_maximize', 'maximize', 'WindowManagerSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('window_restore', 'restore', 'WindowManagerSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('window_switch', 'switch', 'WindowManagerSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('window_desktop', 'desktop', 'WindowManagerSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('window_screenshot', 'screenshot', 'WindowManagerSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('file_create', 'create', 'FileManagerSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('file_delete', 'delete', 'FileManagerSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('file_search', 'search', 'FileManagerSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('file_rename', 'rename', 'FileManagerSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('web_google', 'google', 'WebBrowserSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('web_youtube', 'youtube', 'WebBrowserSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('web_wikipedia', 'wikipedia', 'WebBrowserSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('web_navigate', 'navigate', 'WebBrowserSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('web_weather', 'weather', 'WebBrowserSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('media_play', 'play', 'MediaControlSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('media_pause', 'pause', 'MediaControlSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('media_next', 'next_track', 'MediaControlSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('media_previous', 'previous_track', 'MediaControlSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('clipboard_copy', 'copy', 'ClipboardManagerSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('clipboard_paste', 'paste', 'ClipboardManagerSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('clipboard_cut', 'cut', 'ClipboardManagerSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('clipboard_select_all', 'select_all', 'ClipboardManagerSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('clipboard_read', 'read_clipboard', 'ClipboardManagerSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('process_list', 'list_processes', 'ProcessManagerSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('process_kill', 'kill_process', 'ProcessManagerSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('system_resources', 'system_resources', 'ProcessManagerSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('system_top_cpu', 'top_cpu', 'ProcessManagerSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('system_disk', 'disk_space', 'ProcessManagerSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('system_uptime', 'uptime', 'ProcessManagerSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('system_gpu', 'gpu_info', 'ProcessManagerSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('system_hardware', 'hardware_info', 'ProcessManagerSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('network_status', 'network_status', 'NetworkControlSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('network_ip', 'ip_local', 'NetworkControlSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('network_ip_public', 'ip_public', 'NetworkControlSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('network_ping', 'ping', 'NetworkControlSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('network_wifi_list', 'wifi_list', 'NetworkControlSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('network_speed', 'speed_test', 'NetworkControlSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('power_plan', 'power_plan', 'PowerDisplaySkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('power_high_perf', 'set_high_performance', 'PowerDisplaySkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('power_balanced', 'set_balanced', 'PowerDisplaySkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('power_saver', 'set_power_saver', 'PowerDisplaySkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('power_hibernate', 'hibernate', 'PowerDisplaySkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('display_resolution', 'screen_resolution', 'PowerDisplaySkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('display_night', 'night_mode', 'PowerDisplaySkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('display_settings', 'display_settings', 'PowerDisplaySkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('audio_settings', 'sound_settings', 'PowerDisplaySkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('software_install', 'install', 'SoftwareManagerSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('software_uninstall', 'uninstall', 'SoftwareManagerSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('software_update_all', 'update_all', 'SoftwareManagerSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('software_list', 'list_installed', 'SoftwareManagerSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('software_check_updates', 'check_updates', 'SoftwareManagerSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('navigate_folder', 'navigate', 'NavigationAgent');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('navigate_downloads', '_nav_downloads', 'Jarvis');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('navigate_documents', '_nav_documents', 'Jarvis');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('navigate_desktop', '_nav_desktop', 'Jarvis');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('dictation_start', 'start', 'DictationAgent');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('dictation_stop', 'stop', 'DictationAgent');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('dictation_newline', 'newline', 'DictationAgent');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('dictation_period', 'period', 'DictationAgent');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('timer_set', 'set_timer', 'TimerReminderSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('timer_reminder', 'set_reminder', 'TimerReminderSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('timer_cancel', 'cancel_timer', 'TimerReminderSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('timer_list', 'list_timers', 'TimerReminderSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('note_add', 'add_note', 'QuickNotesSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('note_read', 'read_notes', 'QuickNotesSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('note_clear', 'clear_notes', 'QuickNotesSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('note_search', 'search_notes', 'QuickNotesSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('calc_compute', 'calculate', 'CalculatorSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('calc_percentage', 'percentage', 'CalculatorSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('calc_convert', 'convert_temperature', 'CalculatorSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('vdesktop_new', 'new_desktop', 'VirtualDesktopSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('vdesktop_close', 'close_desktop', 'VirtualDesktopSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('vdesktop_left', 'switch_left', 'VirtualDesktopSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('vdesktop_right', 'switch_right', 'VirtualDesktopSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('vdesktop_task_view', 'task_view', 'VirtualDesktopSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('translate_fr_en', 'translate_fr_en', 'TranslatorSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('translate_en_fr', 'translate_en_fr', 'TranslatorSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('translate_lookup', 'lookup', 'TranslatorSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('unit_convert', 'convert', 'UnitConverterSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('pomodoro_start', 'start', 'PomodoroSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('pomodoro_stop', 'stop', 'PomodoroSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('pomodoro_status', 'status', 'PomodoroSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('snapshot_take', 'take_snapshot', 'SystemSnapshotSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('snapshot_compare', 'compare', 'SystemSnapshotSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('snapshot_history', 'history', 'SystemSnapshotSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('password_generate', 'generate', 'PasswordGeneratorSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('password_strength', 'strength', 'PasswordGeneratorSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('date_days_until', 'days_until', 'DateCalculatorSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('date_add_days', 'add_days_cmd', 'DateCalculatorSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('date_day_of_week', 'day_of_week', 'DateCalculatorSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('text_count', 'count_words', 'TextToolsSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('text_uppercase', 'uppercase', 'TextToolsSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('text_lowercase', 'lowercase', 'TextToolsSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('text_acronym', 'acronym', 'TextToolsSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('text_spell', 'spell', 'TextToolsSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('fav_add', 'add', 'FavoritesSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('fav_list', 'list_favorites', 'FavoritesSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('fav_remove', 'remove', 'FavoritesSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('fav_run', 'run_favorite', 'FavoritesSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('stopwatch_start', 'start', 'StopwatchSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('stopwatch_stop', 'stop', 'StopwatchSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('stopwatch_lap', 'lap', 'StopwatchSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('stopwatch_reset', 'reset', 'StopwatchSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('stopwatch_status', 'status', 'StopwatchSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('agenda_add', 'add_event', 'AgendaSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('agenda_list', 'list_events', 'AgendaSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('agenda_clear', 'clear_events', 'AgendaSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('agenda_next', 'next_event', 'AgendaSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('random_coin', 'flip_coin', 'RandomPickerSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('random_dice', 'roll_dice', 'RandomPickerSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('random_pick', 'pick', 'RandomPickerSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('random_number', 'random_num', 'RandomPickerSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('abbrev_define', 'define', 'AbbreviationsSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('abbrev_list', 'list_category', 'AbbreviationsSkill');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('automation_create', 'create', 'AutomationAgent');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('automation_run', '_run_macro', 'Jarvis');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('jarvis_help', '_help', 'Jarvis');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('jarvis_status', '_status', 'Jarvis');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('jarvis_quit', '_quit', 'Jarvis');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('jarvis_thanks', '_thanks', 'Jarvis');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('jarvis_cancel', '_cancel', 'Jarvis');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('jarvis_repeat', '_repeat', 'Jarvis');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('jarvis_settings', 'open_settings', 'NavigationAgent');
INSERT INTO handlers (intent, method_name, skill_class) VALUES ('unknown', '_unknown', 'Jarvis');

-- === TRAINING CYCLES ===
INSERT INTO training_cycles (cycle_range, test_file, test_count, skills_added, commit_hash, created_at) VALUES ('1-50', 'test_jarvis_simulation + test_jarvis_full_training + test_jarvis_50_cycles', 583, 'AppLauncher, SystemControl, WindowManager, FileManager, WebBrowser, MediaControl, ClipboardManager, ProcessManager, NetworkControl, PowerDisplay, SoftwareManager', 'a3aae3c', '2026-02-17 12:58:54');
INSERT INTO training_cycles (cycle_range, test_file, test_count, skills_added, commit_hash, created_at) VALUES ('51-100', 'test_jarvis_100_cycles', 251, 'DictationAgent, VirtualDesktop, TimerReminder, QuickNotes, Calculator, Translator, UnitConverter', 'eefff6e', '2026-02-17 12:58:54');
INSERT INTO training_cycles (cycle_range, test_file, test_count, skills_added, commit_hash, created_at) VALUES ('101-150', 'test_jarvis_150_cycles', 148, 'PomodoroSkill, SystemSnapshotSkill', 'b4fcc82', '2026-02-17 12:58:54');
INSERT INTO training_cycles (cycle_range, test_file, test_count, skills_added, commit_hash, created_at) VALUES ('151-200', 'test_jarvis_200_cycles', 150, 'PasswordGenerator, DateCalculator, TextTools, Favorites', '837a236', '2026-02-17 12:58:54');
INSERT INTO training_cycles (cycle_range, test_file, test_count, skills_added, commit_hash, created_at) VALUES ('201-250', 'test_jarvis_250_cycles', 127, 'Stopwatch, Agenda, RandomPicker, Abbreviations', '2bb924a', '2026-02-17 12:58:54');

-- === ABBREVIATIONS DATA ===
INSERT INTO abbreviations (abbr, definition, category) VALUES ('ia', 'Intelligence Artificielle', 'Informatique');
INSERT INTO abbreviations (abbr, definition, category) VALUES ('api', 'Application Programming Interface', 'Informatique');
INSERT INTO abbreviations (abbr, definition, category) VALUES ('cpu', 'Central Processing Unit', 'Informatique');
INSERT INTO abbreviations (abbr, definition, category) VALUES ('gpu', 'Graphics Processing Unit', 'Informatique');
INSERT INTO abbreviations (abbr, definition, category) VALUES ('ram', 'Random Access Memory', 'Informatique');
INSERT INTO abbreviations (abbr, definition, category) VALUES ('ssd', 'Solid State Drive', 'Informatique');
INSERT INTO abbreviations (abbr, definition, category) VALUES ('hdd', 'Hard Disk Drive', 'Informatique');
INSERT INTO abbreviations (abbr, definition, category) VALUES ('usb', 'Universal Serial Bus', 'Informatique');
INSERT INTO abbreviations (abbr, definition, category) VALUES ('html', 'HyperText Markup Language', 'Informatique');
INSERT INTO abbreviations (abbr, definition, category) VALUES ('css', 'Cascading Style Sheets', 'Informatique');
INSERT INTO abbreviations (abbr, definition, category) VALUES ('sql', 'Structured Query Language', 'Informatique');
INSERT INTO abbreviations (abbr, definition, category) VALUES ('url', 'Uniform Resource Locator', 'Informatique');
INSERT INTO abbreviations (abbr, definition, category) VALUES ('ip', 'Internet Protocol', 'Informatique');
INSERT INTO abbreviations (abbr, definition, category) VALUES ('http', 'HyperText Transfer Protocol', 'Informatique');
INSERT INTO abbreviations (abbr, definition, category) VALUES ('https', 'HyperText Transfer Protocol Secure', 'Informatique');
INSERT INTO abbreviations (abbr, definition, category) VALUES ('dns', 'Domain Name System', 'Informatique');
INSERT INTO abbreviations (abbr, definition, category) VALUES ('vpn', 'Virtual Private Network', 'Informatique');
INSERT INTO abbreviations (abbr, definition, category) VALUES ('pdf', 'Portable Document Format', 'Informatique');
INSERT INTO abbreviations (abbr, definition, category) VALUES ('json', 'JavaScript Object Notation', 'Informatique');
INSERT INTO abbreviations (abbr, definition, category) VALUES ('xml', 'eXtensible Markup Language', 'Informatique');
INSERT INTO abbreviations (abbr, definition, category) VALUES ('ide', 'Integrated Development Environment', 'Informatique');
INSERT INTO abbreviations (abbr, definition, category) VALUES ('cli', 'Command Line Interface', 'Informatique');
INSERT INTO abbreviations (abbr, definition, category) VALUES ('gui', 'Graphical User Interface', 'Informatique');
INSERT INTO abbreviations (abbr, definition, category) VALUES ('os', 'Operating System', 'Informatique');
INSERT INTO abbreviations (abbr, definition, category) VALUES ('iot', 'Internet of Things', 'Informatique');
INSERT INTO abbreviations (abbr, definition, category) VALUES ('ml', 'Machine Learning', 'Informatique');
INSERT INTO abbreviations (abbr, definition, category) VALUES ('llm', 'Large Language Model', 'Informatique');
INSERT INTO abbreviations (abbr, definition, category) VALUES ('nlp', 'Natural Language Processing', 'Informatique');
INSERT INTO abbreviations (abbr, definition, category) VALUES ('rh', 'Ressources Humaines', 'General FR');
INSERT INTO abbreviations (abbr, definition, category) VALUES ('pme', 'Petite et Moyenne Entreprise', 'General FR');
INSERT INTO abbreviations (abbr, definition, category) VALUES ('tva', 'Taxe sur la Valeur Ajoutée', 'General FR');
INSERT INTO abbreviations (abbr, definition, category) VALUES ('smic', 'Salaire Minimum Interprofessionnel de Croissance', 'General FR');
INSERT INTO abbreviations (abbr, definition, category) VALUES ('bac', 'Baccalauréat', 'General FR');
INSERT INTO abbreviations (abbr, definition, category) VALUES ('bts', 'Brevet de Technicien Supérieur', 'General FR');
INSERT INTO abbreviations (abbr, definition, category) VALUES ('dut', 'Diplôme Universitaire de Technologie', 'General FR');
INSERT INTO abbreviations (abbr, definition, category) VALUES ('cdi', 'Contrat à Durée Indéterminée', 'General FR');
INSERT INTO abbreviations (abbr, definition, category) VALUES ('cdd', 'Contrat à Durée Déterminée', 'General FR');
INSERT INTO abbreviations (abbr, definition, category) VALUES ('cv', 'Curriculum Vitae', 'General FR');
INSERT INTO abbreviations (abbr, definition, category) VALUES ('rsa', 'Revenu de Solidarité Active', 'General FR');
INSERT INTO abbreviations (abbr, definition, category) VALUES ('sncf', 'Société Nationale des Chemins de fer Français', 'General FR');
INSERT INTO abbreviations (abbr, definition, category) VALUES ('ratp', 'Régie Autonome des Transports Parisiens', 'General FR');
INSERT INTO abbreviations (abbr, definition, category) VALUES ('onu', 'Organisation des Nations Unies', 'Organisations');
INSERT INTO abbreviations (abbr, definition, category) VALUES ('ue', 'Union Européenne', 'Organisations');
INSERT INTO abbreviations (abbr, definition, category) VALUES ('otan', 'Organisation du Traité de l''Atlantique Nord', 'Organisations');
INSERT INTO abbreviations (abbr, definition, category) VALUES ('nasa', 'National Aeronautics and Space Administration', 'Organisations');
INSERT INTO abbreviations (abbr, definition, category) VALUES ('oms', 'Organisation Mondiale de la Santé', 'Organisations');
INSERT INTO abbreviations (abbr, definition, category) VALUES ('fmi', 'Fonds Monétaire International', 'Organisations');
INSERT INTO abbreviations (abbr, definition, category) VALUES ('km', 'kilomètre', 'Unites');
INSERT INTO abbreviations (abbr, definition, category) VALUES ('kg', 'kilogramme', 'Unites');
INSERT INTO abbreviations (abbr, definition, category) VALUES ('mb', 'mégaoctet', 'Unites');
INSERT INTO abbreviations (abbr, definition, category) VALUES ('gb', 'gigaoctet', 'Unites');
INSERT INTO abbreviations (abbr, definition, category) VALUES ('tb', 'téraoctet', 'Unites');

-- Total patterns: 147
-- Total handlers: 140
-- Total skill classes: 30
-- Total abbreviations: 52
-- Total tests: 1259
-- Training cycles: 250
-- END OF BACKUP