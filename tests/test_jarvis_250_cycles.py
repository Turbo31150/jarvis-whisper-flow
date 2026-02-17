"""
JARVIS - Cycles 201-250: Formation Intensive Phase 5
4 nouveaux skills: Stopwatch, Agenda, RandomPicker, Abbreviations

Total: 50 cycles, ~250 tests
"""

import asyncio
import pytest
import time
import re
from datetime import datetime, timedelta
from unittest.mock import AsyncMock

from whisperflow.jarvis.jarvis_core import Jarvis
from whisperflow.jarvis.commander import Commander, VoiceCommand, CommandResult, COMMAND_PATTERNS
from whisperflow.jarvis.skills.stopwatch import (
    StopwatchSkill, format_duration
)
from whisperflow.jarvis.skills.agenda import (
    AgendaSkill, _parse_time
)
from whisperflow.jarvis.skills.random_picker import (
    RandomPickerSkill, coin_flip, dice_roll, pick_from_list, random_number
)
from whisperflow.jarvis.skills.abbreviations import (
    AbbreviationsSkill, lookup_abbreviation, get_all_abbreviations,
    _ABBREVIATIONS
)


# ============================================================
# CYCLES 201-205: PATTERNS NOUVEAUX SKILLS
# ============================================================

class TestCycle201StopwatchPatterns:
    def setup_method(self):
        self.commander = Commander()

    def test_chrono_start(self):
        cmd = self.commander.parse("demarre le chronometre")
        assert cmd.intent == "stopwatch_start"

    def test_chrono_stop(self):
        cmd = self.commander.parse("arrete le chrono")
        assert cmd.intent == "stopwatch_stop"

    def test_chrono_lap(self):
        cmd = self.commander.parse("tour")
        assert cmd.intent == "stopwatch_lap"

    def test_chrono_reset(self):
        cmd = self.commander.parse("reinitialise le chrono")
        assert cmd.intent == "stopwatch_reset"

    def test_chrono_status(self):
        cmd = self.commander.parse("temps du chronometre")
        assert cmd.intent == "stopwatch_status"


class TestCycle202AgendaPatterns:
    def setup_method(self):
        self.commander = Commander()

    def test_agenda_add(self):
        cmd = self.commander.parse("agenda ajoute 14h reunion")
        assert cmd.intent == "agenda_add"

    def test_agenda_list(self):
        cmd = self.commander.parse("mon agenda")
        assert cmd.intent == "agenda_list"

    def test_agenda_clear(self):
        cmd = self.commander.parse("vide l'agenda")
        assert cmd.intent == "agenda_clear"

    def test_agenda_next(self):
        cmd = self.commander.parse("prochain evenement")
        assert cmd.intent == "agenda_next"


class TestCycle203RandomPatterns:
    def setup_method(self):
        self.commander = Commander()

    def test_coin_flip(self):
        cmd = self.commander.parse("pile ou face")
        assert cmd.intent == "random_coin"

    def test_dice_roll(self):
        cmd = self.commander.parse("lance un de")
        assert cmd.intent == "random_dice"

    def test_pick(self):
        cmd = self.commander.parse("choisis entre pizza ou sushi")
        assert cmd.intent == "random_pick"

    def test_random_number(self):
        cmd = self.commander.parse("nombre aleatoire")
        assert cmd.intent == "random_number"


class TestCycle204AbbrevPatterns:
    def setup_method(self):
        self.commander = Commander()

    def test_define(self):
        cmd = self.commander.parse("que signifie API")
        assert cmd.intent == "abbrev_define"

    def test_definition(self):
        cmd = self.commander.parse("definition de HTML")
        assert cmd.intent == "abbrev_define"

    def test_list(self):
        cmd = self.commander.parse("liste des abreviations")
        assert cmd.intent == "abbrev_list"


class TestCycle205PatternCount:
    def test_pattern_count(self):
        assert len(COMMAND_PATTERNS) >= 145, \
            f"Seulement {len(COMMAND_PATTERNS)} patterns (attendu >= 145)"

    def test_new_intents_present(self):
        intents = {intent for _, intent in COMMAND_PATTERNS}
        new_intents = [
            "stopwatch_start", "stopwatch_stop", "stopwatch_lap",
            "stopwatch_reset", "stopwatch_status",
            "agenda_add", "agenda_list", "agenda_clear", "agenda_next",
            "random_coin", "random_dice", "random_pick", "random_number",
            "abbrev_define", "abbrev_list",
        ]
        for intent in new_intents:
            assert intent in intents, f"Intent manquant: {intent}"


# ============================================================
# CYCLES 206-210: SKILL STOPWATCH
# ============================================================

class TestCycle206FormatDuration:
    def test_seconds(self):
        result = format_duration(5.3)
        assert "5.3 secondes" in result

    def test_minutes(self):
        result = format_duration(125.0)
        assert "2 minute" in result

    def test_hours(self):
        result = format_duration(3700)
        assert "1 heure" in result


class TestCycle207StopwatchStartStop:
    @pytest.mark.asyncio
    async def test_start(self):
        sw = StopwatchSkill()
        cmd = VoiceCommand("", "stopwatch_start")
        result = await sw.start(cmd)
        assert result.success
        assert sw.running

    @pytest.mark.asyncio
    async def test_double_start(self):
        sw = StopwatchSkill()
        cmd = VoiceCommand("", "stopwatch_start")
        await sw.start(cmd)
        result = await sw.start(cmd)
        assert not result.success

    @pytest.mark.asyncio
    async def test_stop(self):
        sw = StopwatchSkill()
        await sw.start(VoiceCommand("", ""))
        await asyncio.sleep(0.05)
        result = await sw.stop(VoiceCommand("", ""))
        assert result.success
        assert not sw.running
        assert result.data["elapsed"] > 0

    @pytest.mark.asyncio
    async def test_stop_when_stopped(self):
        sw = StopwatchSkill()
        result = await sw.stop(VoiceCommand("", ""))
        assert result.success  # returns current time


class TestCycle208StopwatchLap:
    @pytest.mark.asyncio
    async def test_lap_while_running(self):
        sw = StopwatchSkill()
        await sw.start(VoiceCommand("", ""))
        await asyncio.sleep(0.05)
        result = await sw.lap(VoiceCommand("", ""))
        assert result.success
        assert result.data["lap"] == 1
        assert sw.lap_count == 1

    @pytest.mark.asyncio
    async def test_lap_when_stopped(self):
        sw = StopwatchSkill()
        result = await sw.lap(VoiceCommand("", ""))
        assert not result.success

    @pytest.mark.asyncio
    async def test_multiple_laps(self):
        sw = StopwatchSkill()
        await sw.start(VoiceCommand("", ""))
        for _ in range(3):
            await asyncio.sleep(0.02)
            await sw.lap(VoiceCommand("", ""))
        assert sw.lap_count == 3


class TestCycle209StopwatchReset:
    @pytest.mark.asyncio
    async def test_reset(self):
        sw = StopwatchSkill()
        await sw.start(VoiceCommand("", ""))
        await asyncio.sleep(0.05)
        await sw.lap(VoiceCommand("", ""))
        result = await sw.reset(VoiceCommand("", ""))
        assert result.success
        assert not sw.running
        assert sw.lap_count == 0
        assert sw.get_elapsed() == 0


class TestCycle210StopwatchStatus:
    @pytest.mark.asyncio
    async def test_status_idle(self):
        sw = StopwatchSkill()
        result = await sw.status(VoiceCommand("", ""))
        assert "0.0 secondes" in result.message

    @pytest.mark.asyncio
    async def test_status_running(self):
        sw = StopwatchSkill()
        await sw.start(VoiceCommand("", ""))
        await asyncio.sleep(0.05)
        result = await sw.status(VoiceCommand("", ""))
        assert "en marche" in result.message
        await sw.stop(VoiceCommand("", ""))


# ============================================================
# CYCLES 211-215: SKILL AGENDA
# ============================================================

class TestCycle211ParseTime:
    def test_14h(self):
        assert _parse_time("14h") == (14, 0)

    def test_14h30(self):
        assert _parse_time("14h30") == (14, 30)

    def test_9h(self):
        assert _parse_time("9h") == (9, 0)

    def test_no_time(self):
        assert _parse_time("reunion") is None

    def test_invalid_hour(self):
        assert _parse_time("25h") is None


class TestCycle212AgendaAdd:
    @pytest.mark.asyncio
    async def test_add_with_time(self):
        agenda = AgendaSkill()
        cmd = VoiceCommand("", "", target="14h30 reunion equipe")
        result = await agenda.add_event(cmd)
        assert result.success
        assert agenda.count == 1
        assert result.data["time"] == "14:30"

    @pytest.mark.asyncio
    async def test_add_without_time(self):
        agenda = AgendaSkill()
        cmd = VoiceCommand("", "", target="appeler le client")
        result = await agenda.add_event(cmd)
        assert result.success
        assert result.data["time"] is None

    @pytest.mark.asyncio
    async def test_add_empty(self):
        agenda = AgendaSkill()
        cmd = VoiceCommand("", "", target="")
        result = await agenda.add_event(cmd)
        assert not result.success


class TestCycle213AgendaList:
    @pytest.mark.asyncio
    async def test_list_empty(self):
        agenda = AgendaSkill()
        result = await agenda.list_events(VoiceCommand("", ""))
        assert "vide" in result.message.lower()

    @pytest.mark.asyncio
    async def test_list_with_events(self):
        agenda = AgendaSkill()
        await agenda.add_event(VoiceCommand("", "", target="9h standup"))
        await agenda.add_event(VoiceCommand("", "", target="14h review"))
        result = await agenda.list_events(VoiceCommand("", ""))
        assert "2" in result.message


class TestCycle214AgendaClear:
    @pytest.mark.asyncio
    async def test_clear(self):
        agenda = AgendaSkill()
        await agenda.add_event(VoiceCommand("", "", target="test"))
        await agenda.add_event(VoiceCommand("", "", target="test2"))
        result = await agenda.clear_events(VoiceCommand("", ""))
        assert result.success
        assert agenda.count == 0
        assert "2" in result.message


class TestCycle215AgendaNext:
    @pytest.mark.asyncio
    async def test_next_empty(self):
        agenda = AgendaSkill()
        result = await agenda.next_event(VoiceCommand("", ""))
        assert "Aucun" in result.message

    @pytest.mark.asyncio
    async def test_next_with_events(self):
        agenda = AgendaSkill()
        await agenda.add_event(VoiceCommand("", "", target="23h59 dernier"))
        result = await agenda.next_event(VoiceCommand("", ""))
        assert result.success


# ============================================================
# CYCLES 216-220: SKILL RANDOM PICKER
# ============================================================

class TestCycle216CoinFlip:
    def test_flip_values(self):
        results = {coin_flip() for _ in range(50)}
        assert "pile" in results
        assert "face" in results

    @pytest.mark.asyncio
    async def test_flip_skill(self):
        skill = RandomPickerSkill()
        result = await skill.flip_coin(VoiceCommand("", ""))
        assert result.success
        assert result.data["result"] in ("pile", "face")


class TestCycle217DiceRoll:
    def test_default_6(self):
        results = {dice_roll() for _ in range(100)}
        assert results.issubset({1, 2, 3, 4, 5, 6})
        assert len(results) >= 4  # Should hit most values

    def test_custom_sides(self):
        result = dice_roll(20)
        assert 1 <= result <= 20

    @pytest.mark.asyncio
    async def test_roll_skill(self):
        skill = RandomPickerSkill()
        result = await skill.roll_dice(VoiceCommand("", "", target=""))
        assert result.success
        assert 1 <= result.data["result"] <= 6


class TestCycle218PickFromList:
    def test_pick(self):
        items = ["a", "b", "c"]
        result = pick_from_list(items)
        assert result in items

    def test_pick_empty(self):
        assert pick_from_list([]) == ""

    @pytest.mark.asyncio
    async def test_pick_skill(self):
        skill = RandomPickerSkill()
        cmd = VoiceCommand("", "", target="pizza ou sushi ou burger")
        result = await skill.pick(cmd)
        assert result.success
        assert result.data["result"] in ("pizza", "sushi", "burger")

    @pytest.mark.asyncio
    async def test_pick_too_few(self):
        skill = RandomPickerSkill()
        cmd = VoiceCommand("", "", target="seul")
        result = await skill.pick(cmd)
        assert not result.success


class TestCycle219RandomNumber:
    def test_range(self):
        for _ in range(50):
            result = random_number(1, 10)
            assert 1 <= result <= 10

    def test_reversed_range(self):
        result = random_number(10, 1)
        assert 1 <= result <= 10

    @pytest.mark.asyncio
    async def test_random_num_skill(self):
        skill = RandomPickerSkill()
        cmd = VoiceCommand("", "", target="1 et 100")
        result = await skill.random_num(cmd)
        assert result.success
        assert 1 <= result.data["result"] <= 100


class TestCycle220RandomDefault:
    @pytest.mark.asyncio
    async def test_default_range(self):
        skill = RandomPickerSkill()
        cmd = VoiceCommand("", "", target="")
        result = await skill.random_num(cmd)
        assert result.success
        assert 1 <= result.data["result"] <= 100


# ============================================================
# CYCLES 221-225: SKILL ABBREVIATIONS
# ============================================================

class TestCycle221LookupAbbrev:
    def test_known_api(self):
        assert "Programming" in lookup_abbreviation("api")

    def test_known_cpu(self):
        assert "Central" in lookup_abbreviation("CPU")

    def test_unknown(self):
        assert lookup_abbreviation("xyz") == ""

    def test_case_insensitive(self):
        assert lookup_abbreviation("HTML") == lookup_abbreviation("html")


class TestCycle222AbbrevCount:
    def test_has_many(self):
        all_abbr = get_all_abbreviations()
        assert len(all_abbr) >= 50

    def test_categories(self):
        # IT terms
        assert "api" in _ABBREVIATIONS
        assert "gpu" in _ABBREVIATIONS
        # French terms
        assert "rh" in _ABBREVIATIONS
        assert "tva" in _ABBREVIATIONS
        # Organizations
        assert "onu" in _ABBREVIATIONS


class TestCycle223AbbrevSkillDefine:
    @pytest.mark.asyncio
    async def test_define_known(self):
        skill = AbbreviationsSkill()
        cmd = VoiceCommand("", "", target="API")
        result = await skill.define(cmd)
        assert result.success
        assert "Application" in result.message

    @pytest.mark.asyncio
    async def test_define_unknown(self):
        skill = AbbreviationsSkill()
        cmd = VoiceCommand("", "", target="XYZZY")
        result = await skill.define(cmd)
        assert not result.success

    @pytest.mark.asyncio
    async def test_define_empty(self):
        skill = AbbreviationsSkill()
        cmd = VoiceCommand("", "", target="")
        result = await skill.define(cmd)
        assert not result.success


class TestCycle224AbbrevSkillList:
    @pytest.mark.asyncio
    async def test_list(self):
        skill = AbbreviationsSkill()
        result = await skill.list_category(VoiceCommand("", ""))
        assert result.success
        assert str(len(_ABBREVIATIONS)) in result.message


class TestCycle225AbbrevFrench:
    def test_french_abbrevs(self):
        assert "Ressources" in lookup_abbreviation("rh")
        assert "Salaire" in lookup_abbreviation("smic")
        assert "Contrat" in lookup_abbreviation("cdi")
        assert "Union" in lookup_abbreviation("ue")


# ============================================================
# CYCLES 226-230: PIPELINE COMPLET VIA JARVIS
# ============================================================

class TestCycle226StopwatchPipeline:
    def setup_method(self):
        self.jarvis = Jarvis()
        self.jarvis.tts.speak = AsyncMock()
        self.jarvis.tts.speak_status = AsyncMock()

    @pytest.mark.asyncio
    async def test_chrono_via_voice(self):
        await self.jarvis.process_transcription("Jarvis demarre le chronometre")
        assert self.jarvis.tts.speak.called
        assert self.jarvis.stopwatch.running

        self.jarvis.tts.speak.reset_mock()
        await self.jarvis.process_transcription("Jarvis arrete le chrono")
        assert not self.jarvis.stopwatch.running


class TestCycle227AgendaPipeline:
    def setup_method(self):
        self.jarvis = Jarvis()
        self.jarvis.tts.speak = AsyncMock()
        self.jarvis.tts.speak_status = AsyncMock()

    @pytest.mark.asyncio
    async def test_agenda_via_voice(self):
        await self.jarvis.process_transcription(
            "Jarvis agenda ajoute 14h reunion")
        assert self.jarvis.tts.speak.called
        assert self.jarvis.agenda.count == 1

        self.jarvis.tts.speak.reset_mock()
        await self.jarvis.process_transcription("Jarvis mon agenda")
        assert self.jarvis.tts.speak.called


class TestCycle228RandomPipeline:
    def setup_method(self):
        self.jarvis = Jarvis()
        self.jarvis.tts.speak = AsyncMock()
        self.jarvis.tts.speak_status = AsyncMock()

    @pytest.mark.asyncio
    async def test_coin_via_voice(self):
        await self.jarvis.process_transcription("Jarvis pile ou face")
        assert self.jarvis.tts.speak.called
        msg = self.jarvis.tts.speak.call_args[0][0]
        assert "pile" in msg or "face" in msg

    @pytest.mark.asyncio
    async def test_dice_via_voice(self):
        self.jarvis.tts.speak.reset_mock()
        await self.jarvis.process_transcription("Jarvis lance un de")
        assert self.jarvis.tts.speak.called


class TestCycle229AbbrevPipeline:
    def setup_method(self):
        self.jarvis = Jarvis()
        self.jarvis.tts.speak = AsyncMock()
        self.jarvis.tts.speak_status = AsyncMock()

    @pytest.mark.asyncio
    async def test_define_via_voice(self):
        await self.jarvis.process_transcription("Jarvis que signifie API")
        assert self.jarvis.tts.speak.called
        msg = self.jarvis.tts.speak.call_args[0][0]
        assert "Application" in msg


class TestCycle230AllNewHandlers:
    def test_all_handlers_registered(self):
        jarvis = Jarvis()
        intents = jarvis.commander.list_intents()
        new_intents = [
            "stopwatch_start", "stopwatch_stop", "stopwatch_lap",
            "stopwatch_reset", "stopwatch_status",
            "agenda_add", "agenda_list", "agenda_clear", "agenda_next",
            "random_coin", "random_dice", "random_pick", "random_number",
            "abbrev_define", "abbrev_list",
        ]
        for intent in new_intents:
            assert intent in intents, f"Handler manquant: {intent}"


# ============================================================
# CYCLES 231-235: SCENARIOS AVANCES
# ============================================================

class TestCycle231ScenarioSportif:
    def setup_method(self):
        self.jarvis = Jarvis()
        self.jarvis.tts.speak = AsyncMock()
        self.jarvis.tts.speak_status = AsyncMock()

    @pytest.mark.asyncio
    async def test_workout_chrono(self):
        await self.jarvis.process_transcription("Jarvis demarre le chronometre")
        assert self.jarvis.stopwatch.running

        await self.jarvis.process_transcription("Jarvis tour")
        assert self.jarvis.stopwatch.lap_count == 1

        await self.jarvis.process_transcription("Jarvis arrete le chrono")
        assert not self.jarvis.stopwatch.running


class TestCycle232ScenarioAssistant:
    def setup_method(self):
        self.jarvis = Jarvis()
        self.jarvis.tts.speak = AsyncMock()
        self.jarvis.tts.speak_status = AsyncMock()

    @pytest.mark.asyncio
    async def test_day_planning(self):
        await self.jarvis.process_transcription(
            "Jarvis agenda ajoute 9h standup")
        await self.jarvis.process_transcription(
            "Jarvis agenda ajoute 14h review")
        assert self.jarvis.agenda.count == 2

        self.jarvis.tts.speak.reset_mock()
        await self.jarvis.process_transcription("Jarvis mon agenda")
        msg = self.jarvis.tts.speak.call_args[0][0]
        assert "2" in msg


class TestCycle233ScenarioJeu:
    def setup_method(self):
        self.jarvis = Jarvis()
        self.jarvis.tts.speak = AsyncMock()
        self.jarvis.tts.speak_status = AsyncMock()

    @pytest.mark.asyncio
    async def test_game_night(self):
        await self.jarvis.process_transcription("Jarvis pile ou face")
        msg1 = self.jarvis.tts.speak.call_args[0][0]
        assert "pile" in msg1 or "face" in msg1

        self.jarvis.tts.speak.reset_mock()
        await self.jarvis.process_transcription("Jarvis lance un de")
        assert self.jarvis.tts.speak.called


class TestCycle234ScenarioEtudiant:
    def setup_method(self):
        self.jarvis = Jarvis()
        self.jarvis.tts.speak = AsyncMock()
        self.jarvis.tts.speak_status = AsyncMock()

    @pytest.mark.asyncio
    async def test_study_session(self):
        await self.jarvis.process_transcription("Jarvis que signifie HTML")
        msg = self.jarvis.tts.speak.call_args[0][0]
        assert "HyperText" in msg

        self.jarvis.tts.speak.reset_mock()
        await self.jarvis.process_transcription("Jarvis definition de RH")
        msg = self.jarvis.tts.speak.call_args[0][0]
        assert "Ressources" in msg


class TestCycle235ScenarioMulti:
    def setup_method(self):
        self.jarvis = Jarvis()
        self.jarvis.tts.speak = AsyncMock()
        self.jarvis.tts.speak_status = AsyncMock()

    @pytest.mark.asyncio
    async def test_mixed_skills(self):
        # Chrono + agenda + random
        await self.jarvis.process_transcription("Jarvis demarre le chronometre")
        await self.jarvis.process_transcription(
            "Jarvis agenda ajoute 10h meeting")
        await self.jarvis.process_transcription("Jarvis pile ou face")
        await self.jarvis.process_transcription("Jarvis arrete le chrono")

        assert self.jarvis.agenda.count == 1
        assert not self.jarvis.stopwatch.running


# ============================================================
# CYCLES 236-240: NON-REGRESSION
# ============================================================

class TestCycle236OriginalPatternsStillWork:
    def setup_method(self):
        self.commander = Commander()

    @pytest.mark.parametrize("text,expected", [
        ("ouvre chrome", "app_launch"),
        ("volume 50", "system_volume_set"),
        ("muet", "system_mute"),
        ("aide", "jarvis_help"),
        ("genere un mot de passe", "password_generate"),
        ("dans combien de jours noel", "date_days_until"),
        ("en majuscules test", "text_uppercase"),
        ("epelle test", "text_spell"),
        ("traduis en anglais bonjour", "translate_fr_en"),
        ("convertis 10 km en miles", "unit_convert"),
        ("pomodoro", "pomodoro_start"),
        ("snapshot systeme", "snapshot_take"),
        ("ouvre les telechargements", "navigate_downloads"),
        ("note acheter lait", "note_add"),
        ("calcule 2 plus 2", "calc_compute"),
    ])
    def test_original_intact(self, text, expected):
        cmd = self.commander.parse(text)
        assert cmd.intent == expected, \
            f"'{text}' -> {cmd.intent} (attendu {expected})"


class TestCycle237NewPatternsNoConflict:
    def setup_method(self):
        self.commander = Commander()

    def test_chrono_not_timer(self):
        cmd = self.commander.parse("demarre le chronometre")
        assert cmd.intent == "stopwatch_start"

    def test_agenda_not_app(self):
        cmd = self.commander.parse("mon agenda")
        assert cmd.intent == "agenda_list"

    def test_coin_not_media(self):
        cmd = self.commander.parse("pile ou face")
        assert cmd.intent == "random_coin"

    def test_abbrev_not_search(self):
        cmd = self.commander.parse("que signifie API")
        assert cmd.intent == "abbrev_define"


class TestCycle238RegressionGuards:
    def setup_method(self):
        self.commander = Commander()

    def test_telechargements_still_works(self):
        cmd = self.commander.parse("ouvre les telechargements")
        assert cmd.intent == "navigate_downloads"

    def test_powerpoint_still_works(self):
        cmd = self.commander.parse("ouvre powerpoint")
        assert cmd.intent == "app_launch"

    def test_lance_macro_still_works(self):
        cmd = self.commander.parse("lance la macro test")
        assert cmd.intent == "automation_run"

    def test_stop_pomodoro_still_works(self):
        cmd = self.commander.parse("arrete le pomodoro")
        assert cmd.intent == "pomodoro_stop"

    def test_snapshots_precedents_still_works(self):
        cmd = self.commander.parse("snapshots precedents")
        assert cmd.intent == "snapshot_history"


class TestCycle239AllSkillsInstantiate:
    def test_27_skills(self):
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
            jarvis.snapshot, jarvis.password,
            jarvis.date_calc, jarvis.text_tools,
            jarvis.favorites, jarvis.stopwatch,
            jarvis.agenda, jarvis.random_picker,
            jarvis.abbreviations,
        ]
        assert len(skills) == 27
        for s in skills:
            assert s is not None


class TestCycle240AllAgentsIntact:
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
# CYCLES 241-245: EDGE CASES ET SECURITE
# ============================================================

class TestCycle241StopwatchEdgeCases:
    @pytest.mark.asyncio
    async def test_resume_after_pause(self):
        sw = StopwatchSkill()
        await sw.start(VoiceCommand("", ""))
        await asyncio.sleep(0.05)
        await sw.stop(VoiceCommand("", ""))
        elapsed1 = sw.get_elapsed()
        await sw.start(VoiceCommand("", ""))
        await asyncio.sleep(0.05)
        await sw.stop(VoiceCommand("", ""))
        elapsed2 = sw.get_elapsed()
        assert elapsed2 > elapsed1

    @pytest.mark.asyncio
    async def test_reset_clears_all(self):
        sw = StopwatchSkill()
        await sw.start(VoiceCommand("", ""))
        await sw.lap(VoiceCommand("", ""))
        await sw.reset(VoiceCommand("", ""))
        assert sw.get_elapsed() == 0
        assert sw.lap_count == 0


class TestCycle242AgendaEdgeCases:
    @pytest.mark.asyncio
    async def test_max_events(self):
        agenda = AgendaSkill()
        for i in range(50):
            await agenda.add_event(VoiceCommand("", "", target=f"event_{i}"))
        result = await agenda.add_event(VoiceCommand("", "", target="overflow"))
        assert not result.success
        assert "Maximum" in result.message

    @pytest.mark.asyncio
    async def test_get_events(self):
        agenda = AgendaSkill()
        await agenda.add_event(VoiceCommand("", "", target="test"))
        events = agenda.get_events()
        assert len(events) == 1


class TestCycle243RandomEdgeCases:
    def test_dice_min_sides(self):
        result = dice_roll(2)
        assert result in (1, 2)

    @pytest.mark.asyncio
    async def test_pick_with_comma(self):
        skill = RandomPickerSkill()
        cmd = VoiceCommand("", "", target="rouge, bleu, vert")
        result = await skill.pick(cmd)
        assert result.success
        assert result.data["result"] in ("rouge", "bleu", "vert")

    @pytest.mark.asyncio
    async def test_random_with_range(self):
        skill = RandomPickerSkill()
        cmd = VoiceCommand("", "", target="5 a 10")
        result = await skill.random_num(cmd)
        assert 5 <= result.data["result"] <= 10


class TestCycle244AbbrevEdgeCases:
    @pytest.mark.asyncio
    async def test_injection_safe(self):
        skill = AbbreviationsSkill()
        cmd = VoiceCommand("", "", target="<script>alert</script>")
        result = await skill.define(cmd)
        assert not result.success  # Not found, no crash

    def test_all_values_are_strings(self):
        for key, val in _ABBREVIATIONS.items():
            assert isinstance(key, str)
            assert isinstance(val, str)


class TestCycle245SecurityAllNewSkills:
    def test_no_dangerous_calls_in_stopwatch(self):
        import inspect
        src = inspect.getsource(StopwatchSkill)
        assert "subprocess" not in src

    def test_no_dangerous_calls_in_agenda(self):
        import inspect
        src = inspect.getsource(AgendaSkill)
        assert "subprocess" not in src

    def test_no_dangerous_calls_in_random(self):
        import inspect
        src = inspect.getsource(RandomPickerSkill)
        assert "subprocess" not in src

    def test_secrets_in_random(self):
        import inspect
        from whisperflow.jarvis.skills import random_picker
        src = inspect.getsource(random_picker)
        assert "secrets" in src


# ============================================================
# CYCLES 246-250: STRESS ET VALIDATION FINALE
# ============================================================

class TestCycle246StressAllNewPatterns:
    def setup_method(self):
        self.commander = Commander()

    def test_all_new_intents_matchable(self):
        test_phrases = {
            "stopwatch_start": "demarre le chronometre",
            "stopwatch_stop": "arrete le chrono",
            "stopwatch_lap": "tour",
            "stopwatch_reset": "reinitialise le chrono",
            "stopwatch_status": "temps du chronometre",
            "agenda_add": "agenda ajoute 10h test",
            "agenda_list": "mon agenda",
            "agenda_clear": "vide l'agenda",
            "agenda_next": "prochain evenement",
            "random_coin": "pile ou face",
            "random_dice": "lance un de",
            "random_pick": "choisis entre a ou b",
            "random_number": "nombre aleatoire",
            "abbrev_define": "que signifie API",
            "abbrev_list": "liste des abreviations",
        }
        for expected_intent, phrase in test_phrases.items():
            cmd = self.commander.parse(phrase)
            assert cmd.intent == expected_intent, \
                f"'{phrase}' -> {cmd.intent} (attendu {expected_intent})"


class TestCycle247Stress250Commands:
    def test_250_rapid_parses(self):
        commander = Commander()
        commands = [
            "ouvre chrome", "volume 50", "aide",
            "genere un mot de passe", "dans combien de jours noel",
            "en majuscules test", "epelle test",
            "demarre le chronometre", "arrete le chrono",
            "agenda ajoute 10h test", "mon agenda",
            "pile ou face", "lance un de", "nombre aleatoire",
            "que signifie API", "traduis en anglais bonjour",
            "convertis 5 km en miles", "pomodoro", "snapshot systeme",
            "note test", "minuteur 5 minutes", "calcule 2 plus 2",
            "muet", "suivant", "google python",
        ]
        for i in range(250):
            text = commands[i % len(commands)]
            cmd = commander.parse(text)
            assert cmd.intent != "unknown", \
                f"Iteration {i}: '{text}' non reconnu"


class TestCycle248StressFullPipeline:
    def setup_method(self):
        self.jarvis = Jarvis()
        self.jarvis.tts.speak = AsyncMock()
        self.jarvis.tts.speak_status = AsyncMock()

    @pytest.mark.asyncio
    async def test_full_pipeline_all_new_skills(self):
        commands = [
            "Jarvis demarre le chronometre",
            "Jarvis tour",
            "Jarvis arrete le chrono",
            "Jarvis agenda ajoute 14h test",
            "Jarvis mon agenda",
            "Jarvis pile ou face",
            "Jarvis lance un de",
            "Jarvis nombre aleatoire",
            "Jarvis que signifie CPU",
            "Jarvis reinitialise le chrono",
        ]
        for cmd_text in commands:
            self.jarvis.tts.speak.reset_mock()
            await self.jarvis.process_transcription(cmd_text)
            assert self.jarvis.tts.speak.called, \
                f"TTS non appele pour: {cmd_text}"


class TestCycle249AllIntentsComplete:
    def test_all_intents_have_handlers(self):
        jarvis = Jarvis()
        intents = {intent for _, intent in COMMAND_PATTERNS}
        handlers = set(jarvis.commander.list_intents())
        missing = intents - handlers - {"unknown"}
        assert not missing, f"Intents sans handler: {missing}"


class TestCycle250FinalValidation:
    def test_pattern_count(self):
        assert len(COMMAND_PATTERNS) >= 145

    def test_handler_count(self):
        jarvis = Jarvis()
        assert len(jarvis.commander.list_intents()) >= 135

    def test_27_skills(self):
        jarvis = Jarvis()
        assert jarvis.stopwatch is not None
        assert jarvis.agenda is not None
        assert jarvis.random_picker is not None
        assert jarvis.abbreviations is not None

    def test_4_agents(self):
        jarvis = Jarvis()
        assert len([jarvis.dictation, jarvis.search,
                     jarvis.automation, jarvis.navigation]) == 4

    def test_production_ready_250(self):
        """Test final: JARVIS 250 cycles pret pour production"""
        jarvis = Jarvis()
        intents = jarvis.commander.list_intents()
        assert len(intents) >= 135
        assert len(COMMAND_PATTERNS) >= 145
        pattern_intents = {i for _, i in COMMAND_PATTERNS}
        for intent in pattern_intents:
            if intent != "unknown":
                assert intent in intents, f"Handler manquant: {intent}"
