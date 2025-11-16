import numpy as np

def symlog(x):
    if np.isnan(x):
        return None
    return np.sign(x) * np.log10(abs(x) + 1)

def simplify_geom(geom, tol=0.1):
    if geom is None:
        return None
    if geom.geom_type == 'Polygon':
        return geom.simplify(tol, preserve_topology=True)
    elif geom.geom_type == 'MultiPolygon':
        return type(geom)([poly.simplify(tol, preserve_topology=True) for poly in geom.geoms])
    return geom
