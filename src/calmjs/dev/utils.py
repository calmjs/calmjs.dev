# -*- coding: utf-8 -*-
import os
from itertools import chain


# keys that are needed by various platforms for successful launching of
# graphical browsers:

_GUI_EXEC_KEYS = [
    # due to broken karma-plugins implementation, HOME is a required
    # environment variable (as often times they are joined with path
    # fragments without checking if they are undefined).  Reference:
    # <https://github.com/karma-runner/karma-firefox-launcher/pull/58>
    'HOME',
    # Linux and other posix based system with X11
    'DISPLAY',
    # Windows
    'PROGRAMW6432', 'PROGRAMFILES(X86)', 'PROGRAMFILES',
]


def extract_gui_environ_keys(keys=_GUI_EXEC_KEYS):
    return {key: os.environ[key] for key in keys if key in os.environ}


def get_toolchain_targets_keys(
        toolchain, include_targets_from=(), exclude_targets_from=('bundled',)):
    """
    Derive the keys that a toolchain instance will assign to Spec
    instances that are passed into it for the paths that it wrote to the
    build directory.  This will be acquired from the ``compile_entries``
    attribute and be joined with its ``targetpath_suffix`` attribute.

    Get the write_keys assigned to a given instance of

    Arguments:

    toolchain
        A given Toolchain instance
    include_targets_from
        A list of targets to include from.  The value is a list of key
        prefixes that should be acquired from the toolchain's
        compile_entries.  Leave empty to select all.
    exclude_targets_from
        The list of targets to exclude.  Will be applied after the
        includes.
    """

    all_pfx = (entry[2] for entry in toolchain.compile_entries)
    return (
        (p + toolchain.targetpath_suffix) for p in (
            include_targets_from if include_targets_from else all_pfx)
        if p not in exclude_targets_from
    )


def get_targets_from_spec(spec, spec_keys):
    """
    Used in conjunction with the output from get_toolchain_targets_keys,
    to pull the actual file targets from a given spec.
    """

    return chain.from_iterable(spec.get(key, {}).values() for key in spec_keys)
