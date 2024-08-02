import pytest

# import importlib_resources
# import pathlib

# from contextlib import ExitStack
from harvesters.access_rights_masterfile import (
    bitmap_bytes_to_str,
    bitmap_str_to_bytes,
    bitwise_and,
)


"""
def get_pkg_resource(
    file_manager: ExitStack, path: str, package: str = "text_importer"
) -> pathlib.PosixPath:
    ""Return the resource at `path` in `package`, using a context manager.

    Note:
        The context manager `file_manager` needs to be instantiated prior to
        calling this function and should be closed once the package resource
        is no longer of use.

    Args:
        file_manager (contextlib.ExitStack): Context manager.
        path (str): Path to the desired resource in given package.
        package (str, optional): Package name. Defaults to "text_importer".

    Returns:
        pathlib.PosixPath: Path to desired managed resource.
    ""
    ref = importlib_resources.files(package) / path
    return file_manager.enter_context(importlib_resources.as_file(ref))
"""

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
    "inputs, exp",
    [
        (("1101010", "11010"), None),
        ((b"\x01\x01\x00\x01\x00\x00\x01\x00\x00\x00\x00", "1101010"), None),
    ],
)
def test_bitmap_and_exceptions(inputs, exp) -> str | bytes:
    """Test the bitwise AND between two bitmaps."""
    with pytest.raises(AttributeError) as exc_info:
        m = "The AND operation is not supported for this type of data, only str or bytes!"
        raise AttributeError(m)

    assert str(exc_info.value) == m


@pytest.mark.parametrize(
    "test_input, expected",
    [
        ("1101010", b"\x01\x01\x00\x01\x00\x01\x00"),
        (b"\x01\x01\x00\x01\x00\x01\x00", "1101010"),
    ],
)
def test_conversion(test_input, expected) -> str | bytes:
    """Test the bitwise AND between two bitmaps."""

    if isinstance(test_input, bytes):
        assert bitmap_bytes_to_str(test_input) == expected
    elif isinstance(test_input, str):
        assert bitmap_str_to_bytes(test_input) == expected
    else:
        assert False
