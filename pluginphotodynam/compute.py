from phoebe.parameters import *
from phoebe import u

def photodynam(**kwargs):
    """
    Compute options for using Josh Carter's 'photodynam' code as a
    backend (must be installed).

    Generally, this will be used as an input to the kind argument in
    :meth:`phoebe.frontend.bundle.Bundle.add_compute`

    Please see :func:`phoebe.backend.backends.photodynam` for a list of sources to
    cite when using this backend.

    :parameter **kwargs: defaults for the values of any of the parameters
    :return: a :class:`phoebe.parameters.parameters.ParameterSet` of all newly
        created :class:`phoebe.parameters.parameters.Parameter`s
    """
    params = []

    params += [BoolParameter(qualifier='enabled', copy_for={'context': 'dataset', 'kind': ['LC', 'RV', 'ORB'], 'dataset': '*'}, visible_if='False', dataset='_default', value=kwargs.get('enabled', True), description='Whether to create synthetics in compute/fitting run')]

    params += [FloatParameter(qualifier='stepsize', value=kwargs.get('stepsize', 0.01), default_unit=None, description='blah')]
    params += [FloatParameter(qualifier='orbiterror', value=kwargs.get('orbiterror', 1e-20), default_unit=None, description='blah')]

    return ParameterSet(params)