import unittest

import dwave_networkx as dnx

from dwave_networkx.algorithms_extended.tests.samplers import ExactSolver


#######################################################################################
# Unit Tests
#######################################################################################

class TestPacking(unittest.TestCase):

    def test_maximum_independent_set_basic(self):
        """Runs the function on some small and simple graphs, just to make
        sure it works in basic functionality.
        """

        G = dnx.chimera_graph(1, 2, 2)
        indep_set = dnx.maximum_independent_set_dm(G, ExactSolver())
        self.set_independence_check(G, indep_set)

        G = dnx.path_graph(5)
        indep_set = dnx.maximum_independent_set_dm(G, ExactSolver())
        self.set_independence_check(G, indep_set)

        for __ in range(10):
            G = dnx.gnp_random_graph(5, .5)
            indep_set = dnx.maximum_independent_set_dm(G, ExactSolver())
            self.set_independence_check(G, indep_set)

#######################################################################################
# Helper functions
#######################################################################################

    def set_independence_check(self, G, indep_set):
        """Check that the given set of nodes are in fact nodes in the graph and
        independent of eachother (that is there are no edges between them"""
        subG = G.subgraph(indep_set)
        self.assertTrue(len(subG.edges()) == 0)