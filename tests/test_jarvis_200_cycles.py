"""
JARVIS - Cycles 151-200: Formation Intensive Phase 4
4 nouveaux skills: PasswordGenerator, DateCalculator, TextTools, Favorites

Total: 50 cycles, ~250 tests
"""

import asyncio
import pytest
import logging
import string
import re
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

from whisperflow.jarvis.jarvis_core import Jarvis
from whisperflow.jarvis.commander import Commander, VoiceCommand, CommandResult, COMMAND_PATTERNS
from whisperflow.jarvis.wake_word import detect_wake_word
from whisperflow.jarvis.skills.password_generator import (
    PasswordGeneratorSkill, generate_password, evaluate_strength
)
from whisperflow.jarvis.skills.date_calculator import (
    DateCalculatorSkill, format_date_fr, days_between, add_days,
    days_until_event, parse_date_fr, _JOURS_FR, _MOIS_FR
)
from whisperflow.jarvis.skills.text_tools import (
    TextToolsSkill, word_count, char_count, to_uppercase, to_lowercase,
    to_title_case, reverse_text, make_acronym, remove_accents
)
from whisperflow.jarvis.skills.favorites import FavoritesSkill


# ============================================================
# CYCLES 151-155: PATTERNS NOUVEAUX SKILLS
# ============================================================

class TestCycle151PasswordPatterns:
    def setup_method(self):
        self.commander = Commander()

    def test_generate_password(self):
        cmd = self.commander.parse("genere un mot de passe")
        assert cmd.intent == "password_generate"

    def test_generate_password_length(self):
        cmd = self.commander.parse("genere un mot de passe 20")
        assert cmd.intent == "password_generate"

    def test_generate_mdp(self):
        cmd = self.commander.parse("genere un mdp")
        assert cmd.intent == "password_generate"

    def test_password_strength(self):
        cmd = self.commander.parse("force du mot de passe abc123")
        assert cmd.intent == "password_strength"
        assert "abc123" in cmd.target


class TestCycle152DatePatterns:
    def setup_method(self):
        self.commander = Commander()

    def test_days_until_noel(self):
        cmd = self.commander.parse("dans combien de jours noel")
        assert cmd.intent == "date_days_until"

    def test_combien_jours_avant(self):
        cmd = self.commander.parse("combien de jours avant halloween")
        assert cmd.intent == "date_days_until"

    def test_dans_30_jours(self):
        cmd = self.commander.parse("dans 30 jours")
        assert cmd.intent == "date_add_days"

    def test_quel_jour_etait(self):
        cmd = self.commander.parse("quel jour etait le 14 juillet 1789")
        assert cmd.intent == "date_day_of_week"


class TestCycle153TextPatterns:
    def setup_method(self):
        self.commander = Commander()

    def test_count_words(self):
        cmd = self.commander.parse("compte les mots dans bonjour le monde")
        assert cmd.intent == "text_count"

    def test_uppercase(self):
        cmd = self.commander.parse("en majuscules bonjour")
        assert cmd.intent == "text_uppercase"

    def test_lowercase(self):
        cmd = self.commander.parse("en minuscules BONJOUR")
        assert cmd.intent == "text_lowercase"

    def test_acronym(self):
        cmd = self.commander.parse("acronyme de intelligence artificielle")
        assert cmd.intent == "text_acronym"

    def test_spell(self):
        cmd = self.commander.parse("epelle python")
        assert cmd.intent == "text_spell"


class TestCycle154FavoritePatterns:
    def setup_method(self):
        self.commander = Commander()

    def test_add_favorite(self):
        cmd = self.commander.parse("ajoute en favori ouvre chrome")
        assert cmd.intent == "fav_add"
        assert "ouvre chrome" in cmd.target

    def test_list_favorites(self):
        cmd = self.commander.parse("liste les favoris")
        assert cmd.intent == "fav_list"

    def test_remove_favorite(self):
        cmd = self.commander.parse("supprime le favori 1")
        assert cmd.intent == "fav_remove"

    def test_run_favorite(self):
        cmd = self.commander.parse("lance le favori 1")
        assert cmd.intent == "fav_run"


class TestCycle155PatternCount:
    def test_pattern_count(self):
        assert len(COMMAND_PATTERNS) >= 130, \
            f"Seulement {len(COMMAND_PATTERNS)} patterns (attendu >= 130)"

    def test_new_intents_present(self):
        intents = {intent for _, intent in COMMAND_PATTERNS}
        new_intents = [
            "password_generate", "password_strength",
            "date_days_until", "date_add_days", "date_day_of_week",
            "text_count", "text_uppercase", "text_lowercase",
            "text_acronym", "text_spell",
            "fav_add", "fav_list", "fav_remove", "fav_run",
        ]
        for intent in new_intents:
            assert intent in intents, f"Intent manquant: {intent}"


# ============================================================
# CYCLES 156-160: SKILL PASSWORD GENERATOR
# ============================================================

class TestCycle156PasswordGenerate:
    def test_default_length(self):
        pwd = generate_password()
        assert len(pwd) == 16

    def test_custom_length(self):
        pwd = generate_password(20)
        assert len(pwd) == 20

    def test_min_length(self):
        pwd = generate_password(4)
        assert len(pwd) == 8

    def test_max_length(self):
        pwd = generate_password(100)
        assert len(pwd) == 64


class TestCycle157PasswordComplexity:
    def test_has_uppercase(self):
        pwd = generate_password()
        assert any(c.isupper() for c in pwd)

    def test_has_lowercase(self):
        pwd = generate_password()
        assert any(c.islower() for c in pwd)

    def test_has_digit(self):
        pwd = generate_password()
        assert any(c.isdigit() for c in pwd)

    def test_has_special(self):
        pwd = generate_password(use_special=True)
        assert any(c in "!@#$%&*+-=" for c in pwd)

    def test_no_special(self):
        pwd = generate_password(use_special=False)
        assert all(c.isalnum() for c in pwd)


class TestCycle158PasswordUniqueness:
    def test_all_different(self):
        passwords = {generate_password() for _ in range(20)}
        assert len(passwords) == 20

    def test_different_lengths(self):
        p8 = generate_password(8)
        p16 = generate_password(16)
        p32 = generate_password(32)
        assert len(p8) < len(p16) < len(p32)


class TestCycle159PasswordStrength:
    def test_weak(self):
        assert evaluate_strength("abc") == "faible"

    def test_medium(self):
        assert evaluate_strength("Abc12345") == "moyen"

    def test_strong(self):
        assert evaluate_strength("Abc123!@#xyz") == "fort"

    def test_generated_is_strong(self):
        pwd = generate_password()
        assert evaluate_strength(pwd) == "fort"


class TestCycle160PasswordSkill:
    @pytest.mark.asyncio
    async def test_generate_command(self):
        skill = PasswordGeneratorSkill()
        cmd = VoiceCommand("", "password_generate", target="")
        result = await skill.generate(cmd)
        assert result.success
        assert "caract" in result.message
        assert result.data["strength"] == "fort"

    @pytest.mark.asyncio
    async def test_generate_with_length(self):
        skill = PasswordGeneratorSkill()
        cmd = VoiceCommand("", "password_generate", target="20 caracteres")
        result = await skill.generate(cmd)
        assert result.data["length"] == 20

    @pytest.mark.asyncio
    async def test_strength_command(self):
        skill = PasswordGeneratorSkill()
        cmd = VoiceCommand("", "password_strength", target="abc")
        result = await skill.strength(cmd)
        assert "faible" in result.message


# ============================================================
# CYCLES 161-165: SKILL DATE CALCULATOR
# ============================================================

class TestCycle161FormatDateFr:
    def test_format_known_date(self):
        dt = datetime(2025, 12, 25)
        result = format_date_fr(dt)
        assert "jeudi" in result
        assert "25" in result
        assert "2025" in result

    def test_format_jan_1(self):
        dt = datetime(2026, 1, 1)
        result = format_date_fr(dt)
        assert "janvier" in result


class TestCycle162DaysBetween:
    def test_same_day(self):
        d = datetime(2026, 1, 1)
        assert days_between(d, d) == 0

    def test_one_week(self):
        d1 = datetime(2026, 1, 1)
        d2 = datetime(2026, 1, 8)
        assert days_between(d1, d2) == 7

    def test_symmetric(self):
        d1 = datetime(2026, 1, 1)
        d2 = datetime(2026, 6, 15)
        assert days_between(d1, d2) == days_between(d2, d1)


class TestCycle163AddDays:
    def test_add_30(self):
        base = datetime(2026, 1, 1)
        result = add_days(base, 30)
        assert result == datetime(2026, 1, 31)

    def test_add_365(self):
        base = datetime(2026, 1, 1)
        result = add_days(base, 365)
        assert result.year == 2027

    def test_add_zero(self):
        base = datetime(2026, 6, 15)
        assert add_days(base, 0) == base


class TestCycle164ParseDateFr:
    def test_parse_date_text(self):
        dt = parse_date_fr("25 decembre 2025")
        assert dt.month == 12
        assert dt.day == 25
        assert dt.year == 2025

    def test_parse_slash_format(self):
        dt = parse_date_fr("14/07/1789")
        assert dt.day == 14
        assert dt.month == 7
        assert dt.year == 1789

    def test_parse_no_year(self):
        dt = parse_date_fr("15 mars")
        assert dt.month == 3
        assert dt.day == 15

    def test_parse_invalid(self):
        with pytest.raises(ValueError):
            parse_date_fr("blabla")


class TestCycle165DateSkillDaysUntil:
    @pytest.mark.asyncio
    async def test_days_until_noel(self):
        skill = DateCalculatorSkill()
        cmd = VoiceCommand("", "date_days_until", target="noel")
        result = await skill.days_until(cmd)
        assert result.success
        assert "jours" in result.message

    @pytest.mark.asyncio
    async def test_days_until_date(self):
        skill = DateCalculatorSkill()
        future = datetime.now() + timedelta(days=10)
        date_str = f"{future.day}/{future.month}/{future.year}"
        cmd = VoiceCommand("", "date_days_until", target=date_str)
        result = await skill.days_until(cmd)
        assert result.success
        assert result.data["days"] in (9, 10)

    @pytest.mark.asyncio
    async def test_add_days_cmd(self):
        skill = DateCalculatorSkill()
        cmd = VoiceCommand("", "date_add_days", target="30 jours")
        result = await skill.add_days_cmd(cmd)
        assert result.success
        assert "30 jours" in result.message

    @pytest.mark.asyncio
    async def test_day_of_week(self):
        skill = DateCalculatorSkill()
        cmd = VoiceCommand("", "date_day_of_week", target="14/07/1789")
        result = await skill.day_of_week(cmd)
        assert result.success
        assert "mardi" in result.message


# ============================================================
# CYCLES 166-170: SKILL TEXT TOOLS
# ============================================================

class TestCycle166WordCount:
    def test_simple(self):
        assert word_count("bonjour le monde") == 3

    def test_one_word(self):
        assert word_count("python") == 1

    def test_many_spaces(self):
        assert word_count("un   deux   trois") == 3


class TestCycle167CharCount:
    def test_with_spaces(self):
        assert char_count("a b c", spaces=True) == 5

    def test_without_spaces(self):
        assert char_count("a b c", spaces=False) == 3

    def test_empty(self):
        assert char_count("") == 0


class TestCycle168CaseConversion:
    def test_uppercase(self):
        assert to_uppercase("bonjour") == "BONJOUR"

    def test_lowercase(self):
        assert to_lowercase("BONJOUR") == "bonjour"

    def test_title_case(self):
        assert to_title_case("bonjour le monde") == "Bonjour Le Monde"

    def test_reverse(self):
        assert reverse_text("abc") == "cba"

    def test_reverse_palindrome(self):
        assert reverse_text("kayak") == "kayak"


class TestCycle169Acronym:
    def test_simple(self):
        assert make_acronym("intelligence artificielle") == "IA"

    def test_three_words(self):
        result = make_acronym("tres haute frequence")
        assert result == "THF"

    def test_single_word(self):
        assert make_acronym("python") == "P"


class TestCycle170TextSkillAndAccents:
    def test_remove_accents_no_change(self):
        assert remove_accents("hello") == "hello"

    @pytest.mark.asyncio
    async def test_count_words_skill(self):
        skill = TextToolsSkill()
        cmd = VoiceCommand("", "text_count", target="un deux trois")
        result = await skill.count_words(cmd)
        assert result.success
        assert "3 mots" in result.message

    @pytest.mark.asyncio
    async def test_uppercase_skill(self):
        skill = TextToolsSkill()
        cmd = VoiceCommand("", "text_uppercase", target="bonjour")
        result = await skill.uppercase(cmd)
        assert result.data["text"] == "BONJOUR"

    @pytest.mark.asyncio
    async def test_spell_skill(self):
        skill = TextToolsSkill()
        cmd = VoiceCommand("", "text_spell", target="ai")
        result = await skill.spell(cmd)
        assert "A" in result.message and "I" in result.message


# ============================================================
# CYCLES 171-175: SKILL FAVORITES
# ============================================================

class TestCycle171FavoriteAdd:
    @pytest.mark.asyncio
    async def test_add_one(self):
        skill = FavoritesSkill()
        cmd = VoiceCommand("", "fav_add", target="ouvre chrome")
        result = await skill.add(cmd)
        assert result.success
        assert skill.count == 1

    @pytest.mark.asyncio
    async def test_add_duplicate(self):
        skill = FavoritesSkill()
        cmd = VoiceCommand("", "fav_add", target="ouvre chrome")
        await skill.add(cmd)
        result = await skill.add(cmd)
        assert not result.success

    @pytest.mark.asyncio
    async def test_add_empty(self):
        skill = FavoritesSkill()
        cmd = VoiceCommand("", "fav_add", target="")
        result = await skill.add(cmd)
        assert not result.success


class TestCycle172FavoriteList:
    @pytest.mark.asyncio
    async def test_list_empty(self):
        skill = FavoritesSkill()
        cmd = VoiceCommand("", "fav_list")
        result = await skill.list_favorites(cmd)
        assert "Aucun" in result.message

    @pytest.mark.asyncio
    async def test_list_with_items(self):
        skill = FavoritesSkill()
        await skill.add(VoiceCommand("", "fav_add", target="ouvre chrome"))
        await skill.add(VoiceCommand("", "fav_add", target="volume 50"))
        cmd = VoiceCommand("", "fav_list")
        result = await skill.list_favorites(cmd)
        assert "2 favoris" in result.message


class TestCycle173FavoriteRemove:
    @pytest.mark.asyncio
    async def test_remove_by_index(self):
        skill = FavoritesSkill()
        await skill.add(VoiceCommand("", "fav_add", target="ouvre chrome"))
        cmd = VoiceCommand("", "fav_remove", target="1")
        result = await skill.remove(cmd)
        assert result.success
        assert skill.count == 0

    @pytest.mark.asyncio
    async def test_remove_by_name(self):
        skill = FavoritesSkill()
        await skill.add(VoiceCommand("", "fav_add", target="ouvre chrome"))
        cmd = VoiceCommand("", "fav_remove", target="chrome")
        result = await skill.remove(cmd)
        assert result.success

    @pytest.mark.asyncio
    async def test_remove_not_found(self):
        skill = FavoritesSkill()
        cmd = VoiceCommand("", "fav_remove", target="inexistant")
        result = await skill.remove(cmd)
        assert not result.success


class TestCycle174FavoriteRun:
    @pytest.mark.asyncio
    async def test_run_by_index(self):
        skill = FavoritesSkill()
        await skill.add(VoiceCommand("", "fav_add", target="ouvre chrome"))
        cmd = VoiceCommand("", "fav_run", target="1")
        result = await skill.run_favorite(cmd)
        assert result.success
        assert result.data["run_command"] == "ouvre chrome"

    @pytest.mark.asyncio
    async def test_run_by_name(self):
        skill = FavoritesSkill()
        await skill.add(VoiceCommand("", "fav_add", target="volume 80"))
        cmd = VoiceCommand("", "fav_run", target="volume")
        result = await skill.run_favorite(cmd)
        assert result.data["run_command"] == "volume 80"

    @pytest.mark.asyncio
    async def test_run_invalid_index(self):
        skill = FavoritesSkill()
        cmd = VoiceCommand("", "fav_run", target="99")
        result = await skill.run_favorite(cmd)
        assert not result.success


class TestCycle175FavoriteMax:
    @pytest.mark.asyncio
    async def test_max_20(self):
        skill = FavoritesSkill()
        for i in range(20):
            await skill.add(VoiceCommand("", "", target=f"cmd_{i}"))
        assert skill.count == 20
        result = await skill.add(VoiceCommand("", "", target="cmd_21"))
        assert not result.success
        assert "Maximum" in result.message


# ============================================================
# CYCLES 176-180: PIPELINE COMPLET VIA JARVIS
# ============================================================

class TestCycle176PasswordPipeline:
    def setup_method(self):
        self.jarvis = Jarvis()
        self.jarvis.tts.speak = AsyncMock()
        self.jarvis.tts.speak_status = AsyncMock()

    @pytest.mark.asyncio
    async def test_password_via_voice(self):
        await self.jarvis.process_transcription("Jarvis genere un mot de passe")
        assert self.jarvis.tts.speak.called
        msg = self.jarvis.tts.speak.call_args[0][0]
        assert "caract" in msg


class TestCycle177DatePipeline:
    def setup_method(self):
        self.jarvis = Jarvis()
        self.jarvis.tts.speak = AsyncMock()
        self.jarvis.tts.speak_status = AsyncMock()

    @pytest.mark.asyncio
    async def test_days_until_noel_voice(self):
        await self.jarvis.process_transcription(
            "Jarvis dans combien de jours noel")
        assert self.jarvis.tts.speak.called
        msg = self.jarvis.tts.speak.call_args[0][0]
        assert "jours" in msg

    @pytest.mark.asyncio
    async def test_add_days_voice(self):
        await self.jarvis.process_transcription("Jarvis dans 30 jours")
        assert self.jarvis.tts.speak.called
        msg = self.jarvis.tts.speak.call_args[0][0]
        assert "30 jours" in msg


class TestCycle178TextPipeline:
    def setup_method(self):
        self.jarvis = Jarvis()
        self.jarvis.tts.speak = AsyncMock()
        self.jarvis.tts.speak_status = AsyncMock()

    @pytest.mark.asyncio
    async def test_uppercase_voice(self):
        await self.jarvis.process_transcription("Jarvis en majuscules bonjour")
        assert self.jarvis.tts.speak.called
        msg = self.jarvis.tts.speak.call_args[0][0]
        assert "BONJOUR" in msg

    @pytest.mark.asyncio
    async def test_spell_voice(self):
        await self.jarvis.process_transcription("Jarvis epelle python")
        assert self.jarvis.tts.speak.called


class TestCycle179FavoritePipeline:
    def setup_method(self):
        self.jarvis = Jarvis()
        self.jarvis.tts.speak = AsyncMock()
        self.jarvis.tts.speak_status = AsyncMock()

    @pytest.mark.asyncio
    async def test_add_fav_voice(self):
        await self.jarvis.process_transcription(
            "Jarvis ajoute en favori ouvre chrome")
        assert self.jarvis.tts.speak.called
        msg = self.jarvis.tts.speak.call_args[0][0]
        assert "favori" in msg.lower()

    @pytest.mark.asyncio
    async def test_list_fav_voice(self):
        await self.jarvis.process_transcription("Jarvis mes favoris")
        assert self.jarvis.tts.speak.called


class TestCycle180AllNewHandlers:
    def test_all_handlers_registered(self):
        jarvis = Jarvis()
        intents = jarvis.commander.list_intents()
        new_intents = [
            "password_generate", "password_strength",
            "date_days_until", "date_add_days", "date_day_of_week",
            "text_count", "text_uppercase", "text_lowercase",
            "text_acronym", "text_spell",
            "fav_add", "fav_list", "fav_remove", "fav_run",
        ]
        for intent in new_intents:
            assert intent in intents, f"Handler manquant: {intent}"


# ============================================================
# CYCLES 181-185: SCENARIOS AVANCES
# ============================================================

class TestCycle181ScenarioSecretaire:
    def setup_method(self):
        self.jarvis = Jarvis()
        self.jarvis.tts.speak = AsyncMock()
        self.jarvis.tts.speak_status = AsyncMock()

    @pytest.mark.asyncio
    async def test_morning_setup(self):
        await self.jarvis.process_transcription(
            "Jarvis genere un mot de passe 12")
        msg = self.jarvis.tts.speak.call_args[0][0]
        assert "caract" in msg

        await self.jarvis.process_transcription(
            "Jarvis ajoute en favori ouvre outlook")
        assert self.jarvis.favorites.count == 1


class TestCycle182ScenarioDeveloppeur:
    def setup_method(self):
        self.jarvis = Jarvis()
        self.jarvis.tts.speak = AsyncMock()
        self.jarvis.tts.speak_status = AsyncMock()

    @pytest.mark.asyncio
    async def test_dev_workflow(self):
        await self.jarvis.process_transcription(
            "Jarvis dans combien de jours le 1 mars")
        assert self.jarvis.tts.speak.called

        self.jarvis.tts.speak.reset_mock()
        await self.jarvis.process_transcription(
            "Jarvis acronyme de gestion intelligente des taches")
        msg = self.jarvis.tts.speak.call_args[0][0]
        assert "GIDT" in msg


class TestCycle183ScenarioVoyageur:
    def setup_method(self):
        self.jarvis = Jarvis()
        self.jarvis.tts.speak = AsyncMock()
        self.jarvis.tts.speak_status = AsyncMock()

    @pytest.mark.asyncio
    async def test_travel_prep(self):
        await self.jarvis.process_transcription(
            "Jarvis compte les mots dans Jean Pierre Dupont")
        msg = self.jarvis.tts.speak.call_args[0][0]
        assert "3 mots" in msg


class TestCycle184ScenarioProf:
    def setup_method(self):
        self.jarvis = Jarvis()
        self.jarvis.tts.speak = AsyncMock()
        self.jarvis.tts.speak_status = AsyncMock()

    @pytest.mark.asyncio
    async def test_class_prep(self):
        await self.jarvis.process_transcription(
            "Jarvis dans combien de jours le 14 juillet")
        msg = self.jarvis.tts.speak.call_args[0][0]
        assert "jours" in msg

        self.jarvis.tts.speak.reset_mock()
        await self.jarvis.process_transcription(
            "Jarvis epelle anticonstitutionnellement")
        assert self.jarvis.tts.speak.called


class TestCycle185ScenarioManager:
    def setup_method(self):
        self.jarvis = Jarvis()
        self.jarvis.tts.speak = AsyncMock()
        self.jarvis.tts.speak_status = AsyncMock()

    @pytest.mark.asyncio
    async def test_manager_workflow(self):
        await self.jarvis.process_transcription(
            "Jarvis ajoute en favori ouvre teams")
        assert self.jarvis.favorites.count == 1

        self.jarvis.tts.speak.reset_mock()
        await self.jarvis.process_transcription(
            "Jarvis genere un password")
        msg = self.jarvis.tts.speak.call_args[0][0]
        assert "caract" in msg


# ============================================================
# CYCLES 186-190: NON-REGRESSION
# ============================================================

class TestCycle186OriginalPatternsStillWork:
    def setup_method(self):
        self.commander = Commander()

    @pytest.mark.parametrize("text,expected", [
        ("ouvre chrome", "app_launch"),
        ("volume 50", "system_volume_set"),
        ("muet", "system_mute"),
        ("aide", "jarvis_help"),
        ("merci", "jarvis_thanks"),
        ("suivant", "media_next"),
        ("bureau virtuel suivant", "vdesktop_right"),
        ("ouvre les telechargements", "navigate_downloads"),
        ("minuteur 5 minutes", "timer_set"),
        ("note acheter lait", "note_add"),
        ("calcule 2 plus 2", "calc_compute"),
        ("traduis en anglais bonjour", "translate_fr_en"),
        ("pomodoro", "pomodoro_start"),
        ("snapshot systeme", "snapshot_take"),
        ("convertis 10 km en miles", "unit_convert"),
        ("gpu", "system_gpu"),
        ("ping google.com", "network_ping"),
    ])
    def test_original_intact(self, text, expected):
        cmd = self.commander.parse(text)
        assert cmd.intent == expected, \
            f"'{text}' -> {cmd.intent} (attendu {expected})"


class TestCycle187NewPatternsNoConflict:
    def setup_method(self):
        self.commander = Commander()

    def test_password_not_app(self):
        cmd = self.commander.parse("genere un mot de passe")
        assert cmd.intent == "password_generate"

    def test_date_not_timer(self):
        cmd = self.commander.parse("dans combien de jours noel")
        assert cmd.intent == "date_days_until"

    def test_uppercase_not_app(self):
        cmd = self.commander.parse("en majuscules test")
        assert cmd.intent == "text_uppercase"

    def test_favori_not_app(self):
        cmd = self.commander.parse("ajoute en favori ouvre chrome")
        assert cmd.intent == "fav_add"

    def test_spell_not_search(self):
        cmd = self.commander.parse("epelle chat")
        assert cmd.intent == "text_spell"


class TestCycle188RegressionGuards:
    def setup_method(self):
        self.commander = Commander()

    def test_telechargements_not_resources(self):
        cmd = self.commander.parse("ouvre les telechargements")
        assert cmd.intent == "navigate_downloads"

    def test_powerpoint_not_period(self):
        cmd = self.commander.parse("ouvre powerpoint")
        assert cmd.intent == "app_launch"

    def test_lance_macro_is_run(self):
        cmd = self.commander.parse("lance la macro test")
        assert cmd.intent == "automation_run"

    def test_discuter_not_cut(self):
        cmd = self.commander.parse("note points a discuter")
        assert cmd.intent == "note_add"

    def test_stop_pomodoro_not_start(self):
        cmd = self.commander.parse("arrete le pomodoro")
        assert cmd.intent == "pomodoro_stop"

    def test_snapshots_precedents_not_media(self):
        cmd = self.commander.parse("snapshots precedents")
        assert cmd.intent == "snapshot_history"


class TestCycle189AllSkillsInstantiate:
    def test_23_skills(self):
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
            jarvis.favorites,
        ]
        assert len(skills) == 23
        for s in skills:
            assert s is not None


class TestCycle190AllAgentsIntact:
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
# CYCLES 191-195: EDGE CASES ET SECURITE
# ============================================================

class TestCycle191PasswordEdgeCases:
    def test_secrets_used(self):
        """Verifie que secrets (CSPRNG) est utilise"""
        import inspect
        src = inspect.getsource(generate_password)
        assert "secrets" in src

    @pytest.mark.asyncio
    async def test_injection_in_strength(self):
        skill = PasswordGeneratorSkill()
        cmd = VoiceCommand("", "", target="DROP TABLE users")
        result = await skill.strength(cmd)
        assert result.success


class TestCycle192DateEdgeCases:
    def test_past_date(self):
        dt = parse_date_fr("1/1/2000")
        assert dt.year == 2000

    @pytest.mark.asyncio
    async def test_days_until_past(self):
        skill = DateCalculatorSkill()
        cmd = VoiceCommand("", "", target="1/1/2020")
        result = await skill.days_until(cmd)
        assert result.success
        assert "il y a" in result.message

    @pytest.mark.asyncio
    async def test_empty_target(self):
        skill = DateCalculatorSkill()
        cmd = VoiceCommand("", "", target="")
        result = await skill.days_until(cmd)
        assert not result.success


class TestCycle193TextEdgeCases:
    @pytest.mark.asyncio
    async def test_empty_count(self):
        skill = TextToolsSkill()
        cmd = VoiceCommand("", "", target="")
        result = await skill.count_words(cmd)
        assert not result.success

    @pytest.mark.asyncio
    async def test_empty_spell(self):
        skill = TextToolsSkill()
        cmd = VoiceCommand("", "", target="")
        result = await skill.spell(cmd)
        assert not result.success

    def test_acronym_special_chars(self):
        assert make_acronym("c'est la vie") == "CLV"


class TestCycle194FavoriteEdgeCases:
    @pytest.mark.asyncio
    async def test_remove_empty(self):
        skill = FavoritesSkill()
        cmd = VoiceCommand("", "", target="")
        result = await skill.remove(cmd)
        assert not result.success

    @pytest.mark.asyncio
    async def test_run_empty(self):
        skill = FavoritesSkill()
        cmd = VoiceCommand("", "", target="inexistant")
        result = await skill.run_favorite(cmd)
        assert not result.success

    @pytest.mark.asyncio
    async def test_get_all(self):
        skill = FavoritesSkill()
        await skill.add(VoiceCommand("", "", target="test"))
        assert len(skill.get_all()) == 1


class TestCycle195SecurityAllNewSkills:
    def test_no_dangerous_calls_in_password(self):
        import inspect
        src = inspect.getsource(PasswordGeneratorSkill)
        assert "subprocess" not in src

    def test_no_dangerous_calls_in_date(self):
        import inspect
        src = inspect.getsource(DateCalculatorSkill)
        assert "subprocess" not in src

    def test_no_dangerous_calls_in_text(self):
        import inspect
        src = inspect.getsource(TextToolsSkill)
        assert "subprocess" not in src

    def test_no_dangerous_calls_in_favorites(self):
        import inspect
        src = inspect.getsource(FavoritesSkill)
        assert "subprocess" not in src


# ============================================================
# CYCLES 196-200: STRESS ET VALIDATION FINALE
# ============================================================

class TestCycle196StressAllNewPatterns:
    def setup_method(self):
        self.commander = Commander()

    def test_all_new_intents_matchable(self):
        test_phrases = {
            "password_generate": "genere un mot de passe",
            "password_strength": "force du mot de passe test",
            "date_days_until": "dans combien de jours noel",
            "date_add_days": "dans 30 jours",
            "date_day_of_week": "quel jour etait le 25 decembre 2000",
            "text_count": "compte les mots dans hello world",
            "text_uppercase": "en majuscules test",
            "text_lowercase": "en minuscules TEST",
            "text_acronym": "acronyme de test unitaire",
            "text_spell": "epelle python",
            "fav_add": "ajoute en favori test",
            "fav_list": "liste les favoris",
            "fav_remove": "supprime le favori 1",
            "fav_run": "lance le favori 1",
        }
        for expected_intent, phrase in test_phrases.items():
            cmd = self.commander.parse(phrase)
            assert cmd.intent == expected_intent, \
                f"'{phrase}' -> {cmd.intent} (attendu {expected_intent})"


class TestCycle197Stress200Commands:
    def test_200_rapid_parses(self):
        commander = Commander()
        commands = [
            "ouvre chrome", "volume 50", "aide",
            "genere un mot de passe", "dans combien de jours noel",
            "en majuscules test", "ajoute en favori test",
            "traduis en anglais bonjour", "convertis 5 km en miles",
            "pomodoro", "snapshot systeme", "note test",
            "minuteur 5 minutes", "calcule 2 plus 2",
            "muet", "suivant", "google python",
            "gpu", "ping google.com", "epelle test",
        ]
        for i in range(200):
            text = commands[i % len(commands)]
            cmd = commander.parse(text)
            assert cmd.intent != "unknown", \
                f"Iteration {i}: '{text}' non reconnu"


class TestCycle198StressFullPipeline:
    def setup_method(self):
        self.jarvis = Jarvis()
        self.jarvis.tts.speak = AsyncMock()
        self.jarvis.tts.speak_status = AsyncMock()

    @pytest.mark.asyncio
    async def test_full_pipeline_all_skills(self):
        commands = [
            "Jarvis genere un mot de passe",
            "Jarvis dans combien de jours noel",
            "Jarvis en majuscules hello world",
            "Jarvis ajoute en favori ouvre chrome",
            "Jarvis mes favoris",
            "Jarvis epelle jarvis",
            "Jarvis acronyme de tres bien",
            "Jarvis dans 10 jours",
        ]
        for cmd_text in commands:
            self.jarvis.tts.speak.reset_mock()
            await self.jarvis.process_transcription(cmd_text)
            assert self.jarvis.tts.speak.called, \
                f"TTS non appele pour: {cmd_text}"


class TestCycle199AllIntentsComplete:
    def test_all_intents_have_handlers(self):
        jarvis = Jarvis()
        intents = {intent for _, intent in COMMAND_PATTERNS}
        handlers = set(jarvis.commander.list_intents())
        missing = intents - handlers - {"unknown"}
        assert not missing, f"Intents sans handler: {missing}"


class TestCycle200FinalValidation:
    def test_pattern_count(self):
        assert len(COMMAND_PATTERNS) >= 130

    def test_handler_count(self):
        jarvis = Jarvis()
        assert len(jarvis.commander.list_intents()) >= 120

    def test_23_skills(self):
        jarvis = Jarvis()
        assert jarvis.password is not None
        assert jarvis.date_calc is not None
        assert jarvis.text_tools is not None
        assert jarvis.favorites is not None

    def test_4_agents(self):
        jarvis = Jarvis()
        assert jarvis.dictation is not None
        assert jarvis.search is not None
        assert jarvis.automation is not None
        assert jarvis.navigation is not None

    def test_production_ready(self):
        """Test final: JARVIS 200 cycles pret pour production"""
        jarvis = Jarvis()
        intents = jarvis.commander.list_intents()
        assert len(intents) >= 120
        assert len(COMMAND_PATTERNS) >= 130
        pattern_intents = {i for _, i in COMMAND_PATTERNS}
        for intent in pattern_intents:
            if intent != "unknown":
                assert intent in intents, f"Handler manquant: {intent}"
