import logging
import os
from pkg_resources import find_distributions
from setuptools import find_packages
import sys
from zope.dottedname.resolve import resolve

log = logging.getLogger("z3c.autoinclude")

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
    return result

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
    This function is ugly and probably slow.
    It needs to be heavily commented, it needs narrative doctests, and it needs some broad explanation.
    Then it needs to be profiled.
    """
    valid_dists_for_package = []
    for path in sys.path:
        dists = find_distributions(path, True)
        for dist in dists:
            if not isUnzippedEgg(dist.location):
                continue
            packages = find_packages(dist.location) # TODO: don't use setuptools here; look for ``top_level.txt`` metadata instead
            ns_packages = namespaceDottedNames(dist)
            #if package_dottedname in ns_packages:
                #continue
            if package_dottedname not in packages:
                continue
            valid_dists_for_package.append((dist, ns_packages))
    assert valid_dists_for_package, "No distributions found for package %s." % package_dottedname
    
    if len(valid_dists_for_package) > 1:
        non_namespaced_dists = filter(lambda x: len(x[1]) is 0, valid_dists_for_package)
        if len(non_namespaced_dists) == 0:
            # if we only have namespace packages at this point, 'foo.bar' and 'foo.baz', while looking for 'foo',
            # we can just select the first because the choice has no effect
            return valid_dists_for_package[0][0]

        valid_dists_for_package = non_namespaced_dists ### if we have packages 'foo', 'foo.bar', and 'foo.baz', the correct one is 'foo'.
        assert len(non_namespaced_dists) == 1          ### we really are in trouble if we get into a situation with more than one
                                                       ### non-namespaced package at this point.

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

def debug_includes(dist, include_type, dotted_names):
    if not dotted_names:
        return
    log.debug('%s - autoinclude %s: %r', dist.project_name,
              include_type, list(dotted_names))
