import pytest

from harvesters.access_rights_masterfile import (
    bitmap_bytes_to_str,
    bitmap_str_to_bytes,
    bitwise_and,
)

bitwise_and_params = [
    (("1010101", "1101010"), "1000000"),
    (("1101011", "1101011"), "1101011"),
    (("111000" * 3, "110001" * 3), "110000" * 3),
    (
        (
            b"\x01\x01\x00\x01\x00\x00\x01\x00\x00\x00\x00",
            b"\x01\x01\x01\x00\x00\x00\x01\x01\x00\x00\x01",
        ),
        b"\x01\x01\x00\x00\x00\x00\x01\x00\x00\x00\x00",
    ),
]


@pytest.mark.parametrize(
    "inputs, exp",
    bitwise_and_params,
)
def test_bitmap_and(inputs, exp) -> str | bytes:
    """Test the bitwise AND between two bitmaps."""

    assert bitwise_and(inputs[0], inputs[1]) == exp


@pytest.mark.parametrize(
    "inputs, err_msg, assertion",
    [
        (("1101010", "11010"), "The two bitmaps must be of the same size!", True),
        (
            (b"\x01\x01\x00\x01\x00\x00\x01", "1101010"),
            "The AND operation is not supported for this type of data, only str or bytes!",
            False,
        ),
    ],
)
def test_bitmap_and_size_error(inputs, err_msg, assertion) -> str | bytes:
    """Test whetehr the bitwise AND function correctly through its exceptions."""
    if assertion:
        with pytest.raises(AssertionError) as exc_info:
            bitwise_and(inputs[0], inputs[1])
    else:
        with pytest.raises(AttributeError) as exc_info:
            bitwise_and(inputs[0], inputs[1])

    assert str(exc_info.value) == err_msg


@pytest.mark.parametrize(
    "test_input, expected",
    [
        ("1101010", b"\x01\x01\x00\x01\x00\x01\x00"),
        (b"\x01\x01\x00\x01\x00\x01\x00", "1101010"),
    ],
)
def test_conversion(test_input, expected) -> str | bytes:
    """Test the conversion of bitmaps between byte and str formats."""

    if isinstance(test_input, bytes):
        assert bitmap_bytes_to_str(test_input) == expected
    elif isinstance(test_input, str):
        assert bitmap_str_to_bytes(test_input) == expected
    else:
        assert False
