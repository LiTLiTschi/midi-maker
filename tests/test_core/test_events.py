"""Tests for CCEvent dataclass."""

import pytest
from dataclasses import FrozenInstanceError

from midi_maker.core.events import CCEvent


class TestCCEventCreation:
    """Tests for creating CCEvent instances."""

    def test_create_valid_event(self):
        """Test creating a valid CCEvent."""
        event = CCEvent(cc_number=74, value=64, channel=0, timestamp=1.5)
        
        assert event.cc_number == 74
        assert event.value == 64
        assert event.channel == 0
        assert event.timestamp == 1.5

    def test_create_with_min_values(self):
        """Test creating CCEvent with minimum valid values."""
        event = CCEvent(cc_number=0, value=0, channel=0, timestamp=0.0)
        
        assert event.cc_number == 0
        assert event.value == 0
        assert event.channel == 0
        assert event.timestamp == 0.0

    def test_create_with_max_values(self):
        """Test creating CCEvent with maximum valid values."""
        event = CCEvent(cc_number=127, value=127, channel=15, timestamp=999.999)
        
        assert event.cc_number == 127
        assert event.value == 127
        assert event.channel == 15
        assert event.timestamp == 999.999


class TestCCEventValidation:
    """Tests for CCEvent validation."""

    def test_cc_number_below_zero_raises(self):
        """Test that cc_number below 0 raises ValueError."""
        with pytest.raises(ValueError, match="cc_number must be 0-127"):
            CCEvent(cc_number=-1, value=64, channel=0, timestamp=1.0)

    def test_cc_number_above_127_raises(self):
        """Test that cc_number above 127 raises ValueError."""
        with pytest.raises(ValueError, match="cc_number must be 0-127"):
            CCEvent(cc_number=128, value=64, channel=0, timestamp=1.0)

    def test_value_below_zero_raises(self):
        """Test that value below 0 raises ValueError."""
        with pytest.raises(ValueError, match="value must be 0-127"):
            CCEvent(cc_number=74, value=-1, channel=0, timestamp=1.0)

    def test_value_above_127_raises(self):
        """Test that value above 127 raises ValueError."""
        with pytest.raises(ValueError, match="value must be 0-127"):
            CCEvent(cc_number=74, value=128, channel=0, timestamp=1.0)

    def test_channel_below_zero_raises(self):
        """Test that channel below 0 raises ValueError."""
        with pytest.raises(ValueError, match="channel must be 0-15"):
            CCEvent(cc_number=74, value=64, channel=-1, timestamp=1.0)

    def test_channel_above_15_raises(self):
        """Test that channel above 15 raises ValueError."""
        with pytest.raises(ValueError, match="channel must be 0-15"):
            CCEvent(cc_number=74, value=64, channel=16, timestamp=1.0)

    def test_negative_timestamp_raises(self):
        """Test that negative timestamp raises ValueError."""
        with pytest.raises(ValueError, match="timestamp must be >= 0"):
            CCEvent(cc_number=74, value=64, channel=0, timestamp=-0.1)


class TestCCEventImmutability:
    """Tests for CCEvent immutability (frozen dataclass)."""

    def test_cannot_modify_cc_number(self):
        """Test that cc_number cannot be modified."""
        event = CCEvent(cc_number=74, value=64, channel=0, timestamp=1.0)
        with pytest.raises(FrozenInstanceError):
            event.cc_number = 75

    def test_cannot_modify_value(self):
        """Test that value cannot be modified."""
        event = CCEvent(cc_number=74, value=64, channel=0, timestamp=1.0)
        with pytest.raises(FrozenInstanceError):
            event.value = 65

    def test_cannot_modify_channel(self):
        """Test that channel cannot be modified."""
        event = CCEvent(cc_number=74, value=64, channel=0, timestamp=1.0)
        with pytest.raises(FrozenInstanceError):
            event.channel = 1

    def test_cannot_modify_timestamp(self):
        """Test that timestamp cannot be modified."""
        event = CCEvent(cc_number=74, value=64, channel=0, timestamp=1.0)
        with pytest.raises(FrozenInstanceError):
            event.timestamp = 2.0


class TestCCEventEquality:
    """Tests for CCEvent equality and hashing."""

    def test_equal_events_are_equal(self):
        """Test that events with same values are equal."""
        event1 = CCEvent(cc_number=74, value=64, channel=0, timestamp=1.5)
        event2 = CCEvent(cc_number=74, value=64, channel=0, timestamp=1.5)
        
        assert event1 == event2

    def test_different_cc_number_not_equal(self):
        """Test that events with different cc_number are not equal."""
        event1 = CCEvent(cc_number=74, value=64, channel=0, timestamp=1.5)
        event2 = CCEvent(cc_number=75, value=64, channel=0, timestamp=1.5)
        
        assert event1 != event2

    def test_different_value_not_equal(self):
        """Test that events with different value are not equal."""
        event1 = CCEvent(cc_number=74, value=64, channel=0, timestamp=1.5)
        event2 = CCEvent(cc_number=74, value=65, channel=0, timestamp=1.5)
        
        assert event1 != event2

    def test_different_channel_not_equal(self):
        """Test that events with different channel are not equal."""
        event1 = CCEvent(cc_number=74, value=64, channel=0, timestamp=1.5)
        event2 = CCEvent(cc_number=74, value=64, channel=1, timestamp=1.5)
        
        assert event1 != event2

    def test_different_timestamp_not_equal(self):
        """Test that events with different timestamp are not equal."""
        event1 = CCEvent(cc_number=74, value=64, channel=0, timestamp=1.5)
        event2 = CCEvent(cc_number=74, value=64, channel=0, timestamp=2.5)
        
        assert event1 != event2

    def test_hashable(self):
        """Test that CCEvent is hashable (can be used in sets/dicts)."""
        event1 = CCEvent(cc_number=74, value=64, channel=0, timestamp=1.5)
        event2 = CCEvent(cc_number=74, value=64, channel=0, timestamp=1.5)
        event3 = CCEvent(cc_number=75, value=64, channel=0, timestamp=1.5)
        
        event_set = {event1, event2, event3}
        assert len(event_set) == 2  # event1 and event2 are equal

    def test_can_use_as_dict_key(self):
        """Test that CCEvent can be used as dictionary key."""
        event = CCEvent(cc_number=74, value=64, channel=0, timestamp=1.5)
        event_dict = {event: "test_value"}
        
        assert event_dict[event] == "test_value"


class TestCCEventRepresentation:
    """Tests for CCEvent string representation."""

    def test_repr_contains_all_fields(self):
        """Test that repr contains all field values."""
        event = CCEvent(cc_number=74, value=64, channel=0, timestamp=1.5)
        repr_str = repr(event)
        
        assert "CCEvent" in repr_str
        assert "cc_number=74" in repr_str
        assert "value=64" in repr_str
        assert "channel=0" in repr_str
        assert "timestamp=1.5" in repr_str
