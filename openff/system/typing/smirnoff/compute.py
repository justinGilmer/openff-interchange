import numpy as np

from ...types import UnitArray


def get_distance(a, b):
    """
    get distance between two UnitArray quantities since __array_method__ isn't implemented
    for np.linalg.norm on pint.Quantity
    """
    return np.sqrt(np.sum((b - a) ** 2))


def build_distance_matrix(system_in):
    """
    Hack to generate an n_atoms x n_atoms matrix of distances, intended only
    for use on small systems that do not need neighbor lists
    """
    positions = system_in.positions

    n_atoms = system_in.topology.n_topology_atoms

    distances = UnitArray(np.zeros((n_atoms, n_atoms)), units=system_in.positions.units)

    for i in range(n_atoms):
        for j in range(n_atoms):
            # TODO: Here may be a place to drop in the bonded exceptions, or maybe
            # it would be worth worth carrying this array and a mask
            r = get_distance(positions[i, :], positions[j, :])
            distances[i, j] = UnitArray(r.magnitude, units=r.units)

    return distances


def compute_vdw(system_in):
    """
    Compute the vdW contribution tot he potential energy function.
    This is mean to serve as a stand-in for a something more performant with a similar signature
    """
    slots = system_in.slot_smirks_map['vdW'].keys()
    term = system_in.term_collection.terms['vdW']

    distances = build_distance_matrix(system_in)

    energy = 0
    for i in slots:
        for j in slots:
            if i == j:
                continue

            r = distances[i[0], j[0]]
            sig1 = term.potentials[term.smirks_map[i]].parameters['sigma']
            eps1 = term.potentials[term.smirks_map[i]].parameters['epsilon']
            sig2 = term.potentials[term.smirks_map[j]].parameters['sigma']
            eps2 = term.potentials[term.smirks_map[j]].parameters['epsilon']

            # TODO: Encode mixing rules somewhere?
            sig = (sig1 + sig2) * 0.5
            eps = (eps1 * eps2) ** 0.5

            ener = 4 * eps * ((sig / r) ** 12 - (sig / r) ** 6)
            energy += ener

    return energy