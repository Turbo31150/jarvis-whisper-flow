"""
JARVIS - Tests de simulation d'utilisation réelle
Cycles complets: Wake word -> Commande -> Exécution -> Réponse vocale
Teste TOUS les skills et agents en conditions réelles simulées
"""

import asyncio
import pytest
import logging
from unittest.mock import AsyncMock, patch, MagicMock
from whisperflow.jarvis.jarvis_core import Jarvis
from whisperflow.jarvis.commander import Commander, VoiceCommand
from whisperflow.jarvis.wake_word import detect_wake_word
from whisperflow.jarvis.tts_engine import TTSEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")


# ============================================================
# CYCLE 1: Tests Wake Word
# ============================================================
class TestWakeWord:
    """Teste la détection du mot d'activation JARVIS"""

    def test_exact_match(self):
        detected, cmd = detect_wake_word("Jarvis ouvre Chrome")
        assert detected is True
        assert cmd == "ouvre chrome"

    def test_case_insensitive(self):
        detected, cmd = detect_wake_word("JARVIS ferme notepad")
        assert detected is True
        assert cmd == "ferme notepad"

    def test_with_comma(self):
        detected, cmd = detect_wake_word("Jarvis, ouvre le terminal")
        assert detected is True
        assert "ouvre le terminal" in cmd

    def test_fuzzy_match(self):
        detected, cmd = detect_wake_word("Jarvi ouvre Chrome")
        assert detected is True

    def test_no_wake_word(self):
        detected, cmd = detect_wake_word("Bonjour comment ça va")
        assert detected is False

    def test_wake_word_only(self):
        detected, cmd = detect_wake_word("Jarvis")
        assert detected is True
        assert cmd == ""

    def test_empty_text(self):
        detected, cmd = detect_wake_word("")
        assert detected is False

    def test_hey_jarvis(self):
        detected, cmd = detect_wake_word("Hey Jarvis quelle heure")
        assert detected is True


# ============================================================
# CYCLE 2: Tests Commander (Parseur de commandes)
# ============================================================
class TestCommander:
    """Teste le parsing de toutes les commandes vocales"""

    def setup_method(self):
        self.commander = Commander()

    # --- Applications ---
    def test_parse_ouvre_app(self):
        cmd = self.commander.parse("ouvre chrome")
        assert cmd.intent == "app_launch"
        assert "chrome" in cmd.target

    def test_parse_ferme_app(self):
        cmd = self.commander.parse("ferme notepad")
        assert cmd.intent == "app_close"
        assert "notepad" in cmd.target

    def test_parse_lance_app(self):
        cmd = self.commander.parse("lance le terminal")
        assert cmd.intent == "app_launch"

    def test_parse_open_english(self):
        cmd = self.commander.parse("open chrome")
        assert cmd.intent == "app_launch"

    # --- Système ---
    def test_parse_volume_up(self):
        cmd = self.commander.parse("monte le volume")
        assert cmd.intent == "system_volume_up"

    def test_parse_volume_down(self):
        cmd = self.commander.parse("baisse le volume")
        assert cmd.intent == "system_volume_down"

    def test_parse_volume_set(self):
        cmd = self.commander.parse("volume à 50")
        assert cmd.intent == "system_volume_set"
        assert "50" in cmd.target

    def test_parse_mute(self):
        cmd = self.commander.parse("muet")
        assert cmd.intent == "system_mute"

    def test_parse_brightness(self):
        cmd = self.commander.parse("luminosité à 80")
        assert cmd.intent == "system_brightness"

    def test_parse_time(self):
        cmd = self.commander.parse("quelle heure est-il")
        assert cmd.intent == "system_time"

    def test_parse_date(self):
        cmd = self.commander.parse("quel jour sommes-nous")
        assert cmd.intent == "system_date"

    def test_parse_battery(self):
        cmd = self.commander.parse("batterie")
        assert cmd.intent == "system_battery"

    def test_parse_wifi(self):
        cmd = self.commander.parse("wifi on")
        assert cmd.intent == "system_wifi"

    def test_parse_bluetooth(self):
        cmd = self.commander.parse("bluetooth off")
        assert cmd.intent == "system_bluetooth"

    def test_parse_shutdown(self):
        cmd = self.commander.parse("éteins l'ordinateur")
        assert cmd.intent == "system_shutdown"

    def test_parse_restart(self):
        cmd = self.commander.parse("redémarre")
        assert cmd.intent == "system_restart"

    def test_parse_sleep(self):
        cmd = self.commander.parse("verrouille")
        assert cmd.intent == "system_sleep"

    # --- Fenêtres ---
    def test_parse_minimize(self):
        cmd = self.commander.parse("minimise la fenêtre")
        assert cmd.intent == "window_minimize"

    def test_parse_maximize(self):
        cmd = self.commander.parse("maximise")
        assert cmd.intent == "window_maximize"

    def test_parse_switch(self):
        cmd = self.commander.parse("bascule")
        assert cmd.intent == "window_switch"

    def test_parse_desktop(self):
        cmd = self.commander.parse("bureau")
        assert cmd.intent == "window_desktop"

    def test_parse_screenshot(self):
        cmd = self.commander.parse("capture d'écran")
        assert cmd.intent == "window_screenshot"

    # --- Fichiers ---
    def test_parse_create_file(self):
        cmd = self.commander.parse("crée un fichier rapport")
        assert cmd.intent == "file_create"

    def test_parse_create_folder(self):
        cmd = self.commander.parse("crée un dossier projets")
        assert cmd.intent == "file_create"

    def test_parse_delete_file(self):
        cmd = self.commander.parse("supprime le fichier brouillon")
        assert cmd.intent == "file_delete"

    def test_parse_search_file(self):
        cmd = self.commander.parse("cherche rapport annuel")
        assert cmd.intent == "file_search"

    # --- Web ---
    def test_parse_google(self):
        cmd = self.commander.parse("google intelligence artificielle")
        assert cmd.intent == "web_google"
        assert "intelligence artificielle" in cmd.target

    def test_parse_youtube(self):
        cmd = self.commander.parse("youtube tutoriel python")
        assert cmd.intent == "web_youtube"

    def test_parse_wikipedia(self):
        cmd = self.commander.parse("wikipedia machine learning")
        assert cmd.intent == "web_wikipedia"

    def test_parse_navigate(self):
        cmd = self.commander.parse("va sur github.com")
        assert cmd.intent == "web_navigate"

    def test_parse_weather(self):
        cmd = self.commander.parse("météo")
        assert cmd.intent == "web_weather"

    # --- Média ---
    def test_parse_play(self):
        cmd = self.commander.parse("play")
        assert cmd.intent == "media_play"

    def test_parse_pause(self):
        cmd = self.commander.parse("pause")
        assert cmd.intent == "media_pause"

    def test_parse_next(self):
        cmd = self.commander.parse("suivant")
        assert cmd.intent == "media_next"

    def test_parse_previous(self):
        cmd = self.commander.parse("précédent")
        assert cmd.intent == "media_previous"

    # --- Dictée ---
    def test_parse_dictation_start(self):
        cmd = self.commander.parse("mode dictée")
        assert cmd.intent == "dictation_start"

    def test_parse_dictation_stop(self):
        cmd = self.commander.parse("arrête la dictée")
        assert cmd.intent == "dictation_stop"

    # --- Automatisation ---
    def test_parse_automation_create(self):
        cmd = self.commander.parse("automatise routine du matin")
        assert cmd.intent == "automation_create"

    # --- Contrôle JARVIS ---
    def test_parse_help(self):
        cmd = self.commander.parse("aide")
        assert cmd.intent == "jarvis_help"

    def test_parse_status(self):
        cmd = self.commander.parse("statut")
        assert cmd.intent == "jarvis_status"

    def test_parse_quit(self):
        cmd = self.commander.parse("au revoir")
        assert cmd.intent == "jarvis_quit"

    def test_parse_thanks(self):
        cmd = self.commander.parse("merci")
        assert cmd.intent == "jarvis_thanks"

    def test_parse_cancel(self):
        cmd = self.commander.parse("annule")
        assert cmd.intent == "jarvis_cancel"

    def test_parse_unknown(self):
        cmd = self.commander.parse("blablabla nonsense")
        assert cmd.intent == "unknown"


# ============================================================
# CYCLE 3: Tests Skills en simulation
# ============================================================
class TestSkillsSimulation:
    """Simule l'exécution de chaque skill sans toucher au système"""

    def setup_method(self):
        self.jarvis = Jarvis()

    @pytest.mark.asyncio
    async def test_system_time(self):
        result = await self.jarvis.system_control.time(
            VoiceCommand("quelle heure", "system_time"))
        assert result.success
        assert "heure" in result.message.lower()

    @pytest.mark.asyncio
    async def test_system_date(self):
        result = await self.jarvis.system_control.date(
            VoiceCommand("quel jour", "system_date"))
        assert result.success
        assert any(j in result.message.lower() for j in
                   ["lundi", "mardi", "mercredi", "jeudi",
                    "vendredi", "samedi", "dimanche"])

    @pytest.mark.asyncio
    async def test_file_create(self):
        """Simule création de fichier"""
        cmd = VoiceCommand("crée un fichier test_jarvis", "file_create",
                           target="test_jarvis")
        result = await self.jarvis.file_manager.create(cmd)
        assert result.success
        # Nettoyage
        from pathlib import Path
        test_file = Path.home() / "Desktop" / "test_jarvis.txt"
        if test_file.exists():
            test_file.unlink()

    @pytest.mark.asyncio
    async def test_file_search(self):
        """Simule recherche de fichier"""
        cmd = VoiceCommand("cherche desktop", "file_search", target="desktop")
        result = await self.jarvis.file_manager.search(cmd)
        # Peut trouver ou non, pas d'erreur dans les deux cas
        assert isinstance(result.success, bool)

    @pytest.mark.asyncio
    async def test_app_launch_unknown(self):
        """Teste lancement d'une app non whitelist"""
        cmd = VoiceCommand("ouvre truc_inconnu", "app_launch",
                           target="truc_inconnu")
        result = await self.jarvis.app_launcher.launch(cmd)
        assert result.success is False
        assert "non reconnue" in result.message

    @pytest.mark.asyncio
    async def test_shutdown_pending(self):
        """Teste que shutdown crée une action en attente"""
        cmd = VoiceCommand("éteins", "system_shutdown")
        result = await self.jarvis.system_control.shutdown(cmd)
        assert result.success
        assert result.data is not None
        assert "pending_action" in result.data

    @pytest.mark.asyncio
    async def test_help(self):
        result = await self.jarvis._help(VoiceCommand("aide", "jarvis_help"))
        assert result.success
        assert "applications" in result.message.lower()

    @pytest.mark.asyncio
    async def test_status(self):
        result = await self.jarvis._status(VoiceCommand("statut", "jarvis_status"))
        assert result.success
        assert "JARVIS" in result.message

    @pytest.mark.asyncio
    async def test_thanks(self):
        result = await self.jarvis._thanks(VoiceCommand("merci", "jarvis_thanks"))
        assert result.success

    @pytest.mark.asyncio
    async def test_quit(self):
        result = await self.jarvis._quit(VoiceCommand("au revoir", "jarvis_quit"))
        assert result.success
        assert self.jarvis.is_running is False


# ============================================================
# CYCLE 4: Tests Agents en simulation
# ============================================================
class TestAgentsSimulation:
    """Simule les agents spécialisés"""

    def setup_method(self):
        self.jarvis = Jarvis()

    @pytest.mark.asyncio
    async def test_dictation_lifecycle(self):
        """Cycle complet: activation -> dictée -> arrêt"""
        # Active la dictée
        result = await self.jarvis.dictation.start(
            VoiceCommand("mode dictée", "dictation_start"))
        assert self.jarvis.dictation.active is True

        # Vérifie détection stop
        assert self.jarvis.dictation.should_stop("arrête la dictée") is True
        assert self.jarvis.dictation.should_stop("bonjour") is False

        # Arrête la dictée
        result = await self.jarvis.dictation.stop(
            VoiceCommand("arrête la dictée", "dictation_stop"))
        assert self.jarvis.dictation.active is False

    @pytest.mark.asyncio
    async def test_automation_lifecycle(self):
        """Cycle complet: création macro -> enregistrement -> sauvegarde"""
        # Crée une macro
        result = await self.jarvis.automation.create(
            VoiceCommand("automatise test_macro", "automation_create",
                         target="test_macro"))
        assert self.jarvis.automation.recording is True

        # Enregistre des étapes
        self.jarvis.automation.record_step("ouvre chrome")
        self.jarvis.automation.record_step("google python tutoriel")

        # Sauvegarde
        result = await self.jarvis.automation.stop_recording()
        assert result.success
        assert self.jarvis.automation.recording is False
        assert "test_macro" in self.jarvis.automation.macros

        # Vérifie l'exécution
        result = await self.jarvis.automation.run(
            VoiceCommand("lance macro test_macro", "automation_run",
                         target="test_macro"))
        assert result.success
        assert len(result.data["macro_steps"]) == 2

        # Nettoyage
        await self.jarvis.automation.delete_macro("test_macro")

    @pytest.mark.asyncio
    async def test_search_agent(self):
        """Teste la recherche locale"""
        results = self.jarvis.search._search_local("nonexistent_xyz_123")
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_navigation_settings(self):
        """Teste la résolution des destinations"""
        from whisperflow.jarvis.agents.navigation_agent import SETTINGS_MAP, SHELL_FOLDERS
        assert "wifi" in SETTINGS_MAP
        assert "documents" in SHELL_FOLDERS
        assert SETTINGS_MAP["wifi"].startswith("ms-settings:")


# ============================================================
# CYCLE 5: Tests d'intégration Pipeline complet
# ============================================================
class TestFullPipeline:
    """Simule le pipeline complet: texte transcrit -> action"""

    def setup_method(self):
        self.jarvis = Jarvis()
        # Mock le TTS pour éviter la synthèse vocale pendant les tests
        self.jarvis.tts.speak = AsyncMock()
        self.jarvis.tts.speak_status = AsyncMock()

    @pytest.mark.asyncio
    async def test_full_pipeline_open_app(self):
        """Simule: 'Jarvis ouvre notepad' -> lancement notepad"""
        mock_launch = AsyncMock(return_value=MagicMock(
            success=True, message="J'ai ouvert notepad", data=None))
        self.jarvis.commander._handlers["app_launch"] = mock_launch
        await self.jarvis.process_transcription("Jarvis ouvre notepad")
        mock_launch.assert_called_once()

    @pytest.mark.asyncio
    async def test_full_pipeline_time(self):
        """Simule: 'Jarvis quelle heure' -> annonce heure"""
        await self.jarvis.process_transcription("Jarvis quelle heure est-il")
        self.jarvis.tts.speak.assert_called()
        call_args = self.jarvis.tts.speak.call_args[0][0]
        assert "heure" in call_args.lower()

    @pytest.mark.asyncio
    async def test_full_pipeline_date(self):
        await self.jarvis.process_transcription("Jarvis quel jour sommes-nous")
        self.jarvis.tts.speak.assert_called()

    @pytest.mark.asyncio
    async def test_full_pipeline_help(self):
        await self.jarvis.process_transcription("Jarvis aide")
        self.jarvis.tts.speak.assert_called()

    @pytest.mark.asyncio
    async def test_full_pipeline_status(self):
        await self.jarvis.process_transcription("Jarvis statut")
        self.jarvis.tts.speak.assert_called()

    @pytest.mark.asyncio
    async def test_full_pipeline_wake_only(self):
        """Jarvis seul -> répond 'Oui ?'"""
        await self.jarvis.process_transcription("Jarvis")
        self.jarvis.tts.speak_status.assert_called_with("wake")

    @pytest.mark.asyncio
    async def test_full_pipeline_no_wake(self):
        """Pas de wake word -> rien ne se passe"""
        await self.jarvis.process_transcription("Bonjour tout le monde")
        self.jarvis.tts.speak.assert_not_called()

    @pytest.mark.asyncio
    async def test_full_pipeline_partial_ignored(self):
        """Les résultats partiels sont ignorés"""
        await self.jarvis.process_transcription("Jarvis ouvre chrome", is_partial=True)
        self.jarvis.tts.speak.assert_not_called()

    @pytest.mark.asyncio
    async def test_full_pipeline_dictation_mode(self):
        """Cycle dictée complet"""
        # Active la dictée
        await self.jarvis.process_transcription("Jarvis mode dictée")
        assert self.jarvis.dictation.active is True

        # En mode dictée, pas de wake word nécessaire
        # Le texte est directement traité par l'agent dictée
        with patch.object(self.jarvis.dictation, 'process_text',
                          new_callable=AsyncMock,
                          return_value=MagicMock(success=True, message="")):
            await self.jarvis.process_transcription("Bonjour ceci est un test")
            self.jarvis.dictation.process_text.assert_called_once()

        # Arrête la dictée
        self.jarvis.dictation.active = True  # reset car le mock ne l'a pas fait
        await self.jarvis.process_transcription("arrête la dictée")
        assert self.jarvis.dictation.active is False

    @pytest.mark.asyncio
    async def test_full_pipeline_macro_recording(self):
        """Cycle macro complet"""
        # Démarre enregistrement
        await self.jarvis.process_transcription("Jarvis automatise ma routine")
        assert self.jarvis.automation.recording is True

        # Enregistre des commandes
        await self.jarvis.process_transcription("ouvre chrome")
        assert len(self.jarvis.automation.current_macro_steps) == 1

        # Fin de macro
        await self.jarvis.process_transcription("fin de macro")
        assert self.jarvis.automation.recording is False

    @pytest.mark.asyncio
    async def test_full_pipeline_unknown_command(self):
        """Commande inconnue -> message d'erreur poli"""
        await self.jarvis.process_transcription("Jarvis fais un truc impossible")
        self.jarvis.tts.speak.assert_called()

    @pytest.mark.asyncio
    async def test_full_pipeline_quit(self):
        """Cycle arrêt JARVIS"""
        self.jarvis._running = True
        await self.jarvis.process_transcription("Jarvis au revoir")
        assert self.jarvis.is_running is False


# ============================================================
# CYCLE 6: Scénarios d'utilisation réelle
# ============================================================
class TestRealWorldScenarios:
    """Simule des scénarios d'utilisation quotidienne complets"""

    def setup_method(self):
        self.jarvis = Jarvis()
        self.jarvis.tts.speak = AsyncMock()
        self.jarvis.tts.speak_status = AsyncMock()

    @pytest.mark.asyncio
    async def test_scenario_morning_routine(self):
        """Scénario: Routine du matin"""
        # L'utilisateur arrive et salue JARVIS
        await self.jarvis.process_transcription("Jarvis")
        self.jarvis.tts.speak_status.assert_called_with("wake")

        # Demande l'heure
        await self.jarvis.process_transcription("Jarvis quelle heure est-il")
        assert self.jarvis.tts.speak.called

        # Demande la date
        self.jarvis.tts.speak.reset_mock()
        await self.jarvis.process_transcription("Jarvis quel jour sommes-nous")
        assert self.jarvis.tts.speak.called

        # Demande la batterie
        self.jarvis.tts.speak.reset_mock()
        await self.jarvis.process_transcription("Jarvis batterie")
        assert self.jarvis.tts.speak.called

    @pytest.mark.asyncio
    async def test_scenario_work_session(self):
        """Scénario: Session de travail"""
        mock_launch = AsyncMock(return_value=MagicMock(
            success=True, message="OK", data=None))
        self.jarvis.commander._handlers["app_launch"] = mock_launch
        await self.jarvis.process_transcription("Jarvis ouvre code")
        await self.jarvis.process_transcription("Jarvis ouvre chrome")
        assert mock_launch.call_count == 2

    @pytest.mark.asyncio
    async def test_scenario_dictation_letter(self):
        """Scénario: Dictée d'une lettre"""
        # Active la dictée
        await self.jarvis.process_transcription("Jarvis mode dictée")
        assert self.jarvis.dictation.active is True

        # Vérifie que les commandes stop sont détectées
        assert self.jarvis.dictation.should_stop("arrête la dictée")
        assert not self.jarvis.dictation.should_stop("bonjour monsieur")

        # Arrête
        await self.jarvis.process_transcription("arrête la dictée")
        assert self.jarvis.dictation.active is False

    @pytest.mark.asyncio
    async def test_scenario_media_control(self):
        """Scénario: Contrôle musique pendant le travail"""
        with patch('asyncio.create_subprocess_exec',
                   new_callable=AsyncMock) as mock_proc:
            mock_proc.return_value.wait = AsyncMock()

            result = await self.jarvis.media_control.play(
                VoiceCommand("play", "media_play"))
            assert result.success

            result = await self.jarvis.media_control.next_track(
                VoiceCommand("suivant", "media_next"))
            assert result.success

    @pytest.mark.asyncio
    async def test_scenario_end_of_day(self):
        """Scénario: Fin de journée"""
        self.jarvis._running = True

        # Ferme les apps
        mock_close = AsyncMock(return_value=MagicMock(
            success=True, message="Fermé", data=None))
        self.jarvis.commander._handlers["app_close"] = mock_close
        await self.jarvis.process_transcription("Jarvis ferme chrome")

        # Dit au revoir
        await self.jarvis.process_transcription("Jarvis au revoir")
        assert self.jarvis.is_running is False


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
