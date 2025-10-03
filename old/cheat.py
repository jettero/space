# coding: utf-8

from grid_world import A


def Dv(d):
    return {
        "n": (0, -1),
        "s": (0, 1),
        "e": (1, 0),
        "w": (-1, 0),
        "NE": (1, -1),
        "NW": (-1, -1),
        "SE": (1, 1),
        "SW": (-1, 1),
    }[d]


def Pd(p, d):
    return tuple(l + r for l, r in zip(p, Dv(d)))


def dijkstra_cost(gw, cardinal_cost=1.0000000000000000, diagonal_cost=1.4142135623730951, D=A):
    if gw.s == gw.g:
        return dict()
    unvisited = set([c.pos for c in gw.R.iter_cells()])
    max_cost = diagonal_cost * len(unvisited)
    cost = {p: max_cost for p in unvisited}
    cost[gw.g] = 0
    while unvisited:
        cur = min(unvisited, key=lambda x: cost[x])
        for d in D:
            new = Pd(cur, d)
            if new in cost:
                c = cardinal_cost if len(d) == 1 else diagonal_cost
                new_cost = cost[cur] + c
                if new_cost < cost[new]:
                    cost[new] = new_cost
        unvisited.remove(cur)
    return cost


def dijkstra(gw, cardinal_cost=1.0000000000000000, diagonal_cost=1.4142135623730951, D=A):
    if gw.s == gw.g:
        return tuple()
    cost = dijkstra_cost(gw, cardinal_cost=cardinal_cost, diagonal_cost=diagonal_cost, D=D)
    cur = gw.s
    ret = list()
    while cur != gw.g:
        possible = tuple((d, Pd(cur, d)) for d in D)
        possible = tuple(x for x in possible if x[1] in cost)
        d, cur = min(possible, key=lambda x: cost[x[1]])
        ret.append(d)
    return ret
