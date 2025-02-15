#!/usr/bin/env python3
# solvers.py ---
#
# Filename: solvers.py
# Author: Abhishek Udupa
# Created: Wed Aug 26 09:34:54 2015 (-0400)
#
#
# Copyright (c) 2015, Abhishek Udupa, University of Pennsylvania
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 3. All advertising materials mentioning features or use of this software
#    must display the following acknowledgement:
#    This product includes software developed by The University of Pennsylvania
# 4. Neither the name of the University of Pennsylvania nor the
#    names of its contributors may be used to endorse or promote products
#    derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDER ''AS IS'' AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
#

# Code:

from exprs import evaluation
from exprs import exprs
import signal
import resource
from phogs import phog

EUSOLVER_MEMORY_LIMIT = (1 << 31)

_expr_to_str = exprs.expression_to_string
_is_expr = exprs.is_expression
_get_expr_with_id = exprs.get_expr_with_id

class DuplicatePointException(Exception):
    def __init__(self, point):
        self.point = point

    def __str__(self):
        return 'Duplicate Point %s' % str([self.point[i].value_object
                                           for i in range(len(self.point))])

class Solver(object):
    def __init__(self, syn_ctx):
        self.syn_ctx = syn_ctx
        self.reset()
        self.term_solver_time = 0
        self.unifier_time = 0
        self.report_additional_info = False

    def reset(self):
        self.eval_ctx = evaluation.EvaluationContext()
        self.points = []
        self.point_set = set()

    def add_points(self, points):
        for point in points:
            if (point in self.point_set):
                raise DuplicatePointException(point)
            self.point_set.add(point)
            self.points.append(point)

    def solve(self, generator_factory, term_solver, unifier, verifier, verify_term_solve=True, num_sols=4):
        import time
        # syn_ctx = self.syn_ctx
        # spec = syn_ctx.get_specification()

        time_origin = time.process_time()
        cur_sols = 0
        solved = False
        sols = set()
        while (len(sols) < num_sols):
            # print('________________')
            # iterate until we have terms that are "sufficient"
            success = term_solver.solve()
            if not success:
                return None
            # we now have a sufficient set of terms
            # print('Term solve complete! ')
            # print([ _expr_to_str(term) for sig,term in term_solver.get_signature_to_term().items()])

            # Check term solver for completeness
            if verify_term_solve:
                cexs = verifier.verify_term_solve(list(term_solver.get_signature_to_term().values()))
            else:
                # print("NOT verifying term solve")
                cexs = None

            last_sol = None
            # print('Term solve checked!')
            if cexs is None:
                for unifier_state in unifier.unify_all():
                    # unification = next(unifier_state)
                    # print('Unification done!')
                    sol_or_cex = verifier.verify(unifier_state)
                    # print("Unified....: {}".format(sol_or_cex))
                    if _is_expr(sol_or_cex) and sol_or_cex not in sols:
                        last_sol = sol_or_cex
                        sols.add(sol_or_cex)
                        solution_found_at = time.process_time() - time_origin
                        # print('Solution Found at : {:.2f} sec ::::: {} \n'.format(solution_found_at, _expr_to_str(sol_or_cex)))
                        if self.report_additional_info:
                            yield (sol_or_cex,
                                    unifier.last_dt_size,
                                    term_solver.get_num_distinct_terms(),
                                    unifier.get_num_distinct_preds(),
                                    term_solver.get_largest_term_size_enumerated(),
                                    unifier.get_largest_pred_size_enumerated(),
                                    len(self.points))
                        else:
                            yield sol_or_cex
                        solved = True
                    elif not _is_expr(sol_or_cex):
                        # print("NOT EXPR")
                        # for cex in sol_or_cex:
                            # print('ADDING POINT:', [p.value_object for p in cex])
                        term_solver.add_points(sol_or_cex) # Term solver can add all points at once
                        unifier.add_points(sol_or_cex)
                        self.add_points(sol_or_cex)
                        generator_factory.add_points(sol_or_cex)
                    else:
                        pass
                        # print("got {} - solution set: {}".format(sol_or_cex, ["{}".format(sol) for sol in sols]))
                        # print("THIS IS AN ERROR. Make sure they solver (euphony/eusolver) will generate new unique solutions after the first is found")
                        # print("Unifier: {}".format(unifier))
                        # print("Verifier: {}".format(verifier))
                        # print("TermSolver: {}".format(term_solver))
                        # print("We fked: is_expr: {}, sols: {}".format(_is_expr(sol_or_cex), ["{}".format(sol) for sol in sols]))


                    # print('Verification done!')
            else:
                sol_or_cex = cexs

            # else:
            #     term_solver.reset_signature()

            # print('________________')


#
# solvers.py ends here
