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
# ORDRE CRITIQUE: patterns spécifiques AVANT patterns génériques
COMMAND_PATTERNS = [
    # === DICTÉE (prioritaire - avant app_close qui matche "arrête") ===
    (r"(?:mode\s+dictée|dictation\s+mode|commence\s+à\s+écrire|écris)",
     "dictation_start"),
    (r"(?:arrête\s+la\s+dictée|stop\s+dictation|fin\s+de\s+dictée|arrête\s+d'écrire)",
     "dictation_stop"),
    (r"(?:nouvelle\s+ligne|new\s+line|à\s+la\s+ligne|retour\s+à\s+la\s+ligne)",
     "dictation_newline"),
    (r"(?:point\s+final|point\s*$)",
     "dictation_period"),

    # === MÉDIA (avant app_close car "arrête la musique" conflicte) ===
    (r"(?:arrête\s+la\s+musique|arrête\s+la\s+lecture)",
     "media_pause"),
    (r"(?:play|lecture|joue|jouer)",
     "media_play"),
    (r"(?:pause)",
     "media_pause"),
    (r"(?:suivant|next|piste\s+suivante|chanson\s+suivante)",
     "media_next"),
    (r"(?:précédent|previous|piste\s+précédente|chanson\s+précédente)",
     "media_previous"),

    # === PROCESSUS & MONITORING (avant app_launch car "liste/kill" conflicte) ===
    (r"(?:liste|lister|list)\s+(?:les\s+)?(?:processus|process|tâches)",
     "process_list"),
    (r"(?:tue|tuer|kill)\s+(?:le\s+)?(?:processus|process)\s+(.+)",
     "process_kill"),
    (r"(?:ressources|resources|charge|utilisation)\s*(?:système|system)?",
     "system_resources"),
    (r"(?:utilisation\s+(?:cpu|ram|système|system))",
     "system_resources"),
    (r"(?:cpu|processeur)\s*(?:usage|utilisation)?",
     "system_top_cpu"),
    (r"(?:\bram\b|mémoire|memory)\s*(?:usage|utilisation)?",
     "system_resources"),
    (r"(?:espace\s+disque|disk\s+space|stockage|disque\s+dur)",
     "system_disk"),
    (r"(?:uptime|durée\s+de\s+fonctionnement|allumé\s+depuis)",
     "system_uptime"),
    (r"(?:gpu|carte\s+graphique)",
     "system_gpu"),
    (r"(?:matériel|hardware|specs|configuration\s+matérielle|info(?:rmation)?s?\s+(?:matériel(?:les?)?|système)|system\s+info)",
     "system_hardware"),

    # === RÉSEAU (avant app_launch) ===
    (r"(?:état\s+(?:du\s+)?réseau|network\s+status|interfaces?\s+réseau)",
     "network_status"),
    (r"(?:(?:adresse\s+)?ip\s+publique|public\s+ip|ip\s+externe)",
     "network_ip_public"),
    (r"(?:adresse\s+ip|ip\s+locale|mon\s+ip|ip\s+address)",
     "network_ip"),
    (r"(?:ping)\s+(.+)",
     "network_ping"),
    (r"(?:teste?\s+(?:la\s+)?connexion|connection\s+test)",
     "network_ping"),
    (r"(?:réseaux?\s+wifi|wifi\s+(?:disponibles?|list)|scan\s+wifi)",
     "network_wifi_list"),
    (r"(?:test\s+(?:de\s+)?débit|speed\s*test|vitesse\s+internet)",
     "network_speed"),

    # === ALIMENTATION & AFFICHAGE (avant jarvis_settings car "paramètres" conflicte) ===
    (r"(?:plan\s+(?:d')?alimentation|power\s+plan)",
     "power_plan"),
    (r"(?:haute\s+performance|high\s+performance|mode\s+performance)",
     "power_high_perf"),
    (r"(?:mode\s+équilibré|balanced)",
     "power_balanced"),
    (r"(?:économie\s+d'énergie|power\s+saver|mode\s+éco)",
     "power_saver"),
    (r"(?:hibernation|hiberne|hibernate)",
     "power_hibernate"),
    (r"(?:résolution)\s*(?:d'écran)?",
     "display_resolution"),
    (r"(?:mode\s+nuit|night\s+(?:mode|light)|lumière\s+bleue|filtre\s+bleu)",
     "display_night"),
    (r"(?:paramètres?\s+(?:d')?affichage|display\s+settings)",
     "display_settings"),
    (r"(?:paramètres?\s+(?:du?\s+)?son|audio\s+settings|paramètres?\s+audio)",
     "audio_settings"),

    # === LOGICIELS winget (avant app_launch car "installe/désinstalle" conflicte) ===
    (r"(?:désinstalle|désinstaller|uninstall)\s+(?:le\s+)?(?:logiciel|programme)?\s*(.+)",
     "software_uninstall"),
    (r"(?:installe|installer|install)\s+(?:le\s+)?(?:logiciel|programme|package)?\s*(.+)",
     "software_install"),
    (r"(?:mets?\s+à\s+jour\s+tout|update\s+all|mise\s+à\s+jour\s+(?:de\s+)?tout)",
     "software_update_all"),
    (r"(?:liste\s+(?:les\s+)?(?:logiciels|programmes)|installed\s+software|programmes?\s+installés?)",
     "software_list"),
    (r"(?:mises?\s+à\s+jour|updates?\s+disponibles?|vérifi(?:e|er)\s+(?:les\s+)?mises?\s+à\s+jour)",
     "software_check_updates"),

    # === PRESSE-PAPIERS (avant app_launch) ===
    (r"(?:lis\s+le\s+presse-papiers|read\s+clipboard|contenu\s+(?:du\s+)?presse-papiers)",
     "clipboard_read"),
    (r"(?:coupe\s+le\s+son)",
     "system_mute"),
    (r"(?:coupe|couper|cut)\s*(?:la\s+)?(?:sélection)?",
     "clipboard_cut"),
    (r"(?:sélectionne\s+tout|select\s+all|tout\s+sélectionner)",
     "clipboard_select_all"),

    # === NAVIGATION DOSSIERS (avant app_launch car "ouvre" conflicte) ===
    (r"(?:ouvre|ouvrir)\s+(?:le\s+)?(?:dossier|répertoire|folder)\s+(.+)",
     "navigate_folder"),
    (r"(?:ouvre|ouvrir)\s+(?:les\s+)?(?:téléchargements|downloads)",
     "navigate_downloads"),
    (r"(?:ouvre|ouvrir)\s+(?:les\s+)?(?:documents)",
     "navigate_documents"),
    (r"(?:ouvre|ouvrir)\s+(?:le\s+)?(?:bureau|desktop)",
     "navigate_desktop"),

    # === WEB (avant fichiers car "recherche sur google" conflicte avec file_search) ===
    (r"(?:google|recherche\s+sur\s+google|cherche\s+sur\s+google)\s+(.+)",
     "web_google"),
    (r"(?:youtube)\s+(.+)",
     "web_youtube"),
    (r"(?:wikipedia|wiki)\s+(.+)",
     "web_wikipedia"),
    (r"(?:va\s+sur|ouvre\s+le\s+site|navigate|go\s+to)\s+(.+)",
     "web_navigate"),
    (r"(?:météo|weather|temps\s+qu'il\s+fait)",
     "web_weather"),

    # === AUTOMATISATION (avant app_launch car "lance macro" conflicte) ===
    (r"(?:automatise|automatiser|automate|macro)\s+(.+)",
     "automation_create"),
    (r"(?:exécute|exécuter|run|lance)\s+(?:la\s+)?(?:macro|automatisation|script)\s+(.+)",
     "automation_run"),

    # === APPLICATIONS (générique - après tous les patterns spécifiques) ===
    (r"(?:ouvre|ouvrir|lance|lancer|démarre|démarrer|start|open|launch)\s+(.+)",
     "app_launch"),
    (r"(?:ferme|fermer|quitte|quitter|close|kill|arrête|arrêter)\s+(.+)",
     "app_close"),

    # === FICHIERS ===
    (r"(?:crée|créer|nouveau|nouvelle)\s+(?:un\s+)?(?:fichier|dossier|répertoire)\s+(.+)",
     "file_create"),
    (r"(?:supprime|supprimer|efface|effacer|delete)\s+(?:le\s+)?(?:fichier|dossier)?\s*(.+)",
     "file_delete"),
    (r"(?:cherche|chercher|recherche(?:r)?|trouve|trouver|find|search)\s+(?:le\s+fichier\s+)?(.+)",
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
