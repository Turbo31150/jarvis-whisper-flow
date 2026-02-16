"""
JARVIS TTS Engine - Synthèse vocale pour les réponses de JARVIS
Utilise edge-tts (gratuit, haute qualité) avec fallback pyttsx3
"""

import asyncio
import tempfile
import os
import logging

logger = logging.getLogger("jarvis.tts")


class TTSEngine:
    """Moteur de synthèse vocale multi-backend"""

    def __init__(self, voice="fr-FR-HenriNeural", rate="+10%"):
        self.voice = voice
        self.rate = rate
        self._edge_available = None
        self._pyttsx_engine = None

    async def speak(self, text: str):
        """Prononce le texte à voix haute"""
        if not text or not text.strip():
            return

        logger.info(f"JARVIS dit: {text}")

        if await self._try_edge_tts(text):
            return
        self._fallback_pyttsx(text)

    async def _try_edge_tts(self, text: str) -> bool:
        """Essaye edge-tts (voix Microsoft Neural haute qualité)"""
        if self._edge_available is False:
            return False

        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                tmp_path = f.name

            proc = await asyncio.create_subprocess_exec(
                "edge-tts",
                "--voice", self.voice,
                "--rate", self.rate,
                "--text", text,
                "--write-media", tmp_path,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL
            )
            await proc.wait()

            if proc.returncode == 0 and os.path.getsize(tmp_path) > 0:
                self._edge_available = True
                play_proc = await asyncio.create_subprocess_exec(
                    "powershell", "-c",
                    f"Add-Type -AssemblyName PresentationCore; "
                    f"$player = New-Object System.Windows.Media.MediaPlayer; "
                    f"$player.Open([uri]'{tmp_path}'); "
                    f"$player.Play(); Start-Sleep -Seconds 5",
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL
                )
                await play_proc.wait()
                return True

        except FileNotFoundError:
            self._edge_available = False
            logger.warning("edge-tts non disponible, fallback pyttsx3")
        except Exception as e:
            logger.warning(f"Erreur edge-tts: {e}")
        finally:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass

        return False

    def _fallback_pyttsx(self, text: str):
        """Fallback avec pyttsx3 (voix Windows locale)"""
        try:
            import pyttsx3
            if self._pyttsx_engine is None:
                self._pyttsx_engine = pyttsx3.init()
                voices = self._pyttsx_engine.getProperty("voices")
                for v in voices:
                    if "french" in v.name.lower() or "fr" in v.id.lower():
                        self._pyttsx_engine.setProperty("voice", v.id)
                        break
                self._pyttsx_engine.setProperty("rate", 180)

            self._pyttsx_engine.say(text)
            self._pyttsx_engine.runAndWait()
        except ImportError:
            logger.error("Ni edge-tts ni pyttsx3 disponible. pip install edge-tts pyttsx3")
        except Exception as e:
            logger.error(f"Erreur TTS fallback: {e}")

    async def speak_status(self, status: str):
        """Annonce un statut système court"""
        status_messages = {
            "ready": "JARVIS en ligne. À vos ordres.",
            "listening": "Je vous écoute.",
            "processing": "Un instant.",
            "error": "Désolé, une erreur s'est produite.",
            "goodbye": "À bientôt.",
            "wake": "Oui ?",
            "unknown": "Je n'ai pas compris cette commande.",
            "done": "C'est fait.",
            "dictation_on": "Mode dictée activé.",
            "dictation_off": "Mode dictée désactivé.",
        }
        msg = status_messages.get(status, status)
        await self.speak(msg)
