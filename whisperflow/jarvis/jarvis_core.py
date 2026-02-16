"""
JARVIS Core - Orchestrateur principal
Connecte Whisper-Flow (STT) + Commander + Skills + Agents + TTS
"""

import asyncio
import logging
from typing import Optional

from .commander import Commander, CommandResult, VoiceCommand
from .wake_word import detect_wake_word
from .tts_engine import TTSEngine
from .config import config

# Skills
from .skills.app_launcher import AppLauncherSkill
from .skills.system_control import SystemControlSkill
from .skills.window_manager import WindowManagerSkill
from .skills.file_manager import FileManagerSkill
from .skills.web_browser import WebBrowserSkill
from .skills.media_control import MediaControlSkill
from .skills.clipboard_manager import ClipboardManagerSkill

# Agents
from .agents.dictation_agent import DictationAgent
from .agents.search_agent import SearchAgent
from .agents.automation_agent import AutomationAgent
from .agents.navigation_agent import NavigationAgent

logger = logging.getLogger("jarvis.core")


class Jarvis:
    """JARVIS - Just A Rather Very Intelligent System"""

    def __init__(self):
        self.commander = Commander()
        self.tts = TTSEngine(
            voice=config.get("tts_voice", "fr-FR-HenriNeural"),
            rate=config.get("tts_rate", "+10%")
        )

        # Skills
        self.app_launcher = AppLauncherSkill()
        self.system_control = SystemControlSkill()
        self.window_manager = WindowManagerSkill()
        self.file_manager = FileManagerSkill()
        self.web_browser = WebBrowserSkill()
        self.media_control = MediaControlSkill()
        self.clipboard = ClipboardManagerSkill()

        # Agents
        self.dictation = DictationAgent()
        self.search = SearchAgent()
        self.automation = AutomationAgent()
        self.navigation = NavigationAgent()

        # State
        self._pending_action = None
        self._running = False

        self._register_all_handlers()

    def _register_all_handlers(self):
        """Enregistre tous les handlers de commandes"""
        c = self.commander

        # Applications
        c.register("app_launch", self.app_launcher.launch)
        c.register("app_close", self.app_launcher.close)

        # Système
        c.register("system_volume_set", self.system_control.volume_set)
        c.register("system_volume_up", self.system_control.volume_up)
        c.register("system_volume_down", self.system_control.volume_down)
        c.register("system_mute", self.system_control.mute)
        c.register("system_brightness", self.system_control.brightness)
        c.register("system_wifi", self.system_control.wifi)
        c.register("system_bluetooth", self.system_control.bluetooth)
        c.register("system_shutdown", self.system_control.shutdown)
        c.register("system_restart", self.system_control.restart)
        c.register("system_sleep", self.system_control.sleep)
        c.register("system_battery", self.system_control.battery)
        c.register("system_time", self.system_control.time)
        c.register("system_date", self.system_control.date)

        # Fenêtres
        c.register("window_minimize", self.window_manager.minimize)
        c.register("window_maximize", self.window_manager.maximize)
        c.register("window_restore", self.window_manager.restore)
        c.register("window_switch", self.window_manager.switch)
        c.register("window_desktop", self.window_manager.desktop)
        c.register("window_screenshot", self.window_manager.screenshot)

        # Fichiers
        c.register("file_create", self.file_manager.create)
        c.register("file_delete", self.file_manager.delete)
        c.register("file_search", self.file_manager.search)
        c.register("file_rename", self.file_manager.rename)

        # Web
        c.register("web_google", self.web_browser.google)
        c.register("web_youtube", self.web_browser.youtube)
        c.register("web_wikipedia", self.web_browser.wikipedia)
        c.register("web_navigate", self.web_browser.navigate)
        c.register("web_weather", self.web_browser.weather)

        # Média
        c.register("media_play", self.media_control.play)
        c.register("media_pause", self.media_control.pause)
        c.register("media_next", self.media_control.next_track)
        c.register("media_previous", self.media_control.previous_track)

        # Presse-papiers
        c.register("clipboard_copy", self.clipboard.copy)
        c.register("clipboard_paste", self.clipboard.paste)

        # Dictée
        c.register("dictation_start", self.dictation.start)
        c.register("dictation_stop", self.dictation.stop)
        c.register("dictation_newline", self.dictation.newline)
        c.register("dictation_period", self.dictation.period)

        # Automatisation
        c.register("automation_create", self.automation.create)
        c.register("automation_run", self._run_macro)

        # Contrôle JARVIS
        c.register("jarvis_help", self._help)
        c.register("jarvis_status", self._status)
        c.register("jarvis_quit", self._quit)
        c.register("jarvis_thanks", self._thanks)
        c.register("jarvis_cancel", self._cancel)
        c.register("jarvis_repeat", self._repeat)
        c.register("jarvis_settings", self.navigation.open_settings)
        c.register("unknown", self._unknown)

    async def process_transcription(self, text: str, is_partial: bool = False):
        """
        Point d'entrée principal: traite le texte transcrit par Whisper-Flow.
        Appelé à chaque segment final de transcription.
        """
        if is_partial or not text or not text.strip():
            return

        text = text.strip()
        logger.info(f"Transcription reçue: '{text}'")

        # Mode dictée actif - traite comme texte à taper
        if self.dictation.active:
            if self.dictation.should_stop(text):
                result = await self.dictation.stop(
                    VoiceCommand(text, "dictation_stop")
                )
                await self.tts.speak_status(result.message)
            else:
                await self.dictation.process_text(text)
            return

        # Mode macro enregistrement
        if self.automation.recording:
            if "fin de macro" in text.lower() or "stop macro" in text.lower():
                result = await self.automation.stop_recording()
                await self.tts.speak(result.message)
                return
            self.automation.record_step(text)
            return

        # Détection du wake word "Jarvis"
        detected, command_text = detect_wake_word(text)

        if not detected:
            return

        if not command_text:
            await self.tts.speak_status("wake")
            return

        # Parse et exécute la commande
        result = await self.commander.process_text(command_text)

        # Gère les actions en attente (shutdown, restart)
        if result.data and "pending_action" in result.data:
            self._pending_action = result.data

        # Réponse vocale
        if result.message:
            if result.message in ("dictation_on", "dictation_off"):
                await self.tts.speak_status(result.message)
            elif result.success:
                await self.tts.speak(result.message)
            else:
                await self.tts.speak(f"Désolé. {result.message}")

    # === Handlers internes ===

    async def _help(self, command: VoiceCommand) -> CommandResult:
        return CommandResult(True,
            "Je peux ouvrir des applications, gérer les fenêtres, "
            "contrôler le volume et la luminosité, chercher des fichiers, "
            "naviguer sur le web, dicter du texte, et bien plus. "
            "Dites 'Jarvis' suivi de votre commande."
        )

    async def _status(self, command: VoiceCommand) -> CommandResult:
        intents = len(self.commander.list_intents())
        macros = len(self.automation.macros)
        dictation = "actif" if self.dictation.active else "inactif"
        return CommandResult(True,
            f"JARVIS opérationnel. {intents} commandes disponibles, "
            f"{macros} macros, dictée {dictation}."
        )

    async def _quit(self, command: VoiceCommand) -> CommandResult:
        self._running = False
        return CommandResult(True, "Au revoir. À bientôt.")

    async def _thanks(self, command: VoiceCommand) -> CommandResult:
        return CommandResult(True, "Je vous en prie.")

    async def _cancel(self, command: VoiceCommand) -> CommandResult:
        if self._pending_action:
            await self.system_control.cancel_pending()
            self._pending_action = None
            return CommandResult(True, "Action annulée")
        return CommandResult(True, "Rien à annuler")

    async def _repeat(self, command: VoiceCommand) -> CommandResult:
        last = self.commander.last_command
        if last and last.intent != "jarvis_repeat":
            result = await self.commander.execute(last)
            return result
        return CommandResult(False, "Aucune commande à répéter")

    async def _unknown(self, command: VoiceCommand) -> CommandResult:
        return CommandResult(False,
            f"Je n'ai pas compris '{command.target}'. "
            f"Dites 'aide' pour la liste des commandes."
        )

    async def _run_macro(self, command: VoiceCommand) -> CommandResult:
        result = await self.automation.run(command)
        if result.success and result.data and "macro_steps" in result.data:
            for step in result.data["macro_steps"]:
                await self.commander.process_text(step)
                await asyncio.sleep(0.5)
            return CommandResult(True, "Macro terminée")
        return result

    @property
    def is_running(self):
        return self._running

    async def start(self):
        """Démarre JARVIS"""
        self._running = True
        logger.info("JARVIS démarré")
        await self.tts.speak_status("ready")

    async def stop(self):
        """Arrête JARVIS"""
        self._running = False
        await self.tts.speak_status("goodbye")
        logger.info("JARVIS arrêté")
