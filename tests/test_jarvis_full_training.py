"""
JARVIS - Formation complète: Cycles de simulation d'utilisation réelle
200+ tests couvrant TOUS les scénarios Windows vocaux

Cycles:
  1. Wake word (variations FR/EN)
  2. Commandes de base (53 originales + 40 nouvelles)
  3. Skills individuels en isolation
  4. Agents spécialisés lifecycle complet
  5. Pipeline complet (wake -> command -> execute -> TTS)
  6. Scénarios réels multi-étapes
  7. Edge cases et récupération d'erreurs
  8. Commutation de modes (normal -> dictée -> macro -> normal)
  9. Commandes bilingues FR/EN
  10. Stress test: commandes rapides enchaînées
"""

import asyncio
import pytest
import logging
from datetime import datetime
from unittest.mock import AsyncMock, patch, MagicMock
from pathlib import Path

from whisperflow.jarvis.jarvis_core import Jarvis
from whisperflow.jarvis.commander import Commander, VoiceCommand, CommandResult
from whisperflow.jarvis.wake_word import detect_wake_word, strip_wake_word
from whisperflow.jarvis.config import JarvisConfig

logging.basicConfig(level=logging.INFO)


# ============================================================
# CYCLE 1: WAKE WORD - Formation intensive
# ============================================================
class TestWakeWordTraining:
    """Test exhaustif de détection du wake word"""

    @pytest.mark.parametrize("text,expected_detected,expected_has_cmd", [
        ("Jarvis ouvre Chrome", True, True),
        ("JARVIS ferme notepad", True, True),
        ("jarvis", True, False),
        ("Jarvis, aide moi", True, True),
        ("Jarvis. Quelle heure", True, True),
        ("Hey Jarvis monte le volume", True, True),
        ("Ok Jarvis recherche python", True, True),
        ("Dis Jarvis ouvre youtube", True, True),
        ("Dit Jarvis quelle heure est-il", True, True),
        ("Jarviss ouvre chrome", True, True),
        ("Jarvi lance le terminal", True, True),
        ("Bonjour tout le monde", False, False),
        ("Ouvre Chrome", False, False),
        ("", False, False),
        ("   ", False, False),
        ("Le jarvis est un outil", False, False),
        ("Charvis", True, False),
    ])
    def test_wake_variations(self, text, expected_detected, expected_has_cmd):
        detected, cmd = detect_wake_word(text)
        assert detected == expected_detected
        if expected_has_cmd:
            assert len(cmd) > 0

    def test_strip_wake_word(self):
        assert strip_wake_word("Jarvis ouvre chrome") == "ouvre chrome"
        assert strip_wake_word("Bonjour") == "Bonjour"
        assert strip_wake_word("") == ""


# ============================================================
# CYCLE 2: COMMANDER - Tous les 93 patterns
# ============================================================
class TestCommanderAllPatterns:
    """Test de TOUS les patterns de commandes (originaux + nouveaux)"""

    def setup_method(self):
        self.c = Commander()

    # --- Dictée (prioritaire) ---
    @pytest.mark.parametrize("text,intent", [
        ("mode dictée", "dictation_start"),
        ("dictation mode", "dictation_start"),
        ("commence à écrire", "dictation_start"),
        ("arrête la dictée", "dictation_stop"),
        ("stop dictation", "dictation_stop"),
        ("fin de dictée", "dictation_stop"),
        ("nouvelle ligne", "dictation_newline"),
        ("retour à la ligne", "dictation_newline"),
    ])
    def test_dictation_patterns(self, text, intent):
        assert self.c.parse(text).intent == intent

    # --- Applications ---
    @pytest.mark.parametrize("text,intent", [
        ("ouvre chrome", "app_launch"),
        ("lance le terminal", "app_launch"),
        ("démarre word", "app_launch"),
        ("start notepad", "app_launch"),
        ("open firefox", "app_launch"),
        ("launch vscode", "app_launch"),
        ("ferme chrome", "app_close"),
        ("quitte notepad", "app_close"),
        ("close firefox", "app_close"),
        ("kill discord", "app_close"),
    ])
    def test_app_patterns(self, text, intent):
        assert self.c.parse(text).intent == intent

    # --- Système ---
    @pytest.mark.parametrize("text,intent", [
        ("monte le volume", "system_volume_up"),
        ("augmente le son", "system_volume_up"),
        ("plus fort", "system_volume_up"),
        ("volume up", "system_volume_up"),
        ("baisse le volume", "system_volume_down"),
        ("diminue le son", "system_volume_down"),
        ("moins fort", "system_volume_down"),
        ("volume à 50", "system_volume_set"),
        ("volume à 80", "system_volume_set"),
        ("muet", "system_mute"),
        ("mute", "system_mute"),
        ("coupe le son", "system_mute"),
        ("silence", "system_mute"),
        ("luminosité à 80", "system_brightness"),
        ("brightness à 50", "system_brightness"),
        ("wifi on", "system_wifi"),
        ("wifi off", "system_wifi"),
        ("bluetooth on", "system_bluetooth"),
        ("bluetooth off", "system_bluetooth"),
        ("éteins l'ordinateur", "system_shutdown"),
        ("shutdown", "system_shutdown"),
        ("redémarre", "system_restart"),
        ("restart", "system_restart"),
        ("reboot", "system_restart"),
        ("veille", "system_sleep"),
        ("verrouille", "system_sleep"),
        ("lock", "system_sleep"),
        ("batterie", "system_battery"),
        ("autonomie", "system_battery"),
        ("quelle heure", "system_time"),
        ("heure", "system_time"),
        ("quel jour", "system_date"),
        ("date", "system_date"),
    ])
    def test_system_patterns(self, text, intent):
        assert self.c.parse(text).intent == intent

    # --- Processus & Monitoring ---
    @pytest.mark.parametrize("text,intent", [
        ("liste les processus", "process_list"),
        ("list process", "process_list"),
        ("liste les tâches", "process_list"),
        ("tue le processus chrome", "process_kill"),
        ("kill process notepad", "process_kill"),
        ("ressources système", "system_resources"),
        ("charge système", "system_resources"),
        ("utilisation", "system_resources"),
        ("cpu", "system_top_cpu"),
        ("processeur", "system_top_cpu"),
        ("ram", "system_resources"),
        ("mémoire", "system_resources"),
        ("espace disque", "system_disk"),
        ("disk space", "system_disk"),
        ("stockage", "system_disk"),
        ("uptime", "system_uptime"),
        ("allumé depuis", "system_uptime"),
        ("gpu", "system_gpu"),
        ("carte graphique", "system_gpu"),
        ("matériel", "system_hardware"),
        ("hardware", "system_hardware"),
        ("info système", "system_hardware"),
        ("configuration matérielle", "system_hardware"),
    ])
    def test_process_monitor_patterns(self, text, intent):
        assert self.c.parse(text).intent == intent

    # --- Réseau ---
    @pytest.mark.parametrize("text,intent", [
        ("état du réseau", "network_status"),
        ("network status", "network_status"),
        ("interface réseau", "network_status"),
        ("adresse ip", "network_ip"),
        ("mon ip", "network_ip"),
        ("ip publique", "network_ip_public"),
        ("public ip", "network_ip_public"),
        ("ping google.com", "network_ping"),
        ("teste la connexion", "network_ping"),
        ("réseaux wifi", "network_wifi_list"),
        ("scan wifi", "network_wifi_list"),
        ("test de débit", "network_speed"),
        ("speed test", "network_speed"),
    ])
    def test_network_patterns(self, text, intent):
        assert self.c.parse(text).intent == intent

    # --- Alimentation & Affichage ---
    @pytest.mark.parametrize("text,intent", [
        ("plan d'alimentation", "power_plan"),
        ("power plan", "power_plan"),
        ("haute performance", "power_high_perf"),
        ("mode performance", "power_high_perf"),
        ("mode équilibré", "power_balanced"),
        ("économie d'énergie", "power_saver"),
        ("mode éco", "power_saver"),
        ("hibernation", "power_hibernate"),
        ("résolution", "display_resolution"),
        ("résolution d'écran", "display_resolution"),
        ("mode nuit", "display_night"),
        ("filtre bleu", "display_night"),
        ("paramètres d'affichage", "display_settings"),
        ("paramètres du son", "audio_settings"),
        ("paramètres audio", "audio_settings"),
    ])
    def test_power_display_patterns(self, text, intent):
        assert self.c.parse(text).intent == intent

    # --- Logiciels ---
    @pytest.mark.parametrize("text,intent", [
        ("installe firefox", "software_install"),
        ("installer le logiciel vlc", "software_install"),
        ("désinstalle notepad++", "software_uninstall"),
        ("mets à jour tout", "software_update_all"),
        ("update all", "software_update_all"),
        ("liste les logiciels", "software_list"),
        ("programmes installés", "software_list"),
        ("mises à jour disponibles", "software_check_updates"),
        ("vérifie les mises à jour", "software_check_updates"),
    ])
    def test_software_patterns(self, text, intent):
        assert self.c.parse(text).intent == intent

    # --- Fenêtres ---
    @pytest.mark.parametrize("text,intent", [
        ("minimise", "window_minimize"),
        ("minimise la fenêtre", "window_minimize"),
        ("maximize", "window_maximize"),
        ("restaure", "window_restore"),
        ("bascule", "window_switch"),
        ("alt tab", "window_switch"),
        ("bureau", "window_desktop"),
        ("affiche le bureau", "window_desktop"),
        ("capture d'écran", "window_screenshot"),
        ("screenshot", "window_screenshot"),
    ])
    def test_window_patterns(self, text, intent):
        assert self.c.parse(text).intent == intent

    # --- Web ---
    @pytest.mark.parametrize("text,intent", [
        ("google intelligence artificielle", "web_google"),
        ("recherche sur google python", "web_google"),
        ("youtube tutoriel javascript", "web_youtube"),
        ("wikipedia machine learning", "web_wikipedia"),
        ("va sur github.com", "web_navigate"),
        ("go to stackoverflow.com", "web_navigate"),
        ("météo", "web_weather"),
        ("temps qu'il fait", "web_weather"),
    ])
    def test_web_patterns(self, text, intent):
        assert self.c.parse(text).intent == intent

    # --- Média ---
    @pytest.mark.parametrize("text,intent", [
        ("play", "media_play"),
        ("lecture", "media_play"),
        ("joue", "media_play"),
        ("pause", "media_pause"),
        ("arrête la musique", "media_pause"),
        ("suivant", "media_next"),
        ("piste suivante", "media_next"),
        ("précédent", "media_previous"),
        ("chanson précédente", "media_previous"),
    ])
    def test_media_patterns(self, text, intent):
        assert self.c.parse(text).intent == intent

    # --- Presse-papiers ---
    @pytest.mark.parametrize("text,intent", [
        ("copie le texte", "clipboard_copy"),
        ("colle", "clipboard_paste"),
        ("coupe la sélection", "clipboard_cut"),
        ("sélectionne tout", "clipboard_select_all"),
        ("lis le presse-papiers", "clipboard_read"),
    ])
    def test_clipboard_patterns(self, text, intent):
        assert self.c.parse(text).intent == intent

    # --- Fichiers ---
    @pytest.mark.parametrize("text,intent", [
        ("crée un fichier rapport", "file_create"),
        ("crée un dossier projets", "file_create"),
        ("nouveau fichier test", "file_create"),
        ("supprime le fichier brouillon", "file_delete"),
        ("efface brouillon", "file_delete"),
        ("cherche rapport annuel", "file_search"),
        ("trouve le fichier budget", "file_search"),
        ("find readme", "file_search"),
    ])
    def test_file_patterns(self, text, intent):
        assert self.c.parse(text).intent == intent

    # --- Contrôle JARVIS ---
    @pytest.mark.parametrize("text,intent", [
        ("aide", "jarvis_help"),
        ("help", "jarvis_help"),
        ("qu'est-ce que tu sais faire", "jarvis_help"),
        ("commandes", "jarvis_help"),
        ("statut", "jarvis_status"),
        ("état", "jarvis_status"),
        ("au revoir", "jarvis_quit"),
        ("goodbye", "jarvis_quit"),
        ("bonne nuit", "jarvis_quit"),
        ("merci", "jarvis_thanks"),
        ("thanks", "jarvis_thanks"),
        ("répète", "jarvis_repeat"),
        ("annule", "jarvis_cancel"),
        ("cancel", "jarvis_cancel"),
    ])
    def test_jarvis_control_patterns(self, text, intent):
        assert self.c.parse(text).intent == intent


# ============================================================
# CYCLE 3: Skills isolés - Tous les skills sans toucher au système
# ============================================================
class TestSkillsIsolated:
    """Teste chaque skill individuellement"""

    def setup_method(self):
        self.jarvis = Jarvis()

    @pytest.mark.asyncio
    async def test_time_returns_hours(self):
        r = await self.jarvis.system_control.time(VoiceCommand("", "system_time"))
        assert r.success and "heure" in r.message.lower()

    @pytest.mark.asyncio
    async def test_date_returns_weekday(self):
        r = await self.jarvis.system_control.date(VoiceCommand("", "system_date"))
        assert r.success
        days = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
        assert any(d in r.message.lower() for d in days)

    @pytest.mark.asyncio
    async def test_shutdown_is_pending(self):
        r = await self.jarvis.system_control.shutdown(VoiceCommand("", "system_shutdown"))
        assert r.data and "pending_action" in r.data

    @pytest.mark.asyncio
    async def test_restart_is_pending(self):
        r = await self.jarvis.system_control.restart(VoiceCommand("", "system_restart"))
        assert r.data and "pending_action" in r.data

    @pytest.mark.asyncio
    async def test_app_unknown_rejected(self):
        r = await self.jarvis.app_launcher.launch(
            VoiceCommand("", "app_launch", target="xyz_malware"))
        assert not r.success and "non reconnue" in r.message

    @pytest.mark.asyncio
    async def test_file_create_and_cleanup(self):
        r = await self.jarvis.file_manager.create(
            VoiceCommand("crée un fichier test_training_jarvis", "file_create",
                         target="test_training_jarvis"))
        assert r.success
        f = Path.home() / "Desktop" / "test_training_jarvis.txt"
        if f.exists():
            f.unlink()

    @pytest.mark.asyncio
    async def test_file_search_runs(self):
        r = await self.jarvis.file_manager.search(
            VoiceCommand("", "file_search", target="nonexistent_abc"))
        assert isinstance(r.success, bool)

    @pytest.mark.asyncio
    async def test_help_describes_capabilities(self):
        r = await self.jarvis._help(VoiceCommand("", "jarvis_help"))
        assert r.success and len(r.message) > 20

    @pytest.mark.asyncio
    async def test_status_reports(self):
        r = await self.jarvis._status(VoiceCommand("", "jarvis_status"))
        assert r.success and "JARVIS" in r.message

    @pytest.mark.asyncio
    async def test_quit_stops_running(self):
        self.jarvis._running = True
        await self.jarvis._quit(VoiceCommand("", "jarvis_quit"))
        assert not self.jarvis.is_running

    @pytest.mark.asyncio
    async def test_thanks_polite(self):
        r = await self.jarvis._thanks(VoiceCommand("", "jarvis_thanks"))
        assert r.success

    @pytest.mark.asyncio
    async def test_cancel_no_pending(self):
        r = await self.jarvis._cancel(VoiceCommand("", "jarvis_cancel"))
        assert r.success and "rien" in r.message.lower()

    @pytest.mark.asyncio
    async def test_unknown_command(self):
        r = await self.jarvis._unknown(VoiceCommand("bla", "unknown", target="bla"))
        assert not r.success

    # Nouveaux skills
    @pytest.mark.asyncio
    async def test_power_plan_runs(self):
        r = await self.jarvis.power_display.power_plan(VoiceCommand("", "power_plan"))
        assert isinstance(r.success, bool)

    @pytest.mark.asyncio
    async def test_resolution_runs(self):
        r = await self.jarvis.power_display.screen_resolution(VoiceCommand("", "display_resolution"))
        assert isinstance(r.success, bool)


# ============================================================
# CYCLE 4: Agents lifecycle complet
# ============================================================
class TestAgentsLifecycle:
    """Test complet du cycle de vie de chaque agent"""

    def setup_method(self):
        self.jarvis = Jarvis()

    @pytest.mark.asyncio
    async def test_dictation_full_cycle(self):
        # OFF -> ON
        assert not self.jarvis.dictation.active
        await self.jarvis.dictation.start(VoiceCommand("", "dictation_start"))
        assert self.jarvis.dictation.active

        # Détection stop
        assert self.jarvis.dictation.should_stop("arrête la dictée")
        assert self.jarvis.dictation.should_stop("fin de dictée")
        assert not self.jarvis.dictation.should_stop("bonjour")

        # ON -> OFF
        await self.jarvis.dictation.stop(VoiceCommand("", "dictation_stop"))
        assert not self.jarvis.dictation.active

    @pytest.mark.asyncio
    async def test_automation_full_cycle(self):
        # Crée macro
        await self.jarvis.automation.create(
            VoiceCommand("", "automation_create", target="test_cycle"))
        assert self.jarvis.automation.recording

        # Enregistre 3 étapes
        self.jarvis.automation.record_step("ouvre chrome")
        self.jarvis.automation.record_step("google python")
        self.jarvis.automation.record_step("ferme chrome")

        # Sauvegarde
        r = await self.jarvis.automation.stop_recording()
        assert r.success
        assert "test_cycle" in self.jarvis.automation.macros
        assert len(self.jarvis.automation.macros["test_cycle"]) == 3

        # Exécute
        r = await self.jarvis.automation.run(
            VoiceCommand("", "automation_run", target="test_cycle"))
        assert r.success
        assert len(r.data["macro_steps"]) == 3

        # Liste
        r = await self.jarvis.automation.list_macros(VoiceCommand("", ""))
        assert "test_cycle" in r.message

        # Supprime
        await self.jarvis.automation.delete_macro("test_cycle")
        assert "test_cycle" not in self.jarvis.automation.macros

    @pytest.mark.asyncio
    async def test_search_local_empty(self):
        results = self.jarvis.search._search_local("zzz_impossible_name_xyz")
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_navigation_all_settings_valid(self):
        from whisperflow.jarvis.agents.navigation_agent import SETTINGS_MAP, SHELL_FOLDERS
        for key, uri in SETTINGS_MAP.items():
            assert uri.startswith("ms-settings:"), f"{key} invalide: {uri}"
        for key, folder in SHELL_FOLDERS.items():
            assert folder.startswith("shell:"), f"{key} invalide: {folder}"


# ============================================================
# CYCLE 5: Pipeline complet (wake -> parse -> execute -> TTS)
# ============================================================
class TestFullPipelineExtended:
    """Pipeline complet avec TTS mocké"""

    def setup_method(self):
        self.jarvis = Jarvis()
        self.jarvis.tts.speak = AsyncMock()
        self.jarvis.tts.speak_status = AsyncMock()

    @pytest.mark.asyncio
    async def test_wake_only_responds(self):
        await self.jarvis.process_transcription("Jarvis")
        self.jarvis.tts.speak_status.assert_called_with("wake")

    @pytest.mark.asyncio
    async def test_no_wake_ignored(self):
        await self.jarvis.process_transcription("Bonjour le monde")
        self.jarvis.tts.speak.assert_not_called()

    @pytest.mark.asyncio
    async def test_partial_ignored(self):
        await self.jarvis.process_transcription("Jarvis ouvre chrome", is_partial=True)
        self.jarvis.tts.speak.assert_not_called()

    @pytest.mark.asyncio
    async def test_empty_ignored(self):
        await self.jarvis.process_transcription("")
        self.jarvis.tts.speak.assert_not_called()

    @pytest.mark.asyncio
    async def test_time_pipeline(self):
        await self.jarvis.process_transcription("Jarvis quelle heure est-il")
        self.jarvis.tts.speak.assert_called()
        assert "heure" in self.jarvis.tts.speak.call_args[0][0].lower()

    @pytest.mark.asyncio
    async def test_date_pipeline(self):
        await self.jarvis.process_transcription("Jarvis quel jour sommes-nous")
        self.jarvis.tts.speak.assert_called()

    @pytest.mark.asyncio
    async def test_help_pipeline(self):
        await self.jarvis.process_transcription("Jarvis aide")
        self.jarvis.tts.speak.assert_called()

    @pytest.mark.asyncio
    async def test_status_pipeline(self):
        await self.jarvis.process_transcription("Jarvis statut")
        self.jarvis.tts.speak.assert_called()
        assert "JARVIS" in self.jarvis.tts.speak.call_args[0][0]

    @pytest.mark.asyncio
    async def test_thanks_pipeline(self):
        await self.jarvis.process_transcription("Jarvis merci")
        self.jarvis.tts.speak.assert_called()

    @pytest.mark.asyncio
    async def test_unknown_pipeline(self):
        await self.jarvis.process_transcription("Jarvis fais un truc bizarre")
        self.jarvis.tts.speak.assert_called()

    @pytest.mark.asyncio
    async def test_quit_pipeline(self):
        self.jarvis._running = True
        await self.jarvis.process_transcription("Jarvis au revoir")
        assert not self.jarvis.is_running

    @pytest.mark.asyncio
    async def test_dictation_pipeline(self):
        await self.jarvis.process_transcription("Jarvis mode dictée")
        assert self.jarvis.dictation.active
        self.jarvis.tts.speak_status.assert_called()

    @pytest.mark.asyncio
    async def test_dictation_exit_pipeline(self):
        self.jarvis.dictation.active = True
        await self.jarvis.process_transcription("arrête la dictée")
        assert not self.jarvis.dictation.active

    @pytest.mark.asyncio
    async def test_macro_pipeline(self):
        await self.jarvis.process_transcription("Jarvis automatise test_pipe")
        assert self.jarvis.automation.recording
        await self.jarvis.process_transcription("monte le volume")
        assert len(self.jarvis.automation.current_macro_steps) == 1
        await self.jarvis.process_transcription("fin de macro")
        assert not self.jarvis.automation.recording

    @pytest.mark.asyncio
    async def test_app_launch_mocked(self):
        mock = AsyncMock(return_value=CommandResult(True, "OK"))
        self.jarvis.commander._handlers["app_launch"] = mock
        await self.jarvis.process_transcription("Jarvis ouvre chrome")
        mock.assert_called_once()

    @pytest.mark.asyncio
    async def test_battery_pipeline(self):
        await self.jarvis.process_transcription("Jarvis batterie")
        self.jarvis.tts.speak.assert_called()


# ============================================================
# CYCLE 6: Scénarios d'utilisation réelle multi-étapes
# ============================================================
class TestRealWorldScenariosExtended:
    """Scénarios quotidiens complets"""

    def setup_method(self):
        self.jarvis = Jarvis()
        self.jarvis.tts.speak = AsyncMock()
        self.jarvis.tts.speak_status = AsyncMock()

    @pytest.mark.asyncio
    async def test_scenario_01_morning_check(self):
        """Réveil: heure, date, batterie, météo"""
        await self.jarvis.process_transcription("Jarvis quelle heure est-il")
        assert "heure" in self.jarvis.tts.speak.call_args[0][0].lower()

        self.jarvis.tts.speak.reset_mock()
        await self.jarvis.process_transcription("Jarvis quel jour sommes-nous")
        assert self.jarvis.tts.speak.called

        self.jarvis.tts.speak.reset_mock()
        await self.jarvis.process_transcription("Jarvis batterie")
        assert self.jarvis.tts.speak.called

    @pytest.mark.asyncio
    async def test_scenario_02_work_setup(self):
        """Début de travail: ouvrir apps + volume"""
        mock_launch = AsyncMock(return_value=CommandResult(True, "OK"))
        self.jarvis.commander._handlers["app_launch"] = mock_launch

        await self.jarvis.process_transcription("Jarvis ouvre code")
        await self.jarvis.process_transcription("Jarvis ouvre chrome")
        await self.jarvis.process_transcription("Jarvis ouvre terminal")
        assert mock_launch.call_count == 3

    @pytest.mark.asyncio
    async def test_scenario_03_dictation_session(self):
        """Session dictée complète"""
        # Active dictée
        await self.jarvis.process_transcription("Jarvis mode dictée")
        assert self.jarvis.dictation.active

        # Simule du texte dicté (mock le process_text)
        with patch.object(self.jarvis.dictation, 'process_text',
                          new_callable=AsyncMock,
                          return_value=CommandResult(True, "")):
            await self.jarvis.process_transcription("Bonjour ceci est un test")
            await self.jarvis.process_transcription("Nous sommes en 2026")
            assert self.jarvis.dictation.process_text.call_count == 2

        # Arrête
        self.jarvis.dictation.active = True
        await self.jarvis.process_transcription("arrête la dictée")
        assert not self.jarvis.dictation.active

    @pytest.mark.asyncio
    async def test_scenario_04_web_research(self):
        """Session recherche web"""
        with patch('webbrowser.open') as mock_browser:
            await self.jarvis.process_transcription("Jarvis google intelligence artificielle")
            mock_browser.assert_called_once()
            assert "google.com/search" in mock_browser.call_args[0][0]

        with patch('webbrowser.open') as mock_browser:
            await self.jarvis.process_transcription("Jarvis youtube tutoriel python")
            assert "youtube.com" in mock_browser.call_args[0][0]

        with patch('webbrowser.open') as mock_browser:
            await self.jarvis.process_transcription("Jarvis wikipedia deep learning")
            assert "wikipedia" in mock_browser.call_args[0][0]

    @pytest.mark.asyncio
    async def test_scenario_05_file_management(self):
        """Gestion de fichiers"""
        r = await self.jarvis.file_manager.create(
            VoiceCommand("crée un dossier test_scenario", "file_create",
                         target="test_scenario"))
        assert r.success
        p = Path.home() / "Desktop" / "test_scenario"
        if p.exists():
            p.rmdir()

    @pytest.mark.asyncio
    async def test_scenario_06_macro_workflow(self):
        """Workflow macro complet"""
        # Enregistre
        await self.jarvis.process_transcription("Jarvis automatise routine_test_06")
        assert self.jarvis.automation.recording

        await self.jarvis.process_transcription("ouvre chrome")
        await self.jarvis.process_transcription("monte le volume")
        await self.jarvis.process_transcription("fin de macro")

        assert not self.jarvis.automation.recording
        assert "routine_test_06" in self.jarvis.automation.macros
        assert len(self.jarvis.automation.macros["routine_test_06"]) == 2

        # Nettoyage
        await self.jarvis.automation.delete_macro("routine_test_06")

    @pytest.mark.asyncio
    async def test_scenario_07_system_admin(self):
        """Admin système: check resources, processes"""
        r = await self.jarvis.process_mgr.system_resources(VoiceCommand("", ""))
        # May fail on CI but should not throw
        assert isinstance(r.success, bool)

        r = await self.jarvis.process_mgr.disk_space(VoiceCommand("", ""))
        assert isinstance(r.success, bool)

        r = await self.jarvis.process_mgr.uptime(VoiceCommand("", ""))
        assert isinstance(r.success, bool)

    @pytest.mark.asyncio
    async def test_scenario_08_end_of_day(self):
        """Fin de journée"""
        mock_close = AsyncMock(return_value=CommandResult(True, "OK"))
        self.jarvis.commander._handlers["app_close"] = mock_close

        await self.jarvis.process_transcription("Jarvis ferme chrome")
        assert mock_close.called

        self.jarvis._running = True
        await self.jarvis.process_transcription("Jarvis au revoir")
        assert not self.jarvis.is_running

    @pytest.mark.asyncio
    async def test_scenario_09_entertainment(self):
        """Divertissement: média + volume"""
        with patch('asyncio.create_subprocess_exec', new_callable=AsyncMock) as mock:
            mock.return_value.wait = AsyncMock()
            r = await self.jarvis.media_control.play(VoiceCommand("", "media_play"))
            assert r.success
            r = await self.jarvis.media_control.next_track(VoiceCommand("", "media_next"))
            assert r.success

    @pytest.mark.asyncio
    async def test_scenario_10_troubleshooting(self):
        """Dépannage: network, processes"""
        # Vérification réseau
        r = await self.jarvis.network.ping(
            VoiceCommand("", "network_ping", target="localhost"))
        # localhost devrait toujours répondre
        assert isinstance(r.success, bool)


# ============================================================
# CYCLE 7: Edge cases et récupération d'erreurs
# ============================================================
class TestEdgeCases:

    def setup_method(self):
        self.jarvis = Jarvis()
        self.jarvis.tts.speak = AsyncMock()
        self.jarvis.tts.speak_status = AsyncMock()

    @pytest.mark.asyncio
    async def test_empty_string(self):
        await self.jarvis.process_transcription("")
        self.jarvis.tts.speak.assert_not_called()

    @pytest.mark.asyncio
    async def test_whitespace_only(self):
        await self.jarvis.process_transcription("   \n\t  ")
        self.jarvis.tts.speak.assert_not_called()

    @pytest.mark.asyncio
    async def test_very_long_text(self):
        text = "Jarvis " + "a" * 5000
        await self.jarvis.process_transcription(text)
        # Should not crash

    @pytest.mark.asyncio
    async def test_special_characters(self):
        await self.jarvis.process_transcription("Jarvis @#$%^&*()")
        # Should handle gracefully

    @pytest.mark.asyncio
    async def test_unicode_text(self):
        await self.jarvis.process_transcription("Jarvis éàüöñ 日本語")
        # Should not crash

    @pytest.mark.asyncio
    async def test_repeated_wake_word(self):
        await self.jarvis.process_transcription("Jarvis Jarvis Jarvis")
        # Should parse and respond

    @pytest.mark.asyncio
    async def test_cancel_without_pending(self):
        r = await self.jarvis._cancel(VoiceCommand("", "jarvis_cancel"))
        assert r.success and "rien" in r.message.lower()

    @pytest.mark.asyncio
    async def test_repeat_without_previous(self):
        r = await self.jarvis._repeat(VoiceCommand("", "jarvis_repeat"))
        assert not r.success

    @pytest.mark.asyncio
    async def test_process_kill_invalid_name(self):
        r = await self.jarvis.process_mgr.kill_process(
            VoiceCommand("", "process_kill", target="../../bad"))
        assert not r.success

    @pytest.mark.asyncio
    async def test_volume_set_not_number(self):
        r = await self.jarvis.system_control.volume_set(
            VoiceCommand("", "system_volume_set", target="abc"))
        assert not r.success

    @pytest.mark.asyncio
    async def test_brightness_not_number(self):
        r = await self.jarvis.system_control.brightness(
            VoiceCommand("", "system_brightness", target="haut"))
        assert not r.success

    @pytest.mark.asyncio
    async def test_ping_invalid_host(self):
        r = await self.jarvis.network.ping(
            VoiceCommand("", "network_ping", target="invalid;rm -rf /"))
        assert not r.success


# ============================================================
# CYCLE 8: Mode switching (normal -> dictée -> macro -> normal)
# ============================================================
class TestModeSwitching:

    def setup_method(self):
        self.jarvis = Jarvis()
        self.jarvis.tts.speak = AsyncMock()
        self.jarvis.tts.speak_status = AsyncMock()

    @pytest.mark.asyncio
    async def test_normal_to_dictation_to_normal(self):
        assert not self.jarvis.dictation.active
        assert not self.jarvis.automation.recording

        # Enter dictation
        await self.jarvis.process_transcription("Jarvis mode dictée")
        assert self.jarvis.dictation.active

        # Exit dictation
        await self.jarvis.process_transcription("arrête la dictée")
        assert not self.jarvis.dictation.active

    @pytest.mark.asyncio
    async def test_normal_to_macro_to_normal(self):
        # Enter macro recording
        await self.jarvis.process_transcription("Jarvis automatise test_switch")
        assert self.jarvis.automation.recording

        # Record step
        await self.jarvis.process_transcription("ouvre chrome")
        assert len(self.jarvis.automation.current_macro_steps) == 1

        # Exit macro
        await self.jarvis.process_transcription("fin de macro")
        assert not self.jarvis.automation.recording

        # Cleanup
        await self.jarvis.automation.delete_macro("test_switch")

    @pytest.mark.asyncio
    async def test_dictation_blocks_commands(self):
        """En mode dictée, les commandes normales sont traitées comme texte"""
        self.jarvis.dictation.active = True

        with patch.object(self.jarvis.dictation, 'process_text',
                          new_callable=AsyncMock,
                          return_value=CommandResult(True, "")) as mock:
            await self.jarvis.process_transcription("ouvre chrome")
            mock.assert_called_with("ouvre chrome")

        self.jarvis.dictation.active = False

    @pytest.mark.asyncio
    async def test_macro_records_everything(self):
        """En mode macro, tout est enregistré"""
        self.jarvis.automation.recording = True
        self.jarvis.automation.current_macro_name = "test_rec"
        self.jarvis.automation.current_macro_steps = []

        await self.jarvis.process_transcription("ouvre chrome")
        await self.jarvis.process_transcription("monte le volume")
        assert len(self.jarvis.automation.current_macro_steps) == 2

        self.jarvis.automation.recording = False


# ============================================================
# CYCLE 9: Bilingue FR/EN
# ============================================================
class TestBilingual:
    """Vérifie que les commandes marchent en français ET en anglais"""

    def setup_method(self):
        self.c = Commander()

    @pytest.mark.parametrize("fr,en,intent", [
        ("ouvre chrome", "open chrome", "app_launch"),
        ("ferme notepad", "close notepad", "app_close"),
        ("cherche rapport", "search rapport", "file_search"),
        ("aide", "help", "jarvis_help"),
        ("au revoir", "goodbye", "jarvis_quit"),
        ("merci", "thanks", "jarvis_thanks"),
        ("répète", "repeat", "jarvis_repeat"),
        ("annule", "cancel", "jarvis_cancel"),
        ("muet", "mute", "system_mute"),
        ("play", "lecture", "media_play"),
    ])
    def test_bilingual_commands(self, fr, en, intent):
        assert self.c.parse(fr).intent == intent
        assert self.c.parse(en).intent == intent


# ============================================================
# CYCLE 10: Stress test - commandes rapides enchaînées
# ============================================================
class TestStressRapidCommands:
    """Simule des commandes rapides sans délai"""

    def setup_method(self):
        self.jarvis = Jarvis()
        self.jarvis.tts.speak = AsyncMock()
        self.jarvis.tts.speak_status = AsyncMock()

    @pytest.mark.asyncio
    async def test_rapid_10_commands(self):
        """10 commandes enchaînées sans crash"""
        commands = [
            "Jarvis quelle heure est-il",
            "Jarvis quel jour sommes-nous",
            "Jarvis batterie",
            "Jarvis aide",
            "Jarvis statut",
            "Jarvis merci",
            "Jarvis quelle heure",
            "Jarvis date",
            "Jarvis aide",
            "Jarvis statut",
        ]
        for cmd in commands:
            await self.jarvis.process_transcription(cmd)
        assert self.jarvis.tts.speak.call_count >= 10

    @pytest.mark.asyncio
    async def test_rapid_mode_switches(self):
        """Switchs rapides entre modes"""
        await self.jarvis.process_transcription("Jarvis mode dictée")
        assert self.jarvis.dictation.active
        await self.jarvis.process_transcription("arrête la dictée")
        assert not self.jarvis.dictation.active

        await self.jarvis.process_transcription("Jarvis automatise rapide")
        assert self.jarvis.automation.recording
        await self.jarvis.process_transcription("fin de macro")
        assert not self.jarvis.automation.recording

        await self.jarvis.process_transcription("Jarvis mode dictée")
        assert self.jarvis.dictation.active
        await self.jarvis.process_transcription("arrête la dictée")
        assert not self.jarvis.dictation.active

        # Cleanup
        await self.jarvis.automation.delete_macro("rapide")

    @pytest.mark.asyncio
    async def test_50_wake_word_checks(self):
        """50 vérifications wake word rapides"""
        for i in range(50):
            detected, _ = detect_wake_word(f"Jarvis commande {i}")
            assert detected


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-x"])
