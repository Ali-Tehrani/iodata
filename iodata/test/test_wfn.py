# -*- coding: utf-8 -*-
# IODATA is an input and output module for quantum chemistry.
#
# Copyright (C) 2011-2019 The IODATA Development Team
#
# This file is part of IODATA.
#
# IODATA is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 3
# of the License, or (at your option) any later version.
#
# IODATA is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>
#
# --
# pragma pylint: disable=invalid-name,no-member
"""Test iodata.wfn module."""


import numpy as np
from .common import compute_mulliken_charges, check_orthonormal
from ..wfn import load_wfn_low, get_permutation_basis, get_permutation_orbital, get_mask
from ..iodata import IOData
from ..overlap import compute_overlap
from ..utils import shells_to_nbasis

try:
    from importlib_resources import path
except ImportError:
    from importlib.resources import path

# TODO: removed density, kin, nucnuc checks


def test_load_wfn_low_he_s():
    with path('iodata.test.data', 'he_s_orbital.wfn') as fn_wfn:
        data = load_wfn_low(str(fn_wfn))
    # unpack data
    title, numbers, coordinates, centers, type_assignment = data[:5]
    exponents, mo_count, occ_num, mo_energy, coefficients, energy = data[5:]
    assert title == 'He atom - decontracted 6-31G basis set'
    assert numbers.shape == (1,)
    assert numbers == [2]
    assert coordinates.shape == (1, 3)
    assert (coordinates == [0.00, 0.00, 0.00]).all()
    assert centers.shape == (4,)
    assert (centers == [0, 0, 0, 0]).all()
    assert type_assignment.shape == (4,)
    assert (type_assignment == [1, 1, 1, 1]).all()
    assert exponents.shape == (4,)
    assert (exponents == [0.3842163E+02, 0.5778030E+01, 0.1241774E+01, 0.2979640E+00]).all()
    assert mo_count.shape == (1,)
    assert mo_count == [1]
    assert occ_num.shape == (1,)
    assert occ_num == [2.0]
    assert mo_energy.shape == (1,)
    assert mo_energy == [-0.914127]
    assert coefficients.shape == (4, 1)
    expected = np.array([0.26139500E+00, 0.41084277E+00, 0.39372947E+00, 0.14762025E+00])
    assert (coefficients == expected.reshape(4, 1)).all()
    assert abs(energy - (-2.855160426155)) < 1.e-5


def test_load_wfn_low_h2o():
    with path('iodata.test.data', 'h2o_sto3g.wfn') as fn_wfn:
        data = load_wfn_low(str(fn_wfn))
    # unpack data
    title, numbers, coordinates, centers, type_assignment = data[:5]
    exponents, mo_count, occ_num, mo_energy, coefficients, energy = data[5:]
    assert title == 'H2O Optimization'
    assert numbers.shape == (3,)
    assert (numbers == np.array([8, 1, 1])).all()
    assert coordinates.shape == (3, 3)
    assert (coordinates[0] == [-4.44734101, 3.39697999, 0.00000000]).all()
    assert (coordinates[1] == [-2.58401495, 3.55136194, 0.00000000]).all()
    assert (coordinates[2] == [-4.92380519, 5.20496220, 0.00000000]).all()
    assert centers.shape == (21,)
    assert (centers[:15] == np.zeros(15, int)).all()
    assert (centers[15:] == np.array([1, 1, 1, 2, 2, 2])).all()
    assert type_assignment.shape == (21,)
    assert (type_assignment[:6] == np.ones(6)).all()
    assert (type_assignment[6:15] == np.array([2, 2, 2, 3, 3, 3, 4, 4, 4])).all()
    assert (type_assignment[15:] == np.ones(6)).all()
    assert exponents.shape == (21,)
    assert (exponents[:3] == [0.1307093E+03, 0.2380887E+02, 0.6443608E+01]).all()
    assert (exponents[5:8] == [0.3803890E+00, 0.5033151E+01, 0.1169596E+01]).all()
    assert (exponents[13:16] == [0.1169596E+01, 0.3803890E+00, 0.3425251E+01]).all()
    assert exponents[-1] == 0.1688554E+00
    assert mo_count.shape == (5,)
    assert (mo_count == [1, 2, 3, 4, 5]).all()
    assert occ_num.shape == (5,)
    assert np.sum(occ_num) == 10.0
    assert (occ_num == [2.0, 2.0, 2.0, 2.0, 2.0]).all()
    assert mo_energy.shape == (5,)
    assert (mo_energy == np.sort(mo_energy)).all()
    assert (mo_energy[:3] == [-20.251576, -1.257549, -0.593857]).all()
    assert (mo_energy[3:] == [-0.459729, -0.392617]).all()
    assert coefficients.shape == (21, 5)
    expected = [0.42273517E+01, -0.99395832E+00, 0.19183487E-11, 0.44235381E+00, -0.57941668E-14]
    assert (coefficients[0] == expected).all()
    assert coefficients[6, 2] == 0.83831599E+00
    assert coefficients[10, 3] == 0.65034846E+00
    assert coefficients[17, 1] == 0.12988055E-01
    assert coefficients[-1, 0] == -0.46610858E-03
    assert coefficients[-1, -1] == -0.33277355E-15
    assert abs(energy - (-74.965901217080)) < 1.e-6


def test_get_permutation_orbital():
    assert (get_permutation_orbital(np.array([1, 1, 1])) == [0, 1, 2]).all()
    assert (get_permutation_orbital(np.array([1, 1, 2, 3, 4])) == [0, 1, 2, 3, 4]).all()
    assert (get_permutation_orbital(np.array([2, 3, 4])) == [0, 1, 2]).all()
    assert (get_permutation_orbital(np.array([2, 2, 3, 3, 4, 4])) == [0, 2, 4, 1, 3, 5]).all()
    assign = np.array([1, 1, 2, 2, 3, 3, 4, 4, 1])
    expect = [0, 1, 2, 4, 6, 3, 5, 7, 8]
    assert (get_permutation_orbital(assign) == expect).all()
    assign = np.array([1, 5, 6, 7, 8, 9, 10, 1])
    expect = [0, 1, 2, 3, 4, 5, 6, 7]
    assert (get_permutation_orbital(assign) == expect).all()
    assign = np.array([5, 5, 6, 6, 7, 7, 8, 8, 9, 9, 10, 10])
    expect = [0, 2, 4, 6, 8, 10, 1, 3, 5, 7, 9, 11]
    assert (get_permutation_orbital(assign) == expect).all()
    assign = np.array([1, 2, 2, 3, 3, 4, 4, 5, 6, 7, 8, 9, 10])
    expect = [0, 1, 3, 5, 2, 4, 6, 7, 8, 9, 10, 11, 12]
    assert (get_permutation_orbital(assign) == expect).all()
    # f orbitals
    assign = np.array([11, 12, 13, 17, 14, 15, 18, 19, 16, 20])
    assert (get_permutation_orbital(assign) == list(range(10))).all()
    # g orbitals
    assign = np.array([23, 29, 32, 27, 22, 28, 35, 34, 26, 31, 33, 30, 25, 24, 21])
    assert (get_permutation_orbital(assign) == list(range(15))).all()
    # g orbitals
    assign = np.array([23, 29, 32, 27, 22, 28, 35, 34, 26, 31, 33, 30, 25, 24, 21])
    assert (get_permutation_orbital(assign) == list(range(15))).all()
    # h orbitals
    assert (get_permutation_orbital(np.arange(36, 57)) == list(range(21))).all()
    assign = np.array([1, 1, 11, 12, 13, 17, 14, 15, 18, 19, 16, 20])
    assert (get_permutation_orbital(assign) == list(range(12))).all()
    assign = np.array([2, 3, 4, 11, 12, 13, 17, 14, 15, 18, 19, 16, 20, 1, 1])
    assert (get_permutation_orbital(assign) == list(range(15))).all()


def test_get_permutation_basis():
    assert (get_permutation_basis(np.array([1, 1, 1])) == [0, 1, 2]).all()
    assert (get_permutation_basis(np.array([2, 2, 3, 3, 4, 4])) == [0, 2, 4, 1, 3, 5]).all()
    assert (get_permutation_basis(np.array([1, 2, 3, 4, 1])) == [0, 1, 2, 3, 4]).all()
    assert (get_permutation_basis(np.array([5, 6, 7, 8, 9, 10])) == [0, 3, 4, 1, 5, 2]).all()
    assign = np.repeat([5, 6, 7, 8, 9, 10], 2)
    expect = [0, 6, 8, 2, 10, 4, 1, 7, 9, 3, 11, 5]
    assert (get_permutation_basis(assign) == expect).all()
    assert (get_permutation_basis(np.arange(1, 11)) == [0, 1, 2, 3, 4, 7, 8, 5, 9, 6]).all()
    assign = np.array([1, 5, 6, 7, 8, 9, 10, 1])
    expect = [0, 1, 4, 5, 2, 6, 3, 7]
    assert (get_permutation_basis(assign) == expect).all()
    assign = np.array([11, 12, 13, 17, 14, 15, 18, 19, 16, 20])
    expect = [0, 4, 5, 3, 9, 6, 1, 8, 7, 2]
    assert (get_permutation_basis(assign) == expect).all()
    assign = np.array([1, 11, 12, 13, 17, 14, 15, 18, 19, 16, 20, 1])
    expect = [0, 1, 5, 6, 4, 10, 7, 2, 9, 8, 3, 11]
    assert (get_permutation_basis(assign) == expect).all()
    assign = np.array([1, 11, 12, 13, 17, 14, 15, 18, 19, 16, 20, 2, 2, 3, 3, 4, 4])
    expect = [0, 1, 5, 6, 4, 10, 7, 2, 9, 8, 3, 11, 13, 15, 12, 14, 16]
    assert (get_permutation_basis(assign) == expect).all()
    assign = [1, 11, 12, 13, 17, 14, 15, 18, 19, 16, 20, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    expect = np.array([0, 1, 5, 6, 4, 10, 7, 2, 9, 8, 3, 11, 12, 13, 14, 17, 18, 15, 19, 16])
    assert (get_permutation_basis(np.array(assign)) == expect).all()
    assert (get_permutation_basis(np.arange(36, 57)) == np.arange(21)[::-1]).all()
    assign = [23, 29, 32, 27, 22, 28, 35, 34, 26, 31, 33, 30, 25, 24, 21]
    expect = [14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0]
    assert (get_permutation_basis(np.array(assign)) == expect).all()
    assert (get_permutation_basis(np.arange(36, 57)) == list(range(21))[::-1]).all()


def test_get_mask():
    assert (get_mask(np.array([2, 3, 4])) == [True, False, False]).all()
    expected = [True, True, False, False, True, True, False, False]
    assert (get_mask(np.array([1, 2, 3, 4, 1, 2, 3, 4])) == expected).all()
    expected = [True, False, False, False, False, False]
    assert (get_mask(np.array([5, 6, 7, 8, 9, 10])) == expected).all()
    expected = [True, False, False, True, True, False, False, False, False, False]
    assert (get_mask(np.array([2, 3, 4, 1, 5, 6, 7, 8, 9, 10])) == expected).all()
    expected = [True, False, False, False, False, False, False, False, False, False]
    assert (get_mask(np.arange(11, 21)) == expected).all()
    assert (get_mask(np.array([21, 24, 25])) == [True, False, False]).all()
    assert (get_mask(np.array([11, 21, 36, 1])) == [True, True, True, True]).all()


def check_wfn(fn_wfn, nbasis, energy, expected_charges):
    with path('iodata.test.data', fn_wfn) as file_wfn:
        mol = IOData.from_file(str(file_wfn))
    assert shells_to_nbasis(mol.obasis["shell_types"]) == nbasis
    olp = compute_overlap(**mol.obasis)
    if mol.mo.type == 'restricted':
        check_orthonormal(mol.mo.coeffs, olp, 1.e-5)
    elif mol.mo.type == 'unrestricted':
        check_orthonormal(mol.mo.coeffs[:, :mol.mo.norb_a], olp, 1.e-5)
        check_orthonormal(mol.mo.coeffs[:, mol.mo.norb_a:], olp, 1.e-5)
    if energy is not None:
        assert abs(energy - mol.energy) < 1.e-5
    if expected_charges is not None:
        charges = compute_mulliken_charges(mol)
        assert (abs(expected_charges - charges) < 1e-5).all()
    return mol


def test_load_wfn_h2o_sto3g_decontracted():
    charges = np.array([-0.546656, 0.273328, 0.273328])
    check_wfn('h2o_sto3g_decontracted.wfn', 21, -75.162231674351, charges)


def test_load_wfn_h2_ccpvqz_virtual():
    mol = check_wfn('h2_ccpvqz.wfn', 74, -1.133504568400, np.array([0.0, 0.0]))

    expect = [82.64000, 12.41000, 2.824000, 0.7977000, 0.2581000]
    assert (abs(mol.obasis['alphas'][:5] - expect) < 1.e-5).all()
    expect = [-0.596838, 0.144565, 0.209605, 0.460401, 0.460401]
    assert (mol.mo.energies[:5] == expect).all()
    expect = [12.859067, 13.017471, 16.405834, 25.824716, 26.100443]
    assert (mol.mo.energies[-5:] == expect).all()
    assert (mol.mo.occs[:5] == [2.0, 0.0, 0.0, 0.0, 0.0]).all()
    assert abs(mol.mo.occs.sum() - 2.0) < 1.e-6


def test_load_wfn_h2o_sto3g():
    check_wfn('h2o_sto3g.wfn', 21, -74.96590121708, np.array([-0.330532, 0.165266, 0.165266]))


def test_load_wfn_li_sp_virtual():
    mol = check_wfn('li_sp_virtual.wfn', 8, -3.712905542719, np.array([0.0]))
    assert abs(mol.mo.occs.sum() - 3.0) < 1.e-6
    assert (mol.mo.occs[:8] == [1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]).all()
    assert (mol.mo.occs[8:] == [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]).all()
    expect = [-0.087492, -0.080310, 0.158784, 0.158784, 1.078773, 1.090891, 1.090891, 49.643670]
    assert (abs(mol.mo.energies[:8] - expect) < 1.e-6).all()
    expect = [-0.079905, 0.176681, 0.176681, 0.212494, 1.096631, 1.096631, 1.122821, 49.643827]
    assert (abs(mol.mo.energies[8:] - expect) < 1.e-6).all()
    assert mol.mo.coeffs.shape == (8, 16)


def test_load_wfn_li_sp():
    mol = check_wfn('li_sp_orbital.wfn', 8, -3.712905542719, None)
    assert mol.title == 'Li atom - using s & p orbitals'
    assert mol.mo.norb_a == 2
    assert mol.mo.norb_b == 1
    assert abs(mol.energy - (-3.712905542719)) < 1.e-5


def test_load_wfn_o2():
    mol = check_wfn('o2_uhf.wfn', 72, -149.664140769678, np.array([0.0, 0.0]))
    assert mol.mo.norb_a == 9
    assert mol.mo.norb_b == 7


def test_load_wfn_o2_virtual():
    mol = check_wfn('o2_uhf_virtual.wfn', 72, -149.664140769678, np.array([0.0, 0.0]))
    assert abs(mol.mo.occs[:mol.mo.norb_a].sum() - 9.0) < 1.e-6
    assert abs(mol.mo.occs[mol.mo.norb_a:].sum() - 7.0) < 1.e-6
    assert mol.mo.occs.shape == (88,)
    mo_occs_a = mol.mo.occs[:mol.mo.norb_a]
    assert (mo_occs_a[:9] == np.ones(9)).all()
    assert (mo_occs_a[9:] == np.zeros(35)).all()
    mo_occs_b = mol.mo.occs[mol.mo.norb_a:]
    assert (mo_occs_b[:7] == np.ones(7)).all()
    assert (mo_occs_b[7:] == np.zeros(37)).all()
    assert mol.mo.energies.shape == (88,)
    mo_energies_a = mol.mo.energies[:mol.mo.norb_a]
    assert mo_energies_a[0] == -20.752000
    assert mo_energies_a[10] == 0.179578
    assert mo_energies_a[-1] == 51.503193
    mo_energies_b = mol.mo.energies[mol.mo.norb_a:]
    assert mo_energies_b[0] == -20.697027
    assert mo_energies_b[15] == 0.322590
    assert mo_energies_b[-1] == 51.535258
    assert mol.mo.coeffs.shape == (72, 88)


def test_load_wfn_lif_fci():
    mol = check_wfn('lif_fci.wfn', 44, None, np.array([-0.645282, 0.645282]))
    assert mol.mo.occs.shape == (18,)
    assert abs(mol.mo.occs.sum() - 12.0) < 1.e-6
    assert mol.mo.occs[0] == 2.00000000
    assert mol.mo.occs[10] == 0.00128021
    assert mol.mo.occs[-1] == 0.00000054
    assert mol.mo.energies.shape == (18,)
    assert mol.mo.energies[0] == -26.09321253
    assert mol.mo.energies[15] == 1.70096290
    assert mol.mo.energies[-1] == 2.17434072
    assert mol.mo.coeffs.shape == (44, 18)
    assert abs(mol.energy - (-107.0575700853)) < 1.e-5  # FCI energy


def test_load_wfn_lih_cation_fci():
    mol = check_wfn('lih_cation_fci.wfn', 26, None, np.array([0.913206, 0.086794]))
    assert (mol.numbers == [3, 1]).all()
    assert mol.mo.occs.shape == (11,)
    assert abs(mol.mo.occs.sum() - 3.) < 1.e-6
    # assert abs(mol.mo.occs[:mol.mo.norb_a].sum() - 1.5) < 1.e-6
    assert abs(mol.energy - (-7.7214366383)) < 1.e-5  # FCI energy
