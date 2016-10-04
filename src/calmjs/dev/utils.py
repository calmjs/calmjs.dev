# -*- coding: utf-8 -*-
from itertools import chain


def get_toolchain_targets_keys(
        toolchain, include_targets_from=(), exclude_targets_from=('bundled',)):
    """
    Derive the keys that a toolchain instance will assign to Spec
    instances that are passed into it for the paths that it wrote to the
    build directory.  This will be acquired from the ``compile_entries``
    attribute and be joined with its ``target_suffix`` attribute.

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
        (p + toolchain.target_suffix) for p in (
            include_targets_from if include_targets_from else all_pfx)
        if p not in exclude_targets_from
    )


def get_targets_from_spec(spec, spec_keys):
    """
    Used in conjunction with the output from get_toolchain_targets_keys,
    to pull the actual file targets from a given spec.
    """

    return chain.from_iterable(spec.get(key, {}).values() for key in spec_keys)
