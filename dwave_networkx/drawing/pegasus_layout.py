# Copyright 2018 D-Wave Systems Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

"""
Tools to visualize Pegasus lattices and weighted graph problems on them.
"""

import networkx as nx
from networkx import draw

from dwave_networkx.drawing.qubit_layout import draw_qubit_graph, draw_embedding, draw_yield
from dwave_networkx.generators.pegasus import pegasus_graph, pegasus_coordinates
from dwave_networkx.drawing.chimera_layout import chimera_node_placer_2d


__all__ = ['pegasus_layout',
           'draw_pegasus',
           'draw_pegasus_embedding',
           'draw_pegasus_yield',
           ]


def pegasus_layout(G, scale=1., center=None, dim=2, crosses=False):
    """Positions the nodes of graph G in a Pegasus topology.

    `NumPy <https://scipy.org>`_ is required for this function.

    Parameters
    ----------
    G : NetworkX graph
        A Pegasus graph or a subgraph of a Pegasus graph, as produced by
        the :func:`dwave_networkx.pegasus_graph` function.

    scale : float (default 1.)
        Scale factor. A setting of ``scale = 1`` fits all positions within
        [0, 1] on the x-axis and [-1, 0] on the y-axis.

    center : None or array (default None)
        Coordinates of the top left corner.

    dim : int (default 2)
        Number of dimensions. When dim > 2, all extra dimensions are
        set to 0.

    crosses: boolean (optional, default False)
        If True, :math:`K_{4,4}` subgraphs are shown in a cross
        rather than L configuration. Ignored if G is defined with
        ``nice_coordinates=True``.

    Returns
    -------
    pos : dict
        Positions as a dictionary keyed by node.

    Examples
    --------
        This example gives the positions of a Pegasus lattice of size 2.

    >>> G = dnx.pegasus_graph(2)
    >>> pos = dnx.pegasus_layout(G)

    """

    if not isinstance(G, nx.Graph) or G.graph.get("family") != "pegasus":
        raise ValueError("G must be generated by dwave_networkx.pegasus_graph")

    if G.graph.get('labels') == 'nice':
        m = 3*(G.graph['rows']-1)
        c_coords = chimera_node_placer_2d(m, m, 4, scale=scale, center=center, dim=dim)
        def xy_coords(t, y, x, u, k):
            return c_coords(3*y+2-t, 3*x+t, u, k)
        pos = {v: xy_coords(*v) for v in G.nodes()}
    else:
        xy_coords = pegasus_node_placer_2d(G, scale, center, dim, crosses=crosses)

        if G.graph.get('labels') == 'coordinate':
            pos = {v: xy_coords(*v) for v in G.nodes()}
        elif G.graph.get('data'):
            pos = {v: xy_coords(*dat['pegasus_index']) for v, dat in G.nodes(data=True)}
        else:
            m = G.graph.get('rows')
            coord = pegasus_coordinates(m)
            pos = {v: xy_coords(*coord.linear_to_pegasus(v)) for v in G.nodes()}

    return pos


def pegasus_node_placer_2d(G, scale=1., center=None, dim=2, crosses=False):
    """Generates a function to convert Pegasus indices to plottable coordinates.

    Parameters
    ----------
    G : NetworkX graph
        A Pegasus graph or a subgraph of a Pegasus graph, as produced by
        the :func:`dwave_networkx.pegasus_graph` function.

    scale : float (default 1.)
        Scale factor. A setting of ``scale = 1`` fits all positions within
        [0, 1] on the x-axis and [-1, 0] on the y-axis.

    center : None or array (default None)
        Coordinates of the top left corner.

    dim : int (default 2)
        Number of dimensions. When dim > 2, all extra dimensions are
        set to 0.

    crosses: boolean (optional, default False)
        If True, :math:`K_{4,4}` subgraphs are shown in a cross
        rather than L configuration.

    Returns
    -------
    xy_coords : function
        A function that maps a Pegasus index (u, w, k, z) in a
        Pegasus lattice to plottable x,y coordinates.

    """
    import numpy as np

    m = G.graph.get('rows')
    h_offsets = G.graph.get("horizontal_offsets")
    v_offsets = G.graph.get("vertical_offsets")
    tile_width = G.graph.get("tile")
    tile_center = tile_width / 2 - .5

    # want the enter plot to fill in [0, 1] when scale=1
    scale /= m * tile_width

    if center is None:
        center = np.zeros(dim)
    else:
        center = np.asarray(center)

    paddims = dim - 2
    if paddims < 0:
        raise ValueError("layout must have at least two dimensions")

    if len(center) != dim:
        raise ValueError("length of center coordinates must match dimension of layout")

    if crosses:
        # adjustment for crosses
        cross_shift = 2.
    else:
        cross_shift = 0.

    def _xy_coords(u, w, k, z):
        # orientation, major perpendicular offset, minor perpendicular offset, parallel offset

        if k % 2:
            p = -.1
        else:
            p = .1

        if u:
            xy = np.array([z*tile_width+h_offsets[k] + tile_center, -tile_width*w-k-p+cross_shift])
        else:
            xy = np.array([tile_width*w+k+p+cross_shift, -z*tile_width-v_offsets[k]-tile_center])

        # convention for Pegasus-lattice pictures is to invert the y-axis
        return np.hstack((xy * scale, np.zeros(paddims))) + center

    return _xy_coords


def draw_pegasus(G, crosses=False, **kwargs):
    """Draws graph G in a Pegasus topology.

    If ``linear_biases`` and/or ``quadratic_biases`` are provided, these
    are visualized on the plot.

    Parameters
    ----------
    G : NetworkX graph
        A Pegasus graph or a subgraph of a Pegasus graph, as produced by
        the :func:`dwave_networkx.pegasus_graph` function.

    linear_biases : dict (optional, default {})
        Biases as a dict, of form {node: bias, ...}, where keys are
        nodes in G and biases are numeric.

    quadratic_biases : dict (optional, default {})
        Biases as a dict, of form {edge: bias, ...}, where keys are
        edges in G and biases are numeric. Self-loop
        edges (i.e., :math:`i=j`) are treated as linear biases.

    crosses: boolean (optional, default False)
        If True, :math:`K_{4,4}` subgraphs are shown in a cross
        rather than L configuration. Ignored if G is defined with
        ``nice_coordinates=True``.

    kwargs : optional keywords
       See networkx.draw_networkx() for a description of optional keywords,
       with the exception of the ``pos`` parameter, which is not used by this
       function. If ``linear_biases`` or ``quadratic_biases`` are provided,
       any provided ``node_color`` or ``edge_color`` arguments are ignored.

    Examples
    --------
        This example plots a Pegasus graph with size parameter 2.

    >>> import networkx as nx
    >>> import dwave_networkx as dnx
    >>> import matplotlib.pyplot as plt   # doctest: +SKIP
    >>> G = dnx.pegasus_graph(2)
    >>> dnx.draw_pegasus(G)    # doctest: +SKIP
    >>> plt.show()    # doctest: +SKIP

    """

    draw_qubit_graph(G, pegasus_layout(G, crosses=crosses), **kwargs)


def draw_pegasus_embedding(G, *args, **kwargs):
    """Draws an embedding onto Pegasus graph G.

    Parameters
    ----------
    G : NetworkX graph
        A Pegasus graph or a subgraph of a Pegasus graph, as produced by
        the :func:`dwave_networkx.pegasus_graph` function.

    emb : dict
        Chains, as a dict of form {qubit: chain, ...}, where qubits are
        nodes in G and chains are iterables of qubit labels.

    embedded_graph : NetworkX graph (optional, default None)
        A graph that contains all keys of ``emb`` as nodes.  If specified,
        edges of G are considered interactions if and only if (1) they
        exist between two chains of ``emb`` and (2) their keys are connected
        by an edge in this graph. If given, only couplers between chains
        based on this graph are displayed.

    interaction_edges : list (optional, default None)
        A list of edges used as interactions. If given,
        only these couplers are displayed.

    show_labels: boolean (optional, default False)
        If True, each chain in ``emb`` is labelled with its key.

    chain_color : dict (optional, default None)
        Colors as a dict of form {node: rgba_color, ...} associated with
        each key in ``emb``, where colors are length-4 tuples of floats
        between 0 and 1 inclusive. If None, each chain is assigned a
        different color.

    unused_color : tuple (optional, default (0.9,0.9,0.9,1.0))
        Color for nodes of G that are not part of chains, and edges
        that are neither chain edges nor interactions. If None, these
        nodes and edges are not shown.

    crosses: boolean (optional, default False)
        If True, :math:`K_{4,4}` subgraphs are shown in a cross
        rather than L configuration. Ignored if G is defined with
        ``nice_coordinates=True``.

    overlapped_embedding: boolean (optional, default False)
        If True, chains in ``emb`` may overlap (contain the same vertices
        in G), and these overlaps are displayed as concentric circles.

    kwargs : optional keywords
       See networkx.draw_networkx() for a description of optional keywords,
       with the exception of the ``pos`` parameter, which is not used by this
       function. If ``linear_biases`` or ``quadratic_biases`` are provided,
       any provided ``node_color`` or ``edge_color`` arguments are ignored.
    """
    crosses = kwargs.pop("crosses", False)
    draw_embedding(G, pegasus_layout(G, crosses=crosses), *args, **kwargs)

def draw_pegasus_yield(G, **kwargs):
    """Draws the given graph G with highlighted faults, according to layout.

    Parameters
    ----------
    G : NetworkX graph
        Graph to be parsed for faults.

    unused_color : tuple or color string (optional, default (0.9,0.9,0.9,1.0))
        The color to use for nodes and edges of G which are not faults.
        If unused_color is None, these nodes and edges will not be shown at all.

    fault_color : tuple or color string (optional, default (1.0,0.0,0.0,1.0))
        A color to represent nodes absent from the graph G. Colors should be
        length-4 tuples of floats between 0 and 1 inclusive.

    fault_shape : string, optional (default='x')
        The shape of the fault nodes. Specification is as matplotlib.scatter
        marker, one of 'so^>v<dph8'.

    fault_style : string, optional (default='dashed')
        Edge fault line style (solid|dashed|dotted|dashdot)

    kwargs : optional keywords
       See networkx.draw_networkx() for a description of optional keywords,
       with the exception of the `pos` parameter which is not used by this
       function. If `linear_biases` or `quadratic_biases` are provided,
       any provided `node_color` or `edge_color` arguments are ignored.
    """
    try:
        assert(G.graph["family"] == "pegasus")
        m = G.graph['columns']
        offset_lists = (G.graph['vertical_offsets'], G.graph['horizontal_offsets'])
        coordinates = G.graph["labels"] == "coordinate"
        nice = G.graph["labels"] == "nice"
        # Can't interpret fabric_only from graph attributes
    except:
        raise ValueError("Target pegasus graph needs to have columns, rows, \
        tile, and label attributes to be able to identify faulty qubits.")


    perfect_graph = pegasus_graph(m, offset_lists=offset_lists, coordinates=coordinates, nice_coordinates=nice)

    draw_yield(G, pegasus_layout(perfect_graph), perfect_graph, **kwargs)
