"""This demo program solves Poisson's equation

  - div grad u(x, y) = 0

on the unit square with boundary conditions given by:

  u(0, y) = 0
  v(1, y) = 42

Homogeneous Neumann boundary conditions are applied naturally on the
other two sides of the domain.

This has the analytical solution

  u(x, y) = 42*x[1]
"""
from __future__ import absolute_import, print_function, division
import pytest
import numpy as np
from firedrake import *


def run_test(x, degree, parameters={}, quadrilateral=False):
    # Create mesh and define function space
    mesh = UnitSquareMesh(2 ** x, 2 ** x, quadrilateral=quadrilateral)
    V = FunctionSpace(mesh, "CG", degree)

    # Define variational problem
    u = Function(V)
    v = TestFunction(V)
    a = dot(grad(v), grad(u)) * dx

    bcs = [DirichletBC(V, 0, 3),
           DirichletBC(V, 42, 4)]

    # Compute solution
    solve(a == 0, u, solver_parameters=parameters, bcs=bcs)

    f = Function(V)
    f.interpolate(Expression("42*x[1]"))

    return sqrt(assemble(dot(u - f, u - f) * dx))


def run_test_linear(x, degree, parameters={}, quadrilateral=False):
    # Create mesh and define function space
    mesh = UnitSquareMesh(2 ** x, 2 ** x, quadrilateral=quadrilateral)
    V = FunctionSpace(mesh, "CG", degree)

    # Define variational problem
    u = TrialFunction(V)
    v = TestFunction(V)
    a = dot(grad(v), grad(u)) * dx
    L = v*Constant(0)*dx

    bcs = [DirichletBC(V, 0, 3),
           DirichletBC(V, 42, 4)]

    # Compute solution
    u = Function(V)
    solve(a == L, u, solver_parameters=parameters, bcs=bcs)

    f = Function(V)
    f.interpolate(Expression("42*x[1]"))

    return sqrt(assemble(dot(u - f, u - f) * dx))


def run_test_preassembled(x, degree, parameters={}, quadrilateral=False):
    mesh = UnitSquareMesh(2 ** x, 2 ** x, quadrilateral=quadrilateral)
    V = FunctionSpace(mesh, "CG", degree)

    u = TrialFunction(V)
    v = TestFunction(V)
    a = dot(grad(v), grad(u)) * dx
    f = Function(V)
    f.assign(0)
    L = v*f*dx
    bcs = [DirichletBC(V, 0, 3),
           DirichletBC(V, 42, 4)]

    u = Function(V)

    A = assemble(a)
    b = assemble(L)
    for bc in bcs:
        bc.apply(A)
        bc.apply(b)
    solve(A, u, b, solver_parameters=parameters)

    expected = Function(V)
    expected.interpolate(Expression("42*x[1]"))

    method_A = sqrt(assemble(dot(u - expected, u - expected) * dx))

    A = assemble(a)
    b = assemble(L)
    solve(A, u, b, bcs=bcs, solver_parameters=parameters)
    method_B = sqrt(assemble(dot(u - expected, u - expected) * dx))

    A = assemble(a, bcs=bcs)
    b = assemble(L, bcs=bcs)
    solve(A, u, b, solver_parameters=parameters)
    method_C = sqrt(assemble(dot(u - expected, u - expected) * dx))

    A = assemble(a, bcs=bcs)
    b = assemble(L)
    solve(A, u, b, solver_parameters=parameters)
    method_D = sqrt(assemble(dot(u - expected, u - expected) * dx))

    A = assemble(a)
    b = assemble(L)
    # Don't actually need to apply the bcs to b explicitly since it's
    # done in the solve if A has any.
    for bc in bcs:
        bc.apply(A)
    solve(A, u, b, solver_parameters=parameters)
    method_E = sqrt(assemble(dot(u - expected, u - expected) * dx))

    A = assemble(a, bcs=[bcs[0]])
    b = assemble(L)
    # This will not give the right answer
    solve(A, u, b, solver_parameters=parameters)
    bcs[1].apply(A)
    b = assemble(L)
    # This will, because we reassemble using the new set of bcs
    solve(A, u, b, solver_parameters=parameters)
    method_F = sqrt(assemble(dot(u - expected, u - expected) * dx))

    return np.asarray([method_A, method_B, method_C, method_D, method_E, method_F])


@pytest.mark.parametrize(['params', 'degree', 'quadrilateral'],
                         [(p, d, q)
                          for p in [{}, {'snes_type': 'ksponly', 'ksp_type': 'preonly', 'pc_type': 'lu'}]
                          for d in (1, 2)
                          for q in [False, True]])
def test_poisson_analytic(params, degree, quadrilateral):
    assert (run_test(2, degree, parameters=params, quadrilateral=quadrilateral) < 1.e-9)


@pytest.mark.parametrize(['params', 'degree', 'quadrilateral'],
                         [(p, d, q)
                          for p in [{}, {'snes_type': 'ksponly', 'ksp_type': 'preonly', 'pc_type': 'lu'}]
                          for d in (1, 2)
                          for q in [False, True]])
def test_poisson_analytic_linear(params, degree, quadrilateral):
    assert (run_test_linear(2, degree, parameters=params, quadrilateral=quadrilateral) < 5.e-6)


@pytest.mark.parametrize(['params', 'degree', 'quadrilateral'],
                         [(p, d, q)
                          for p in [{}, {'snes_type': 'ksponly', 'ksp_type': 'preonly', 'pc_type': 'lu'}]
                          for d in (1, 2)
                          for q in [False, True]])
def test_poisson_analytic_preassembled(params, degree, quadrilateral):
    assert (run_test_preassembled(2, degree, parameters=params, quadrilateral=quadrilateral) < 5.e-6).all()


@pytest.mark.parallel(nprocs=2)
def test_poisson_analytic_linear_parallel():
    from mpi4py import MPI
    error = run_test_linear(1, 1)
    print('[%d]' % MPI.COMM_WORLD.rank, 'error:', error)
    assert error < 5e-6


if __name__ == '__main__':
    import os
    pytest.main(os.path.abspath(__file__))
