from __future__ import division
from builtins import str
from builtins import object
import logging
from itertools import zip_longest
from nipype.interfaces.matlab import MatlabCommand
from arcana.exception import (
    ArcanaError, ArcanaRequirementVersionException)
from .utils import split_version
import subprocess as sp
from arcana.exception import ArcanaRequirementNotSatisfiedError


logger = logging.getLogger('arcana')


class Requirement(object):
    """
    Defines a software package that is required by a processing Node, which is
    typically wrapped up in an environment module (see
    http://modules.sourceforge.net)

    Parameters
    ----------
    name : str
        Name of the package
    min_version : tuple(int|str)
        The minimum version required by the node
    max_version : tuple(int|str) | None
        The maximum version that is compatible with the Node
    version_split : function
        A function that splits the version string into major/minor/micro
        parts or equivalent
    references : list[Citation]
        A list of references that should be cited when using this software
        requirement
    website : str
        Address of the website detailing the software
    """

    def __init__(self, name, min_version, max_version=None,
                 version_split=split_version, references=None,
                 website=None):
        self._name = name.lower()
        self._min_ver = tuple(min_version)
        if max_version is not None:
            self._max_ver = tuple(max_version)
            if not self.later_or_equal_version(self._max_ver, self._min_ver):
                raise ArcanaError(
                    "Supplied max version ({}) is not greater than min "
                    " version ({})".format(self._min_ver, self._max_ver))
        else:
            self._max_ver = None
        self._version_split = version_split
        self._references = references if references is not None else []
        self._website = website

    @property
    def name(self):
        return self._name

    def __repr__(self):
        return "{} (v >= {}{})".format(
            self.name, self.min_version,
            (", v <= {}".format(self.max_version)
             if self.max_version is not None else ''))

    @property
    def min_version(self):
        return self._min_ver

    @property
    def references(self):
        return iter(self._references)

    @property
    def website(self):
        return self._website

    @property
    def max_version(self):
        return self._max_ver

    def split_version(self, version_str):
        return tuple(self._version_split(version_str))

    def best_version(self, available_versions):
        """
        Picks the latest acceptible version from the versions available

        Parameters
        ----------
        available_versions : list(str)
            List of possible versions
        """
        best = None
        for ver in available_versions:
            try:
                v_parts = self.split_version(ver)
            except ArcanaRequirementVersionException:
                continue  # Incompatible version
            if (self.later_or_equal_version(v_parts, self._min_ver) and
                (self._max_ver is None or
                 self.later_or_equal_version(self._max_ver, v_parts))):
                if best is None or self.later_or_equal_version(v_parts,
                                                               best[1]):
                    best = ver, v_parts
        if best is None:
            msg = ("Could not find version of '{}' matching requirements "
                   "> ({})"
                   .format(self.name,
                           ', '.join(str(v) for v in self._min_ver)))
            if self._max_ver is not None:
                msg += " and < ({})".format(
                    ', '.join(str(v) for v in self._max_ver))
            msg += " from available versions '{}'".format(
                "', '".join(available_versions))
            raise ArcanaRequirementVersionException(msg)
        return best[0]

    def valid_version(self, version):
        return (self.later_or_equal_version(version, self.min_version) and
                (self.max_version is None or
                 self.later_or_equal_version(self.max_version, version)))

    @classmethod
    def later_or_equal_version(cls, version, reference):
        for v_part, r_part in zip_longest(version, reference, fillvalue=0):
            if type(v_part) != type(r_part):
                raise ArcanaError(
                    "Type of version part {} (of '{}'), {}, does not match "
                    "type of reference part {}, {}".format(
                        v_part, version, type(v_part), r_part, type(r_part)))
            if v_part > r_part:
                return True
            elif v_part < r_part:
                return False
        return True

    @classmethod
    def best_requirement(cls, possible_requirements, available_modules,
                         preloaded_modules=None):
        if preloaded_modules is None:
            preloaded_modules = {}
        # If possible reqs is a singleton, wrap it in a list for
        # iterating
        if isinstance(possible_requirements, Requirement):
            possible_requirements = [possible_requirements]
        # Loop through all parameters for a given requirement and see
        # if at least one can be satisfied.
        logger.debug(
            "Searching for one of {}".format(
                ', '.join(str(r) for r in possible_requirements)))
        ver_exceptions = []  # Will hold all version error messages
        for req in possible_requirements:
            try:
                version = preloaded_modules[req.name]
                logger.debug("Found preloaded version {} of module '{}'"
                             .format(version, req.name))
                if req.valid_version(req.split_version(version)):
                    return req.name, version
                else:
                    raise ArcanaError(
                        "Incompatible module version already loaded {}/{},"
                        " (valid {}->{}) please unload before running "
                        "pipeline"
                        .format(
                            req.name, version, req.min_version,
                            (req.max_version if req.max_version is not None
                             else '')))
            except KeyError:
                try:
                    best_version = req.best_version(
                        available_modules[req.name])
                    logger.debug("Found best version '{}' of module '{}' for"
                                 " requirement {}".format(best_version,
                                                          req.name, req))
                    return req.name, best_version
                except ArcanaRequirementVersionException as e:
                    ver_exceptions.append(e)
        # If no parameters can be satisfied, otherwise raise exception with
        # combined messages from all parameters.
        raise ArcanaRequirementVersionException(
            ' and '.join(str(e) for e in ver_exceptions))


class CLIRequirement(Requirement):
    """
    Defines a software package that is available on the command line

    Parameters
    ----------
    name : str
        Name of the package
    min_version : tuple(int|str)
        The minimum version required by the node
    max_version : tuple(int|str) | None
        The maximum version that is compatible with the Node
    test_cmd : str
        The name of a command that should be available when the
        requirement is satisfied.
    version_split : function
        A function that splits the version string into major/minor/micro
        parts or equivalent
    references : list[Citation]
        A list of references that should be cited when using this software
        requirement
    """

    def __init__(self, name, min_version, test_cmd, **kwargs):
        super(CLIRequirement, self).__init__(name, min_version, **kwargs)
        self._test_cmd = test_cmd

    @property
    def satisfied(self):
        if self.test_cmd is None:
            return True  # No test available
        return sp.call(self.test_cmd, shell=True) == 127

    @property
    def test_cmd(self):
        return self._test_cmd


class MatlabRequirement(Requirement):
    """
    Defines a software package within Matlab

    Parameters
    ----------
    name : str
        Name of the package
    min_version : tuple(int|str)
        The minimum version required by the node
    max_version : tuple(int|str) | None
        The maximum version that is compatible with the Node
    test_func : str
        The name of a function that should be available when the
        requirement is satisfied.
    version_split : function
        A function that splits the version string into major/minor/micro
        parts or equivalent
    references : list[Citation]
        A list of references that should be cited when using this software
        requirement
    """

    def __init__(self, name, min_version, test_func, **kwargs):
        super(CLIRequirement, self).__init__(name, min_version, **kwargs)
        self._test_func = test_func

    @property
    def satisfied(self):
        if self.test_func is None:
            return True  # No test available
        script = (
            "try\n"
            "    {}\n"
            "catch E\n"
            "    fprintf(E.identifier);\n"
            "end\n".format(self.test_func))
        result = MatlabCommand(script=script, mfile=True).run()
        output = result.runtime.stdout
        return output != 'MATLAB:UndefinedFunction'

    @property
    def test_func(self):
        return self._test_func


class RequirementManager(object):
    """
    Checks to see if requirements are satisfiable by the current
    computing environment. Subclasses can also manage the loading and
    unloading of modules
    """

    def __eq__(self, other):
        return type(self) == type(other)

    def satisfiable(self, *requirements, **kwargs):
        """
        Checks whether the given requirements are satisfiable within the given
        execution context

        Parameter
        ---------
        requirements : list(Requirement)
            List of requirements to check whether they are satisfiable
        """
        self.load(*requirements, **kwargs)
        not_satisfied = [r for r in requirements if not r.satisfied]
        if not_satisfied:
            raise ArcanaRequirementNotSatisfiedError(
                "Could not satisfy the following requirements:\n"
                .format('\n'.join(str(r) for r in not_satisfied)))
        self.unload(*requirements, **kwargs)

    def load(self, *requirements, **kwargs):
        """
        Loads the given requirements if necessary

        Parameter
        ---------
        requirements : list(Requirement)
            List of requirements to load
        """
        pass  # Nothing is done in the basic case

    def unload(self, *requirements, **kwargs):
        """
        Unloads the given requirements if necessary

        Parameter
        ---------
        requirements : list(Requirement)
            List of requirements to unload
        """
        pass  # Nothing is done in the basic case
