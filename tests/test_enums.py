"""Tests for core enumerations."""

import pytest
from enum import Enum

from midi_maker.core.enums import (
    RecordingState,
    RecordingMode,
    PlaybackMode,
    CCAutomationType,
    GateState,
)


class TestRecordingState:
    """Tests for RecordingState enum."""

    def test_has_all_expected_values(self):
        """Test that RecordingState has exactly the expected values."""
        expected = {"IDLE", "RECORDING", "STOPPED"}
        actual = {state.name for state in RecordingState}
        assert actual == expected

    def test_is_enum(self):
        """Test that RecordingState is an Enum."""
        assert issubclass(RecordingState, Enum)

    def test_values_are_unique(self):
        """Test that all values are unique."""
        values = [state.value for state in RecordingState]
        assert len(values) == len(set(values))

    def test_can_access_by_name(self):
        """Test that enum members can be accessed by name."""
        assert RecordingState.IDLE == RecordingState["IDLE"]
        assert RecordingState.RECORDING == RecordingState["RECORDING"]
        assert RecordingState.STOPPED == RecordingState["STOPPED"]

    def test_membership(self):
        """Test that membership checks work."""
        assert RecordingState.IDLE in RecordingState
        assert RecordingState.RECORDING in RecordingState
        assert RecordingState.STOPPED in RecordingState


class TestRecordingMode:
    """Tests for RecordingMode enum."""

    def test_has_all_expected_values(self):
        """Test that RecordingMode has exactly the expected values."""
        expected = {"HOLD", "TOGGLE"}
        actual = {mode.name for mode in RecordingMode}
        assert actual == expected

    def test_is_enum(self):
        """Test that RecordingMode is an Enum."""
        assert issubclass(RecordingMode, Enum)

    def test_values_are_unique(self):
        """Test that all values are unique."""
        values = [mode.value for mode in RecordingMode]
        assert len(values) == len(set(values))

    def test_can_access_by_name(self):
        """Test that enum members can be accessed by name."""
        assert RecordingMode.HOLD == RecordingMode["HOLD"]
        assert RecordingMode.TOGGLE == RecordingMode["TOGGLE"]


class TestPlaybackMode:
    """Tests for PlaybackMode enum."""

    def test_has_all_expected_values(self):
        """Test that PlaybackMode has exactly the expected values."""
        expected = {
            "FULL_SEQUENCE",
            "ATTACK_ONLY",
            "DECAY_ONLY",
            "ATTACK_DECAY",
            "SNAPSHOT",
        }
        actual = {mode.name for mode in PlaybackMode}
        assert actual == expected

    def test_is_enum(self):
        """Test that PlaybackMode is an Enum."""
        assert issubclass(PlaybackMode, Enum)

    def test_values_are_unique(self):
        """Test that all values are unique."""
        values = [mode.value for mode in PlaybackMode]
        assert len(values) == len(set(values))

    def test_can_access_by_name(self):
        """Test that enum members can be accessed by name."""
        assert PlaybackMode.FULL_SEQUENCE == PlaybackMode["FULL_SEQUENCE"]
        assert PlaybackMode.ATTACK_ONLY == PlaybackMode["ATTACK_ONLY"]
        assert PlaybackMode.DECAY_ONLY == PlaybackMode["DECAY_ONLY"]
        assert PlaybackMode.ATTACK_DECAY == PlaybackMode["ATTACK_DECAY"]
        assert PlaybackMode.SNAPSHOT == PlaybackMode["SNAPSHOT"]


class TestCCAutomationType:
    """Tests for CCAutomationType enum."""

    def test_has_all_expected_values(self):
        """Test that CCAutomationType has exactly the expected values."""
        expected = {
            "FILTER_SWEEP",
            "VOLUME_FADE",
            "PAN_SWEEP",
            "RESONANCE",
            "CUSTOM",
        }
        actual = {type_.name for type_ in CCAutomationType}
        assert actual == expected

    def test_is_enum(self):
        """Test that CCAutomationType is an Enum."""
        assert issubclass(CCAutomationType, Enum)

    def test_values_are_unique(self):
        """Test that all values are unique."""
        values = [type_.value for type_ in CCAutomationType]
        assert len(values) == len(set(values))

    def test_can_access_by_name(self):
        """Test that enum members can be accessed by name."""
        assert CCAutomationType.FILTER_SWEEP == CCAutomationType["FILTER_SWEEP"]
        assert CCAutomationType.VOLUME_FADE == CCAutomationType["VOLUME_FADE"]
        assert CCAutomationType.PAN_SWEEP == CCAutomationType["PAN_SWEEP"]
        assert CCAutomationType.RESONANCE == CCAutomationType["RESONANCE"]
        assert CCAutomationType.CUSTOM == CCAutomationType["CUSTOM"]


class TestGateState:
    """Tests for GateState enum."""

    def test_has_all_expected_values(self):
        """Test that GateState has exactly the expected values."""
        expected = {"CLOSED", "OPEN"}
        actual = {state.name for state in GateState}
        assert actual == expected

    def test_is_enum(self):
        """Test that GateState is an Enum."""
        assert issubclass(GateState, Enum)

    def test_values_are_unique(self):
        """Test that all values are unique."""
        values = [state.value for state in GateState]
        assert len(values) == len(set(values))

    def test_can_access_by_name(self):
        """Test that enum members can be accessed by name."""
        assert GateState.CLOSED == GateState["CLOSED"]
        assert GateState.OPEN == GateState["OPEN"]

    def test_boolean_like_usage(self):
        """Test that gate states can be used in boolean-like contexts."""
        # This is a semantic test - OPEN might be used as truthy, CLOSED as falsy
        # But since they're enums, they're both truthy in Python
        assert GateState.OPEN
        assert GateState.CLOSED


class TestEnumComparisons:
    """Tests for comparisons between enum values."""

    def test_equality(self):
        """Test that enum values support equality comparison."""
        assert RecordingState.IDLE == RecordingState.IDLE
        assert RecordingState.IDLE != RecordingState.RECORDING
        
    def test_identity(self):
        """Test that enum values support identity comparison."""
        assert RecordingState.IDLE is RecordingState.IDLE
        assert RecordingState.IDLE is not RecordingState.RECORDING

    def test_cross_enum_inequality(self):
        """Test that values from different enums are not equal."""
        # Even if they have the same name, different enum types are not equal
        assert RecordingState.IDLE != GateState.OPEN
        

class TestEnumIteration:
    """Tests for iterating over enums."""

    def test_recording_state_iteration(self):
        """Test that we can iterate over RecordingState."""
        states = list(RecordingState)
        assert len(states) == 3
        assert RecordingState.IDLE in states
        assert RecordingState.RECORDING in states
        assert RecordingState.STOPPED in states

    def test_recording_mode_iteration(self):
        """Test that we can iterate over RecordingMode."""
        modes = list(RecordingMode)
        assert len(modes) == 2
        assert RecordingMode.HOLD in modes
        assert RecordingMode.TOGGLE in modes

    def test_playback_mode_iteration(self):
        """Test that we can iterate over PlaybackMode."""
        modes = list(PlaybackMode)
        assert len(modes) == 5

    def test_cc_automation_type_iteration(self):
        """Test that we can iterate over CCAutomationType."""
        types = list(CCAutomationType)
        assert len(types) == 5

    def test_gate_state_iteration(self):
        """Test that we can iterate over GateState."""
        states = list(GateState)
        assert len(states) == 2


class TestEnumStringRepresentation:
    """Tests for string representation of enums."""

    def test_str_representation(self):
        """Test that enums have useful string representations."""
        assert "IDLE" in str(RecordingState.IDLE)
        assert "HOLD" in str(RecordingMode.HOLD)
        assert "FULL_SEQUENCE" in str(PlaybackMode.FULL_SEQUENCE)
        assert "FILTER_SWEEP" in str(CCAutomationType.FILTER_SWEEP)
        assert "OPEN" in str(GateState.OPEN)

    def test_repr_representation(self):
        """Test that enums have useful repr representations."""
        assert "RecordingState" in repr(RecordingState.IDLE)
        assert "IDLE" in repr(RecordingState.IDLE)
