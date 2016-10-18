from phoebe.parameters import ParameterSet
from phoebe import u, c
from phoebe.backend.backends import _extract_from_bundle_by_dataset, _extract_from_bundle_by_time

import numpy as np

def photodynam(b, compute, times=[], **kwargs):
    """
    Use Josh Carter's photodynamical code (photodynam) to compute
    velocities (dynamical only), orbital positions and velocities
    (center of mass only), and light curves (assumes spherical stars).
    The code is available here:

    https://github.com/dfm/photodynam

    photodynam must be installed and available on the system in order to
    use this plugin.

    Please cite both

    * Science 4 February 2011: Vol. 331 no. 6017 pp. 562-565 DOI:10.1126/science.1201274
    * MNRAS (2012) 420 (2): 1630-1635. doi: 10.1111/j.1365-2966.2011.20151.x

    when using this code.

    Parameters that are used by this backend:

    * Compute:
        - all parameters in :func:`phoebe.parameters.compute.photodynam`

    * Orbit:
        - sma
        - ecc
        - incl
        - per0
        - long_an
        - t0_perpass

    * Star:
        - mass
        - radius

    * lc dataset:
        - pblum
        - ld_coeffs (if ld_func=='linear')

    Values that are filled by this backend:

    * lc:
        - times
        - fluxes

    * rv (dynamical only):
        - times
        - rvs

    This function will almost always be called through the bundle, using
        * :meth:`phoebe.frontend.bundle.Bundle.add_compute`
        * :meth:`phoebe.frontend.bundle.Bundle.run_compute`

    :parameter b: the :class:`phoebe.frontend.bundle.Bundle` containing the system
        and datasets
    :parameter str compute: the label of the computeoptions to use (in the bundle).
        These computeoptions must have a kind of 'photodynam'.
    :parameter **kwargs: any temporary overrides to computeoptions
    :return: a list of new synthetic :class:`phoebe.parameters.parameters.ParameterSet`s
    :raises ImportError: if the photodynam executable cannot be found or is not installed
    :raises ValueError: if pblums are invalid
    """
    # check whether photodynam is installed
    out = commands.getoutput('photodynam')
    if 'not found' in out:
        raise ImportError('photodynam executable not found')

    computeparams = b.get_compute(compute, force_ps=True)
    hier = b.get_hierarchy()

    starrefs  = hier.get_stars()
    orbitrefs = hier.get_orbits()

    infos, new_syns = _extract_from_bundle_by_dataset(b, compute=compute, times=times)

    step_size = computeparams.get_value('stepsize', **kwargs)
    orbit_error = computeparams.get_value('orbiterror', **kwargs)
    time0 = b.get_value(qualifier='t0', context='system', unit=u.d, **kwargs)

    for info in infos:
        info = info[0] # TODO: make sure this is an ok assumption

        # write the input file
        fi = open('_tmp_pd_inp', 'w')
        fi.write('{} {}\n'.format(len(starrefs), time0))
        fi.write('{} {}\n'.format(step_size, orbit_error))
        fi.write('\n')
        fi.write(' '.join([str(b.get_value('mass', component=star,
                context='component', unit=u.solMass) * c.G.to('AU3 / (Msun d2)').value)
                for star in starrefs])+'\n') # GM

        fi.write(' '.join([str(b.get_value('rpole', component=star,
                context='component', unit=u.AU))
                for star in starrefs])+'\n')

        if info['kind'] == 'lc':
            pblums = [b.get_value(qualifier='pblum', component=star,
                    context='dataset', dataset=info['dataset'])
                    for star in starrefs]  # TODO: units or unitless?
            u1s, u2s = [], []
            for star in starrefs:
                if b.get_value(qualifier='ld_func', component=star, dataset=info['dataset'], context='dataset') == 'quadratic':
                    ld_coeffs = b.get_value(qualifier='ld_coeffs', component=star, dataset=info['dataset'], context='dataset')
                else:
                    ld_coeffs = (0,0)
                    logger.warning("ld_func for {} {} must be 'quadratic' for the photodynam backend, but is not: defaulting to quadratic with coeffs of {}".format(star, info['dataset'], ld_coeffs))

                u1s.append(str(ld_coeffs[0]))
                u2s.append(str(ld_coeffs[1]))

        else:
            # we only care about the dynamics, so let's just pass dummy values
            pblums = [1 for star in starrefs]
            u1s = ['0' for star in starrefs]
            u2s = ['0' for star in starrefs]

        if -1 in pblums:
            raise ValueError('pblums must be set in order to run photodynam')

        fi.write(' '.join([str(pbl / (4*np.pi)) for pbl in pblums])+'\n')

        fi.write(' '.join(u1s)+'\n')
        fi.write(' '.join(u2s)+'\n')

        fi.write('\n')

        for orbitref in orbitrefs:
            a = b.get_value('sma', component=orbitref,
                context='component', unit=u.AU)
            e = b.get_value('ecc', component=orbitref,
                context='component')
            i = b.get_value('incl', component=orbitref,
                context='component', unit=u.rad)
            o = b.get_value('per0', component=orbitref,
                context='component', unit=u.rad)
            l = b.get_value('long_an', component=orbitref,
                context='component', unit=u.rad)

            # t0 = b.get_value('t0_perpass', component=orbitref,
                # context='component', unit=u.d)
            # period = b.get_value('period', component=orbitref,
                # context='component', unit=u.d)

            # om = 2 * np.pi * (time0 - t0) / period
            om = b.get_value('mean_anom', component=orbitref,
                             context='component', unit=u.rad)

            fi.write('{} {} {} {} {} {}\n'.format(a, e, i, o, l, om))
        fi.close()

        # write the report file
        fr = open('_tmp_pd_rep', 'w')
        # t times
        # F fluxes
        # x light-time corrected positions
        # v light-time corrected velocities
        fr.write('t F x v \n')   # TODO: don't always get all?

        for t in b.get_value('times', component=info['component'], dataset=info['dataset'], context='dataset', unit=u.d):
            fr.write('{}\n'.format(t))
        fr.close()

        # run photodynam
        cmd = 'photodynam _tmp_pd_inp _tmp_pd_rep > _tmp_pd_out'
        logger.info("running photodynam backend: '{}'".format(cmd))
        out = commands.getoutput(cmd)
        stuff = np.loadtxt('_tmp_pd_out', unpack=True)

        # parse output to fill syns
        this_syn = new_syns.filter(component=info['component'], dataset=info['dataset'])

        nbodies = len(starrefs)
        if info['kind']=='lc':
            this_syn['times'] = stuff[0] * u.d
            this_syn['fluxes'] = stuff[1] # + 1  # TODO: figure out why and actually fix the problem instead of fudging it!?!!?
        elif info['kind']=='orb':
            cind = starrefs.index(info['component'])
            this_syn['times'] = stuff[0] * u.d
            this_syn['xs'] = -1*stuff[2+(cind*3)] * u.AU
            this_syn['ys'] = -1*stuff[3+(cind*3)] * u.AU
            this_syn['zs'] = stuff[4+(cind*3)] * u.AU
            this_syn['vxs'] = -1*stuff[3*nbodies+2+(cind*3)] * u.AU/u.d
            this_syn['vys'] = -1*stuff[3*nbodies+3+(cind*3)] * u.AU/u.d
            this_syn['vzs'] = stuff[3*nbodies+4+(cind*3)] * u.AU/u.d
        elif info['kind']=='rv':
            cind = starrefs.index(info['component'])
            this_syn['times'] = stuff[0] * u.d
            this_syn['rvs'] = -stuff[3*nbodies+4+(cind*3)] * u.AU/u.d
        else:
            raise NotImplementedError("kind {} not yet supported by this backend".format(kind))

    yield new_syns