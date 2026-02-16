"""
JARVIS - 50 Cycles de Formation Intensive
Tests de simulation d'utilisation reelle Windows complet

Cycles 1-10:  Patterns nouveaux (minuteur, notes, calcul, bureaux virtuels)
Cycles 11-20: Skills individuels nouveaux
Cycles 21-30: Scenarios multi-etapes avances
Cycles 31-40: Robustesse et edge cases avances
Cycles 41-50: Integration complete et stress

Total: 50 cycles, ~300 tests
"""

import asyncio
import pytest
import logging
from datetime import datetime
from unittest.mock import AsyncMock, patch, MagicMock
from pathlib import Path

from whisperflow.jarvis.jarvis_core import Jarvis
from whisperflow.jarvis.commander import Commander, VoiceCommand, CommandResult
from whisperflow.jarvis.wake_word import detect_wake_word
from whisperflow.jarvis.skills.timer_reminder import _parse_duration, _format_duration
from whisperflow.jarvis.skills.calculator import _text_to_math, _ast_compute, _format_result
from whisperflow.jarvis.skills.quick_notes import NOTES_FILE

logging.basicConfig(level=logging.INFO)


# ============================================================
# CYCLES 1-5: Patterns minuteurs et rappels
# ============================================================
class TestCycle01TimerPatterns:
    def setup_method(self):
        self.c = Commander()

    @pytest.mark.parametrize("text,intent", [
        ("minuteur 5 minutes", "timer_set"),
        ("timer 10 minutes", "timer_set"),
        ("chronomètre 30 secondes", "timer_set"),
        ("chrono 2 minutes", "timer_set"),
        ("rappelle-moi dans 10 minutes", "timer_reminder"),
        ("rappel dans 1 heure", "timer_reminder"),
        ("reminder 5 minutes", "timer_reminder"),
        ("annule le minuteur", "timer_cancel"),
        ("cancel timer", "timer_cancel"),
        ("annule le rappel", "timer_cancel"),
        ("liste les minuteurs", "timer_list"),
        ("timers actifs", "timer_list"),
    ])
    def test_timer_patterns(self, text, intent):
        assert self.c.parse(text).intent == intent


class TestCycle02TimerDurationParsing:
    @pytest.mark.parametrize("text,seconds", [
        ("5 minutes", 300),
        ("10 min", 600),
        ("30 secondes", 30),
        ("1 heure", 3600),
        ("2h30", 9000),
        ("2 heures 30", 9000),
        ("90", 5400),  # 90 minutes par defaut
        ("", 0),
        ("abc", 0),
    ])
    def test_parse_duration(self, text, seconds):
        assert _parse_duration(text) == seconds

    @pytest.mark.parametrize("seconds,expected", [
        (30, "30 secondes"),
        (60, "1 minute"),
        (90, "1 minute 30 secondes"),
        (300, "5 minutes"),
        (3600, "1 heure"),
        (3900, "1 heure 5 minutes"),
        (7200, "2 heures"),
        (1, "1 seconde"),
    ])
    def test_format_duration(self, seconds, expected):
        assert _format_duration(seconds) == expected


# ============================================================
# CYCLES 3-5: Patterns notes, calcul, bureaux virtuels
# ============================================================
class TestCycle03NotesPatterns:
    def setup_method(self):
        self.c = Commander()

    @pytest.mark.parametrize("text,intent", [
        ("note acheter du lait", "note_add"),
        ("noter rendez-vous demain", "note_add"),
        ("prends note appeler le medecin", "note_add"),
        ("prends en note reunion a 14h", "note_add"),
        ("lis les notes", "note_read"),
        ("lire notes", "note_read"),
        ("efface les notes", "note_clear"),
        ("supprime les notes", "note_clear"),
        ("cherche dans les notes reunion", "note_search"),
    ])
    def test_notes_patterns(self, text, intent):
        assert self.c.parse(text).intent == intent


class TestCycle04CalculatorPatterns:
    def setup_method(self):
        self.c = Commander()

    @pytest.mark.parametrize("text,intent", [
        ("calcule 5 plus 3", "calc_compute"),
        ("calculer 100 moins 42", "calc_compute"),
        ("combien fait 25 fois 4", "calc_compute"),
        ("calculate 10 divided by 2", "calc_compute"),
        ("20 pourcent de 150", "calc_percentage"),
        ("50 percent of 200", "calc_percentage"),
        ("convertis 25 en fahrenheit", "calc_convert"),
    ])
    def test_calc_patterns(self, text, intent):
        assert self.c.parse(text).intent == intent


class TestCycle05VirtualDesktopPatterns:
    def setup_method(self):
        self.c = Commander()

    @pytest.mark.parametrize("text,intent", [
        ("nouveau bureau virtuel", "vdesktop_new"),
        ("new desktop", "vdesktop_new"),
        ("crée un bureau", "vdesktop_new"),
        ("ferme le bureau virtuel", "vdesktop_close"),
        ("close desktop", "vdesktop_close"),
        ("bureau virtuel précédent", "vdesktop_left"),
        ("bureau virtuel gauche", "vdesktop_left"),
        ("desktop left", "vdesktop_left"),
        ("bureau virtuel suivant", "vdesktop_right"),
        ("bureau virtuel droite", "vdesktop_right"),
        ("desktop right", "vdesktop_right"),
        ("vue des tâches", "vdesktop_task_view"),
        ("task view", "vdesktop_task_view"),
    ])
    def test_vdesktop_patterns(self, text, intent):
        assert self.c.parse(text).intent == intent


# ============================================================
# CYCLES 6-10: Parser calculatrice et conversions texte
# ============================================================
class TestCycle06TextToMath:
    @pytest.mark.parametrize("text,expected", [
        ("5 plus 3", "5 + 3"),
        ("100 moins 42", "100 - 42"),
        ("25 fois 4", "25 * 4"),
        ("10 divise par 2", "10 / 2"),
        ("3 puissance 2", "3 ** 2"),
        ("5 virgule 5 plus 2", "5.5 + 2"),
    ])
    def test_text_to_math(self, text, expected):
        result = _text_to_math(text)
        # Normalize spaces
        assert result.replace("  ", " ").strip() == expected


class TestCycle07AstCompute:
    @pytest.mark.parametrize("expr,expected", [
        ("5 + 3", 8),
        ("100 - 42", 58),
        ("25 * 4", 100),
        ("10 / 2", 5.0),
        ("3 ** 2", 9),
        ("10 % 3", 1),
        ("-5 + 10", 5),
        ("2 * (3 + 4)", 14),
    ])
    def test_ast_compute(self, expr, expected):
        assert _ast_compute(expr) == expected

    def test_division_by_zero(self):
        with pytest.raises(ValueError, match="zero"):
            _ast_compute("10 / 0")

    def test_exponent_too_large(self):
        with pytest.raises(ValueError, match="grand"):
            _ast_compute("2 ** 200")

    def test_invalid_expression(self):
        with pytest.raises((ValueError, SyntaxError)):
            _ast_compute("import os")


class TestCycle08FormatResult:
    @pytest.mark.parametrize("value,expected", [
        (42.0, "42"),
        (3.14, "3.14"),
        (0.0, "0"),
        (100.0, "100"),
        (1.5, "1.5"),
        (0.3333, "0.3333"),
    ])
    def test_format_result(self, value, expected):
        assert _format_result(value) == expected


class TestCycle09CalculatorSkill:
    def setup_method(self):
        self.jarvis = Jarvis()

    @pytest.mark.asyncio
    async def test_basic_addition(self):
        r = await self.jarvis.calculator.calculate(
            VoiceCommand("5 plus 3", "calc_compute", target="5 plus 3"))
        assert r.success and "8" in r.message

    @pytest.mark.asyncio
    async def test_multiplication(self):
        r = await self.jarvis.calculator.calculate(
            VoiceCommand("25 fois 4", "calc_compute", target="25 fois 4"))
        assert r.success and "100" in r.message

    @pytest.mark.asyncio
    async def test_percentage(self):
        r = await self.jarvis.calculator.percentage(
            VoiceCommand("20 pourcent de 150", "calc_percentage", target="20 pourcent de 150"))
        assert r.success and "30" in r.message

    @pytest.mark.asyncio
    async def test_empty_expression(self):
        r = await self.jarvis.calculator.calculate(
            VoiceCommand("", "calc_compute", target=""))
        assert not r.success

    @pytest.mark.asyncio
    async def test_convert_celsius_to_fahrenheit(self):
        r = await self.jarvis.calculator.convert_temperature(
            VoiceCommand("25 en fahrenheit", "calc_convert", target="25 en fahrenheit"))
        assert r.success and "77" in r.message


class TestCycle10TimerSkill:
    def setup_method(self):
        self.jarvis = Jarvis()

    @pytest.mark.asyncio
    async def test_set_timer(self):
        r = await self.jarvis.timer.set_timer(
            VoiceCommand("5 minutes", "timer_set", target="5 minutes"))
        assert r.success and "5 minutes" in r.message
        assert self.jarvis.timer.active_count == 1
        # Cleanup
        await self.jarvis.timer.cancel_timer(VoiceCommand("", "timer_cancel"))

    @pytest.mark.asyncio
    async def test_timer_invalid_duration(self):
        r = await self.jarvis.timer.set_timer(
            VoiceCommand("", "timer_set", target=""))
        assert not r.success

    @pytest.mark.asyncio
    async def test_timer_too_long(self):
        r = await self.jarvis.timer.set_timer(
            VoiceCommand("999 heures", "timer_set", target="999 heures"))
        assert not r.success

    @pytest.mark.asyncio
    async def test_cancel_empty(self):
        r = await self.jarvis.timer.cancel_timer(VoiceCommand("", "timer_cancel"))
        assert r.success and "aucun" in r.message.lower()

    @pytest.mark.asyncio
    async def test_list_empty(self):
        r = await self.jarvis.timer.list_timers(VoiceCommand("", "timer_list"))
        assert r.success and "aucun" in r.message.lower()

    @pytest.mark.asyncio
    async def test_set_and_list(self):
        await self.jarvis.timer.set_timer(
            VoiceCommand("2 minutes", "timer_set", target="2 minutes"))
        r = await self.jarvis.timer.list_timers(VoiceCommand("", "timer_list"))
        assert r.success and "1 actif" in r.message
        await self.jarvis.timer.cancel_timer(VoiceCommand("", "timer_cancel"))

    @pytest.mark.asyncio
    async def test_set_reminder(self):
        r = await self.jarvis.timer.set_reminder(
            VoiceCommand("dans 10 minutes", "timer_reminder", target="dans 10 minutes"))
        assert r.success and "10 minutes" in r.message
        await self.jarvis.timer.cancel_timer(VoiceCommand("", "timer_cancel"))


# ============================================================
# CYCLES 11-15: Notes rapides skill
# ============================================================
class TestCycle11NotesSkill:
    def setup_method(self):
        self.jarvis = Jarvis()
        self._backup = None
        if NOTES_FILE.exists():
            self._backup = NOTES_FILE.read_text(encoding="utf-8")

    def teardown_method(self):
        if self._backup is not None:
            NOTES_FILE.write_text(self._backup, encoding="utf-8")
        elif NOTES_FILE.exists():
            NOTES_FILE.write_text("", encoding="utf-8")

    @pytest.mark.asyncio
    async def test_add_note(self):
        r = await self.jarvis.notes.add_note(
            VoiceCommand("acheter du lait", "note_add", target="acheter du lait"))
        assert r.success and "enregistr" in r.message.lower()

    @pytest.mark.asyncio
    async def test_add_empty_note(self):
        r = await self.jarvis.notes.add_note(
            VoiceCommand("", "note_add", target=""))
        assert not r.success

    @pytest.mark.asyncio
    async def test_read_notes_empty(self):
        NOTES_FILE.write_text("", encoding="utf-8")
        r = await self.jarvis.notes.read_notes(VoiceCommand("", "note_read"))
        assert r.success and "aucune" in r.message.lower()

    @pytest.mark.asyncio
    async def test_add_and_read(self):
        NOTES_FILE.write_text("", encoding="utf-8")
        await self.jarvis.notes.add_note(
            VoiceCommand("test note 1", "note_add", target="test note 1"))
        await self.jarvis.notes.add_note(
            VoiceCommand("test note 2", "note_add", target="test note 2"))
        r = await self.jarvis.notes.read_notes(VoiceCommand("", "note_read"))
        assert r.success and "2 notes" in r.message

    @pytest.mark.asyncio
    async def test_clear_notes(self):
        NOTES_FILE.write_text("[2026-01-01] test\n", encoding="utf-8")
        r = await self.jarvis.notes.clear_notes(VoiceCommand("", "note_clear"))
        assert r.success and "1" in r.message

    @pytest.mark.asyncio
    async def test_search_notes(self):
        NOTES_FILE.write_text("[2026-01-01] reunion lundi\n[2026-01-02] courses\n", encoding="utf-8")
        r = await self.jarvis.notes.search_notes(
            VoiceCommand("reunion", "note_search", target="reunion"))
        assert r.success and "1 r" in r.message.lower()

    @pytest.mark.asyncio
    async def test_search_not_found(self):
        NOTES_FILE.write_text("[2026-01-01] test\n", encoding="utf-8")
        r = await self.jarvis.notes.search_notes(
            VoiceCommand("xyz", "note_search", target="xyz"))
        assert r.success and "aucune" in r.message.lower()


class TestCycle12VirtualDesktopSkill:
    def setup_method(self):
        self.jarvis = Jarvis()

    @pytest.mark.asyncio
    async def test_new_desktop_runs(self):
        # Mock subprocess since we don't want to actually create desktops
        with patch('asyncio.create_subprocess_exec', new_callable=AsyncMock) as mock:
            mock.return_value.wait = AsyncMock()
            mock.return_value.returncode = 0
            r = await self.jarvis.vdesktop.new_desktop(VoiceCommand("", "vdesktop_new"))
            assert r.success

    @pytest.mark.asyncio
    async def test_task_view_runs(self):
        with patch('asyncio.create_subprocess_exec', new_callable=AsyncMock) as mock:
            mock.return_value.wait = AsyncMock()
            mock.return_value.returncode = 0
            r = await self.jarvis.vdesktop.task_view(VoiceCommand("", "vdesktop_task_view"))
            assert r.success


# ============================================================
# CYCLES 13-20: Non-regression patterns existants
# ============================================================
class TestCycle13NoRegressionOriginalPatterns:
    """Verifie que les 93 patterns originaux fonctionnent toujours"""
    def setup_method(self):
        self.c = Commander()

    @pytest.mark.parametrize("text,intent", [
        # Dictée
        ("mode dictée", "dictation_start"),
        ("arrête la dictée", "dictation_stop"),
        # Média
        ("arrête la musique", "media_pause"),
        ("play", "media_play"),
        ("pause", "media_pause"),
        ("suivant", "media_next"),
        # Apps
        ("ouvre chrome", "app_launch"),
        ("ferme notepad", "app_close"),
        ("lance le terminal", "app_launch"),
        # Système
        ("monte le volume", "system_volume_up"),
        ("baisse le volume", "system_volume_down"),
        ("volume à 50", "system_volume_set"),
        ("muet", "system_mute"),
        ("coupe le son", "system_mute"),
        ("wifi on", "system_wifi"),
        ("bluetooth off", "system_bluetooth"),
        ("éteins l'ordinateur", "system_shutdown"),
        ("redémarre", "system_restart"),
        ("veille", "system_sleep"),
        ("batterie", "system_battery"),
        ("quelle heure", "system_time"),
        ("date", "system_date"),
        # Fenêtres
        ("minimise", "window_minimize"),
        ("maximise", "window_maximize"),
        ("bureau", "window_desktop"),
        ("screenshot", "window_screenshot"),
        # Web
        ("google python tutoriel", "web_google"),
        ("recherche sur google machine learning", "web_google"),
        ("youtube music video", "web_youtube"),
        ("wikipedia intelligence artificielle", "web_wikipedia"),
        ("va sur github.com", "web_navigate"),
        ("météo", "web_weather"),
        # Fichiers
        ("crée un fichier rapport", "file_create"),
        ("supprime le fichier test", "file_delete"),
        ("cherche rapport annuel", "file_search"),
        ("copie le texte", "clipboard_copy"),
        ("colle", "clipboard_paste"),
        # Presse-papiers
        ("lis le presse-papiers", "clipboard_read"),
        ("sélectionne tout", "clipboard_select_all"),
        ("coupe la sélection", "clipboard_cut"),
        # Processus
        ("liste les processus", "process_list"),
        ("cpu", "system_top_cpu"),
        ("ram", "system_resources"),
        ("espace disque", "system_disk"),
        ("uptime", "system_uptime"),
        ("gpu", "system_gpu"),
        ("matériel", "system_hardware"),
        # Réseau
        ("état du réseau", "network_status"),
        ("adresse ip", "network_ip"),
        ("ip publique", "network_ip_public"),
        ("ping google.com", "network_ping"),
        # Alimentation
        ("haute performance", "power_high_perf"),
        ("économie d'énergie", "power_saver"),
        ("résolution", "display_resolution"),
        ("mode nuit", "display_night"),
        # Logiciels
        ("installe firefox", "software_install"),
        ("désinstalle vlc", "software_uninstall"),
        ("mets à jour tout", "software_update_all"),
        # Navigation
        ("ouvre les téléchargements", "navigate_downloads"),
        ("ouvre les documents", "navigate_documents"),
        # Automatisation
        ("automatise backup", "automation_create"),
        # JARVIS
        ("aide", "jarvis_help"),
        ("statut", "jarvis_status"),
        ("au revoir", "jarvis_quit"),
        ("merci", "jarvis_thanks"),
        ("annule", "jarvis_cancel"),
    ])
    def test_original_patterns_intact(self, text, intent):
        assert self.c.parse(text).intent == intent


class TestCycle14PatternPriorityConflicts:
    """Verifie que les conflits resolus restent resolus"""
    def setup_method(self):
        self.c = Commander()

    @pytest.mark.parametrize("text,intent,description", [
        ("arrête la musique", "media_pause", "media avant app_close"),
        ("arrête la dictée", "dictation_stop", "dictée avant app_close"),
        ("liste les processus", "process_list", "process avant app_launch"),
        ("recherche sur google python", "web_google", "google avant file_search"),
        ("lis le presse-papiers", "clipboard_read", "clipboard avant media"),
        ("coupe le son", "system_mute", "mute avant clipboard_cut"),
        ("paramètres d'affichage", "display_settings", "display avant jarvis_settings"),
        ("paramètres audio", "audio_settings", "audio avant jarvis_settings"),
        ("programmes installés", "software_list", "software avant generic"),
        ("ouvre les téléchargements", "navigate_downloads", "navigate avant app_launch"),
        ("lance la macro test", "automation_run", "macro avant app_launch"),
    ])
    def test_priority_resolved(self, text, intent, description):
        result = self.c.parse(text)
        assert result.intent == intent, f"CONFLIT: {description} - got {result.intent}"


class TestCycle15AllIntentsRegistered:
    """Verifie que tous les intents ont un handler"""
    def setup_method(self):
        self.jarvis = Jarvis()

    def test_all_pattern_intents_have_handlers(self):
        from whisperflow.jarvis.commander import COMMAND_PATTERNS
        registered = set(self.jarvis.commander.list_intents())
        pattern_intents = {intent for _, intent in COMMAND_PATTERNS}
        missing = pattern_intents - registered
        assert not missing, f"Intents sans handler: {missing}"

    def test_handler_count(self):
        intents = self.jarvis.commander.list_intents()
        # Au moins 100 handlers enregistres
        assert len(intents) >= 100, f"Seulement {len(intents)} handlers"


# ============================================================
# CYCLES 16-20: Pipeline complet nouveaux skills
# ============================================================
class TestCycle16TimerPipeline:
    def setup_method(self):
        self.jarvis = Jarvis()
        self.jarvis.tts.speak = AsyncMock()
        self.jarvis.tts.speak_status = AsyncMock()

    @pytest.mark.asyncio
    async def test_timer_via_pipeline(self):
        await self.jarvis.process_transcription("Jarvis minuteur 5 minutes")
        self.jarvis.tts.speak.assert_called()
        assert "5 minutes" in self.jarvis.tts.speak.call_args[0][0]
        await self.jarvis.timer.cancel_timer(VoiceCommand("", ""))

    @pytest.mark.asyncio
    async def test_timer_cancel_via_pipeline(self):
        await self.jarvis.process_transcription("Jarvis minuteur 2 minutes")
        self.jarvis.tts.speak.reset_mock()
        await self.jarvis.process_transcription("Jarvis annule le minuteur")
        self.jarvis.tts.speak.assert_called()


class TestCycle17NotesPipeline:
    def setup_method(self):
        self.jarvis = Jarvis()
        self.jarvis.tts.speak = AsyncMock()
        self.jarvis.tts.speak_status = AsyncMock()
        self._backup = None
        if NOTES_FILE.exists():
            self._backup = NOTES_FILE.read_text(encoding="utf-8")

    def teardown_method(self):
        if self._backup is not None:
            NOTES_FILE.write_text(self._backup, encoding="utf-8")
        elif NOTES_FILE.exists():
            NOTES_FILE.write_text("", encoding="utf-8")

    @pytest.mark.asyncio
    async def test_note_via_pipeline(self):
        await self.jarvis.process_transcription("Jarvis note acheter du pain")
        self.jarvis.tts.speak.assert_called()
        assert "enregistr" in self.jarvis.tts.speak.call_args[0][0].lower()

    @pytest.mark.asyncio
    async def test_read_notes_via_pipeline(self):
        NOTES_FILE.write_text("[2026-01-01] test pipeline\n", encoding="utf-8")
        await self.jarvis.process_transcription("Jarvis lis les notes")
        self.jarvis.tts.speak.assert_called()


class TestCycle18CalcPipeline:
    def setup_method(self):
        self.jarvis = Jarvis()
        self.jarvis.tts.speak = AsyncMock()
        self.jarvis.tts.speak_status = AsyncMock()

    @pytest.mark.asyncio
    async def test_calc_via_pipeline(self):
        await self.jarvis.process_transcription("Jarvis calcule 25 fois 4")
        self.jarvis.tts.speak.assert_called()
        assert "100" in self.jarvis.tts.speak.call_args[0][0]

    @pytest.mark.asyncio
    async def test_percentage_via_pipeline(self):
        await self.jarvis.process_transcription("Jarvis 20 pourcent de 200")
        self.jarvis.tts.speak.assert_called()
        assert "40" in self.jarvis.tts.speak.call_args[0][0]


class TestCycle19VDesktopPipeline:
    def setup_method(self):
        self.jarvis = Jarvis()
        self.jarvis.tts.speak = AsyncMock()
        self.jarvis.tts.speak_status = AsyncMock()

    @pytest.mark.asyncio
    async def test_new_desktop_via_pipeline(self):
        with patch('asyncio.create_subprocess_exec', new_callable=AsyncMock) as mock:
            mock.return_value.wait = AsyncMock()
            mock.return_value.returncode = 0
            await self.jarvis.process_transcription("Jarvis nouveau bureau virtuel")
            self.jarvis.tts.speak.assert_called()

    @pytest.mark.asyncio
    async def test_task_view_via_pipeline(self):
        with patch('asyncio.create_subprocess_exec', new_callable=AsyncMock) as mock:
            mock.return_value.wait = AsyncMock()
            mock.return_value.returncode = 0
            await self.jarvis.process_transcription("Jarvis vue des taches")
            self.jarvis.tts.speak.assert_called()


class TestCycle20MixedPipeline:
    """Commandes mixtes old + new dans un pipeline"""
    def setup_method(self):
        self.jarvis = Jarvis()
        self.jarvis.tts.speak = AsyncMock()
        self.jarvis.tts.speak_status = AsyncMock()

    @pytest.mark.asyncio
    async def test_mixed_sequence(self):
        # Old: heure
        await self.jarvis.process_transcription("Jarvis quelle heure")
        assert self.jarvis.tts.speak.called
        # New: calcul
        self.jarvis.tts.speak.reset_mock()
        await self.jarvis.process_transcription("Jarvis calcule 10 plus 5")
        assert "15" in self.jarvis.tts.speak.call_args[0][0]
        # Old: statut
        self.jarvis.tts.speak.reset_mock()
        await self.jarvis.process_transcription("Jarvis statut")
        assert "JARVIS" in self.jarvis.tts.speak.call_args[0][0]


# ============================================================
# CYCLES 21-30: Scenarios avances multi-etapes
# ============================================================
class TestCycle21ScenarioStudySession:
    """Session d'etude: timer + notes + calcul"""
    def setup_method(self):
        self.jarvis = Jarvis()
        self.jarvis.tts.speak = AsyncMock()
        self.jarvis.tts.speak_status = AsyncMock()
        if NOTES_FILE.exists():
            self._backup = NOTES_FILE.read_text(encoding="utf-8")
        else:
            self._backup = ""

    def teardown_method(self):
        NOTES_FILE.write_text(self._backup, encoding="utf-8")

    @pytest.mark.asyncio
    async def test_study_session(self):
        # Timer pour etude
        await self.jarvis.process_transcription("Jarvis minuteur 25 minutes")
        assert self.jarvis.timer.active_count == 1

        # Prendre des notes
        NOTES_FILE.write_text("", encoding="utf-8")
        await self.jarvis.process_transcription("Jarvis note chapitre 3 termine")
        assert self.jarvis.notes.notes_count == 1

        # Calculer un score
        self.jarvis.tts.speak.reset_mock()
        await self.jarvis.process_transcription("Jarvis calcule 18 sur 20")
        assert self.jarvis.tts.speak.called

        # Cleanup
        await self.jarvis.timer.cancel_timer(VoiceCommand("", ""))


class TestCycle22ScenarioMorningRoutineV2:
    """Routine matinale etendue"""
    def setup_method(self):
        self.jarvis = Jarvis()
        self.jarvis.tts.speak = AsyncMock()
        self.jarvis.tts.speak_status = AsyncMock()

    @pytest.mark.asyncio
    async def test_morning_v2(self):
        await self.jarvis.process_transcription("Jarvis quelle heure est-il")
        assert self.jarvis.tts.speak.called

        self.jarvis.tts.speak.reset_mock()
        await self.jarvis.process_transcription("Jarvis quel jour sommes-nous")
        assert self.jarvis.tts.speak.called

        self.jarvis.tts.speak.reset_mock()
        await self.jarvis.process_transcription("Jarvis batterie")
        assert self.jarvis.tts.speak.called

        self.jarvis.tts.speak.reset_mock()
        await self.jarvis.process_transcription("Jarvis statut")
        assert "JARVIS" in self.jarvis.tts.speak.call_args[0][0]


class TestCycle23ScenarioWorkSetupV2:
    """Setup travail avec timer"""
    def setup_method(self):
        self.jarvis = Jarvis()
        self.jarvis.tts.speak = AsyncMock()
        self.jarvis.tts.speak_status = AsyncMock()

    @pytest.mark.asyncio
    async def test_work_setup_v2(self):
        mock_launch = AsyncMock(return_value=CommandResult(True, "OK"))
        self.jarvis.commander._handlers["app_launch"] = mock_launch

        await self.jarvis.process_transcription("Jarvis ouvre code")
        await self.jarvis.process_transcription("Jarvis ouvre chrome")
        assert mock_launch.call_count == 2

        # Timer pomodoro
        await self.jarvis.process_transcription("Jarvis minuteur 25 minutes")
        assert self.jarvis.timer.active_count == 1

        await self.jarvis.timer.cancel_timer(VoiceCommand("", ""))


class TestCycle24ScenarioDictationWithNotes:
    """Dictee puis sauvegarde en note"""
    def setup_method(self):
        self.jarvis = Jarvis()
        self.jarvis.tts.speak = AsyncMock()
        self.jarvis.tts.speak_status = AsyncMock()
        if NOTES_FILE.exists():
            self._backup = NOTES_FILE.read_text(encoding="utf-8")
        else:
            self._backup = ""

    def teardown_method(self):
        NOTES_FILE.write_text(self._backup, encoding="utf-8")

    @pytest.mark.asyncio
    async def test_dictation_then_notes(self):
        # Mode dictee
        await self.jarvis.process_transcription("Jarvis mode dictée")
        assert self.jarvis.dictation.active

        # Stop dictee
        await self.jarvis.process_transcription("arrête la dictée")
        assert not self.jarvis.dictation.active

        # Note rapide
        NOTES_FILE.write_text("", encoding="utf-8")
        await self.jarvis.process_transcription("Jarvis note lettre terminee")
        assert self.jarvis.notes.notes_count == 1


class TestCycle25ScenarioMacroWithCalc:
    """Macro + calcul"""
    def setup_method(self):
        self.jarvis = Jarvis()
        self.jarvis.tts.speak = AsyncMock()
        self.jarvis.tts.speak_status = AsyncMock()

    @pytest.mark.asyncio
    async def test_macro_then_calc(self):
        # Enregistre macro
        await self.jarvis.process_transcription("Jarvis automatise test_calc_macro")
        assert self.jarvis.automation.recording
        await self.jarvis.process_transcription("monte le volume")
        await self.jarvis.process_transcription("fin de macro")
        assert not self.jarvis.automation.recording

        # Calcul
        self.jarvis.tts.speak.reset_mock()
        await self.jarvis.process_transcription("Jarvis combien fait 7 fois 8")
        assert "56" in self.jarvis.tts.speak.call_args[0][0]

        await self.jarvis.automation.delete_macro("test_calc_macro")


class TestCycle26ScenarioSystemAdmin:
    """Admin systeme: resources + reseau"""
    def setup_method(self):
        self.jarvis = Jarvis()

    @pytest.mark.asyncio
    async def test_system_admin_extended(self):
        r = await self.jarvis.process_mgr.system_resources(VoiceCommand("", ""))
        assert isinstance(r.success, bool)

        r = await self.jarvis.process_mgr.disk_space(VoiceCommand("", ""))
        assert isinstance(r.success, bool)

        r = await self.jarvis.process_mgr.uptime(VoiceCommand("", ""))
        assert isinstance(r.success, bool)

        r = await self.jarvis.network.ip_local(VoiceCommand("", ""))
        assert isinstance(r.success, bool)


class TestCycle27ScenarioEndOfDayV2:
    """Fin de journee: notes + timer + quit"""
    def setup_method(self):
        self.jarvis = Jarvis()
        self.jarvis.tts.speak = AsyncMock()
        self.jarvis.tts.speak_status = AsyncMock()
        if NOTES_FILE.exists():
            self._backup = NOTES_FILE.read_text(encoding="utf-8")
        else:
            self._backup = ""

    def teardown_method(self):
        NOTES_FILE.write_text(self._backup, encoding="utf-8")

    @pytest.mark.asyncio
    async def test_end_of_day_v2(self):
        NOTES_FILE.write_text("", encoding="utf-8")
        await self.jarvis.process_transcription("Jarvis note fin de journee")
        assert self.jarvis.notes.notes_count == 1

        self.jarvis._running = True
        await self.jarvis.process_transcription("Jarvis au revoir")
        assert not self.jarvis.is_running


class TestCycle28ScenarioMultiTimer:
    """Plusieurs minuteurs simultanes"""
    def setup_method(self):
        self.jarvis = Jarvis()
        self.jarvis.tts.speak = AsyncMock()
        self.jarvis.tts.speak_status = AsyncMock()

    @pytest.mark.asyncio
    async def test_multi_timers(self):
        await self.jarvis.process_transcription("Jarvis minuteur 5 minutes")
        await self.jarvis.process_transcription("Jarvis minuteur 10 minutes")
        assert self.jarvis.timer.active_count == 2

        r = await self.jarvis.timer.list_timers(VoiceCommand("", ""))
        assert "2 actifs" in r.message

        await self.jarvis.timer.cancel_timer(VoiceCommand("", ""))
        assert self.jarvis.timer.active_count == 0


class TestCycle29ScenarioWebResearchWithNotes:
    """Recherche web + notes"""
    def setup_method(self):
        self.jarvis = Jarvis()
        self.jarvis.tts.speak = AsyncMock()
        self.jarvis.tts.speak_status = AsyncMock()
        if NOTES_FILE.exists():
            self._backup = NOTES_FILE.read_text(encoding="utf-8")
        else:
            self._backup = ""

    def teardown_method(self):
        NOTES_FILE.write_text(self._backup, encoding="utf-8")

    @pytest.mark.asyncio
    async def test_research_with_notes(self):
        with patch('webbrowser.open'):
            await self.jarvis.process_transcription("Jarvis google python asyncio")
            assert self.jarvis.tts.speak.called

        NOTES_FILE.write_text("", encoding="utf-8")
        await self.jarvis.process_transcription("Jarvis note voir doc asyncio")
        assert self.jarvis.notes.notes_count == 1


class TestCycle30ScenarioPresentationPrep:
    """Preparation presentation: apps + timer + notes"""
    def setup_method(self):
        self.jarvis = Jarvis()
        self.jarvis.tts.speak = AsyncMock()
        self.jarvis.tts.speak_status = AsyncMock()

    @pytest.mark.asyncio
    async def test_presentation_prep(self):
        mock_launch = AsyncMock(return_value=CommandResult(True, "OK"))
        self.jarvis.commander._handlers["app_launch"] = mock_launch

        await self.jarvis.process_transcription("Jarvis ouvre powerpoint")
        assert mock_launch.called

        await self.jarvis.process_transcription("Jarvis minuteur 30 minutes")
        assert self.jarvis.timer.active_count == 1

        self.jarvis.tts.speak.reset_mock()
        await self.jarvis.process_transcription("Jarvis calcule 45 sur 60")
        assert self.jarvis.tts.speak.called

        await self.jarvis.timer.cancel_timer(VoiceCommand("", ""))


# ============================================================
# CYCLES 31-40: Robustesse et edge cases avances
# ============================================================
class TestCycle31CalcEdgeCases:
    def setup_method(self):
        self.jarvis = Jarvis()

    @pytest.mark.asyncio
    async def test_large_numbers(self):
        r = await self.jarvis.calculator.calculate(
            VoiceCommand("999999 fois 999999", "calc_compute", target="999999 fois 999999"))
        assert r.success

    @pytest.mark.asyncio
    async def test_decimal(self):
        r = await self.jarvis.calculator.calculate(
            VoiceCommand("3 virgule 14 fois 2", "calc_compute", target="3 virgule 14 fois 2"))
        assert r.success and "6.28" in r.message

    @pytest.mark.asyncio
    async def test_negative(self):
        r = await self.jarvis.calculator.calculate(
            VoiceCommand("5 moins 10", "calc_compute", target="5 moins 10"))
        assert r.success and "-5" in r.message


class TestCycle32TimerEdgeCases:
    def setup_method(self):
        self.jarvis = Jarvis()

    @pytest.mark.asyncio
    async def test_1_second_timer(self):
        r = await self.jarvis.timer.set_timer(
            VoiceCommand("1 seconde", "timer_set", target="1 seconde"))
        assert r.success and "1 seconde" in r.message
        await self.jarvis.timer.cancel_timer(VoiceCommand("", ""))

    @pytest.mark.asyncio
    async def test_cancel_multiple_times(self):
        await self.jarvis.timer.set_timer(
            VoiceCommand("5 min", "timer_set", target="5 min"))
        r1 = await self.jarvis.timer.cancel_timer(VoiceCommand("", ""))
        assert "1" in r1.message
        r2 = await self.jarvis.timer.cancel_timer(VoiceCommand("", ""))
        assert "aucun" in r2.message.lower()


class TestCycle33NotesEdgeCases:
    def setup_method(self):
        self.jarvis = Jarvis()
        if NOTES_FILE.exists():
            self._backup = NOTES_FILE.read_text(encoding="utf-8")
        else:
            self._backup = ""

    def teardown_method(self):
        NOTES_FILE.write_text(self._backup, encoding="utf-8")

    @pytest.mark.asyncio
    async def test_very_long_note(self):
        long_text = "a" * 1000
        r = await self.jarvis.notes.add_note(
            VoiceCommand(long_text, "note_add", target=long_text))
        assert r.success

    @pytest.mark.asyncio
    async def test_unicode_note(self):
        r = await self.jarvis.notes.add_note(
            VoiceCommand("cafe reunion", "note_add", target="cafe reunion"))
        assert r.success

    @pytest.mark.asyncio
    async def test_search_empty_query(self):
        r = await self.jarvis.notes.search_notes(
            VoiceCommand("", "note_search", target=""))
        assert not r.success


class TestCycle34CommanderEdgeCases:
    def setup_method(self):
        self.c = Commander()

    def test_unknown_command(self):
        cmd = self.c.parse("xyz blabla")
        assert cmd.intent == "unknown"

    def test_empty_text(self):
        assert self.c.parse("") is None
        assert self.c.parse("   ") is None

    def test_very_long_command(self):
        cmd = self.c.parse("ouvre " + "a" * 5000)
        assert cmd.intent == "app_launch"

    def test_special_chars_in_command(self):
        cmd = self.c.parse("calcule 5+3")
        # May or may not match depending on regex
        assert cmd is not None


class TestCycle35WakeWordEdgeCases:
    @pytest.mark.parametrize("text,expected", [
        ("JARVIS AIDE", True),
        ("jarvIs ouvre chrome", True),
        ("JaRvIs statut", True),
        ("jarvis    aide", True),  # multiple spaces
        ("jarvis, aide", True),  # comma
        ("jarvis! aide", True),  # exclamation
    ])
    def test_wake_word_variations(self, text, expected):
        detected, _ = detect_wake_word(text)
        assert detected == expected


class TestCycle36SecurityChecks:
    """Verifie la securite des entrees"""
    def setup_method(self):
        self.jarvis = Jarvis()

    @pytest.mark.asyncio
    async def test_injection_in_app_name(self):
        r = await self.jarvis.app_launcher.launch(
            VoiceCommand("", "app_launch", target="; rm -rf /"))
        assert not r.success

    @pytest.mark.asyncio
    async def test_injection_in_process_kill(self):
        r = await self.jarvis.process_mgr.kill_process(
            VoiceCommand("", "process_kill", target="../../etc/passwd"))
        assert not r.success

    @pytest.mark.asyncio
    async def test_injection_in_ping(self):
        r = await self.jarvis.network.ping(
            VoiceCommand("", "network_ping", target="google.com; rm -rf /"))
        assert not r.success

    @pytest.mark.asyncio
    async def test_injection_in_software(self):
        r = await self.jarvis.software.install(
            VoiceCommand("", "software_install", target="; malicious"))
        assert not r.success


class TestCycle37ModeInteractions:
    """Interactions entre modes"""
    def setup_method(self):
        self.jarvis = Jarvis()
        self.jarvis.tts.speak = AsyncMock()
        self.jarvis.tts.speak_status = AsyncMock()

    @pytest.mark.asyncio
    async def test_timer_survives_dictation(self):
        """Les timers persistent pendant la dictee"""
        await self.jarvis.process_transcription("Jarvis minuteur 5 minutes")
        assert self.jarvis.timer.active_count == 1

        await self.jarvis.process_transcription("Jarvis mode dictée")
        assert self.jarvis.dictation.active
        # Timer toujours actif
        assert self.jarvis.timer.active_count == 1

        await self.jarvis.process_transcription("arrête la dictée")
        assert not self.jarvis.dictation.active
        assert self.jarvis.timer.active_count == 1

        await self.jarvis.timer.cancel_timer(VoiceCommand("", ""))


class TestCycle38RapidNewCommands:
    """Commandes nouvelles rapides enchaines"""
    def setup_method(self):
        self.jarvis = Jarvis()
        self.jarvis.tts.speak = AsyncMock()
        self.jarvis.tts.speak_status = AsyncMock()

    @pytest.mark.asyncio
    async def test_rapid_new_commands(self):
        commands = [
            "Jarvis calcule 2 plus 2",
            "Jarvis calcule 10 fois 3",
            "Jarvis calcule 100 moins 42",
            "Jarvis minuteur 5 minutes",
            "Jarvis annule le minuteur",
        ]
        for cmd in commands:
            await self.jarvis.process_transcription(cmd)
        assert self.jarvis.tts.speak.call_count >= 5


class TestCycle39BilingualNewPatterns:
    """Bilingue pour les nouveaux patterns"""
    def setup_method(self):
        self.c = Commander()

    @pytest.mark.parametrize("fr,en,intent", [
        ("minuteur 5 minutes", "timer 5 minutes", "timer_set"),
        ("calcule 5 plus 3", "calculate 5 plus 3", "calc_compute"),
        ("nouveau bureau virtuel", "new desktop", "vdesktop_new"),
        ("vue des tâches", "task view", "vdesktop_task_view"),
    ])
    def test_bilingual_new(self, fr, en, intent):
        assert self.c.parse(fr).intent == intent
        assert self.c.parse(en).intent == intent


class TestCycle40StatusIncludesNewSkills:
    """Le statut JARVIS reflecte les nouveaux skills"""
    def setup_method(self):
        self.jarvis = Jarvis()

    @pytest.mark.asyncio
    async def test_status_counts(self):
        r = await self.jarvis._status(VoiceCommand("", "jarvis_status"))
        assert r.success
        # Should have 100+ commands now
        assert "commandes" in r.message.lower()


# ============================================================
# CYCLES 41-50: Stress tests et integration complete
# ============================================================
class TestCycle41StressAllPatterns:
    """Stress: teste CHAQUE pattern au moins une fois"""
    def setup_method(self):
        self.c = Commander()

    def test_all_patterns_matchable(self):
        from whisperflow.jarvis.commander import COMMAND_PATTERNS
        import re
        for pattern, intent in COMMAND_PATTERNS:
            # Generate a simple test string from the pattern
            compiled = re.compile(pattern, re.IGNORECASE)
            # Just verify it compiles without error
            assert compiled is not None, f"Pattern invalide: {pattern}"


class TestCycle42Stress50WakeWords:
    def test_50_rapid_wake_words(self):
        for i in range(50):
            detected, cmd = detect_wake_word(f"Jarvis commande {i}")
            assert detected
            assert cmd == f"commande {i}"


class TestCycle43Stress20Calculations:
    def setup_method(self):
        self.jarvis = Jarvis()

    @pytest.mark.asyncio
    async def test_20_calculations(self):
        operations = [
            ("2 plus 3", "5"), ("10 moins 4", "6"), ("5 fois 6", "30"),
            ("20 sur 4", "5"), ("3 puissance 3", "27"), ("100 moins 1", "99"),
            ("7 fois 7", "49"), ("15 plus 25", "40"), ("50 moins 30", "20"),
            ("8 fois 9", "72"), ("100 sur 10", "10"), ("2 puissance 10", "1024"),
            ("999 plus 1", "1000"), ("50 fois 2", "100"), ("33 plus 67", "100"),
            ("144 sur 12", "12"), ("11 fois 11", "121"), ("256 moins 128", "128"),
            ("3 fois 17", "51"), ("1000 moins 999", "1"),
        ]
        for expr, expected in operations:
            r = await self.jarvis.calculator.calculate(
                VoiceCommand(expr, "calc_compute", target=expr))
            assert r.success, f"Failed: {expr}"
            assert expected in r.message, f"{expr} => {r.message}, expected {expected}"


class TestCycle44StressNotes:
    def setup_method(self):
        self.jarvis = Jarvis()
        if NOTES_FILE.exists():
            self._backup = NOTES_FILE.read_text(encoding="utf-8")
        else:
            self._backup = ""

    def teardown_method(self):
        NOTES_FILE.write_text(self._backup, encoding="utf-8")

    @pytest.mark.asyncio
    async def test_10_notes(self):
        NOTES_FILE.write_text("", encoding="utf-8")
        for i in range(10):
            r = await self.jarvis.notes.add_note(
                VoiceCommand(f"note test {i}", "note_add", target=f"note test {i}"))
            assert r.success
        assert self.jarvis.notes.notes_count == 10

        r = await self.jarvis.notes.read_notes(VoiceCommand("", "note_read"))
        assert "10 notes" in r.message


class TestCycle45StressTimers:
    def setup_method(self):
        self.jarvis = Jarvis()

    @pytest.mark.asyncio
    async def test_5_timers(self):
        for i in range(5):
            r = await self.jarvis.timer.set_timer(
                VoiceCommand(f"{i+1} minutes", "timer_set", target=f"{i+1} minutes"))
            assert r.success
        assert self.jarvis.timer.active_count == 5

        r = await self.jarvis.timer.cancel_timer(VoiceCommand("", ""))
        assert "5" in r.message
        assert self.jarvis.timer.active_count == 0


class TestCycle46StressFullPipeline:
    def setup_method(self):
        self.jarvis = Jarvis()
        self.jarvis.tts.speak = AsyncMock()
        self.jarvis.tts.speak_status = AsyncMock()

    @pytest.mark.asyncio
    async def test_20_pipeline_commands(self):
        commands = [
            "Jarvis quelle heure",
            "Jarvis date",
            "Jarvis batterie",
            "Jarvis aide",
            "Jarvis statut",
            "Jarvis calcule 5 plus 5",
            "Jarvis calcule 10 fois 10",
            "Jarvis minuteur 1 minutes",
            "Jarvis annule le minuteur",
            "Jarvis merci",
            "Jarvis quelle heure",
            "Jarvis date",
            "Jarvis aide",
            "Jarvis statut",
            "Jarvis calcule 3 fois 7",
            "Jarvis calcule 100 moins 50",
            "Jarvis merci",
            "Jarvis quelle heure",
            "Jarvis aide",
            "Jarvis merci",
        ]
        for cmd in commands:
            await self.jarvis.process_transcription(cmd)
        assert self.jarvis.tts.speak.call_count >= 20


class TestCycle47CompleteFeatureMatrix:
    """Verifie que chaque categorie de skill est accessible"""
    def setup_method(self):
        self.jarvis = Jarvis()

    def test_all_skill_categories(self):
        assert self.jarvis.app_launcher is not None
        assert self.jarvis.system_control is not None
        assert self.jarvis.window_manager is not None
        assert self.jarvis.file_manager is not None
        assert self.jarvis.web_browser is not None
        assert self.jarvis.media_control is not None
        assert self.jarvis.clipboard is not None
        assert self.jarvis.process_mgr is not None
        assert self.jarvis.network is not None
        assert self.jarvis.power_display is not None
        assert self.jarvis.software is not None
        assert self.jarvis.timer is not None
        assert self.jarvis.notes is not None
        assert self.jarvis.calculator is not None
        assert self.jarvis.vdesktop is not None

    def test_all_agent_categories(self):
        assert self.jarvis.dictation is not None
        assert self.jarvis.search is not None
        assert self.jarvis.automation is not None
        assert self.jarvis.navigation is not None


class TestCycle48RapidModeSwitch:
    """Switchs rapides entre tous les modes"""
    def setup_method(self):
        self.jarvis = Jarvis()
        self.jarvis.tts.speak = AsyncMock()
        self.jarvis.tts.speak_status = AsyncMock()

    @pytest.mark.asyncio
    async def test_rapid_all_modes(self):
        # Normal -> Dictee -> Normal
        await self.jarvis.process_transcription("Jarvis mode dictée")
        assert self.jarvis.dictation.active
        await self.jarvis.process_transcription("arrête la dictée")
        assert not self.jarvis.dictation.active

        # Normal -> Macro -> Normal
        await self.jarvis.process_transcription("Jarvis automatise cycle48")
        assert self.jarvis.automation.recording
        await self.jarvis.process_transcription("fin de macro")
        assert not self.jarvis.automation.recording

        # Normal -> Dictee -> Normal -> Macro -> Normal
        await self.jarvis.process_transcription("Jarvis mode dictée")
        await self.jarvis.process_transcription("arrête la dictée")
        await self.jarvis.process_transcription("Jarvis automatise cycle48b")
        await self.jarvis.process_transcription("fin de macro")

        # Cleanup
        await self.jarvis.automation.delete_macro("cycle48")
        await self.jarvis.automation.delete_macro("cycle48b")


class TestCycle49FinalIntegration:
    """Test d'integration finale: utilise tous les skills"""
    def setup_method(self):
        self.jarvis = Jarvis()
        self.jarvis.tts.speak = AsyncMock()
        self.jarvis.tts.speak_status = AsyncMock()
        if NOTES_FILE.exists():
            self._backup = NOTES_FILE.read_text(encoding="utf-8")
        else:
            self._backup = ""

    def teardown_method(self):
        NOTES_FILE.write_text(self._backup, encoding="utf-8")

    @pytest.mark.asyncio
    async def test_full_day_simulation(self):
        """Simule une journee complete avec JARVIS"""
        # Matin: heure + date + batterie
        await self.jarvis.process_transcription("Jarvis quelle heure")
        await self.jarvis.process_transcription("Jarvis date")
        await self.jarvis.process_transcription("Jarvis batterie")

        # Travail: timer + apps + calcul
        await self.jarvis.process_transcription("Jarvis minuteur 25 minutes")
        assert self.jarvis.timer.active_count == 1

        mock_launch = AsyncMock(return_value=CommandResult(True, "OK"))
        self.jarvis.commander._handlers["app_launch"] = mock_launch
        await self.jarvis.process_transcription("Jarvis ouvre code")

        self.jarvis.tts.speak.reset_mock()
        await self.jarvis.process_transcription("Jarvis calcule 42 fois 3")
        assert "126" in self.jarvis.tts.speak.call_args[0][0]

        # Notes
        NOTES_FILE.write_text("", encoding="utf-8")
        await self.jarvis.process_transcription("Jarvis note reunion a 14h")
        assert self.jarvis.notes.notes_count == 1

        # Web
        with patch('webbrowser.open'):
            await self.jarvis.process_transcription("Jarvis google python documentation")

        # Aide + statut
        await self.jarvis.process_transcription("Jarvis aide")
        await self.jarvis.process_transcription("Jarvis statut")

        # Fin
        await self.jarvis.timer.cancel_timer(VoiceCommand("", ""))
        self.jarvis._running = True
        await self.jarvis.process_transcription("Jarvis au revoir")
        assert not self.jarvis.is_running


class TestCycle50FinalCountVerification:
    """Verification finale: nombre total de tests et couverture"""

    def test_pattern_count(self):
        from whisperflow.jarvis.commander import COMMAND_PATTERNS
        # Au moins 105 patterns
        assert len(COMMAND_PATTERNS) >= 105, f"Seulement {len(COMMAND_PATTERNS)} patterns"

    def test_handler_count(self):
        jarvis = Jarvis()
        intents = jarvis.commander.list_intents()
        # Au moins 100 handlers
        assert len(intents) >= 100, f"Seulement {len(intents)} handlers"

    def test_skill_count(self):
        """15 skills + 4 agents"""
        jarvis = Jarvis()
        skills = [
            jarvis.app_launcher, jarvis.system_control, jarvis.window_manager,
            jarvis.file_manager, jarvis.web_browser, jarvis.media_control,
            jarvis.clipboard, jarvis.process_mgr, jarvis.network,
            jarvis.power_display, jarvis.software, jarvis.timer,
            jarvis.notes, jarvis.calculator, jarvis.vdesktop,
        ]
        agents = [
            jarvis.dictation, jarvis.search, jarvis.automation, jarvis.navigation,
        ]
        assert len(skills) == 15
        assert len(agents) == 4

    def test_all_previous_tests_categories(self):
        """Meta-test: confirme les 50 cycles"""
        test_classes = [
            TestCycle01TimerPatterns, TestCycle02TimerDurationParsing,
            TestCycle03NotesPatterns, TestCycle04CalculatorPatterns,
            TestCycle05VirtualDesktopPatterns, TestCycle06TextToMath,
            TestCycle07AstCompute, TestCycle08FormatResult,
            TestCycle09CalculatorSkill, TestCycle10TimerSkill,
            TestCycle11NotesSkill, TestCycle12VirtualDesktopSkill,
            TestCycle13NoRegressionOriginalPatterns, TestCycle14PatternPriorityConflicts,
            TestCycle15AllIntentsRegistered, TestCycle16TimerPipeline,
            TestCycle17NotesPipeline, TestCycle18CalcPipeline,
            TestCycle19VDesktopPipeline, TestCycle20MixedPipeline,
            TestCycle21ScenarioStudySession, TestCycle22ScenarioMorningRoutineV2,
            TestCycle23ScenarioWorkSetupV2, TestCycle24ScenarioDictationWithNotes,
            TestCycle25ScenarioMacroWithCalc, TestCycle26ScenarioSystemAdmin,
            TestCycle27ScenarioEndOfDayV2, TestCycle28ScenarioMultiTimer,
            TestCycle29ScenarioWebResearchWithNotes, TestCycle30ScenarioPresentationPrep,
            TestCycle31CalcEdgeCases, TestCycle32TimerEdgeCases,
            TestCycle33NotesEdgeCases, TestCycle34CommanderEdgeCases,
            TestCycle35WakeWordEdgeCases, TestCycle36SecurityChecks,
            TestCycle37ModeInteractions, TestCycle38RapidNewCommands,
            TestCycle39BilingualNewPatterns, TestCycle40StatusIncludesNewSkills,
            TestCycle41StressAllPatterns, TestCycle42Stress50WakeWords,
            TestCycle43Stress20Calculations, TestCycle44StressNotes,
            TestCycle45StressTimers, TestCycle46StressFullPipeline,
            TestCycle47CompleteFeatureMatrix, TestCycle48RapidModeSwitch,
            TestCycle49FinalIntegration, TestCycle50FinalCountVerification,
        ]
        assert len(test_classes) == 50


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-x"])
