"""
JARVIS Commander - Parseur et dispatcher de commandes vocales
Analyse le texte transcrit et route vers le bon skill/agent
"""

import re
import logging
import asyncio
from typing import Optional, Callable, Awaitable

logger = logging.getLogger("jarvis.commander")


class CommandResult:
    """Résultat d'une commande exécutée"""
    def __init__(self, success: bool, message: str = "", data=None):
        self.success = success
        self.message = message
        self.data = data


class VoiceCommand:
    """Représentation d'une commande vocale parsée"""
    def __init__(self, raw_text: str, intent: str, target: str = "",
                 params: dict = None, confidence: float = 1.0):
        self.raw_text = raw_text
        self.intent = intent
        self.target = target
        self.params = params or {}
        self.confidence = confidence

    def __repr__(self):
        return f"VoiceCommand(intent='{self.intent}', target='{self.target}')"


# Patterns de commandes vocales FR/EN
COMMAND_PATTERNS = [
    # === DICTÉE (prioritaire - avant app_close qui matche aussi "arrête") ===
    (r"(?:mode\s+dictée|dictation\s+mode|commence\s+à\s+écrire|écris)",
     "dictation_start"),
    (r"(?:arrête\s+la\s+dictée|stop\s+dictation|fin\s+de\s+dictée|arrête\s+d'écrire)",
     "dictation_stop"),
    (r"(?:nouvelle\s+ligne|new\s+line|à\s+la\s+ligne|retour\s+à\s+la\s+ligne)",
     "dictation_newline"),
    (r"(?:point\s+final|point\s*$)",
     "dictation_period"),

    # === APPLICATIONS ===
    (r"(?:ouvre|ouvrir|lance|lancer|démarre|démarrer|start|open|launch)\s+(.+)",
     "app_launch"),
    (r"(?:ferme|fermer|quitte|quitter|close|kill|arrête|arrêter)\s+(.+)",
     "app_close"),

    # === FICHIERS ===
    (r"(?:crée|créer|nouveau|nouvelle)\s+(?:un\s+)?(?:fichier|dossier|répertoire)\s+(.+)",
     "file_create"),
    (r"(?:supprime|supprimer|efface|effacer|delete)\s+(?:le\s+)?(?:fichier|dossier)?\s*(.+)",
     "file_delete"),
    (r"(?:cherche|chercher|recherche|rechercher|trouve|trouver|find|search)\s+(?:le\s+)?(?:fichier\s+)?(.+)",
     "file_search"),
    (r"(?:renomme|renommer|rename)\s+(.+)\s+en\s+(.+)",
     "file_rename"),
    (r"(?:copie|copier|copy)\s+(.+)",
     "clipboard_copy"),
    (r"(?:colle|coller|paste)",
     "clipboard_paste"),

    # === FENÊTRES ===
    (r"(?:minimise|minimiser|minimize)\s*(?:la\s+)?(?:fenêtre)?",
     "window_minimize"),
    (r"(?:maximise|maximiser|maximize)\s*(?:la\s+)?(?:fenêtre)?",
     "window_maximize"),
    (r"(?:restaure|restaurer|restore)\s*(?:la\s+)?(?:fenêtre)?",
     "window_restore"),
    (r"(?:bascule|basculer|switch|alt.?tab)",
     "window_switch"),
    (r"(?:bureau|show\s+desktop|affiche\s+le\s+bureau)",
     "window_desktop"),
    (r"(?:capture|screenshot|écran)\s*(?:d'écran)?",
     "window_screenshot"),

    # === SYSTÈME ===
    (r"(?:volume)\s+(?:à|a|au)?\s*(\d+)",
     "system_volume_set"),
    (r"(?:monte|augmente|plus\s+fort|volume\s+up|up\s+volume)\s*(?:le\s+)?(?:volume|son)?",
     "system_volume_up"),
    (r"(?:baisse|diminue|moins\s+fort|volume\s+down|down\s+volume)\s*(?:le\s+)?(?:volume|son)?",
     "system_volume_down"),
    (r"(?:muet|mute|coupe\s+le\s+son|silence)",
     "system_mute"),
    (r"(?:luminosité|brightness)\s+(?:à|a|au)?\s*(\d+)",
     "system_brightness"),
    (r"(?:wifi)\s+(on|off|active|désactive)",
     "system_wifi"),
    (r"(?:bluetooth)\s+(on|off|active|désactive)",
     "system_bluetooth"),
    (r"(?:éteins|éteindre|shutdown|arrête\s+l'ordinateur)",
     "system_shutdown"),
    (r"(?:redémarre|redémarrer|restart|reboot)",
     "system_restart"),
    (r"(?:veille|sleep|mise\s+en\s+veille|verrouille|lock)",
     "system_sleep"),
    (r"(?:batterie|battery|autonomie)",
     "system_battery"),
    (r"(?:heure|quelle\s+heure|time)",
     "system_time"),
    (r"(?:date|quel\s+jour|today)",
     "system_date"),
    (r"(?:météo|weather|temps\s+qu'il\s+fait)",
     "web_weather"),

    # === WEB ===
    (r"(?:google|recherche\s+sur\s+google|cherche\s+sur\s+google)\s+(.+)",
     "web_google"),
    (r"(?:youtube)\s+(.+)",
     "web_youtube"),
    (r"(?:wikipedia|wiki)\s+(.+)",
     "web_wikipedia"),
    (r"(?:va\s+sur|ouvre\s+le\s+site|navigate|go\s+to)\s+(.+)",
     "web_navigate"),

    # === MÉDIA ===
    (r"(?:play|lecture|joue|jouer|lis|lire)",
     "media_play"),
    (r"(?:pause|stop|arrête\s+la\s+musique|arrête\s+la\s+lecture)",
     "media_pause"),
    (r"(?:suivant|next|piste\s+suivante|chanson\s+suivante)",
     "media_next"),
    (r"(?:précédent|previous|piste\s+précédente|chanson\s+précédente)",
     "media_previous"),

    # === AUTOMATISATION ===
    (r"(?:automatise|automatiser|automate|macro)\s+(.+)",
     "automation_create"),
    (r"(?:exécute|exécuter|run|lance)\s+(?:la\s+)?(?:macro|automatisation|script)\s+(.+)",
     "automation_run"),

    # === CONTRÔLE JARVIS ===
    (r"(?:aide|help|qu'est-ce\s+que\s+tu\s+(?:sais|peux)\s+faire|commandes)",
     "jarvis_help"),
    (r"(?:statut|status|état|state)",
     "jarvis_status"),
    (r"(?:au\s+revoir|goodbye|bye|à\s+plus|bonne\s+nuit|stop\s+jarvis|quitte\s+jarvis)",
     "jarvis_quit"),
    (r"(?:merci|thanks|thank\s+you)",
     "jarvis_thanks"),
    (r"(?:répète|repeat|redis)",
     "jarvis_repeat"),
    (r"(?:annule|cancel|undo|annuler)",
     "jarvis_cancel"),
    (r"(?:paramètres|settings|configuration|config)\s*(?:de\s+)?(?:jarvis)?",
     "jarvis_settings"),
]


class Commander:
    """Parseur et dispatcher principal de commandes vocales"""

    def __init__(self):
        self._handlers: dict[str, Callable] = {}
        self._last_command: Optional[VoiceCommand] = None
        self._compiled_patterns = [
            (re.compile(pattern, re.IGNORECASE), intent)
            for pattern, intent in COMMAND_PATTERNS
        ]

    def register(self, intent: str, handler: Callable[..., Awaitable[CommandResult]]):
        """Enregistre un handler pour un intent donné"""
        self._handlers[intent] = handler
        logger.debug(f"Handler enregistré: {intent}")

    def parse(self, text: str) -> Optional[VoiceCommand]:
        """Parse le texte en une commande vocale structurée"""
        if not text or not text.strip():
            return None

        text_clean = text.strip().lower()

        for pattern, intent in self._compiled_patterns:
            match = pattern.search(text_clean)
            if match:
                groups = match.groups()
                target = groups[0].strip() if groups else ""
                params = {"groups": groups} if len(groups) > 1 else {}

                cmd = VoiceCommand(
                    raw_text=text,
                    intent=intent,
                    target=target,
                    params=params,
                    confidence=0.9
                )
                logger.info(f"Commande parsée: {cmd}")
                return cmd

        return VoiceCommand(
            raw_text=text,
            intent="unknown",
            target=text_clean,
            confidence=0.3
        )

    async def execute(self, command: VoiceCommand) -> CommandResult:
        """Exécute une commande vocale via le handler approprié"""
        self._last_command = command

        handler = self._handlers.get(command.intent)
        if handler:
            try:
                logger.info(f"Exécution: {command.intent} -> {command.target}")
                return await handler(command)
            except Exception as e:
                logger.error(f"Erreur exécution {command.intent}: {e}")
                return CommandResult(False, f"Erreur: {e}")

        logger.warning(f"Aucun handler pour intent: {command.intent}")
        return CommandResult(False, "Commande non reconnue")

    async def process_text(self, text: str) -> CommandResult:
        """Pipeline complet: parse + execute"""
        command = self.parse(text)
        if command is None:
            return CommandResult(False, "Texte vide")
        return await self.execute(command)

    @property
    def last_command(self) -> Optional[VoiceCommand]:
        return self._last_command

    def list_intents(self) -> list:
        """Liste tous les intents enregistrés"""
        return list(self._handlers.keys())
