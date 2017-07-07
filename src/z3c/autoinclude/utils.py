from __future__ import absolute_import
from __future__ import print_function
#  cargo-culted from setuptools 0.6c9's __init__.py;
#  importing setuptools is unsafe, but i can't find any
#  way to get the information that find_packages provides
#  using pkg_resources and i can't figure out a way to
#  avoid needing it.
from distutils.util import convert_path
from pkg_resources import find_distributions
from pprint import pformat

import os
import sys


class DistributionManager(object):
    def __init__(self, dist):
        self.context = dist

    def namespaceDottedNames(self):
        """Return dotted names of all namespace packages in distribution.
        """
        return namespaceDottedNames(self.context)

    def dottedNames(self):
        """Return dotted names of all relevant packages in a distribution.

        Relevant packages are those packages that are directly under the
        namespace packages in the distribution, but not the namespace packages
        themselves. If no namespace packages exist, return those packages that
        are directly in the distribution.
        """
        dist_path = self.context.location
        ns_dottednames = self.namespaceDottedNames()
        if not ns_dottednames:
            return subpackageDottedNames(dist_path)
        result = []
        for ns_dottedname in ns_dottednames:
            path = os.path.join(dist_path, *ns_dottedname.split('.'))
            subpackages = subpackageDottedNames(path, ns_dottedname)
            for subpackage in subpackages:
                if subpackage not in ns_dottednames:
                    result.append(subpackage)
        return result


class ZCMLInfo(dict):

    def __init__(self, zcml_to_look_for):
        dict.__init__(self)
        for zcml_group in zcml_to_look_for:
            self[zcml_group] = []


def subpackageDottedNames(package_path, ns_dottedname=None):
    # we do not look for subpackages in zipped eggs
    if not isUnzippedEgg(package_path):
        return []

    result = []
    for subpackage_name in os.listdir(package_path):
        full_path = os.path.join(package_path, subpackage_name)
        if isPythonPackage(full_path):
            if ns_dottedname:
                result.append('%s.%s' % (ns_dottedname, subpackage_name))
            else:
                result.append(subpackage_name)
    return sorted(result)


def isPythonPackage(path):
    if not os.path.isdir(path):
        return False
    for init_variant in ['__init__.py', '__init__.pyc', '__init__.pyo']:
        if os.path.isfile(os.path.join(path, init_variant)):
            return True
    return False


def distributionForPackage(package):
    package_dottedname = package.__name__
    return distributionForDottedName(package_dottedname)


def distributionForDottedName(package_dottedname):
    """
    This function is ugly and probably slow. It needs to be heavily
    commented, it needs narrative doctests, it needs some broad
    explanation, and it is arbitrary in some namespace cases.
    Then it needs to be profiled.
    """
    valid_dists_for_package = []
    partial_matches = []
    full_matches = []
    for path in sys.path:
        dists = find_distributions(path, True)
        for dist in dists:
            if not isUnzippedEgg(dist.location):
                continue
            ns_packages = namespaceDottedNames(dist)
            packages = find_packages(dist.location)
            # if package_dottedname in ns_packages:
            #   continue
            if package_dottedname not in packages:
                continue
            if dist.key.lower() == package_dottedname.lower():
                full_matches.append((dist, ns_packages))
            else:
                if not dist.key.lower().startswith(package_dottedname.lower()):
                    continue
                # make sure that the dottedname bla.blubb
                # matches bla.blubb.xx but not bla.blubber
                if dist.key[len(package_dottedname)] != '.':
                    continue
                partial_matches.append((dist, ns_packages))

    valid_dists_for_package = full_matches + sorted(partial_matches)

    if len(valid_dists_for_package) == 0:
        raise LookupError("No distributions found for package `%s`; are you sure it is importable?" % package_dottedname)

    if len(valid_dists_for_package) > 1:
        non_namespaced_dists = [(dist, namespace_packages)
                                for dist, namespace_packages
                                in valid_dists_for_package if len(namespace_packages) == 0]
        if len(non_namespaced_dists) == 0:
            # if we only have namespace packages at this point,
            # 'foo.bar' and 'foo.baz', while looking for 'foo', we can
            # just select the first because the choice has no effect.
            # However, if possible, we prefer to select the one that matches the package name
            # if it's the "root" namespace
            if '.' not in package_dottedname:
                for dist, _ in valid_dists_for_package:
                    if dist.project_name == package_dottedname:
                        return dist

            # Otherwise, to be deterministic (because the order depends on both sys.path
            # and `find_distributions`) we will sort them by project_name and return
            # the first value.
            valid_dists_for_package.sort(key=lambda dist_ns: dist_ns[0].project_name)

            return valid_dists_for_package[0][0]

        valid_dists_for_package = non_namespaced_dists
        # if we have packages 'foo', 'foo.bar', and 'foo.baz',
        # the correct one is 'foo'.

        # we really are in trouble if we get into a situation with more than one non-namespaced package at this point.
        error_msg = '''
Multiple distributions were found that claim to provide the `%s` package.
This is most likely because one or more of them uses `%s` as a namespace package,
but forgot to declare it in the `namespace_packages` section of its `setup.py`.
Please make any necessary adjustments and reinstall the modified distribution(s).

Distributions found: %s
'''

        assert len(non_namespaced_dists) == 1, error_msg % (
            package_dottedname, package_dottedname,
            pformat(non_namespaced_dists))

    return valid_dists_for_package[0][0]


def namespaceDottedNames(dist):
    """
    Return a list of dotted names of all namespace packages in a distribution.
    """
    try:
        ns_dottednames = list(dist.get_metadata_lines('namespace_packages.txt'))
    except IOError:
        ns_dottednames = []
    except KeyError:
        ns_dottednames = []
    return ns_dottednames


def isUnzippedEgg(path):
    """
    Check whether a filesystem path points to an unzipped egg; z3c.autoinclude
    does not support zipped eggs or python libraries that are not packaged as
    eggs. This function can be called on e.g. entries in sys.path or the
    location of a distribution object.
    """
    return os.path.isdir(path)


CACHE = {}


def find_packages(where='.', exclude=()):
    """Return a list all Python packages found within directory 'where'

    'where' should be supplied as a "cross-platform" (i.e. URL-style) path; it
    will be converted to the appropriate local path syntax.  'exclude' is a
    sequence of package names to exclude; '*' can be used as a wildcard in the
    names, such that 'foo.*' will exclude all subpackages of 'foo' (but not
    'foo' itself).
    """
    original_where = where
    if where in CACHE:
        return CACHE[where]
    out = []
    stack = [(convert_path(where), '')]
    while stack:
        where, prefix = stack.pop(0)
        os.listdir(where)
        for name in os.listdir(where):
            fn = os.path.join(where, name)
            if ('.' not in name and os.path.isdir(fn)):
                stack.append((fn, prefix + name + '.'))
                if os.path.isfile(os.path.join(fn, '__init__.py')):
                    out.append(prefix + name)
    for pat in list(exclude) + ['ez_setup']:
        from fnmatch import fnmatchcase
        out = [item for item in out if not fnmatchcase(item, pat)]
    CACHE[original_where] = out
    return out
