# -*- coding: utf-8 -*-
"""
Module that provides extra distribution functions
"""

from calmjs.dist import get_module_registry_dependencies


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


def get_module_default_test_registries_dependencies(
        pkg_names, registry_names, working_set=None):
    """
    For the given registry names, compute the default test registries
    and then resolve packages 'pkg_names' for modules from the located
    test registries.
    """

    result = {}
    for registry_name in registry_names:
        result.update(
            get_module_registry_dependencies(pkg_names, registry_name))

    return result
