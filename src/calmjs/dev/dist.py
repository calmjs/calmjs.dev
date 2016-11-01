# -*- coding: utf-8 -*-
"""
Module that provides extra distribution functions
"""

from calmjs.dist import get_module_registry_dependencies
from calmjs.dist import TEST_REGISTRY_NAME_SUFFIX


def get_module_registries_dependencies(
        pkg_names, registry_names, working_set=None):
    """
    For given packages 'pkg_names' and registries identify by names,
    resolve the targeted locations.
    """

    result = {}
    for registry_name in registry_names:
        result.update(
            get_module_registry_dependencies(pkg_names, registry_name))

    return result


def map_registry_name_to_test(
        registry_names, test_registry_name_suffix=TEST_REGISTRY_NAME_SUFFIX):
    """
    Map a given list of registry_names to its test equivalent.
    """

    for registry_name in registry_names:
        yield registry_name + test_registry_name_suffix


def get_module_default_test_registries_dependencies(
        pkg_names, registry_names,
        test_registry_name_suffix=TEST_REGISTRY_NAME_SUFFIX,
        working_set=None):
    """
    For the given registry names, compute the default test registries
    and then resolve packages 'pkg_names' for modules from the located
    test registries.
    """

    result = {}
    for registry_name in map_registry_name_to_test(
            registry_names, test_registry_name_suffix):
        result.update(get_module_registry_dependencies(
            pkg_names, registry_name))

    return result
