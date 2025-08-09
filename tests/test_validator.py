import pytest

from emotion_therapy.models import CommandType, SessionState
from emotion_therapy.validator import (
    get_available_commands,
    validate_command,
    parse_command,
    validate_command_from_raw,
)


class TestAvailableCommands:
    def test_no_session(self):
        cmds = set(get_available_commands(SessionState.NO_SESSION))
        assert cmds == {"start", "sos", "checkin"}

    def test_session_started(self):
        cmds = set(get_available_commands(SessionState.SESSION_STARTED))
        assert {"ask", "wheel", "feel", "breathe", "quote", "journal", "audio", "exit", "sos"} <= cmds

    def test_emotion_identified(self):
        cmds = set(get_available_commands(SessionState.EMOTION_IDENTIFIED))
        assert {"why", "remedy", "moodlog", "exit", "sos", "breathe", "quote", "journal", "audio"} <= cmds

    def test_diagnostic_complete(self):
        cmds = set(get_available_commands(SessionState.DIAGNOSTIC_COMPLETE))
        assert {"remedy", "moodlog", "exit", "sos", "breathe", "quote", "journal", "audio"} <= cmds

    def test_remedy_provided(self):
        cmds = set(get_available_commands(SessionState.REMEDY_PROVIDED))
        assert {"ask", "checkin", "moodlog", "exit", "sos", "breathe", "quote", "journal", "audio"} <= cmds

    def test_emergency(self):
        cmds = set(get_available_commands(SessionState.EMERGENCY))
        assert cmds == {"sos", "exit"}


class TestValidationTransitions:
    def test_unknown_command(self):
        res = validate_command("/nope", None, SessionState.NO_SESSION, None)
        assert not res.is_valid
        assert res.command_type == CommandType.UNKNOWN
        assert "/start" in res.suggested_commands

    @pytest.mark.parametrize("state", list(SessionState))
    def test_emergency_always_valid(self, state):
        res = validate_command("/sos", None, state, None)
        assert res.is_valid
        assert res.next_state == SessionState.EMERGENCY

    def test_start_from_no_session(self):
        res = validate_command("/start", None, SessionState.NO_SESSION, None)
        assert res.is_valid
        assert res.next_state == SessionState.SESSION_STARTED

    def test_ask_blocked_without_start(self):
        res = validate_command("/ask", "hi", SessionState.NO_SESSION, None)
        assert not res.is_valid
        assert "/start" in res.suggested_commands

    def test_feel_identifies_emotion(self):
        res = validate_command("/feel", "anger", SessionState.SESSION_STARTED, None)
        assert res.is_valid
        assert res.next_state == SessionState.EMOTION_IDENTIFIED

    def test_why_requires_identified(self):
        res = validate_command("/why", None, SessionState.SESSION_STARTED, None)
        assert not res.is_valid
        assert any(s in res.suggested_commands for s in ["/feel", "/ask", "/wheel"])

    def test_why_transitions_to_diagnostic_complete(self):
        res = validate_command("/why", None, SessionState.EMOTION_IDENTIFIED, None)
        assert res.is_valid
        assert res.next_state == SessionState.DIAGNOSTIC_COMPLETE

    def test_remedy_requires_identified_or_diagnostic(self):
        blocked = validate_command("/remedy", None, SessionState.SESSION_STARTED, None)
        assert not blocked.is_valid

        ok1 = validate_command("/remedy", None, SessionState.EMOTION_IDENTIFIED, None)
        ok2 = validate_command("/remedy", None, SessionState.DIAGNOSTIC_COMPLETE, None)
        assert ok1.is_valid and ok1.next_state == SessionState.REMEDY_PROVIDED
        assert ok2.is_valid and ok2.next_state == SessionState.REMEDY_PROVIDED

    def test_remedy_provided_allows_ask_and_checkin(self):
        res1 = validate_command("/ask", "new topic", SessionState.REMEDY_PROVIDED, None)
        res2 = validate_command("/checkin", None, SessionState.REMEDY_PROVIDED, None)
        assert res1.is_valid and res1.next_state == SessionState.SESSION_STARTED
        assert res2.is_valid and res2.next_state == SessionState.SESSION_STARTED

    def test_exit_ends_session(self):
        res = validate_command("/exit", None, SessionState.SESSION_STARTED, None)
        assert res.is_valid
        assert res.next_state == SessionState.NO_SESSION

    def test_moodlog_requires_post_identification(self):
        blocked = validate_command("/moodlog", None, SessionState.SESSION_STARTED, None)
        assert not blocked.is_valid

        ok = validate_command("/moodlog", None, SessionState.EMOTION_IDENTIFIED, None)
        assert ok.is_valid
        assert ok.next_state == SessionState.EMOTION_IDENTIFIED  # remains


class TestCommandParsing:
    def test_parse_explicit_commands(self):
        assert parse_command("/start") == ("start", None)
        assert parse_command("/exit") == ("exit", None)
        assert parse_command("/sos") == ("sos", None)
        assert parse_command("/feel angry") == ("feel", "angry")
        assert parse_command("/ask help") == ("ask", "help")
        assert parse_command("/feel very sad and tired") == ("feel", "very sad and tired")
        assert parse_command("/ask I'm feeling overwhelmed today") == ("ask", "I'm feeling overwhelmed today")

    def test_parse_implicit_ask_commands(self):
        assert parse_command("I'm feeling sad") == ("ask", "I'm feeling sad")
        assert parse_command("help me") == ("ask", "help me")
        assert parse_command("anxiety") == ("ask", "anxiety")
        assert parse_command("I don't know what I'm feeling right now") == (
            "ask",
            "I don't know what I'm feeling right now",
        )

    def test_parse_edge_cases(self):
        assert parse_command("") == ("ask", None)
        assert parse_command("   ") == ("ask", None)
        assert parse_command("\t\n") == ("ask", None)
        assert parse_command("/") == ("ask", None)
        assert parse_command("/   ") == ("ask", None)
        assert parse_command("/ ") == ("ask", None)
        assert parse_command("  /feel   angry  ") == ("feel", "angry")
        assert parse_command("  I'm sad  ") == ("ask", "I'm sad")

    def test_parse_case_insensitive(self):
        assert parse_command("/FEEL angry") == ("feel", "angry")
        assert parse_command("/Feel Angry") == ("feel", "Angry")
        assert parse_command("/START") == ("start", None)

    def test_validate_command_from_raw_integration(self):
        res = validate_command_from_raw("/start", SessionState.NO_SESSION)
        assert res.is_valid
        assert res.next_state == SessionState.SESSION_STARTED

        res = validate_command_from_raw("I'm feeling sad", SessionState.SESSION_STARTED)
        assert res.is_valid
        assert res.command_type in {CommandType.EMOTION_IDENTIFICATION, CommandType.SELF_HELP, CommandType.TRACKING}

        res = validate_command_from_raw("/why", SessionState.SESSION_STARTED)
        assert not res.is_valid
        assert any(s in res.suggested_commands for s in ["/feel", "/ask", "/wheel"])
