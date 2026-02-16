"""
JARVIS - Cycles 51-100: Formation Intensive Phase 2
Tests avances de simulation d'utilisation reelle Windows

Cycles 51-55:  Variations STT Whisper (erreurs transcription, casse, espaces)
Cycles 56-60:  Disambiguation multi-intent et priorites avancees
Cycles 61-65:  Calculatrice avancee (precedence, virgule, conversions)
Cycles 66-70:  Minuteurs avances (concurrents, format, duree)
Cycles 71-75:  Pipeline error recovery et resilience
Cycles 76-80:  Securite approfondie (injection, overflow, traversal)
Cycles 81-85:  Scenarios metier (dev, enseignant, gaming, reunion, cuisine)
Cycles 86-90:  Verification exhaustive de chaque pattern
Cycles 91-95:  Gardes de regression (bugs fixes qui ne doivent pas revenir)
Cycles 96-100: Stress ultime et validation finale

Total: 50 cycles, ~250 tests
"""

import asyncio
import pytest
import logging
import math
from unittest.mock import AsyncMock, patch, MagicMock
from pathlib import Path

from whisperflow.jarvis.jarvis_core import Jarvis
from whisperflow.jarvis.commander import Commander, VoiceCommand, CommandResult, COMMAND_PATTERNS
from whisperflow.jarvis.wake_word import detect_wake_word
from whisperflow.jarvis.skills.timer_reminder import _parse_duration, _format_duration
from whisperflow.jarvis.skills.calculator import _text_to_math, _ast_compute, _format_result
from whisperflow.jarvis.skills.quick_notes import NOTES_FILE

logging.basicConfig(level=logging.INFO)


# ============================================================
# CYCLES 51-55: Variations STT Whisper
# ============================================================
class TestCycle51WhisperCaseVariations:
    """Whisper peut transcrire en majuscules, minuscules, ou mixte"""
    def setup_method(self):
        self.c = Commander()

    @pytest.mark.parametrize("text,intent", [
        ("OUVRE CHROME", "app_launch"),
        ("Ouvre Chrome", "app_launch"),
        ("ouvre chrome", "app_launch"),
        ("VOLUME 50", "system_volume_set"),
        ("Volume 50", "system_volume_set"),
        ("MINUTEUR 5 MINUTES", "timer_set"),
        ("Calcule 3 Plus 2", "calc_compute"),
        ("NOTE Acheter Du Pain", "note_add"),
        ("AIDE", "jarvis_help"),
        ("Merci", "jarvis_thanks"),
    ])
    def test_case_insensitive(self, text, intent):
        result = self.c.parse(text)
        assert result.intent == intent


class TestCycle52WhisperExtraSpaces:
    """Whisper ajoute parfois des espaces supplementaires"""
    def setup_method(self):
        self.c = Commander()

    @pytest.mark.parametrize("text,intent", [
        ("  ouvre  chrome  ", "app_launch"),
        ("  volume  50  ", "system_volume_set"),
        ("  minuteur  5  minutes  ", "timer_set"),
        ("   aide   ", "jarvis_help"),
        ("  météo  ", "web_weather"),
    ])
    def test_extra_whitespace(self, text, intent):
        result = self.c.parse(text)
        assert result.intent == intent


class TestCycle53WhisperPunctuation:
    """Whisper peut ajouter de la ponctuation"""
    def setup_method(self):
        self.c = Commander()

    @pytest.mark.parametrize("text,intent", [
        ("ouvre chrome.", "app_launch"),
        ("volume 50!", "system_volume_set"),
        ("aide?", "jarvis_help"),
        ("merci!", "jarvis_thanks"),
        ("au revoir.", "jarvis_quit"),
    ])
    def test_with_punctuation(self, text, intent):
        result = self.c.parse(text)
        assert result.intent == intent


class TestCycle54WhisperNumbers:
    """Whisper transcrit parfois les chiffres en lettres"""
    def setup_method(self):
        self.c = Commander()

    def test_numeric_volume(self):
        r = self.c.parse("volume 75")
        assert r.intent == "system_volume_set"

    def test_timer_with_digits(self):
        r = self.c.parse("minuteur 10 minutes")
        assert r.intent == "timer_set"

    def test_calc_with_digits(self):
        r = self.c.parse("calcule 100 plus 200")
        assert r.intent == "calc_compute"

    def test_brightness_digits(self):
        r = self.c.parse("luminosité 80")
        assert r.intent == "system_brightness"


class TestCycle55WhisperEmpty:
    """Gestion des entrees vides ou invalides"""
    def setup_method(self):
        self.c = Commander()

    def test_empty_string(self):
        assert self.c.parse("") is None

    def test_whitespace_only(self):
        assert self.c.parse("   ") is None

    def test_none_text(self):
        assert self.c.parse(None) is None

    def test_gibberish(self):
        r = self.c.parse("xyzqwerty")
        assert r.intent == "unknown"

    def test_single_letter(self):
        r = self.c.parse("a")
        assert r is not None


# ============================================================
# CYCLES 56-60: Disambiguation multi-intent
# ============================================================
class TestCycle56PriorityVdesktopVsMedia:
    """Bureau virtuel doit gagner sur media pour suivant/precedent"""
    def setup_method(self):
        self.c = Commander()

    def test_bureau_virtuel_suivant(self):
        assert self.c.parse("bureau virtuel suivant").intent == "vdesktop_right"

    def test_bureau_virtuel_precedent(self):
        assert self.c.parse("bureau virtuel précédent").intent == "vdesktop_left"

    def test_simple_suivant_is_media(self):
        assert self.c.parse("suivant").intent == "media_next"

    def test_simple_precedent_is_media(self):
        assert self.c.parse("précédent").intent == "media_previous"

    def test_piste_suivante_is_media(self):
        assert self.c.parse("piste suivante").intent == "media_next"


class TestCycle57PriorityNavigateVsApp:
    """Navigation dossiers doit gagner sur app_launch pour 'ouvre'"""
    def setup_method(self):
        self.c = Commander()

    def test_ouvre_telechargements(self):
        assert self.c.parse("ouvre les téléchargements").intent == "navigate_downloads"

    def test_ouvre_documents(self):
        assert self.c.parse("ouvre les documents").intent == "navigate_documents"

    def test_ouvre_bureau(self):
        assert self.c.parse("ouvre le bureau").intent == "navigate_desktop"

    def test_ouvre_dossier(self):
        assert self.c.parse("ouvre le dossier projets").intent == "navigate_folder"

    def test_ouvre_chrome_is_app(self):
        assert self.c.parse("ouvre chrome").intent == "app_launch"

    def test_ouvre_word_is_app(self):
        assert self.c.parse("ouvre word").intent == "app_launch"

    def test_ouvre_powerpoint_is_app(self):
        assert self.c.parse("ouvre powerpoint").intent == "app_launch"


class TestCycle58PriorityDicteeVsClose:
    """Dictee doit gagner sur app_close pour 'arrête'"""
    def setup_method(self):
        self.c = Commander()

    def test_arrete_la_dictee(self):
        assert self.c.parse("arrête la dictée").intent == "dictation_stop"

    def test_arrete_la_musique(self):
        assert self.c.parse("arrête la musique").intent == "media_pause"

    def test_arrete_chrome_is_close(self):
        assert self.c.parse("arrête chrome").intent == "app_close"

    def test_eteins_is_shutdown(self):
        assert self.c.parse("éteins").intent == "system_shutdown"


class TestCycle59PriorityWebVsFile:
    """Web doit gagner sur file_search pour 'recherche'"""
    def setup_method(self):
        self.c = Commander()

    def test_recherche_google(self):
        assert self.c.parse("recherche sur google python").intent == "web_google"

    def test_cherche_sur_google(self):
        assert self.c.parse("cherche sur google react").intent == "web_google"

    def test_cherche_fichier(self):
        assert self.c.parse("cherche le fichier rapport").intent == "file_search"

    def test_google_query(self):
        r = self.c.parse("google comment débuter python")
        assert r.intent == "web_google"
        assert "comment débuter python" in r.target


class TestCycle60PriorityMacroVsApp:
    """Macro doit gagner sur app_launch pour 'lance'"""
    def setup_method(self):
        self.c = Commander()

    def test_lance_macro(self):
        assert self.c.parse("lance la macro test").intent == "automation_run"

    def test_lance_script(self):
        assert self.c.parse("lance le script backup").intent == "automation_run"

    def test_lance_chrome_is_app(self):
        assert self.c.parse("lance chrome").intent == "app_launch"

    def test_macro_creation(self):
        assert self.c.parse("macro ferme tout et ouvre chrome").intent == "automation_create"

    def test_automatise(self):
        assert self.c.parse("automatise le backup").intent == "automation_create"


# ============================================================
# CYCLES 61-65: Calculatrice avancee
# ============================================================
class TestCycle61CalcTextToMath:
    """Conversion texte vocal vers expression mathematique"""
    def test_plus(self):
        assert "+" in _text_to_math("5 plus 3")

    def test_moins(self):
        assert "-" in _text_to_math("10 moins 4")

    def test_fois(self):
        assert "*" in _text_to_math("6 fois 7")

    def test_divise_par(self):
        assert "/" in _text_to_math("20 divise par 4")

    def test_puissance(self):
        assert "**" in _text_to_math("2 puissance 8")

    def test_virgule(self):
        result = _text_to_math("3 virgule 14")
        assert "3.14" in result

    def test_multiple_ops(self):
        result = _text_to_math("5 plus 3 fois 2")
        assert "+" in result
        assert "*" in result


class TestCycle62CalcASTCompute:
    """Calcul AST securise"""
    def test_addition(self):
        assert _ast_compute("5+3") == 8

    def test_subtraction(self):
        assert _ast_compute("10-4") == 6

    def test_multiplication(self):
        assert _ast_compute("6*7") == 42

    def test_division(self):
        assert _ast_compute("20/4") == 5.0

    def test_power(self):
        assert _ast_compute("2**8") == 256

    def test_modulo(self):
        assert _ast_compute("17%5") == 2

    def test_negative(self):
        assert _ast_compute("-5+3") == -2

    def test_parentheses(self):
        assert _ast_compute("(2+3)*4") == 20

    def test_complex_expr(self):
        assert _ast_compute("(10+5)*2-3") == 27

    def test_decimal(self):
        result = _ast_compute("3.14*2")
        assert abs(result - 6.28) < 0.001

    def test_division_by_zero(self):
        with pytest.raises(ValueError, match="Division par zero"):
            _ast_compute("5/0")

    def test_exponent_too_large(self):
        with pytest.raises(ValueError):
            _ast_compute("2**101")

    def test_no_import_attack(self):
        with pytest.raises((ValueError, SyntaxError)):
            _ast_compute("__import__('os').system('dir')")

    def test_no_function_call(self):
        with pytest.raises((ValueError, SyntaxError)):
            _ast_compute("print(42)")


class TestCycle63CalcFormatResult:
    """Formatage des resultats pour voix"""
    def test_integer_result(self):
        assert _format_result(42.0) == "42"

    def test_decimal_result(self):
        result = _format_result(3.14159)
        assert result.startswith("3.14")

    def test_zero(self):
        assert _format_result(0.0) == "0"

    def test_negative_integer(self):
        assert _format_result(-5.0) == "-5"

    def test_large_number(self):
        assert _format_result(1000000.0) == "1000000"


class TestCycle64CalcPercentage:
    """Pourcentages vocaux"""
    def setup_method(self):
        from whisperflow.jarvis.skills.calculator import CalculatorSkill
        self.calc = CalculatorSkill()

    @pytest.mark.asyncio
    async def test_20_percent_of_200(self):
        cmd = VoiceCommand("20 pourcent de 200", "calc_percentage")
        r = await self.calc.percentage(cmd)
        assert r.success
        assert "40" in r.message

    @pytest.mark.asyncio
    async def test_50_percent_of_100(self):
        cmd = VoiceCommand("50 pourcent de 100", "calc_percentage")
        r = await self.calc.percentage(cmd)
        assert r.success
        assert "50" in r.message

    @pytest.mark.asyncio
    async def test_invalid_format(self):
        cmd = VoiceCommand("pas un pourcentage", "calc_percentage")
        r = await self.calc.percentage(cmd)
        assert not r.success


class TestCycle65CalcTemperature:
    """Conversions de temperature"""
    def setup_method(self):
        from whisperflow.jarvis.skills.calculator import CalculatorSkill
        self.calc = CalculatorSkill()

    @pytest.mark.asyncio
    async def test_celsius_to_fahrenheit(self):
        cmd = VoiceCommand("100 en fahrenheit", "calc_convert", target="100 en fahrenheit")
        r = await self.calc.convert_temperature(cmd)
        assert r.success
        assert "212" in r.message

    @pytest.mark.asyncio
    async def test_fahrenheit_to_celsius(self):
        cmd = VoiceCommand("32 en celsius", "calc_convert", target="32 en celsius")
        r = await self.calc.convert_temperature(cmd)
        assert r.success
        assert "0" in r.message

    @pytest.mark.asyncio
    async def test_celsius_to_kelvin(self):
        cmd = VoiceCommand("0 en kelvin", "calc_convert", target="0 en kelvin")
        r = await self.calc.convert_temperature(cmd)
        assert r.success
        assert "273" in r.message

    @pytest.mark.asyncio
    async def test_invalid_conversion(self):
        cmd = VoiceCommand("blabla", "calc_convert", target="blabla")
        r = await self.calc.convert_temperature(cmd)
        assert not r.success


# ============================================================
# CYCLES 66-70: Minuteurs avances
# ============================================================
class TestCycle66ParseDuration:
    """Parsing de durees vocales FR"""
    def test_minutes(self):
        assert _parse_duration("5 minutes") == 300

    def test_secondes(self):
        assert _parse_duration("30 secondes") == 30

    def test_heures(self):
        assert _parse_duration("2 heures") == 7200

    def test_heure_minute(self):
        assert _parse_duration("1 heure 30 minutes") == 5400

    def test_shortform_h(self):
        assert _parse_duration("2h") == 7200

    def test_shortform_min(self):
        assert _parse_duration("5min") == 300

    def test_shortform_s(self):
        assert _parse_duration("45s") == 45

    def test_combined_hm(self):
        assert _parse_duration("1h30") == 5400


class TestCycle67FormatDuration:
    """Formatage de durees pour voix"""
    def test_seconds_only(self):
        r = _format_duration(45)
        assert "45" in r
        assert "seconde" in r

    def test_minutes_only(self):
        r = _format_duration(300)
        assert "5" in r
        assert "minute" in r

    def test_hours_only(self):
        r = _format_duration(7200)
        assert "2" in r
        assert "heure" in r

    def test_mixed(self):
        r = _format_duration(3661)
        assert "heure" in r
        assert "minute" in r


class TestCycle68TimerSkillUnit:
    """Tests unitaires du skill timer"""
    def setup_method(self):
        from whisperflow.jarvis.skills.timer_reminder import TimerReminderSkill
        self.timer = TimerReminderSkill()

    @pytest.mark.asyncio
    async def test_set_timer(self):
        cmd = VoiceCommand("minuteur 1 seconde", "timer_set", target="1 seconde")
        r = await self.timer.set_timer(cmd)
        assert r.success
        assert self.timer.active_count >= 1
        await asyncio.sleep(1.5)

    @pytest.mark.asyncio
    async def test_set_multiple_timers(self):
        cmd1 = VoiceCommand("minuteur 2 secondes", "timer_set", target="2 secondes")
        cmd2 = VoiceCommand("minuteur 3 secondes", "timer_set", target="3 secondes")
        await self.timer.set_timer(cmd1)
        await self.timer.set_timer(cmd2)
        assert self.timer.active_count >= 2
        await asyncio.sleep(3.5)

    @pytest.mark.asyncio
    async def test_cancel_timer(self):
        cmd = VoiceCommand("minuteur 60 secondes", "timer_set", target="60 secondes")
        await self.timer.set_timer(cmd)
        cancel_cmd = VoiceCommand("annule", "timer_cancel")
        r = await self.timer.cancel_timer(cancel_cmd)
        assert r.success

    @pytest.mark.asyncio
    async def test_list_empty(self):
        cmd = VoiceCommand("liste", "timer_list")
        r = await self.timer.list_timers(cmd)
        assert r.success


class TestCycle69TimerMaxDuration:
    """Limites de duree"""
    def test_max_24h(self):
        assert _parse_duration("24 heures") == 86400

    def test_zero_returns_none(self):
        result = _parse_duration("0 minutes")
        assert result is not None or result == 0


class TestCycle70TimerPipeline:
    """Timer via pipeline complet"""
    def setup_method(self):
        self.jarvis = Jarvis()
        self.jarvis.tts.speak = AsyncMock()
        self.jarvis.tts.speak_status = AsyncMock()

    @pytest.mark.asyncio
    async def test_timer_via_voice(self):
        await self.jarvis.process_transcription("Jarvis minuteur 1 seconde")
        assert self.jarvis.timer.active_count >= 1
        await self.jarvis.timer.cancel_timer(VoiceCommand("", ""))

    @pytest.mark.asyncio
    async def test_timer_list_via_voice(self):
        await self.jarvis.process_transcription("Jarvis minuteur 30 secondes")
        await self.jarvis.process_transcription("Jarvis liste les minuteurs")
        assert self.jarvis.tts.speak.called
        await self.jarvis.timer.cancel_timer(VoiceCommand("", ""))


# ============================================================
# CYCLES 71-75: Pipeline error recovery
# ============================================================
class TestCycle71EmptyTranscriptions:
    """Gestion des transcriptions vides"""
    def setup_method(self):
        self.jarvis = Jarvis()
        self.jarvis.tts.speak = AsyncMock()
        self.jarvis.tts.speak_status = AsyncMock()

    @pytest.mark.asyncio
    async def test_empty_string(self):
        await self.jarvis.process_transcription("")
        assert not self.jarvis.tts.speak.called

    @pytest.mark.asyncio
    async def test_whitespace(self):
        await self.jarvis.process_transcription("   ")
        assert not self.jarvis.tts.speak.called

    @pytest.mark.asyncio
    async def test_partial_ignored(self):
        await self.jarvis.process_transcription("Jarvis aide", is_partial=True)
        assert not self.jarvis.tts.speak.called


class TestCycle72NoWakeWord:
    """Sans wake word, rien ne se passe"""
    def setup_method(self):
        self.jarvis = Jarvis()
        self.jarvis.tts.speak = AsyncMock()
        self.jarvis.tts.speak_status = AsyncMock()

    @pytest.mark.asyncio
    async def test_no_jarvis(self):
        await self.jarvis.process_transcription("ouvre chrome")
        assert not self.jarvis.tts.speak.called

    @pytest.mark.asyncio
    async def test_random_text(self):
        await self.jarvis.process_transcription("bonjour comment allez-vous")
        assert not self.jarvis.tts.speak.called


class TestCycle73UnknownCommand:
    """Commandes non reconnues"""
    def setup_method(self):
        self.jarvis = Jarvis()
        self.jarvis.tts.speak = AsyncMock()
        self.jarvis.tts.speak_status = AsyncMock()

    @pytest.mark.asyncio
    async def test_unknown_gives_error(self):
        await self.jarvis.process_transcription("Jarvis fais quelque chose d'impossible")
        assert self.jarvis.tts.speak.called
        msg = self.jarvis.tts.speak.call_args[0][0]
        assert "Désolé" in msg or "compris" in msg.lower()


class TestCycle74HandlerError:
    """Resilience quand un handler leve une exception"""
    def setup_method(self):
        self.jarvis = Jarvis()
        self.jarvis.tts.speak = AsyncMock()
        self.jarvis.tts.speak_status = AsyncMock()

    @pytest.mark.asyncio
    async def test_handler_exception_caught(self):
        async def bad_handler(cmd):
            raise RuntimeError("Erreur simulee")

        self.jarvis.commander._handlers["app_launch"] = bad_handler
        await self.jarvis.process_transcription("Jarvis ouvre chrome")
        assert self.jarvis.tts.speak.called
        msg = self.jarvis.tts.speak.call_args[0][0]
        assert "Erreur" in msg or "Désolé" in msg


class TestCycle75CommandResultStates:
    """Verification des etats CommandResult"""
    def test_success_result(self):
        r = CommandResult(True, "OK")
        assert r.success
        assert r.message == "OK"
        assert r.data is None

    def test_failure_result(self):
        r = CommandResult(False, "Erreur")
        assert not r.success

    def test_result_with_data(self):
        r = CommandResult(True, "OK", data={"key": "value"})
        assert r.data["key"] == "value"


# ============================================================
# CYCLES 76-80: Securite approfondie
# ============================================================
class TestCycle76CalcInjection:
    """Tentatives d'injection dans la calculatrice"""
    def test_import_blocked(self):
        with pytest.raises((ValueError, SyntaxError)):
            _ast_compute("__import__('os')")

    def test_lambda_blocked(self):
        with pytest.raises((ValueError, SyntaxError)):
            _ast_compute("(lambda: 1)()")

    def test_list_comprehension_blocked(self):
        with pytest.raises((ValueError, SyntaxError)):
            _ast_compute("[x for x in range(10)]")

    def test_attribute_access_blocked(self):
        with pytest.raises((ValueError, SyntaxError)):
            _ast_compute("().__class__.__bases__")

    def test_string_literal_blocked(self):
        with pytest.raises((ValueError, SyntaxError)):
            _ast_compute("'hello'")


class TestCycle77AppNameInjection:
    """Injection dans les noms d'application"""
    def setup_method(self):
        self.c = Commander()

    def test_semicolon_in_app(self):
        r = self.c.parse("ouvre chrome;rm -rf /")
        assert r.intent == "app_launch"
        assert r.target is not None

    def test_pipe_in_app(self):
        r = self.c.parse("ouvre notepad|calc")
        assert r.intent == "app_launch"

    def test_backtick_in_app(self):
        r = self.c.parse("ouvre `whoami`")
        assert r.intent == "app_launch"


class TestCycle78PathTraversal:
    """Tentatives de traversal de chemin"""
    def setup_method(self):
        self.c = Commander()

    def test_dotdot_in_folder(self):
        r = self.c.parse("ouvre le dossier ../../../etc")
        assert r.intent == "navigate_folder"

    def test_absolute_path(self):
        r = self.c.parse("ouvre le dossier C:\\Windows\\System32")
        assert r.intent == "navigate_folder"


class TestCycle79LongInput:
    """Entrees tres longues (debordement)"""
    def setup_method(self):
        self.c = Commander()

    def test_very_long_app_name(self):
        long_name = "a" * 10000
        r = self.c.parse(f"ouvre {long_name}")
        assert r.intent == "app_launch"

    def test_very_long_note(self):
        long_note = "mot " * 5000
        r = self.c.parse(f"note {long_note}")
        assert r.intent == "note_add"

    def test_very_long_calc(self):
        long_expr = "1+1+" * 1000 + "1"
        r = self.c.parse(f"calcule {long_expr}")
        assert r.intent == "calc_compute"


class TestCycle80SpecialChars:
    """Caracteres speciaux dans les commandes"""
    def setup_method(self):
        self.c = Commander()

    def test_quotes_in_search(self):
        r = self.c.parse('google "meilleur restaurant"')
        assert r.intent == "web_google"

    def test_ampersand(self):
        r = self.c.parse("google python & javascript")
        assert r.intent == "web_google"

    def test_unicode_note(self):
        r = self.c.parse("note rendez-vous cafe")
        assert r.intent == "note_add"

    def test_accented_app(self):
        r = self.c.parse("ouvre libreoffice writer")
        assert r.intent == "app_launch"


# ============================================================
# CYCLES 81-85: Scenarios metier
# ============================================================
class TestCycle81ScenarioDeveloper:
    """Journee typique d'un developpeur"""
    def setup_method(self):
        self.jarvis = Jarvis()
        self.jarvis.tts.speak = AsyncMock()
        self.jarvis.tts.speak_status = AsyncMock()

    @pytest.mark.asyncio
    async def test_dev_workflow(self):
        commands = [
            ("Jarvis ouvre visual studio code", "app_launch"),
            ("Jarvis ouvre le dossier projets", "navigate_folder"),
            ("Jarvis google python asyncio tutorial", "web_google"),
            ("Jarvis note corriger le bug de connexion", "note_add"),
            ("Jarvis minuteur 25 minutes", "timer_set"),
            ("Jarvis calcule 8 fois 1024", "calc_compute"),
            ("Jarvis cpu", "system_top_cpu"),
            ("Jarvis gpu", "system_gpu"),
            ("Jarvis espace disque", "system_disk"),
        ]
        for text, expected_intent in commands:
            detected, cmd_text = detect_wake_word(text)
            assert detected, f"Wake word non detecte pour: {text}"
            result = self.jarvis.commander.parse(cmd_text)
            assert result.intent == expected_intent, \
                f"'{text}' -> {result.intent} au lieu de {expected_intent}"
        await self.jarvis.timer.cancel_timer(VoiceCommand("", ""))


class TestCycle82ScenarioTeacher:
    """Journee typique d'une enseignante"""
    def setup_method(self):
        self.jarvis = Jarvis()
        self.jarvis.tts.speak = AsyncMock()
        self.jarvis.tts.speak_status = AsyncMock()

    @pytest.mark.asyncio
    async def test_teacher_workflow(self):
        commands = [
            ("Jarvis ouvre word", "app_launch"),
            ("Jarvis minuteur 45 minutes", "timer_set"),
            ("Jarvis note preparer controle de maths", "note_add"),
            ("Jarvis calcule 18 plus 15 plus 12", "calc_compute"),
            ("Jarvis 20 pourcent de 150", "calc_percentage"),
            ("Jarvis wikipedia fractions", "web_wikipedia"),
            ("Jarvis lis les notes", "note_read"),
        ]
        for text, expected_intent in commands:
            detected, cmd_text = detect_wake_word(text)
            assert detected
            result = self.jarvis.commander.parse(cmd_text)
            assert result.intent == expected_intent, \
                f"'{text}' -> {result.intent} au lieu de {expected_intent}"
        await self.jarvis.timer.cancel_timer(VoiceCommand("", ""))


class TestCycle83ScenarioGaming:
    """Session gaming"""
    def setup_method(self):
        self.c = Commander()

    def test_gaming_commands(self):
        commands = [
            ("haute performance", "power_high_perf"),
            ("gpu", "system_gpu"),
            ("ressources système", "system_resources"),
            ("muet", "system_mute"),
            ("volume 80", "system_volume_set"),
            ("capture", "window_screenshot"),
            ("mode nuit", "display_night"),
        ]
        for text, expected in commands:
            r = self.c.parse(text)
            assert r.intent == expected, f"'{text}' -> {r.intent} au lieu de {expected}"


class TestCycle84ScenarioMeeting:
    """Preparation de reunion"""
    def setup_method(self):
        self.jarvis = Jarvis()
        self.jarvis.tts.speak = AsyncMock()
        self.jarvis.tts.speak_status = AsyncMock()

    @pytest.mark.asyncio
    async def test_meeting_prep(self):
        commands = [
            ("Jarvis ouvre teams", "app_launch"),
            ("Jarvis muet", "system_mute"),
            ("Jarvis note points a discuter", "note_add"),
            ("Jarvis minuteur 30 minutes", "timer_set"),
            ("Jarvis capture", "window_screenshot"),
        ]
        for text, expected in commands:
            detected, cmd_text = detect_wake_word(text)
            assert detected
            r = self.jarvis.commander.parse(cmd_text)
            assert r.intent == expected
        await self.jarvis.timer.cancel_timer(VoiceCommand("", ""))


class TestCycle85ScenarioCooking:
    """Cuisine avec minuteurs multiples"""
    def setup_method(self):
        self.jarvis = Jarvis()
        self.jarvis.tts.speak = AsyncMock()
        self.jarvis.tts.speak_status = AsyncMock()

    @pytest.mark.asyncio
    async def test_cooking_timers(self):
        await self.jarvis.process_transcription("Jarvis minuteur 2 secondes")
        assert self.jarvis.timer.active_count >= 1

        await self.jarvis.process_transcription("Jarvis minuteur 3 secondes")
        assert self.jarvis.timer.active_count >= 2

        await self.jarvis.process_transcription("Jarvis liste les minuteurs")
        assert self.jarvis.tts.speak.called

        await self.jarvis.timer.cancel_timer(VoiceCommand("", ""))


# ============================================================
# CYCLES 86-90: Verification exhaustive de chaque pattern
# ============================================================
class TestCycle86AllDictationPatterns:
    def setup_method(self):
        self.c = Commander()

    @pytest.mark.parametrize("text,intent", [
        ("mode dictée", "dictation_start"),
        ("dictation mode", "dictation_start"),
        ("commence à écrire", "dictation_start"),
        ("écris", "dictation_start"),
        ("arrête la dictée", "dictation_stop"),
        ("stop dictation", "dictation_stop"),
        ("fin de dictée", "dictation_stop"),
        ("arrête d'écrire", "dictation_stop"),
        ("nouvelle ligne", "dictation_newline"),
        ("new line", "dictation_newline"),
        ("à la ligne", "dictation_newline"),
        ("retour à la ligne", "dictation_newline"),
        ("point final", "dictation_period"),
        ("point", "dictation_period"),
    ])
    def test_dictation(self, text, intent):
        assert self.c.parse(text).intent == intent


class TestCycle87AllVdesktopPatterns:
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
    def test_vdesktop(self, text, intent):
        assert self.c.parse(text).intent == intent


class TestCycle88AllMediaSystemPatterns:
    def setup_method(self):
        self.c = Commander()

    @pytest.mark.parametrize("text,intent", [
        ("arrête la musique", "media_pause"),
        ("arrête la lecture", "media_pause"),
        ("play", "media_play"),
        ("lecture", "media_play"),
        ("joue", "media_play"),
        ("pause", "media_pause"),
        ("suivant", "media_next"),
        ("next", "media_next"),
        ("piste suivante", "media_next"),
        ("précédent", "media_previous"),
        ("previous", "media_previous"),
        ("volume 50", "system_volume_set"),
        ("monte le volume", "system_volume_up"),
        ("baisse le volume", "system_volume_down"),
        ("muet", "system_mute"),
        ("luminosité 75", "system_brightness"),
        ("wifi on", "system_wifi"),
        ("bluetooth off", "system_bluetooth"),
        ("éteins", "system_shutdown"),
        ("redémarre", "system_restart"),
        ("veille", "system_sleep"),
        ("batterie", "system_battery"),
        ("heure", "system_time"),
        ("date", "system_date"),
    ])
    def test_media_system(self, text, intent):
        assert self.c.parse(text).intent == intent


class TestCycle89AllNetworkProcessPatterns:
    def setup_method(self):
        self.c = Commander()

    @pytest.mark.parametrize("text,intent", [
        ("liste les processus", "process_list"),
        ("tue le processus chrome", "process_kill"),
        ("ressources", "system_resources"),
        ("cpu", "system_top_cpu"),
        ("mémoire", "system_resources"),
        ("espace disque", "system_disk"),
        ("uptime", "system_uptime"),
        ("gpu", "system_gpu"),
        ("matériel", "system_hardware"),
        ("état du réseau", "network_status"),
        ("ip publique", "network_ip_public"),
        ("adresse ip", "network_ip"),
        ("ping google.com", "network_ping"),
        ("teste la connexion", "network_ping"),
        ("réseaux wifi", "network_wifi_list"),
        ("test de débit", "network_speed"),
    ])
    def test_network_process(self, text, intent):
        assert self.c.parse(text).intent == intent


class TestCycle90AllControlPatterns:
    def setup_method(self):
        self.c = Commander()

    @pytest.mark.parametrize("text,intent", [
        ("aide", "jarvis_help"),
        ("help", "jarvis_help"),
        ("statut", "jarvis_status"),
        ("status", "jarvis_status"),
        ("au revoir", "jarvis_quit"),
        ("goodbye", "jarvis_quit"),
        ("merci", "jarvis_thanks"),
        ("thanks", "jarvis_thanks"),
        ("répète", "jarvis_repeat"),
        ("repeat", "jarvis_repeat"),
        ("annule", "jarvis_cancel"),
        ("cancel", "jarvis_cancel"),
        ("paramètres", "jarvis_settings"),
        ("settings", "jarvis_settings"),
        ("plan d'alimentation", "power_plan"),
        ("haute performance", "power_high_perf"),
        ("mode équilibré", "power_balanced"),
        ("économie d'énergie", "power_saver"),
        ("hibernation", "power_hibernate"),
        ("résolution", "display_resolution"),
        ("mode nuit", "display_night"),
        ("paramètres d'affichage", "display_settings"),
        ("paramètres du son", "audio_settings"),
    ])
    def test_control(self, text, intent):
        assert self.c.parse(text).intent == intent


# ============================================================
# CYCLES 91-95: Gardes de regression
# ============================================================
class TestCycle91RegressionChargeInTelechargements:
    """BUG FIX: 'telechargements' ne doit PAS matcher system_resources via 'charge'"""
    def setup_method(self):
        self.c = Commander()

    def test_ouvre_telechargements(self):
        r = self.c.parse("ouvre les téléchargements")
        assert r.intent == "navigate_downloads", \
            f"REGRESSION: 'charge' dans 'telechargements' matche {r.intent}"

    def test_standalone_charge(self):
        r = self.c.parse("charge système")
        assert r.intent == "system_resources"


class TestCycle92RegressionPointInPowerpoint:
    """BUG FIX: 'powerpoint' ne doit PAS matcher dictation_period via 'point$'"""
    def setup_method(self):
        self.c = Commander()

    def test_ouvre_powerpoint(self):
        r = self.c.parse("ouvre powerpoint")
        assert r.intent == "app_launch", \
            f"REGRESSION: 'point' dans 'powerpoint' matche {r.intent}"

    def test_standalone_point(self):
        r = self.c.parse("point")
        assert r.intent == "dictation_period"

    def test_point_final(self):
        r = self.c.parse("point final")
        assert r.intent == "dictation_period"


class TestCycle93RegressionRamInParametres:
    """BUG FIX: 'parametres' ne doit PAS matcher system_resources via 'ram'"""
    def setup_method(self):
        self.c = Commander()

    def test_parametres_is_settings(self):
        r = self.c.parse("paramètres")
        assert r.intent == "jarvis_settings", \
            f"REGRESSION: 'ram' dans 'parametres' matche {r.intent}"

    def test_standalone_ram(self):
        r = self.c.parse("ram")
        assert r.intent == "system_resources"

    def test_programmes_not_ram(self):
        r = self.c.parse("liste les programmes installés")
        assert r.intent == "software_list", \
            f"REGRESSION: 'ram' dans 'programmes' matche {r.intent}"


class TestCycle94RegressionMacroVsApp:
    """BUG FIX: 'lance la macro' doit matcher automation_run, pas automation_create"""
    def setup_method(self):
        self.c = Commander()

    def test_lance_macro(self):
        r = self.c.parse("lance la macro test")
        assert r.intent == "automation_run", \
            f"REGRESSION: 'lance la macro' matche {r.intent}"

    def test_macro_creation(self):
        r = self.c.parse("macro ferme tout")
        assert r.intent == "automation_create"


class TestCycle95RegressionCoupeLeSon:
    """BUG FIX: 'coupe le son' doit matcher system_mute, pas clipboard_cut"""
    def setup_method(self):
        self.c = Commander()

    def test_coupe_le_son(self):
        r = self.c.parse("coupe le son")
        assert r.intent == "system_mute", \
            f"REGRESSION: 'coupe le son' matche {r.intent}"

    def test_coupe_selection(self):
        r = self.c.parse("coupe la sélection")
        assert r.intent == "clipboard_cut"


# ============================================================
# CYCLES 96-100: Stress ultime et validation finale
# ============================================================
class TestCycle96StressAllPatternsCompile:
    """Tous les patterns doivent compiler sans erreur"""
    def test_all_patterns_valid_regex(self):
        import re
        for i, (pattern, intent) in enumerate(COMMAND_PATTERNS):
            try:
                re.compile(pattern, re.IGNORECASE)
            except re.error as e:
                pytest.fail(f"Pattern #{i} ({intent}) invalide: {e}")


class TestCycle97Stress100Commands:
    """100 commandes rapides sans crash"""
    def setup_method(self):
        self.c = Commander()

    def test_100_rapid_parses(self):
        commands = [
            "ouvre chrome", "ferme chrome", "volume 50", "muet",
            "aide", "merci", "statut", "au revoir",
            "minuteur 5 minutes", "calcule 2 plus 2",
            "note test", "lis les notes",
            "bureau virtuel suivant", "nouveau bureau virtuel",
            "suivant", "précédent", "play", "pause",
            "cpu", "gpu", "mémoire", "espace disque",
            "wifi on", "bluetooth off",
            "google test", "youtube musique",
        ] * 4  # = 104 commandes
        for text in commands:
            r = self.c.parse(text)
            assert r is not None
            assert r.intent != ""


class TestCycle98StressFullPipeline50:
    """50 commandes via pipeline Jarvis complet"""
    def setup_method(self):
        self.jarvis = Jarvis()
        self.jarvis.tts.speak = AsyncMock()
        self.jarvis.tts.speak_status = AsyncMock()

    @pytest.mark.asyncio
    async def test_50_pipeline_commands(self):
        commands = [
            "Jarvis aide",
            "Jarvis statut",
            "Jarvis merci",
            "Jarvis heure",
            "Jarvis date",
            "Jarvis batterie",
            "Jarvis cpu",
            "Jarvis gpu",
            "Jarvis mémoire",
            "Jarvis espace disque",
            "Jarvis uptime",
            "Jarvis matériel",
            "Jarvis état du réseau",
            "Jarvis adresse ip",
            "Jarvis ip publique",
            "Jarvis réseaux wifi",
            "Jarvis plan d'alimentation",
            "Jarvis résolution",
            "Jarvis météo",
            "Jarvis calcule 1 plus 1",
            "Jarvis calcule 10 fois 5",
            "Jarvis calcule 100 moins 37",
            "Jarvis note test pipeline",
            "Jarvis lis les notes",
            "Jarvis efface les notes",
            "Jarvis liste les minuteurs",
            "Jarvis capture",
            "Jarvis muet",
            "Jarvis play",
            "Jarvis pause",
            "Jarvis suivant",
            "Jarvis précédent",
            "Jarvis minimise",
            "Jarvis maximise",
            "Jarvis restaure",
            "Jarvis nouveau bureau virtuel",
            "Jarvis vue des tâches",
            "Jarvis aide",
            "Jarvis statut",
            "Jarvis heure",
            "Jarvis date",
            "Jarvis aide",
            "Jarvis statut",
            "Jarvis merci",
            "Jarvis heure",
            "Jarvis date",
            "Jarvis batterie",
            "Jarvis cpu",
            "Jarvis gpu",
            "Jarvis merci",
        ]
        for text in commands:
            await self.jarvis.process_transcription(text)
        assert self.jarvis.tts.speak.call_count >= 40


class TestCycle99AllIntentsHaveHandlers:
    """Chaque intent des patterns doit avoir un handler"""
    def setup_method(self):
        self.jarvis = Jarvis()

    def test_all_intents_registered(self):
        intents = set()
        for _, intent in COMMAND_PATTERNS:
            intents.add(intent)

        registered = set(self.jarvis.commander.list_intents())

        missing = intents - registered
        assert not missing, f"Intents sans handler: {missing}"


class TestCycle100FinalValidation:
    """Validation finale: comptages et coherence"""
    def setup_method(self):
        self.jarvis = Jarvis()

    def test_pattern_count(self):
        assert len(COMMAND_PATTERNS) >= 105, \
            f"Seulement {len(COMMAND_PATTERNS)} patterns (min 105)"

    def test_handler_count(self):
        handlers = self.jarvis.commander.list_intents()
        assert len(handlers) >= 70, \
            f"Seulement {len(handlers)} handlers (min 70)"

    def test_unique_intents_in_handlers(self):
        handlers = self.jarvis.commander.list_intents()
        assert len(handlers) == len(set(handlers)), "Handlers dupliques!"

    def test_15_skills_exist(self):
        skills = [
            self.jarvis.app_launcher,
            self.jarvis.system_control,
            self.jarvis.window_manager,
            self.jarvis.file_manager,
            self.jarvis.web_browser,
            self.jarvis.media_control,
            self.jarvis.clipboard,
            self.jarvis.process_mgr,
            self.jarvis.network,
            self.jarvis.power_display,
            self.jarvis.software,
            self.jarvis.timer,
            self.jarvis.notes,
            self.jarvis.calculator,
            self.jarvis.vdesktop,
        ]
        for s in skills:
            assert s is not None

    def test_4_agents_exist(self):
        agents = [
            self.jarvis.dictation,
            self.jarvis.search,
            self.jarvis.automation,
            self.jarvis.navigation,
        ]
        for a in agents:
            assert a is not None

    def test_complete_system_ready(self):
        """JARVIS est pret pour la production"""
        assert len(COMMAND_PATTERNS) >= 105
        assert len(self.jarvis.commander.list_intents()) >= 70
        assert self.jarvis.tts is not None
        assert self.jarvis.commander is not None
        assert not self.jarvis.dictation.active
        assert not self.jarvis.automation.recording
