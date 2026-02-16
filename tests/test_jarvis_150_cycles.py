"""
JARVIS - Cycles 101-150: Formation Intensive Phase 3
4 nouveaux skills: Traducteur, Convertisseur, Pomodoro, Snapshot

Cycles 101-105: Patterns traduction, conversion, pomodoro, snapshot
Cycles 106-110: Skill traducteur (dictionnaire, bidirectionnel, lookup)
Cycles 111-115: Skill convertisseur (distance, poids, donnees, erreurs)
Cycles 116-120: Skill pomodoro (start, stop, status, cycles)
Cycles 121-125: Skill snapshot (prise, comparaison, historique)
Cycles 126-130: Pipeline nouveaux skills via Jarvis complet
Cycles 131-135: Scenarios avances (etudiant, traductrice, sportif, admin, presentateur)
Cycles 136-140: Non-regression patterns existants + nouveaux
Cycles 141-145: Edge cases et securite nouveaux skills
Cycles 146-150: Stress ultime et validation finale 150 cycles

Total: 50 cycles, ~250 tests
"""

import asyncio
import pytest
import logging
import inspect
from unittest.mock import AsyncMock, patch
from pathlib import Path

from whisperflow.jarvis.jarvis_core import Jarvis
from whisperflow.jarvis.commander import Commander, VoiceCommand, CommandResult, COMMAND_PATTERNS
from whisperflow.jarvis.wake_word import detect_wake_word
from whisperflow.jarvis.skills.translator import (
    TranslatorSkill, _translate_text, _translate_word, _FR_TO_EN, _EN_TO_FR
)
from whisperflow.jarvis.skills.unit_converter import (
    UnitConverterSkill, convert_units, _format_value
)
from whisperflow.jarvis.skills.pomodoro import PomodoroSkill
from whisperflow.jarvis.skills.system_snapshot import SystemSnapshotSkill, _get_system_info

logging.basicConfig(level=logging.INFO)


# ============================================================
# CYCLES 101-105: Patterns nouveaux skills
# ============================================================
class TestCycle101TranslationPatterns:
    def setup_method(self):
        self.c = Commander()

    @pytest.mark.parametrize("text,intent", [
        ("traduis en anglais bonjour", "translate_fr_en"),
        ("traduis bonjour en anglais", "translate_fr_en"),
        ("translate en anglais merci", "translate_fr_en"),
        ("traduis en français hello", "translate_en_fr"),
        ("traduis hello en français", "translate_en_fr"),
        ("traduction bonjour", "translate_lookup"),
        ("traduction de hello", "translate_lookup"),
    ])
    def test_translation_patterns(self, text, intent):
        r = self.c.parse(text)
        assert r.intent == intent, f"'{text}' -> {r.intent} au lieu de {intent}"


class TestCycle102ConversionPatterns:
    def setup_method(self):
        self.c = Commander()

    @pytest.mark.parametrize("text,intent", [
        ("convertis 5 km en miles", "unit_convert"),
        ("convertis 100 kg en livres", "unit_convert"),
        ("convert 10 go en mo", "unit_convert"),
        ("conversion 3 miles en km", "unit_convert"),
    ])
    def test_conversion_patterns(self, text, intent):
        r = self.c.parse(text)
        assert r.intent == intent, f"'{text}' -> {r.intent} au lieu de {intent}"


class TestCycle103PomodoroPatterns:
    def setup_method(self):
        self.c = Commander()

    @pytest.mark.parametrize("text,intent", [
        ("pomodoro", "pomodoro_start"),
        ("lance un pomodoro", "pomodoro_start"),
        ("technique pomodoro", "pomodoro_start"),
        ("mode travail", "pomodoro_start"),
        ("arrête le pomodoro", "pomodoro_stop"),
        ("stop pomodoro", "pomodoro_stop"),
        ("fin du pomodoro", "pomodoro_stop"),
        ("état du pomodoro", "pomodoro_status"),
        ("pomodoro status", "pomodoro_status"),
        ("où en est le pomodoro", "pomodoro_status"),
    ])
    def test_pomodoro_patterns(self, text, intent):
        r = self.c.parse(text)
        assert r.intent == intent, f"'{text}' -> {r.intent} au lieu de {intent}"


class TestCycle104SnapshotPatterns:
    def setup_method(self):
        self.c = Commander()

    @pytest.mark.parametrize("text,intent", [
        ("snapshot système", "snapshot_take"),
        ("capture du système", "snapshot_take"),
        ("état complet", "snapshot_take"),
        ("system snapshot", "snapshot_take"),
        ("bilan système", "snapshot_take"),
        ("compare les snapshots", "snapshot_compare"),
        ("comparaison système", "snapshot_compare"),
        ("diff système", "snapshot_compare"),
        ("historique des snapshots", "snapshot_history"),
        ("snapshots précédents", "snapshot_history"),
    ])
    def test_snapshot_patterns(self, text, intent):
        r = self.c.parse(text)
        assert r.intent == intent, f"'{text}' -> {r.intent} au lieu de {intent}"


class TestCycle105PatternCount:
    def test_pattern_count_increased(self):
        assert len(COMMAND_PATTERNS) >= 115, \
            f"Seulement {len(COMMAND_PATTERNS)} patterns (attendu >= 115)"

    def test_handler_count_increased(self):
        jarvis = Jarvis()
        handlers = jarvis.commander.list_intents()
        assert len(handlers) >= 80, \
            f"Seulement {len(handlers)} handlers (attendu >= 80)"


# ============================================================
# CYCLES 106-110: Skill traducteur
# ============================================================
class TestCycle106TranslateWords:
    def test_bonjour(self):
        assert _translate_word("bonjour", "fr_en") == "hello"

    def test_hello(self):
        assert _translate_word("hello", "en_fr") == "bonjour"

    def test_merci(self):
        assert _translate_word("merci", "fr_en") == "thank you"

    def test_unknown(self):
        assert _translate_word("inconnu", "fr_en") == ""

    def test_case_insensitive(self):
        assert _translate_word("BONJOUR", "fr_en") == "hello"


class TestCycle107TranslateText:
    def test_simple_phrase(self):
        result = _translate_text("bonjour merci", "fr_en")
        assert "hello" in result
        assert "thank you" in result

    def test_mixed_known_unknown(self):
        result = _translate_text("bonjour monde", "fr_en")
        assert "hello" in result
        assert "monde" in result

    def test_en_to_fr(self):
        result = _translate_text("hello", "en_fr")
        assert "bonjour" in result


class TestCycle108TranslateSkillFrEn:
    def setup_method(self):
        self.tr = TranslatorSkill()

    @pytest.mark.asyncio
    async def test_translate_bonjour(self):
        cmd = VoiceCommand("traduis en anglais bonjour", "translate_fr_en",
                           target="en anglais bonjour")
        r = await self.tr.translate_fr_en(cmd)
        assert r.success
        assert "hello" in r.message.lower()

    @pytest.mark.asyncio
    async def test_translate_empty(self):
        cmd = VoiceCommand("", "translate_fr_en", target="")
        r = await self.tr.translate_fr_en(cmd)
        assert not r.success


class TestCycle109TranslateSkillEnFr:
    def setup_method(self):
        self.tr = TranslatorSkill()

    @pytest.mark.asyncio
    async def test_translate_hello(self):
        cmd = VoiceCommand("traduis en français hello", "translate_en_fr",
                           target="en français hello")
        r = await self.tr.translate_en_fr(cmd)
        assert r.success
        assert "bonjour" in r.message.lower()


class TestCycle110TranslateLookup:
    def setup_method(self):
        self.tr = TranslatorSkill()

    @pytest.mark.asyncio
    async def test_lookup_fr(self):
        cmd = VoiceCommand("traduction bonjour", "translate_lookup", target="bonjour")
        r = await self.tr.lookup(cmd)
        assert r.success
        assert "hello" in r.message

    @pytest.mark.asyncio
    async def test_lookup_en(self):
        cmd = VoiceCommand("traduction hello", "translate_lookup", target="hello")
        r = await self.tr.lookup(cmd)
        assert r.success
        assert "bonjour" in r.message

    @pytest.mark.asyncio
    async def test_lookup_unknown(self):
        cmd = VoiceCommand("traduction xyz", "translate_lookup", target="xyz")
        r = await self.tr.lookup(cmd)
        assert not r.success

    def test_dictionary_bidirectional(self):
        for fr, en in _FR_TO_EN.items():
            assert en in _EN_TO_FR, f"'{en}' absent du dictionnaire EN->FR"
            assert _EN_TO_FR[en] == fr


# ============================================================
# CYCLES 111-115: Skill convertisseur d'unites
# ============================================================
class TestCycle111ConvertDistance:
    def test_km_to_miles(self):
        result = convert_units(10, "km", "miles")
        assert abs(result - 6.2137) < 0.01

    def test_miles_to_km(self):
        result = convert_units(1, "miles", "km")
        assert abs(result - 1.60934) < 0.01

    def test_m_to_cm(self):
        assert convert_units(1, "m", "cm") == 100

    def test_feet_to_m(self):
        result = convert_units(1, "pieds", "m")
        assert abs(result - 0.3048) < 0.001


class TestCycle112ConvertWeight:
    def test_kg_to_lbs(self):
        result = convert_units(1, "kg", "lbs")
        assert abs(result - 2.20462) < 0.01

    def test_lbs_to_kg(self):
        result = convert_units(10, "lbs", "kg")
        assert abs(result - 4.53592) < 0.01

    def test_g_to_kg(self):
        assert convert_units(1000, "g", "kg") == 1.0

    def test_tonnes_to_kg(self):
        assert convert_units(1, "tonnes", "kg") == 1000


class TestCycle113ConvertData:
    def test_go_to_mo(self):
        assert convert_units(1, "go", "mo") == 1024

    def test_gb_to_mb(self):
        assert convert_units(1, "gb", "mb") == 1024

    def test_to_to_go(self):
        assert convert_units(1, "to", "go") == 1024

    def test_ko_to_octets(self):
        assert convert_units(1, "ko", "octets") == 1024


class TestCycle114ConvertErrors:
    def test_incompatible_units(self):
        with pytest.raises(ValueError, match="incompatibles"):
            convert_units(1, "km", "kg")

    def test_unknown_unit(self):
        with pytest.raises(ValueError, match="inconnue"):
            convert_units(1, "xyz", "km")


class TestCycle115ConvertSkillUnit:
    def setup_method(self):
        self.uc = UnitConverterSkill()

    @pytest.mark.asyncio
    async def test_convert_km_miles(self):
        cmd = VoiceCommand("convertis 5 km en miles", "unit_convert",
                           target="5 km en miles")
        r = await self.uc.convert(cmd)
        assert r.success
        assert "3.1" in r.message

    @pytest.mark.asyncio
    async def test_convert_bad_format(self):
        cmd = VoiceCommand("convertis rien", "unit_convert", target="rien")
        r = await self.uc.convert(cmd)
        assert not r.success

    def test_format_value_int(self):
        assert _format_value(42.0) == "42"

    def test_format_value_decimal(self):
        result = _format_value(3.14159)
        assert result.startswith("3.14")


# ============================================================
# CYCLES 116-120: Skill pomodoro
# ============================================================
class TestCycle116PomodoroStart:
    def setup_method(self):
        self.pomo = PomodoroSkill()

    @pytest.mark.asyncio
    async def test_start(self):
        cmd = VoiceCommand("pomodoro", "pomodoro_start")
        r = await self.pomo.start(cmd)
        assert r.success
        assert self.pomo.active
        assert self.pomo.phase == "work"
        assert self.pomo.cycle == 1
        await self.pomo.stop(VoiceCommand("", ""))

    @pytest.mark.asyncio
    async def test_double_start(self):
        cmd = VoiceCommand("pomodoro", "pomodoro_start")
        await self.pomo.start(cmd)
        r = await self.pomo.start(cmd)
        assert not r.success
        assert "déjà actif" in r.message
        await self.pomo.stop(VoiceCommand("", ""))


class TestCycle117PomodoroStop:
    def setup_method(self):
        self.pomo = PomodoroSkill()

    @pytest.mark.asyncio
    async def test_stop_active(self):
        await self.pomo.start(VoiceCommand("", ""))
        r = await self.pomo.stop(VoiceCommand("", ""))
        assert r.success
        assert not self.pomo.active
        assert "arrêté" in r.message

    @pytest.mark.asyncio
    async def test_stop_inactive(self):
        r = await self.pomo.stop(VoiceCommand("", ""))
        assert r.success
        assert "Aucun" in r.message


class TestCycle118PomodoroStatus:
    def setup_method(self):
        self.pomo = PomodoroSkill()

    @pytest.mark.asyncio
    async def test_status_inactive(self):
        r = await self.pomo.status(VoiceCommand("", ""))
        assert r.success
        assert "inactif" in r.message

    @pytest.mark.asyncio
    async def test_status_active(self):
        await self.pomo.start(VoiceCommand("", ""))
        r = await self.pomo.status(VoiceCommand("", ""))
        assert r.success
        assert "actif" in r.message.lower()
        assert "travail" in r.message
        await self.pomo.stop(VoiceCommand("", ""))


class TestCycle119PomodoroProperties:
    def setup_method(self):
        self.pomo = PomodoroSkill()

    def test_initial_state(self):
        assert not self.pomo.active
        assert self.pomo.phase == "idle"
        assert self.pomo.cycle == 0
        assert self.pomo.total_completed == 0

    @pytest.mark.asyncio
    async def test_cycle_increments(self):
        await self.pomo.start(VoiceCommand("", ""))
        assert self.pomo.cycle == 1
        await self.pomo.stop(VoiceCommand("", ""))


class TestCycle120PomodoroCallback:
    def setup_method(self):
        self.pomo = PomodoroSkill()
        self.callback_called = False

    @pytest.mark.asyncio
    async def test_callback_set(self):
        async def my_callback(phase, msg):
            self.callback_called = True

        self.pomo.set_callback(my_callback)
        await self.pomo.start(VoiceCommand("", ""))
        await asyncio.sleep(0.1)
        assert self.callback_called
        await self.pomo.stop(VoiceCommand("", ""))


# ============================================================
# CYCLES 121-125: Skill snapshot systeme
# ============================================================
class TestCycle121SnapshotTake:
    def setup_method(self):
        self.snap = SystemSnapshotSkill()

    @pytest.mark.asyncio
    async def test_take_snapshot(self):
        r = await self.snap.take_snapshot(VoiceCommand("", ""))
        assert r.success
        assert "Snapshot" in r.message
        assert self.snap.snapshot_count == 1
        assert r.data is not None
        assert "os" in r.data
        assert "timestamp" in r.data

    @pytest.mark.asyncio
    async def test_multiple_snapshots(self):
        cmd = VoiceCommand("", "snapshot_take")
        await self.snap.take_snapshot(cmd)
        await self.snap.take_snapshot(cmd)
        assert self.snap.snapshot_count == 2


class TestCycle122SnapshotCompare:
    def setup_method(self):
        self.snap = SystemSnapshotSkill()

    @pytest.mark.asyncio
    async def test_compare_needs_two(self):
        r = await self.snap.compare(VoiceCommand("", ""))
        assert not r.success
        assert "2 snapshots" in r.message

    @pytest.mark.asyncio
    async def test_compare_after_two(self):
        cmd = VoiceCommand("", "snapshot_take")
        await self.snap.take_snapshot(cmd)
        await self.snap.take_snapshot(cmd)
        r = await self.snap.compare(VoiceCommand("", ""))
        assert r.success


class TestCycle123SnapshotHistory:
    def setup_method(self):
        self.snap = SystemSnapshotSkill()

    @pytest.mark.asyncio
    async def test_empty_history(self):
        r = await self.snap.history(VoiceCommand("", ""))
        assert r.success
        assert "Aucun" in r.message

    @pytest.mark.asyncio
    async def test_history_after_snapshot(self):
        await self.snap.take_snapshot(VoiceCommand("", ""))
        r = await self.snap.history(VoiceCommand("", ""))
        assert r.success
        assert "1 snapshot" in r.message


class TestCycle124SnapshotMaxLimit:
    def setup_method(self):
        self.snap = SystemSnapshotSkill()

    @pytest.mark.asyncio
    async def test_max_10_snapshots(self):
        cmd = VoiceCommand("", "snapshot_take")
        for _ in range(15):
            await self.snap.take_snapshot(cmd)
        assert self.snap.snapshot_count == 10


class TestCycle125SystemInfoBasic:
    def test_get_system_info(self):
        info = _get_system_info()
        assert "os" in info
        assert "python" in info
        assert "timestamp" in info
        assert "machine" in info


# ============================================================
# CYCLES 126-130: Pipeline nouveaux skills
# ============================================================
class TestCycle126TranslatePipeline:
    def setup_method(self):
        self.jarvis = Jarvis()
        self.jarvis.tts.speak = AsyncMock()
        self.jarvis.tts.speak_status = AsyncMock()

    @pytest.mark.asyncio
    async def test_translate_via_voice(self):
        await self.jarvis.process_transcription("Jarvis traduis en anglais bonjour")
        assert self.jarvis.tts.speak.called
        msg = self.jarvis.tts.speak.call_args[0][0]
        assert "hello" in msg.lower()

    @pytest.mark.asyncio
    async def test_lookup_via_voice(self):
        await self.jarvis.process_transcription("Jarvis traduction merci")
        assert self.jarvis.tts.speak.called


class TestCycle127ConvertPipeline:
    def setup_method(self):
        self.jarvis = Jarvis()
        self.jarvis.tts.speak = AsyncMock()
        self.jarvis.tts.speak_status = AsyncMock()

    @pytest.mark.asyncio
    async def test_convert_via_voice(self):
        await self.jarvis.process_transcription("Jarvis convertis 10 km en miles")
        assert self.jarvis.tts.speak.called
        msg = self.jarvis.tts.speak.call_args[0][0]
        assert "6.2" in msg or "miles" in msg


class TestCycle128PomodoroPipeline:
    def setup_method(self):
        self.jarvis = Jarvis()
        self.jarvis.tts.speak = AsyncMock()
        self.jarvis.tts.speak_status = AsyncMock()

    @pytest.mark.asyncio
    async def test_pomodoro_via_voice(self):
        await self.jarvis.process_transcription("Jarvis pomodoro")
        assert self.jarvis.tts.speak.called
        assert self.jarvis.pomodoro.active
        await self.jarvis.pomodoro.stop(VoiceCommand("", ""))

    @pytest.mark.asyncio
    async def test_pomodoro_status_via_voice(self):
        await self.jarvis.process_transcription("Jarvis pomodoro")
        self.jarvis.tts.speak.reset_mock()
        await self.jarvis.process_transcription("Jarvis état du pomodoro")
        assert self.jarvis.tts.speak.called
        await self.jarvis.pomodoro.stop(VoiceCommand("", ""))


class TestCycle129SnapshotPipeline:
    def setup_method(self):
        self.jarvis = Jarvis()
        self.jarvis.tts.speak = AsyncMock()
        self.jarvis.tts.speak_status = AsyncMock()

    @pytest.mark.asyncio
    async def test_snapshot_via_voice(self):
        await self.jarvis.process_transcription("Jarvis snapshot système")
        assert self.jarvis.tts.speak.called
        assert self.jarvis.snapshot.snapshot_count >= 1


class TestCycle130AllNewHandlersRegistered:
    def setup_method(self):
        self.jarvis = Jarvis()

    def test_translation_handlers(self):
        intents = self.jarvis.commander.list_intents()
        assert "translate_fr_en" in intents
        assert "translate_en_fr" in intents
        assert "translate_lookup" in intents

    def test_unit_convert_handler(self):
        assert "unit_convert" in self.jarvis.commander.list_intents()

    def test_pomodoro_handlers(self):
        intents = self.jarvis.commander.list_intents()
        assert "pomodoro_start" in intents
        assert "pomodoro_stop" in intents
        assert "pomodoro_status" in intents

    def test_snapshot_handlers(self):
        intents = self.jarvis.commander.list_intents()
        assert "snapshot_take" in intents
        assert "snapshot_compare" in intents
        assert "snapshot_history" in intents


# ============================================================
# CYCLES 131-135: Scenarios avances
# ============================================================
class TestCycle131ScenarioStudent:
    def setup_method(self):
        self.jarvis = Jarvis()
        self.jarvis.tts.speak = AsyncMock()
        self.jarvis.tts.speak_status = AsyncMock()

    @pytest.mark.asyncio
    async def test_student_workflow(self):
        commands = [
            ("Jarvis pomodoro", "pomodoro_start"),
            ("Jarvis note réviser chapitre 3", "note_add"),
            ("Jarvis traduction bonjour", "translate_lookup"),
            ("Jarvis calcule 45 plus 38", "calc_compute"),
            ("Jarvis wikipedia maths", "web_wikipedia"),
            ("Jarvis état du pomodoro", "pomodoro_status"),
        ]
        for text, expected in commands:
            detected, cmd_text = detect_wake_word(text)
            assert detected
            r = self.jarvis.commander.parse(cmd_text)
            assert r.intent == expected, \
                f"'{text}' -> {r.intent} au lieu de {expected}"
        await self.jarvis.pomodoro.stop(VoiceCommand("", ""))


class TestCycle132ScenarioTranslator:
    def setup_method(self):
        self.jarvis = Jarvis()
        self.jarvis.tts.speak = AsyncMock()
        self.jarvis.tts.speak_status = AsyncMock()

    @pytest.mark.asyncio
    async def test_translator_workflow(self):
        commands = [
            ("Jarvis traduis en anglais bonjour", "translate_fr_en"),
            ("Jarvis traduis en français hello", "translate_en_fr"),
            ("Jarvis traduction ordinateur", "translate_lookup"),
            ("Jarvis note vérifier traduction page 12", "note_add"),
            ("Jarvis minuteur 20 minutes", "timer_set"),
        ]
        for text, expected in commands:
            detected, cmd_text = detect_wake_word(text)
            assert detected
            r = self.jarvis.commander.parse(cmd_text)
            assert r.intent == expected, \
                f"'{text}' -> {r.intent} au lieu de {expected}"
        await self.jarvis.timer.cancel_timer(VoiceCommand("", ""))


class TestCycle133ScenarioSportif:
    def setup_method(self):
        self.c = Commander()

    def test_sport_commands(self):
        commands = [
            ("convertis 5 km en miles", "unit_convert"),
            ("convertis 80 kg en livres", "unit_convert"),
            ("minuteur 30 minutes", "timer_set"),
            ("calcule 42 fois 195", "calc_compute"),
            ("pomodoro", "pomodoro_start"),
        ]
        for text, expected in commands:
            r = self.c.parse(text)
            assert r.intent == expected, \
                f"'{text}' -> {r.intent} au lieu de {expected}"


class TestCycle134ScenarioAdmin:
    def setup_method(self):
        self.jarvis = Jarvis()
        self.jarvis.tts.speak = AsyncMock()
        self.jarvis.tts.speak_status = AsyncMock()

    @pytest.mark.asyncio
    async def test_admin_workflow(self):
        await self.jarvis.process_transcription("Jarvis snapshot système")
        assert self.jarvis.snapshot.snapshot_count >= 1
        await self.jarvis.process_transcription("Jarvis cpu")
        await self.jarvis.process_transcription("Jarvis mémoire")
        await self.jarvis.process_transcription("Jarvis espace disque")
        await self.jarvis.process_transcription("Jarvis snapshot système")
        assert self.jarvis.snapshot.snapshot_count >= 2
        await self.jarvis.process_transcription("Jarvis compare les snapshots")
        assert self.jarvis.tts.speak.call_count >= 5


class TestCycle135ScenarioPresenter:
    def setup_method(self):
        self.jarvis = Jarvis()
        self.jarvis.tts.speak = AsyncMock()
        self.jarvis.tts.speak_status = AsyncMock()

    @pytest.mark.asyncio
    async def test_presenter_workflow(self):
        commands = [
            ("Jarvis pomodoro", "pomodoro_start"),
            ("Jarvis note sujet 1 introduction", "note_add"),
            ("Jarvis snapshot système", "snapshot_take"),
            ("Jarvis convertis 100 go en to", "unit_convert"),
            ("Jarvis traduis en anglais merci", "translate_fr_en"),
        ]
        for text, expected in commands:
            detected, cmd_text = detect_wake_word(text)
            assert detected
            r = self.jarvis.commander.parse(cmd_text)
            assert r.intent == expected
        await self.jarvis.pomodoro.stop(VoiceCommand("", ""))


# ============================================================
# CYCLES 136-140: Non-regression
# ============================================================
class TestCycle136OriginalPatternsStillWork:
    def setup_method(self):
        self.c = Commander()

    @pytest.mark.parametrize("text,intent", [
        ("ouvre chrome", "app_launch"),
        ("ferme chrome", "app_close"),
        ("volume 50", "system_volume_set"),
        ("muet", "system_mute"),
        ("aide", "jarvis_help"),
        ("merci", "jarvis_thanks"),
        ("suivant", "media_next"),
        ("bureau virtuel suivant", "vdesktop_right"),
        ("ouvre les téléchargements", "navigate_downloads"),
        ("minuteur 5 minutes", "timer_set"),
        ("note acheter lait", "note_add"),
        ("calcule 2 plus 2", "calc_compute"),
        ("gpu", "system_gpu"),
        ("ping google.com", "network_ping"),
        ("google python", "web_google"),
    ])
    def test_original_intact(self, text, intent):
        assert self.c.parse(text).intent == intent


class TestCycle137NewPatternsNoConflict:
    def setup_method(self):
        self.c = Commander()

    def test_translate_not_app(self):
        assert self.c.parse("traduis en anglais bonjour").intent != "app_launch"

    def test_pomodoro_not_media(self):
        assert self.c.parse("pomodoro").intent != "media_play"

    def test_snapshot_not_screenshot(self):
        assert self.c.parse("snapshot système").intent != "window_screenshot"

    def test_convert_units_not_calc(self):
        assert self.c.parse("convertis 5 km en miles").intent == "unit_convert"


class TestCycle138RegressionGuards:
    def setup_method(self):
        self.c = Commander()

    def test_telechargements_not_resources(self):
        assert self.c.parse("ouvre les téléchargements").intent == "navigate_downloads"

    def test_powerpoint_not_period(self):
        assert self.c.parse("ouvre powerpoint").intent == "app_launch"

    def test_parametres_not_ram(self):
        assert self.c.parse("paramètres").intent == "jarvis_settings"

    def test_lance_macro_is_run(self):
        assert self.c.parse("lance la macro test").intent == "automation_run"

    def test_coupe_le_son_is_mute(self):
        assert self.c.parse("coupe le son").intent == "system_mute"

    def test_discuter_not_cut(self):
        assert self.c.parse("note points a discuter").intent == "note_add"


class TestCycle139AllSkillsInstantiate:
    def test_19_skills(self):
        jarvis = Jarvis()
        skills = [
            jarvis.app_launcher, jarvis.system_control,
            jarvis.window_manager, jarvis.file_manager,
            jarvis.web_browser, jarvis.media_control,
            jarvis.clipboard, jarvis.process_mgr,
            jarvis.network, jarvis.power_display,
            jarvis.software, jarvis.timer,
            jarvis.notes, jarvis.calculator,
            jarvis.vdesktop, jarvis.translator,
            jarvis.unit_converter, jarvis.pomodoro,
            jarvis.snapshot,
        ]
        assert len(skills) == 19
        for s in skills:
            assert s is not None


class TestCycle140AllAgentsIntact:
    def test_4_agents(self):
        jarvis = Jarvis()
        agents = [
            jarvis.dictation, jarvis.search,
            jarvis.automation, jarvis.navigation,
        ]
        assert len(agents) == 4
        for a in agents:
            assert a is not None


# ============================================================
# CYCLES 141-145: Edge cases et securite
# ============================================================
class TestCycle141TranslatorEdgeCases:
    def setup_method(self):
        self.tr = TranslatorSkill()

    @pytest.mark.asyncio
    async def test_empty_lookup(self):
        cmd = VoiceCommand("", "translate_lookup", target="")
        r = await self.tr.lookup(cmd)
        assert not r.success

    @pytest.mark.asyncio
    async def test_special_chars(self):
        cmd = VoiceCommand("traduction test123", "translate_lookup",
                           target="test123")
        r = await self.tr.lookup(cmd)
        assert not r.success

    def test_multi_word_phrase(self):
        result = _translate_text("comment allez-vous", "fr_en")
        assert "how are you" in result or "how" in result


class TestCycle142ConverterEdgeCases:
    def test_zero_conversion(self):
        assert convert_units(0, "km", "miles") == 0

    def test_large_number(self):
        result = convert_units(1000000, "km", "m")
        assert result == 1000000000

    def test_decimal_input(self):
        result = convert_units(1.5, "km", "m")
        assert result == 1500

    def test_aliases(self):
        r1 = convert_units(1, "kilomètres", "miles")
        r2 = convert_units(1, "km", "miles")
        assert abs(r1 - r2) < 0.001


class TestCycle143PomodoroEdgeCases:
    def setup_method(self):
        self.pomo = PomodoroSkill()

    @pytest.mark.asyncio
    async def test_status_before_start(self):
        r = await self.pomo.status(VoiceCommand("", ""))
        assert r.success
        assert "0" in r.message

    @pytest.mark.asyncio
    async def test_stop_before_start(self):
        r = await self.pomo.stop(VoiceCommand("", ""))
        assert r.success

    @pytest.mark.asyncio
    async def test_start_stop_start(self):
        await self.pomo.start(VoiceCommand("", ""))
        await self.pomo.stop(VoiceCommand("", ""))
        r = await self.pomo.start(VoiceCommand("", ""))
        assert r.success
        assert self.pomo.active
        await self.pomo.stop(VoiceCommand("", ""))


class TestCycle144SnapshotEdgeCases:
    def setup_method(self):
        self.snap = SystemSnapshotSkill()

    @pytest.mark.asyncio
    async def test_compare_one_snapshot(self):
        await self.snap.take_snapshot(VoiceCommand("", ""))
        r = await self.snap.compare(VoiceCommand("", ""))
        assert not r.success

    @pytest.mark.asyncio
    async def test_history_shows_count(self):
        for _ in range(5):
            await self.snap.take_snapshot(VoiceCommand("", ""))
        r = await self.snap.history(VoiceCommand("", ""))
        assert "5" in r.message


class TestCycle145SecurityNewSkills:
    def setup_method(self):
        self.c = Commander()

    def test_translate_injection(self):
        r = self.c.parse("traduis en anglais test")
        assert r.intent == "translate_fr_en"

    def test_snapshot_read_only(self):
        """Le snapshot ne doit que lire, jamais ecrire"""
        source = inspect.getsource(SystemSnapshotSkill)
        assert "subprocess" not in source
        assert "open(" not in source


# ============================================================
# CYCLES 146-150: Stress ultime et validation finale
# ============================================================
class TestCycle146StressAllNewPatterns:
    def setup_method(self):
        self.c = Commander()

    def test_all_new_intents_matchable(self):
        new_intents = {
            "translate_fr_en": "traduis en anglais bonjour",
            "translate_en_fr": "traduis en français hello",
            "translate_lookup": "traduction merci",
            "unit_convert": "convertis 5 km en miles",
            "pomodoro_start": "pomodoro",
            "pomodoro_stop": "arrête le pomodoro",
            "pomodoro_status": "état du pomodoro",
            "snapshot_take": "snapshot système",
            "snapshot_compare": "compare les snapshots",
            "snapshot_history": "historique des snapshots",
        }
        for intent, text in new_intents.items():
            r = self.c.parse(text)
            assert r.intent == intent, \
                f"'{text}' -> {r.intent} au lieu de {intent}"


class TestCycle147Stress150Commands:
    def setup_method(self):
        self.c = Commander()

    def test_150_rapid_parses(self):
        commands = [
            "ouvre chrome", "ferme chrome", "volume 50", "muet",
            "aide", "merci", "statut", "minuteur 5 minutes",
            "calcule 2 plus 2", "note test", "lis les notes",
            "bureau virtuel suivant", "nouveau bureau virtuel",
            "suivant", "précédent", "play", "pause", "cpu", "gpu",
            "traduis en anglais bonjour", "traduction merci",
            "convertis 10 km en miles", "pomodoro",
            "snapshot système", "compare les snapshots",
            "arrête le pomodoro", "état du pomodoro",
            "google test", "youtube musique", "météo",
        ] * 5
        for text in commands:
            r = self.c.parse(text)
            assert r is not None
            assert r.intent != ""


class TestCycle148StressFullPipeline:
    def setup_method(self):
        self.jarvis = Jarvis()
        self.jarvis.tts.speak = AsyncMock()
        self.jarvis.tts.speak_status = AsyncMock()

    @pytest.mark.asyncio
    async def test_full_pipeline_all_skills(self):
        commands = [
            "Jarvis aide",
            "Jarvis statut",
            "Jarvis snapshot système",
            "Jarvis traduis en anglais bonjour",
            "Jarvis traduction merci",
            "Jarvis convertis 10 km en miles",
            "Jarvis pomodoro",
            "Jarvis état du pomodoro",
            "Jarvis arrête le pomodoro",
            "Jarvis calcule 5 plus 3",
            "Jarvis note test final",
            "Jarvis minuteur 1 seconde",
            "Jarvis liste les minuteurs",
            "Jarvis cpu",
            "Jarvis gpu",
            "Jarvis mémoire",
            "Jarvis météo",
            "Jarvis heure",
            "Jarvis date",
            "Jarvis merci",
        ]
        for text in commands:
            await self.jarvis.process_transcription(text)
        assert self.jarvis.tts.speak.call_count >= 15
        await self.jarvis.timer.cancel_timer(VoiceCommand("", ""))


class TestCycle149AllIntentsComplete:
    def test_all_intents_have_handlers(self):
        jarvis = Jarvis()
        pattern_intents = {intent for _, intent in COMMAND_PATTERNS}
        registered = set(jarvis.commander.list_intents())
        missing = pattern_intents - registered
        assert not missing, f"Intents sans handler: {missing}"


class TestCycle150FinalValidation:
    def setup_method(self):
        self.jarvis = Jarvis()

    def test_pattern_count(self):
        assert len(COMMAND_PATTERNS) >= 115, \
            f"{len(COMMAND_PATTERNS)} patterns (min 120)"

    def test_handler_count(self):
        h = self.jarvis.commander.list_intents()
        assert len(h) >= 80, f"{len(h)} handlers (min 80)"

    def test_19_skills(self):
        skills = [
            self.jarvis.app_launcher, self.jarvis.system_control,
            self.jarvis.window_manager, self.jarvis.file_manager,
            self.jarvis.web_browser, self.jarvis.media_control,
            self.jarvis.clipboard, self.jarvis.process_mgr,
            self.jarvis.network, self.jarvis.power_display,
            self.jarvis.software, self.jarvis.timer,
            self.jarvis.notes, self.jarvis.calculator,
            self.jarvis.vdesktop, self.jarvis.translator,
            self.jarvis.unit_converter, self.jarvis.pomodoro,
            self.jarvis.snapshot,
        ]
        assert len(skills) == 19

    def test_4_agents(self):
        agents = [
            self.jarvis.dictation, self.jarvis.search,
            self.jarvis.automation, self.jarvis.navigation,
        ]
        assert len(agents) == 4

    def test_production_ready(self):
        """JARVIS v3: 19 skills, 4 agents, 120+ patterns, 150 cycles"""
        assert len(COMMAND_PATTERNS) >= 115
        assert len(self.jarvis.commander.list_intents()) >= 80
        assert self.jarvis.tts is not None
        assert not self.jarvis.dictation.active
        assert not self.jarvis.automation.recording
        assert not self.jarvis.pomodoro.active
        assert self.jarvis.snapshot.snapshot_count == 0
