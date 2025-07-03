# By Jake Vanderplas (2013) <jakevdp@cs.washington.edu>
# written for the scikit-learn project
# License: BSD

import numpy as np
cimport numpy as np
np.import_array()  # required in order to use C-API


# First, define a function to get an ndarray from a memory buffer
cdef extern from "arrayobject.h":
    object PyArray_SimpleNewFromData(int nd, np.npy_intp* dims,
                                     int typenum, void* data)


cdef inline np.ndarray _buffer_to_ndarray(const DTYPE_t* x, np.npy_intp n):
    # Wrap a memory buffer with an ndarray. Warning: this is not robust.
    # In particular, if x is deallocated before the returned array goes
    # out of scope, this could cause memory errors.  Since there is not
    # a possibility of this for our use-case, this should be safe.

    # Note: this Segfaults unless np.import_array() is called above
    return PyArray_SimpleNewFromData(1, &n, DTYPECODE, <void*>x)


# some handy constants
from libc.math cimport fabs, sqrt, exp, pow, cos, sin, asin
cdef DTYPE_t INF = np.inf

from ..utils._typedefs cimport DTYPE_t, ITYPE_t, DITYPE_t, DTYPECODE
from ..utils._typedefs import DTYPE, ITYPE
from ..utils._readonly_array_wrapper import ReadonlyArrayWrapper
from ..utils import check_array

######################################################################
# newObj function
#  this is a helper function for pickling
def newObj(obj):
    return obj.__new__(obj)


######################################################################
# metric mappings
#  These map from metric id strings to class names
METRIC_MAPPING = {'euclidean': EuclideanDistance,
                  'l2': EuclideanDistance,
                  'minkowski': MinkowskiDistance,
                  'p': MinkowskiDistance,
                  'manhattan': ManhattanDistance,
                  'cityblock': ManhattanDistance,
                  'l1': ManhattanDistance,
                  'chebyshev': ChebyshevDistance,
                  'infinity': ChebyshevDistance,
                  'seuclidean': SEuclideanDistance,
                  'mahalanobis': MahalanobisDistance,
                  'wminkowski': WMinkowskiDistance,
                  'hamming': HammingDistance,
                  'canberra': CanberraDistance,
                  'braycurtis': BrayCurtisDistance,
                  'matching': MatchingDistance,
                  'jaccard': JaccardDistance,
                  'dice': DiceDistance,
                  'kulsinski': KulsinskiDistance,
                  'rogerstanimoto': RogersTanimotoDistance,
                  'russellrao': RussellRaoDistance,
                  'sokalmichener': SokalMichenerDistance,
                  'sokalsneath': SokalSneathDistance,
                  'haversine': HaversineDistance,
                  'pyfunc': PyFuncDistance}


def get_valid_metric_ids(L):
    """Given an iterable of metric class names or class identifiers,
    return a list of metric IDs which map to those classes.

    Example:
    >>> L = get_valid_metric_ids([EuclideanDistance, 'ManhattanDistance'])
    >>> sorted(L)
    ['cityblock', 'euclidean', 'l1', 'l2', 'manhattan']
    """
    return [key for (key, val) in METRIC_MAPPING.items()
            if (val.__name__ in L) or (val in L)]


######################################################################
# Distance Metric Classes
cdef class DistanceMetric:
    """DistanceMetric class

    This class provides a uniform interface to fast distance metric
    functions.  The various metrics can be accessed via the :meth:`get_metric`
    class method and the metric string identifier (see below).

    Examples
    --------
    >>> from sklearn.metrics import DistanceMetric
    >>> dist = DistanceMetric.get_metric('euclidean')
    >>> X = [[0, 1, 2],
             [3, 4, 5]]
    >>> dist.pairwise(X)
    array([[ 0.        ,  5.19615242],
           [ 5.19615242,  0.        ]])

    Available Metrics

    The following lists the string metric identifiers and the associated
    distance metric classes:

    **Metrics intended for real-valued vector spaces:**

    ==============  ====================  ========  ===============================
    identifier      class name            args      distance function
    --------------  --------------------  --------  -------------------------------
    "euclidean"     EuclideanDistance     -         ``sqrt(sum((x - y)^2))``
    "manhattan"     ManhattanDistance     -         ``sum(|x - y|)``
    "chebyshev"     ChebyshevDistance     -         ``max(|x - y|)``
    "minkowski"     MinkowskiDistance     p, w      ``sum(w * |x - y|^p)^(1/p)``
    "wminkowski"    WMinkowskiDistance    p, w      ``sum(|w * (x - y)|^p)^(1/p)``
    "seuclidean"    SEuclideanDistance    V         ``sqrt(sum((x - y)^2 / V))``
    "mahalanobis"   MahalanobisDistance   V or VI   ``sqrt((x - y)' V^-1 (x - y))``
    ==============  ====================  ========  ===============================

    .. deprecated:: 1.1
        `WMinkowskiDistance` is deprecated in version 1.1 and will be removed in version 1.3.
        Use `MinkowskiDistance` instead. Note that in `MinkowskiDistance`, the weights are
        applied to the absolute differences already raised to the p power. This is different from
        `WMinkowskiDistance` where weights are applied to the absolute differences before raising
        to the p power. The deprecation aims to remain consistent with SciPy 1.8 convention.

    **Metrics intended for two-dimensional vector spaces:**  Note that the haversine
    distance metric requires data in the form of [latitude, longitude] and both
    inputs and outputs are in units of radians.

    ============  ==================  ===============================================================
    identifier    class name          distance function
    ------------  ------------------  ---------------------------------------------------------------
    "haversine"   HaversineDistance   ``2 arcsin(sqrt(sin^2(0.5*dx) + cos(x1)cos(x2)sin^2(0.5*dy)))``
    ============  ==================  ===============================================================


    **Metrics intended for integer-valued vector spaces:**  Though intended
    for integer-valued vectors, these are also valid metrics in the case of
    real-valued vectors.

    =============  ====================  ========================================
    identifier     class name            distance function
    -------------  --------------------  ----------------------------------------
    "hamming"      HammingDistance       ``N_unequal(x, y) / N_tot``
    "canberra"     CanberraDistance      ``sum(|x - y| / (|x| + |y|))``
    "braycurtis"   BrayCurtisDistance    ``sum(|x - y|) / (sum(|x|) + sum(|y|))``
    =============  ====================  ========================================

    **Metrics intended for boolean-valued vector spaces:**  Any nonzero entry
    is evaluated to "True".  In the listings below, the following
    abbreviations are used:

     - N  : number of dimensions
     - NTT : number of dims in which both values are True
     - NTF : number of dims in which the first value is True, second is False
     - NFT : number of dims in which the first value is False, second is True
     - NFF : number of dims in which both values are False
     - NNEQ : number of non-equal dimensions, NNEQ = NTF + NFT
     - NNZ : number of nonzero dimensions, NNZ = NTF + NFT + NTT

    =================  =======================  ===============================
    identifier         class name               distance function
    -----------------  -----------------------  -------------------------------
    "jaccard"          JaccardDistance          NNEQ / NNZ
    "matching"         MatchingDistance         NNEQ / N
    "dice"             DiceDistance             NNEQ / (NTT + NNZ)
    "kulsinski"        KulsinskiDistance        (NNEQ + N - NTT) / (NNEQ + N)
    "rogerstanimoto"   RogersTanimotoDistance   2 * NNEQ / (N + NNEQ)
    "russellrao"       RussellRaoDistance       (N - NTT) / N
    "sokalmichener"    SokalMichenerDistance    2 * NNEQ / (N + NNEQ)
    "sokalsneath"      SokalSneathDistance      NNEQ / (NNEQ + 0.5 * NTT)
    =================  =======================  ===============================

    **User-defined distance:**

    ===========    ===============    =======
    identifier     class name         args
    -----------    ---------------    -------
    "pyfunc"       PyFuncDistance     func
    ===========    ===============    =======

    Here ``func`` is a function which takes two one-dimensional numpy
    arrays, and returns a distance.  Note that in order to be used within
    the BallTree, the distance must be a true metric:
    i.e. it must satisfy the following properties

    1) Non-negativity: d(x, y) >= 0
    2) Identity: d(x, y) = 0 if and only if x == y
    3) Symmetry: d(x, y) = d(y, x)
    4) Triangle Inequality: d(x, y) + d(y, z) >= d(x, z)

    Because of the Python object overhead involved in calling the python
    function, this will be fairly slow, but it will have the same
    scaling as other distances.
    """
    def __cinit__(self):
        self.p = 2
        self.vec = np.zeros(1, dtype=DTYPE, order='c')
        self.mat = np.zeros((1, 1), dtype=DTYPE, order='c')
        self.size = 1

    def __reduce__(self):
        """
        reduce method used for pickling
        """
        return (newObj, (self.__class__,), self.__getstate__())

    def __getstate__(self):
        """
        get state for pickling
        """
        if self.__class__.__name__ == "PyFuncDistance":
            return (float(self.p), np.asarray(self.vec), np.asarray(self.mat), self.func, self.kwargs)
        return (float(self.p), np.asarray(self.vec), np.asarray(self.mat))

    def __setstate__(self, state):
        """
        set state for pickling
        """
        self.p = state[0]
        self.vec = ReadonlyArrayWrapper(state[1])
        self.mat = ReadonlyArrayWrapper(state[2])
        if self.__class__.__name__ == "PyFuncDistance":
            self.func = state[3]
            self.kwargs = state[4]
        self.size = self.vec.shape[0]

    @classmethod
    def get_metric(cls, metric, **kwargs):
        """Get the given distance metric from the string identifier.

        See the docstring of DistanceMetric for a list of available metrics.

        Parameters
        ----------
        metric : str or class name
            The distance metric to use
        **kwargs
            additional arguments will be passed to the requested metric
        """
        if isinstance(metric, DistanceMetric):
            return metric

        if callable(metric):
            return PyFuncDistance(metric, **kwargs)

        # Map the metric string ID to the metric class
        if isinstance(metric, type) and issubclass(metric, DistanceMetric):
            pass
        else:
            try:
                metric = METRIC_MAPPING[metric]
            except:
                raise ValueError("Unrecognized metric '%s'" % metric)

        # In Minkowski special cases, return more efficient methods
        if metric is MinkowskiDistance:
            p = kwargs.pop('p', 2)
            w = kwargs.pop('w', None)
            if p == 1 and w is None:
                return ManhattanDistance(**kwargs)
            elif p == 2 and w is None:
                return EuclideanDistance(**kwargs)
            elif np.isinf(p) and w is None:
                return ChebyshevDistance(**kwargs)
            else:
                return MinkowskiDistance(p, w, **kwargs)
        else:
            return metric(**kwargs)

    def __init__(self):
        if self.__class__ is DistanceMetric:
            raise NotImplementedError("DistanceMetric is an abstract class")

    def _validate_data(self, X):
        """Validate the input data.

        This should be overridden in a base class if a specific input format
        is required.
        """
        return

    cdef DTYPE_t dist(self, const DTYPE_t* x1, const DTYPE_t* x2,
                      ITYPE_t size) nogil except -1:
        """Compute the distance between vectors x1 and x2

        This should be overridden in a base class.
        """
        return -999

    cdef DTYPE_t rdist(self, const DTYPE_t* x1, const DTYPE_t* x2,
                       ITYPE_t size) nogil except -1:
        """Compute the rank-preserving surrogate distance between vectors x1 and x2.

        This can optionally be overridden in a base class.

        The rank-preserving surrogate distance is any measure that yields the same
        rank as the distance, but is more efficient to compute. For example, for the
        Euclidean metric, the surrogate distance is the squared-euclidean distance.
        """
        return self.dist(x1, x2, size)

    cdef int pdist(self, const DTYPE_t[:, ::1] X, DTYPE_t[:, ::1] D) except -1:
        """compute the pairwise distances between points in X"""
        cdef ITYPE_t i1, i2
        for i1 in range(X.shape[0]):
            for i2 in range(i1, X.shape[0]):
                D[i1, i2] = self.dist(&X[i1, 0], &X[i2, 0], X.shape[1])
                D[i2, i1] = D[i1, i2]
        return 0

    cdef int cdist(self, const DTYPE_t[:, ::1] X, const DTYPE_t[:, ::1] Y,
                   DTYPE_t[:, ::1] D) except -1:
        """compute the cross-pairwise distances between arrays X and Y"""
        cdef ITYPE_t i1, i2
        if X.shape[1] != Y.shape[1]:
            raise ValueError('X and Y must have the same second dimension')
        for i1 in range(X.shape[0]):
            for i2 in range(Y.shape[0]):
                D[i1, i2] = self.dist(&X[i1, 0], &Y[i2, 0], X.shape[1])
        return 0

    cdef DTYPE_t _rdist_to_dist(self, DTYPE_t rdist) nogil except -1:
        """Convert the rank-preserving surrogate distance to the distance"""
        return rdist

    cdef DTYPE_t _dist_to_rdist(self, DTYPE_t dist) nogil except -1:
        """Convert the distance to the rank-preserving surrogate distance"""
        return dist

    def rdist_to_dist(self, rdist):
        """Convert the rank-preserving surrogate distance to the distance.

        The surrogate distance is any measure that yields the same rank as the
        distance, but is more efficient to compute. For example, for the
        Euclidean metric, the surrogate distance is the squared-euclidean distance.

        Parameters
        ----------
        rdist : double
            Surrogate distance.

        Returns
        -------
        double
            True distance.
        """
        return rdist

    def dist_to_rdist(self, dist):
        """Convert the true distance to the rank-preserving surrogate distance.

        The surrogate distance is any measure that yields the same rank as the
        distance, but is more efficient to compute. For example, for the
        Euclidean metric, the surrogate distance is the squared-euclidean distance.

        Parameters
        ----------
        dist : double
            True distance.

        Returns
        -------
        double
            Surrogate distance.
        """
        return dist

    def pairwise(self, X, Y=None):
        """Compute the pairwise distances between X and Y

        This is a convenience routine for the sake of testing.  For many
        metrics, the utilities in scipy.spatial.distance.cdist and
        scipy.spatial.distance.pdist will be faster.

        Parameters
        ----------
        X : array-like
            Array of shape (Nx, D), representing Nx points in D dimensions.
        Y : array-like (optional)
            Array of shape (Ny, D), representing Ny points in D dimensions.
            If not specified, then Y=X.

        Returns
        -------
        dist : ndarray
            The shape (Nx, Ny) array of pairwise distances between points in
            X and Y.
        """
        cdef np.ndarray[DTYPE_t, ndim=2, mode='c'] Xarr
        cdef np.ndarray[DTYPE_t, ndim=2, mode='c'] Yarr
        cdef np.ndarray[DTYPE_t, ndim=2, mode='c'] Darr

        Xarr = np.asarray(X, dtype=DTYPE, order='C')
        self._validate_data(Xarr)
        if Y is None:
            Darr = np.zeros((Xarr.shape[0], Xarr.shape[0]),
                         dtype=DTYPE, order='C')
            self.pdist(Xarr, Darr)
        else:
            Yarr = np.asarray(Y, dtype=DTYPE, order='C')
            self._validate_data(Yarr)
            Darr = np.zeros((Xarr.shape[0], Yarr.shape[0]),
                         dtype=DTYPE, order='C')
            self.cdist(Xarr, Yarr, Darr)
        return Darr


#------------------------------------------------------------
# Euclidean Distance
#  d = sqrt(sum(x_i^2 - y_i^2))
cdef class EuclideanDistance(DistanceMetric):
    r"""Euclidean Distance metric

    .. math::
       D(x, y) = \sqrt{ \sum_i (x_i - y_i) ^ 2 }
    """
    def __init__(self):
        self.p = 2

    cdef inline DTYPE_t dist(self, const DTYPE_t* x1, const DTYPE_t* x2,
                             ITYPE_t size) nogil except -1:
        return euclidean_dist(x1, x2, size)

    cdef inline DTYPE_t rdist(self, const DTYPE_t* x1, const DTYPE_t* x2,
                              ITYPE_t size) nogil except -1:
        return euclidean_rdist(x1, x2, size)

    cdef inline DTYPE_t _rdist_to_dist(self, DTYPE_t rdist) nogil except -1:
        return sqrt(rdist)

    cdef inline DTYPE_t _dist_to_rdist(self, DTYPE_t dist) nogil except -1:
        return dist * dist

    def rdist_to_dist(self, rdist):
        return np.sqrt(rdist)

    def dist_to_rdist(self, dist):
        return dist ** 2


#------------------------------------------------------------
# SEuclidean Distance
#  d = sqrt(sum((x_i - y_i2)^2 / v_i))
cdef class SEuclideanDistance(DistanceMetric):
    r"""Standardized Euclidean Distance metric

    .. math::
       D(x, y) = \sqrt{ \sum_i \frac{ (x_i - y_i) ^ 2}{V_i} }
    """
    def __init__(self, V):
        self.vec = ReadonlyArrayWrapper(np.asarray(V, dtype=DTYPE))
        self.size = self.vec.shape[0]
        self.p = 2

    def _validate_data(self, X):
        if X.shape[1] != self.size:
            raise ValueError('SEuclidean dist: size of V does not match')

    cdef inline DTYPE_t rdist(self, const DTYPE_t* x1, const DTYPE_t* x2,
                              ITYPE_t size) nogil except -1:
        cdef DTYPE_t tmp, d=0
        cdef np.intp_t j
        for j in range(size):
            tmp = x1[j] - x2[j]
            d += tmp * tmp / self.vec[j]
        return d

    cdef inline DTYPE_t dist(self, const DTYPE_t* x1, const DTYPE_t* x2,
                             ITYPE_t size) nogil except -1:
        return sqrt(self.rdist(x1, x2, size))

    cdef inline DTYPE_t _rdist_to_dist(self, DTYPE_t rdist) nogil except -1:
        return sqrt(rdist)

    cdef inline DTYPE_t _dist_to_rdist(self, DTYPE_t dist) nogil except -1:
        return dist * dist

    def rdist_to_dist(self, rdist):
        return np.sqrt(rdist)

    def dist_to_rdist(self, dist):
        return dist ** 2


#------------------------------------------------------------
# Manhattan Distance
#  d = sum(abs(x_i - y_i))
cdef class ManhattanDistance(DistanceMetric):
    r"""Manhattan/City-block Distance metric

    .. math::
       D(x, y) = \sum_i |x_i - y_i|
    """
    def __init__(self):
        self.p = 1

    cdef inline DTYPE_t dist(self, const DTYPE_t* x1, const DTYPE_t* x2,
                             ITYPE_t size) nogil except -1:
        cdef DTYPE_t d = 0
        cdef np.intp_t j
        for j in range(size):
            d += fabs(x1[j] - x2[j])
        return d


#------------------------------------------------------------
# Chebyshev Distance
#  d = max_i(abs(x_i - y_i))
cdef class ChebyshevDistance(DistanceMetric):
    """Chebyshev/Infinity Distance

    .. math::
       D(x, y) = max_i (|x_i - y_i|)

    Examples
    --------
    >>> from sklearn.metrics.dist_metrics import DistanceMetric
    >>> dist = DistanceMetric.get_metric('chebyshev')
    >>> X = [[0, 1, 2],
    ...      [3, 4, 5]]
    >>> Y = [[-1, 0, 1],
    ...      [3, 4, 5]]
    >>> dist.pairwise(X, Y)
    array([[1.732..., 5.196...],
           [6.928..., 0....   ]])
    """
    def __init__(self):
        self.p = INF

    cdef inline DTYPE_t dist(self, const DTYPE_t* x1, const DTYPE_t* x2,
                             ITYPE_t size) nogil except -1:
        cdef DTYPE_t d = 0
        cdef np.intp_t j
        for j in range(size):
            d = fmax(d, fabs(x1[j] - x2[j]))
        return d


#------------------------------------------------------------
# Minkowski Distance
cdef class MinkowskiDistance(DistanceMetric):
    r"""Minkowski Distance

    .. math::
        D(x, y) = {||u-v||}_p

    when w is None.

    Here is the more general expanded expression for the weighted case:

    .. math::
        D(x, y) = [\sum_i w_i *|x_i - y_i|^p] ^ (1/p)

    Parameters
    ----------
    p : int
        The order of the p-norm of the difference (see above).
    w : (N,) array-like (optional)
        The weight vector.

    Minkowski Distance requires p >= 1 and finite. For p = infinity,
    use ChebyshevDistance.
    Note that for p=1, ManhattanDistance is more efficient, and for
    p=2, EuclideanDistance is more efficient.
    """
    def __init__(self, p, w=None):
        if p < 1:
            raise ValueError("p must be greater than 1")
        elif np.isinf(p):
            raise ValueError("MinkowskiDistance requires finite p. "
                             "For p=inf, use ChebyshevDistance.")

        self.p = p
        if w is not None:
            w_array = check_array(
                w, ensure_2d=False, dtype=DTYPE, input_name="w"
            )
            if (w_array < 0).any():
                raise ValueError("w cannot contain negative weights")
            self.vec = ReadonlyArrayWrapper(w_array)
            self.size = self.vec.shape[0]
        else:
            self.vec = ReadonlyArrayWrapper(np.asarray([], dtype=DTYPE))
            self.size = 0

    def _validate_data(self, X):
        if self.size > 0 and X.shape[1] != self.size:
            raise ValueError("MinkowskiDistance: the size of w must match "
                             f"the number of features ({X.shape[1]}). "
                             f"Currently len(w)={self.size}.")

    cdef inline DTYPE_t rdist(self, const DTYPE_t* x1, const DTYPE_t* x2,
                              ITYPE_t size) nogil except -1:
        cdef DTYPE_t d=0
        cdef np.intp_t j
        cdef bint has_w = self.size > 0
        if has_w:
            for j in range(size):
                d += self.vec[j] * pow(fabs(x1[j] - x2[j]), self.p)
        else:
            for j in range(size):
                d += pow(fabs(x1[j] - x2[j]), self.p)
        return d

    cdef inline DTYPE_t dist(self, const DTYPE_t* x1, const DTYPE_t* x2,
                             ITYPE_t size) nogil except -1:
        return pow(self.rdist(x1, x2, size), 1. / self.p)

    cdef inline DTYPE_t _rdist_to_dist(self, DTYPE_t rdist) nogil except -1:
        return pow(rdist, 1. / self.p)

    cdef inline DTYPE_t _dist_to_rdist(self, DTYPE_t dist) nogil except -1:
        return pow(dist, self.p)

    def rdist_to_dist(self, rdist):
        return rdist ** (1. / self.p)

    def dist_to_rdist(self, dist):
        return dist ** self.p


#------------------------------------------------------------
# TODO: Remove in 1.3 - WMinkowskiDistance class
# W-Minkowski Distance
cdef class WMinkowskiDistance(DistanceMetric):
    r"""Weighted Minkowski Distance

    .. math::
       D(x, y) = [\sum_i |w_i * (x_i - y_i)|^p] ^ (1/p)

    Weighted Minkowski Distance requires p >= 1 and finite.

    Parameters
    ----------
    p : int
        The order of the norm of the difference :math:`{||u-v||}_p`.
    w : (N,) array-like
        The weight vector.

    """
    def __init__(self, p, w):
        from warnings import warn
        warn("WMinkowskiDistance is deprecated in version 1.1 and will be "
            "removed in version 1.3. Use MinkowskiDistance instead. Note "
            "that in MinkowskiDistance, the weights are applied to the "
            "absolute differences raised to the p power. This is different "
            "from WMinkowskiDistance where weights are applied to the "
            "absolute differences before raising to the p power. "
            "The deprecation aims to remain consistent with SciPy 1.8 "
            "convention.", FutureWarning)

        if p < 1:
            raise ValueError("p must be greater than 1")
        elif np.isinf(p):
            raise ValueError("WMinkowskiDistance requires finite p. "
                             "For p=inf, use ChebyshevDistance.")
        self.p = p
        self.vec = ReadonlyArrayWrapper(np.asarray(w, dtype=DTYPE))
        self.size = self.vec.shape[0]

    def _validate_data(self, X):
        if X.shape[1] != self.size:
            raise ValueError('WMinkowskiDistance dist: '
                             'size of w does not match')

    cdef inline DTYPE_t rdist(self, const DTYPE_t* x1, const DTYPE_t* x2,
                              ITYPE_t size) nogil except -1:
        cdef DTYPE_t d=0
        cdef np.intp_t j
        for j in range(size):
            d += pow(self.vec[j] * fabs(x1[j] - x2[j]), self.p)
        return d

    cdef inline DTYPE_t dist(self, const DTYPE_t* x1, const DTYPE_t* x2,
                             ITYPE_t size) nogil except -1:
        return pow(self.rdist(x1, x2, size), 1. / self.p)

    cdef inline DTYPE_t _rdist_to_dist(self, DTYPE_t rdist) nogil except -1:
        return pow(rdist, 1. / self.p)

    cdef inline DTYPE_t _dist_to_rdist(self, DTYPE_t dist) nogil except -1:
        return pow(dist, self.p)

    def rdist_to_dist(self, rdist):
        return rdist ** (1. / self.p)

    def dist_to_rdist(self, dist):
        return dist ** self.p


#------------------------------------------------------------
# Mahalanobis Distance
#  d = sqrt( (x - y)^T V^-1 (x - y) )
cdef class MahalanobisDistance(DistanceMetric):
    """Mahalanobis Distance

    .. math::
       D(x, y) = \sqrt{ (x - y)^T V^{-1} (x - y) }

    Parameters
    ----------
    V : array-like
        Symmetric positive-definite covariance matrix.
        The inverse of this matrix will be explicitly computed.
    VI : array-like
        optionally specify the inverse directly.  If VI is passed,
        then V is not referenced.
    """
    def __init__(self, V=None, VI=None):
        if VI is None:
            if V is None:
                raise ValueError("Must provide either V or VI "
                                 "for Mahalanobis distance")
            VI = np.linalg.inv(V)
        if VI.ndim != 2 or VI.shape[0] != VI.shape[1]:
            raise ValueError("V/VI must be square")

        self.mat = ReadonlyArrayWrapper(np.asarray(VI, dtype=float, order='C'))

        self.size = self.mat.shape[0]

        # we need vec as a work buffer
        self.vec = np.zeros(self.size, dtype=DTYPE)

    def _validate_data(self, X):
        if X.shape[1] != self.size:
            raise ValueError('Mahalanobis dist: size of V does not match')

    cdef inline DTYPE_t rdist(self, const DTYPE_t* x1, const DTYPE_t* x2,
                              ITYPE_t size) nogil except -1:
        cdef DTYPE_t tmp, d = 0
        cdef np.intp_t i, j

        # compute (x1 - x2).T * VI * (x1 - x2)
        for i in range(size):
            self.vec[i] = x1[i] - x2[i]

        for i in range(size):
            tmp = 0
            for j in range(size):
                tmp += self.mat[i, j] * self.vec[j]
            d += tmp * self.vec[i]
        return d

    cdef inline DTYPE_t dist(self, const DTYPE_t* x1, const DTYPE_t* x2,
                             ITYPE_t size) nogil except -1:
        return sqrt(self.rdist(x1, x2, size))

    cdef inline DTYPE_t _rdist_to_dist(self, DTYPE_t rdist) nogil except -1:
        return sqrt(rdist)

    cdef inline DTYPE_t _dist_to_rdist(self, DTYPE_t dist) nogil except -1:
        return dist * dist

    def rdist_to_dist(self, rdist):
        return np.sqrt(rdist)

    def dist_to_rdist(self, dist):
        return dist ** 2


#------------------------------------------------------------
# Hamming Distance
#  d = N_unequal(x, y) / N_tot
cdef class HammingDistance(DistanceMetric):
    r"""Hamming Distance

    Hamming distance is meant for discrete-valued vectors, though it is
    a valid metric for real-valued vectors.

    .. math::
       D(x, y) = \frac{1}{N} \sum_i \delta_{x_i, y_i}
    """
    cdef inline DTYPE_t dist(self, const DTYPE_t* x1, const DTYPE_t* x2,
                             ITYPE_t size) nogil except -1:
        cdef int n_unequal = 0
        cdef np.intp_t j
        for j in range(size):
            if x1[j] != x2[j]:
                n_unequal += 1
        return float(n_unequal) / size


#------------------------------------------------------------
# Canberra Distance
#  D(x, y) = sum[ abs(x_i - y_i) / (abs(x_i) + abs(y_i)) ]
cdef class CanberraDistance(DistanceMetric):
    r"""Canberra Distance

    Canberra distance is meant for discrete-valued vectors, though it is
    a valid metric for real-valued vectors.

    .. math::
       D(x, y) = \sum_i \frac{|x_i - y_i|}{|x_i| + |y_i|}
    """
    cdef inline DTYPE_t dist(self, const DTYPE_t* x1, const DTYPE_t* x2,
                             ITYPE_t size) nogil except -1:
        cdef DTYPE_t denom, d = 0
        cdef np.intp_t j
        for j in range(size):
            denom = fabs(x1[j]) + fabs(x2[j])
            if denom > 0:
                d += fabs(x1[j] - x2[j]) / denom
        return d


#------------------------------------------------------------
# Bray-Curtis Distance
#  D(x, y) = sum[abs(x_i - y_i)] / sum[abs(x_i) + abs(y_i)]
cdef class BrayCurtisDistance(DistanceMetric):
    r"""Bray-Curtis Distance

    Bray-Curtis distance is meant for discrete-valued vectors, though it is
    a valid metric for real-valued vectors.

    .. math::
       D(x, y) = \frac{\sum_i |x_i - y_i|}{\sum_i(|x_i| + |y_i|)}
    """
    cdef inline DTYPE_t dist(self, const DTYPE_t* x1, const DTYPE_t* x2,
                             ITYPE_t size) nogil except -1:
        cdef DTYPE_t num = 0, denom = 0
        cdef np.intp_t j
        for j in range(size):
            num += fabs(x1[j] - x2[j])
            denom += fabs(x1[j]) + fabs(x2[j])
        if denom > 0:
            return num / denom
        else:
            return 0.0


#------------------------------------------------------------
# Jaccard Distance (boolean)
#  D(x, y) = N_unequal(x, y) / N_nonzero(x, y)
cdef class JaccardDistance(DistanceMetric):
    r"""Jaccard Distance

    Jaccard Distance is a dissimilarity measure for boolean-valued
    vectors. All nonzero entries will be treated as True, zero entries will
    be treated as False.

    .. math::
       D(x, y) = \frac{N_{TF} + N_{FT}}{N_{TT} + N_{TF} + N_{FT}}
    """
    cdef inline DTYPE_t dist(self, const DTYPE_t* x1, const DTYPE_t* x2,
                             ITYPE_t size) nogil except -1:
        cdef int tf1, tf2, n_eq = 0, nnz = 0
        cdef np.intp_t j
        for j in range(size):
            tf1 = x1[j] != 0
            tf2 = x2[j] != 0
            nnz += (tf1 or tf2)
            n_eq += (tf1 and tf2)
        # Based on https://github.com/scipy/scipy/pull/7373
        # When comparing two all-zero vectors, scipy>=1.2.0 jaccard metric
        # was changed to return 0, instead of nan.
        if nnz == 0:
            return 0
        return (nnz - n_eq) * 1.0 / nnz


#------------------------------------------------------------
# Matching Distance (boolean)
#  D(x, y) = n_neq / n
cdef class MatchingDistance(DistanceMetric):
    r"""Matching Distance

    Matching Distance is a dissimilarity measure for boolean-valued
    vectors. All nonzero entries will be treated as True, zero entries will
    be treated as False.

    .. math::
       D(x, y) = \frac{N_{TF} + N_{FT}}{N}
    """
    cdef inline DTYPE_t dist(self, const DTYPE_t* x1, const DTYPE_t* x2,
                             ITYPE_t size) nogil except -1:
        cdef int tf1, tf2, n_neq = 0
        cdef np.intp_t j
        for j in range(size):
            tf1 = x1[j] != 0
            tf2 = x2[j] != 0
            n_neq += (tf1 != tf2)
        return n_neq * 1. / size


#------------------------------------------------------------
# Dice Distance (boolean)
#  D(x, y) = n_neq / (2 * ntt + n_neq)
cdef class DiceDistance(DistanceMetric):
    r"""Dice Distance

    Dice Distance is a dissimilarity measure for boolean-valued
    vectors. All nonzero entries will be treated as True, zero entries will
    be treated as False.

    .. math::
       D(x, y) = \frac{N_{TF} + N_{FT}}{2 * N_{TT} + N_{TF} + N_{FT}}
    """
    cdef inline DTYPE_t dist(self, const DTYPE_t* x1, const DTYPE_t* x2,
                             ITYPE_t size) nogil except -1:
        cdef int tf1, tf2, n_neq = 0, ntt = 0
        cdef np.intp_t j
        for j in range(size):
            tf1 = x1[j] != 0
            tf2 = x2[j] != 0
            ntt += (tf1 and tf2)
            n_neq += (tf1 != tf2)
        return n_neq / (2.0 * ntt + n_neq)


#------------------------------------------------------------
# Kulsinski Distance (boolean)
#  D(x, y) = (ntf + nft - ntt + n) / (n_neq + n)
cdef class KulsinskiDistance(DistanceMetric):
    r"""Kulsinski Distance

    Kulsinski Distance is a dissimilarity measure for boolean-valued
    vectors. All nonzero entries will be treated as True, zero entries will
    be treated as False.

    .. math::
       D(x, y) = 1 - \frac{N_{TT}}{N + N_{TF} + N_{FT}}
    """
    cdef inline DTYPE_t dist(self, const DTYPE_t* x1, const DTYPE_t* x2,
                             ITYPE_t size) nogil except -1:
        cdef int tf1, tf2, ntt = 0, n_neq = 0
        cdef np.intp_t j
        for j in range(size):
            tf1 = x1[j] != 0
            tf2 = x2[j] != 0
            n_neq += (tf1 != tf2)
            ntt += (tf1 and tf2)
        return (n_neq - ntt + size) * 1.0 / (n_neq + size)


#------------------------------------------------------------
# Rogers-Tanimoto Distance (boolean)
#  D(x, y) = 2 * n_neq / (n + n_neq)
cdef class RogersTanimotoDistance(DistanceMetric):
    r"""Rogers-Tanimoto Distance

    Rogers-Tanimoto Distance is a dissimilarity measure for boolean-valued
    vectors. All nonzero entries will be treated as True, zero entries will
    be treated as False.

    .. math::
       D(x, y) = \frac{2 (N_{TF} + N_{FT})}{N + N_{TF} + N_{FT}}
    """
    cdef inline DTYPE_t dist(self, const DTYPE_t* x1, const DTYPE_t* x2,
                             ITYPE_t size) nogil except -1:
        cdef int tf1, tf2, n_neq = 0
        cdef np.intp_t j
        for j in range(size):
            tf1 = x1[j] != 0
            tf2 = x2[j] != 0
            n_neq += (tf1 != tf2)
        return (2.0 * n_neq) / (size + n_neq)


#------------------------------------------------------------
# Russell-Rao Distance (boolean)
#  D(x, y) = (n - ntt) / n
cdef class RussellRaoDistance(DistanceMetric):
    r"""Russell-Rao Distance

    Russell-Rao Distance is a dissimilarity measure for boolean-valued
    vectors. All nonzero entries will be treated as True, zero entries will
    be treated as False.

    .. math::
       D(x, y) = \frac{N - N_{TT}}{N}
    """
    cdef inline DTYPE_t dist(self, const DTYPE_t* x1, const DTYPE_t* x2,
                             ITYPE_t size) nogil except -1:
        cdef int tf1, tf2, ntt = 0
        cdef np.intp_t j
        for j in range(size):
            tf1 = x1[j] != 0
            tf2 = x2[j] != 0
            ntt += (tf1 and tf2)
        return (size - ntt) * 1. / size


#------------------------------------------------------------
# Sokal-Michener Distance (boolean)
#  D(x, y) = 2 * n_neq / (n + n_neq)
cdef class SokalMichenerDistance(DistanceMetric):
    r"""Sokal-Michener Distance

    Sokal-Michener Distance is a dissimilarity measure for boolean-valued
    vectors. All nonzero entries will be treated as True, zero entries will
    be treated as False.

    .. math::
       D(x, y) = \frac{2 (N_{TF} + N_{FT})}{N + N_{TF} + N_{FT}}
    """
    cdef inline DTYPE_t dist(self, const DTYPE_t* x1, const DTYPE_t* x2,
                             ITYPE_t size) nogil except -1:
        cdef int tf1, tf2, n_neq = 0
        cdef np.intp_t j
        for j in range(size):
            tf1 = x1[j] != 0
            tf2 = x2[j] != 0
            n_neq += (tf1 != tf2)
        return (2.0 * n_neq) / (size + n_neq)


#------------------------------------------------------------
# Sokal-Sneath Distance (boolean)
#  D(x, y) = n_neq / (0.5 * n_tt + n_neq)
cdef class SokalSneathDistance(DistanceMetric):
    r"""Sokal-Sneath Distance

    Sokal-Sneath Distance is a dissimilarity measure for boolean-valued
    vectors. All nonzero entries will be treated as True, zero entries will
    be treated as False.

    .. math::
       D(x, y) = \frac{N_{TF} + N_{FT}}{N_{TT} / 2 + N_{TF} + N_{FT}}
    """
    cdef inline DTYPE_t dist(self, const DTYPE_t* x1, const DTYPE_t* x2,
                             ITYPE_t size) nogil except -1:
        cdef int tf1, tf2, ntt = 0, n_neq = 0
        cdef np.intp_t j
        for j in range(size):
            tf1 = x1[j] != 0
            tf2 = x2[j] != 0
            n_neq += (tf1 != tf2)
            ntt += (tf1 and tf2)
        return n_neq / (0.5 * ntt + n_neq)


#------------------------------------------------------------
# Haversine Distance (2 dimensional)
#  D(x, y) = 2 arcsin{sqrt[sin^2 ((x1 - y1) / 2)
#                          + cos(x1) cos(y1) sin^2 ((x2 - y2) / 2)]}
cdef class HaversineDistance(DistanceMetric):
    """Haversine (Spherical) Distance

    The Haversine distance is the angular distance between two points on
    the surface of a sphere.  The first distance of each point is assumed
    to be the latitude, the second is the longitude, given in radians.
    The dimension of the points must be 2:

    .. math::
       D(x, y) = 2\\arcsin[\\sqrt{\\sin^2((x1 - y1) / 2)
                                + \\cos(x1)\\cos(y1)\\sin^2((x2 - y2) / 2)}]
    """

    def _validate_data(self, X):
        if X.shape[1] != 2:
            raise ValueError("Haversine distance only valid "
                             "in 2 dimensions")

    cdef inline DTYPE_t rdist(self, const DTYPE_t* x1, const DTYPE_t* x2,
                              ITYPE_t size) nogil except -1:
        cdef DTYPE_t sin_0 = sin(0.5 * (x1[0] - x2[0]))
        cdef DTYPE_t sin_1 = sin(0.5 * (x1[1] - x2[1]))
        return (sin_0 * sin_0 + cos(x1[0]) * cos(x2[0]) * sin_1 * sin_1)

    cdef inline DTYPE_t dist(self, const DTYPE_t* x1, const DTYPE_t* x2,
                             ITYPE_t size) nogil except -1:
        return 2 * asin(sqrt(self.rdist(x1, x2, size)))

    cdef inline DTYPE_t _rdist_to_dist(self, DTYPE_t rdist) nogil except -1:
        return 2 * asin(sqrt(rdist))

    cdef inline DTYPE_t _dist_to_rdist(self, DTYPE_t dist) nogil except -1:
        cdef DTYPE_t tmp = sin(0.5 * dist)
        return tmp * tmp

    def rdist_to_dist(self, rdist):
        return 2 * np.arcsin(np.sqrt(rdist))

    def dist_to_rdist(self, dist):
        tmp = np.sin(0.5 * dist)
        return tmp * tmp


#------------------------------------------------------------
# Yule Distance (boolean)
#  D(x, y) = 2 * ntf * nft / (ntt * nff + ntf * nft)
# [This is not a true metric, so we will leave it out.]
#
#cdef class YuleDistance(DistanceMetric):
#    cdef inline DTYPE_t dist(self, const DTYPE_t* x1, const DTYPE_t* x2,
#                             ITYPE_t size):
#        cdef int tf1, tf2, ntf = 0, nft = 0, ntt = 0, nff = 0
#        cdef np.intp_t j
#        for j in range(size):
#            tf1 = x1[j] != 0
#            tf2 = x2[j] != 0
#            ntt += tf1 and tf2
#            ntf += tf1 and (tf2 == 0)
#            nft += (tf1 == 0) and tf2
#        nff = size - ntt - ntf - nft
#        return (2.0 * ntf * nft) / (ntt * nff + ntf * nft)


#------------------------------------------------------------
# Cosine Distance
#  D(x, y) = dot(x, y) / (|x| * |y|)
# [This is not a true metric, so we will leave it out.]
#
#cdef class CosineDistance(DistanceMetric):
#    cdef inline DTYPE_t dist(self, const DTYPE_t* x1, const DTYPE_t* x2,
#                             ITYPE_t size):
#        cdef DTYPE_t d = 0, norm1 = 0, norm2 = 0
#        cdef np.intp_t j
#        for j in range(size):
#            d += x1[j] * x2[j]
#            norm1 += x1[j] * x1[j]
#            norm2 += x2[j] * x2[j]
#        return 1.0 - d / sqrt(norm1 * norm2)


#------------------------------------------------------------
# Correlation Distance
#  D(x, y) = dot((x - mx), (y - my)) / (|x - mx| * |y - my|)
# [This is not a true metric, so we will leave it out.]
#
#cdef class CorrelationDistance(DistanceMetric):
#    cdef inline DTYPE_t dist(self, const DTYPE_t* x1, const DTYPE_t* x2,
#                             ITYPE_t size):
#        cdef DTYPE_t mu1 = 0, mu2 = 0, x1nrm = 0, x2nrm = 0, x1Tx2 = 0
#        cdef DTYPE_t tmp1, tmp2
#
#        cdef np.intp_t i
#        for i in range(size):
#            mu1 += x1[i]
#            mu2 += x2[i]
#        mu1 /= size
#        mu2 /= size
#
#        for i in range(size):
#            tmp1 = x1[i] - mu1
#            tmp2 = x2[i] - mu2
#            x1nrm += tmp1 * tmp1
#            x2nrm += tmp2 * tmp2
#            x1Tx2 += tmp1 * tmp2
#
#        return (1. - x1Tx2) / sqrt(x1nrm * x2nrm)


#------------------------------------------------------------
# User-defined distance
#
cdef class PyFuncDistance(DistanceMetric):
    """PyFunc Distance

    A user-defined distance

    Parameters
    ----------
    func : function
        func should take two numpy arrays as input, and return a distance.
    """
    def __init__(self, func, **kwargs):
        self.func = func
        self.kwargs = kwargs

    # in cython < 0.26, GIL was required to be acquired during definition of
    # the function and inside the body of the function. This behaviour is not
    # allowed in cython >= 0.26 since it is a redundant GIL acquisition. The
    # only way to be back compatible is to inherit `dist` from the base class
    # without GIL and called an inline `_dist` which acquire GIL.
    cdef inline DTYPE_t dist(self, const DTYPE_t* x1, const DTYPE_t* x2,
                             ITYPE_t size) nogil except -1:
        return self._dist(x1, x2, size)

    cdef inline DTYPE_t _dist(self, const DTYPE_t* x1, const DTYPE_t* x2,
                              ITYPE_t size) except -1 with gil:
        cdef np.ndarray x1arr
        cdef np.ndarray x2arr
        x1arr = _buffer_to_ndarray(x1, size)
        x2arr = _buffer_to_ndarray(x2, size)
        d = self.func(x1arr, x2arr, **self.kwargs)
        try:
            # Cython generates code here that results in a TypeError
            # if d is the wrong type.
            return d
        except TypeError:
            raise TypeError("Custom distance function must accept two "
                            "vectors and return a float.")


cdef inline double fmax(double a, double b) nogil:
    return max(a, b)
