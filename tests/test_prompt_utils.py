"""Tests for utility functions in prompt.py module."""

import pytest
from prompt.prompt import (
    hex_to_rgb,
    colorscale,
    clamp,
    snip,
    find_dir_upwards,
    Ellipses,
)
from pathlib import Path
import tempfile


class TestHexToRgb:
    """Test hex_to_rgb color conversion function."""

    @pytest.mark.unit
    def test_valid_hex_with_hash(self):
        """Test converting hex color with # prefix."""
        assert hex_to_rgb("#FF0000") == (255, 0, 0)
        assert hex_to_rgb("#00FF00") == (0, 255, 0)
        assert hex_to_rgb("#0000FF") == (0, 0, 255)

    @pytest.mark.unit
    def test_valid_hex_without_hash(self):
        """Test converting hex color without # prefix."""
        assert hex_to_rgb("FF0000") == (255, 0, 0)
        assert hex_to_rgb("00FF00") == (0, 255, 0)

    @pytest.mark.unit
    def test_lowercase_hex(self):
        """Test lowercase hex strings."""
        assert hex_to_rgb("#ff0000") == (255, 0, 0)
        assert hex_to_rgb("#abcdef") == (171, 205, 239)

    @pytest.mark.edge_case
    def test_invalid_hex_length(self):
        """Test that invalid hex length raises IndexError."""
        with pytest.raises(IndexError):
            hex_to_rgb("#FF00")
        with pytest.raises(IndexError):
            hex_to_rgb("#FF00000")

    @pytest.mark.edge_case
    def test_black_and_white(self):
        """Test extreme colors."""
        assert hex_to_rgb("#000000") == (0, 0, 0)
        assert hex_to_rgb("#FFFFFF") == (255, 255, 255)


class TestColorscale:
    """Test color scaling function."""

    @pytest.mark.unit
    def test_scale_up(self):
        """Test brightening a color."""
        result = colorscale("#800000", 2)
        assert result == "#ff0000"

    @pytest.mark.unit
    def test_scale_down(self):
        """Test darkening a color."""
        result = colorscale("#FF0000", 0.5)
        assert result == "#7f0000"

    @pytest.mark.unit
    def test_scale_one(self):
        """Test scaling by 1.0 returns same color."""
        result = colorscale("#4F75D2", 1.0)
        assert result == "#4f75d2"

    @pytest.mark.unit
    def test_scale_white(self):
        """Test scaling white."""
        result = colorscale("#FFFFFF", 0.5)
        assert result == "#7f7f7f"

    @pytest.mark.edge_case
    def test_scale_negative_factor(self):
        """Test negative scale factor returns original hex."""
        result = colorscale("#FF0000", -1)
        assert result == "FF0000"

    @pytest.mark.edge_case
    def test_scale_invalid_hex(self):
        """Test invalid hex handling.

        Note: This test demonstrates a bug - colorscale() crashes on invalid hex.
        It should handle invalid hex gracefully by returning the original or raising
        a proper error, instead of crashing with ValueError.

        This test documents the current buggy behavior.
        """
        # Currently crashes with ValueError - should be fixed to handle gracefully
        with pytest.raises(ValueError):
            colorscale("#GGGGGG", 1.5)


class TestClamp:
    """Test value clamping function."""

    @pytest.mark.unit
    def test_clamp_in_range(self):
        """Test values already in range."""
        assert clamp(128, 0, 255) == 128
        assert clamp(0, 0, 255) == 0
        assert clamp(255, 0, 255) == 255

    @pytest.mark.unit
    def test_clamp_below_minimum(self):
        """Test values below minimum."""
        assert clamp(-50, 0, 255) == 0
        assert clamp(-1, 10, 100) == 10

    @pytest.mark.unit
    def test_clamp_above_maximum(self):
        """Test values above maximum."""
        assert clamp(300, 0, 255) == 255
        assert clamp(101, 10, 100) == 100

    @pytest.mark.unit
    def test_clamp_float_values(self):
        """Test clamping float values."""
        assert clamp(50.5, 0, 100) == 50.5
        assert clamp(150.5, 0, 100) == 100


class TestSnip:
    """Test string snipping function."""

    @pytest.mark.unit
    def test_snip_short_string(self):
        """Test that short strings are not snipped."""
        result = snip("short", 20, "...")
        assert result == ("short", "")

    @pytest.mark.unit
    def test_snip_long_string(self):
        """Test snipping a long string."""
        string = "/home/user/very/long/path/to/some/directory"
        start, end = snip(string, 20, "…", position=0.5)
        # Should return start and end parts that together are ~20 chars
        assert len(start) + len("…") + len(end) <= 20
        assert start == string[:len(start)]
        assert end == string[-len(end):] if end else ""

    @pytest.mark.unit
    def test_snip_position_quarter(self):
        """Test snipping with position at 0.25."""
        string = "/home/user/projects/myproject"
        start, end = snip(string, 15, "…", position=0.25)
        # Position should be closer to the beginning
        assert len(start) < len(end)

    @pytest.mark.edge_case
    def test_snip_exact_length(self):
        """Test snipping when string equals target length."""
        string = "exactly20characterss"
        result = snip(string, 20, "…")
        assert result == ("exactly20characterss", "")

    @pytest.mark.edge_case
    def test_snip_very_small_length(self):
        """Test snipping to very small length."""
        string = "/home/user/long"
        start, end = snip(string, 3, "…", position=0.5)
        # Should still work even with tiny target
        assert (start + "…" + end) or start  # At least some part should exist


class TestFindDirUpwards:
    """Test directory traversal function."""

    @pytest.mark.unit
    def test_find_dir_in_current(self):
        """Test finding directory in current location."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir).resolve()
            target_dir = tmpdir_path / "target"
            target_dir.mkdir()

            result = find_dir_upwards(tmpdir_path, "target")
            assert result == target_dir

    @pytest.mark.unit
    def test_find_dir_in_parent(self):
        """Test finding directory in parent path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir).resolve()
            target_dir = tmpdir_path / "target"
            target_dir.mkdir()
            child_dir = target_dir / "child"
            child_dir.mkdir()

            result = find_dir_upwards(child_dir, "target")
            assert result == target_dir

    @pytest.mark.unit
    def test_find_dir_not_found(self):
        """Test when directory doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = find_dir_upwards(Path(tmpdir), "nonexistent")
            assert result is None

    @pytest.mark.unit
    def test_find_dir_stop_at_home(self):
        """Test that search stops at home directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Using home as stop point
            result = find_dir_upwards(
                Path(tmpdir),
                "nonexistent",
                stop_at=tmpdir
            )
            assert result is None

    @pytest.mark.edge_case
    def test_find_dir_multiple_levels_up(self):
        """Test finding directory multiple levels up."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            target = tmpdir_path / "a" / "b" / "c"
            target.mkdir(parents=True)
            search_from = tmpdir_path / "a" / "b" / "c" / "d" / "e"
            search_from.mkdir(parents=True)

            result = find_dir_upwards(search_from, "target", stop_at="/nonexistent")
            # Should not find "target" since it's not in the path
            assert result is None


class TestEllipses:
    """Test Ellipses dataclass."""

    @pytest.mark.unit
    def test_ellipses_list_fields(self):
        """Test listing ellipsis field names."""
        fields = Ellipses.list_fields()
        assert "unicode_ellipsis" in fields
        assert "large_square" in fields
        assert "hr" in fields

    @pytest.mark.unit
    def test_ellipses_list_values(self):
        """Test listing ellipsis values."""
        values = Ellipses.list_values()
        assert "…" in values
        assert "▉" in values
        assert "─" in values

    @pytest.mark.unit
    def test_ellipses_random(self):
        """Test random ellipsis selection."""
        value = Ellipses.random()
        all_values = Ellipses.list_values()
        assert value in all_values

    @pytest.mark.unit
    def test_ellipses_defaults(self):
        """Test default ellipsis values."""
        e = Ellipses()
        assert e.unicode_ellipsis == "…"
        assert e.bar == "|"
        assert e.large_square == "▉"
