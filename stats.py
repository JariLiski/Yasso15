# This file is originally in scipy.stats as stats.py
#  the content of this module is shortened for Yasso use
#
# Copyright (c) Gary Strangman.  All rights reserved
#
# Disclaimer
#
# This software is provided "as-is".  There are no expressed or implied
# warranties of any kind, including, but not limited to, the warranties
# of merchantability and fittness for a given application.  In no event
# shall Gary Strangman be liable for any direct, indirect, incidental,
# special, exemplary or consequential damages (including, but not limited
# to, loss of use, data or profits, or business interruption) however
# caused and on any theory of liability, whether in contract, strict
# liability or tort (including negligence or otherwise) arising in any way
# out of the use of this software, even if advised of the possibility of
# such damage.
#

#
# Heavily adapted for use by SciPy 2002 by Travis Oliphant
"""
stats.py module

#################################################
#######  Written by:  Gary Strangman  ###########
#################################################

A collection of basic statistical functions for python.  The function
names appear below.

 *** Some scalar functions defined here are also available in the scipy.special
     package where they work on arbitrary sized arrays. ****

Disclaimers:  The function list is obviously incomplete and, worse, the
functions are not optimized.  All functions have been tested (some more
so than others), but they are far from bulletproof.  Thus, as with any
free software, no warranty or guarantee is expressed or implied. :-)  A
few extra functions that don't appear in the list below can be found by
interested treasure-hunters.  These functions don't necessarily have
both list and array versions but were deemed useful

CENTRAL TENDENCY:  gmean    (geometric mean)
                   hmean    (harmonic mean)
                   mean
                   median
                   medianscore
                   mode

MOMENTS:  moment
          variation
          skew
          kurtosis
          normaltest (for arrays only)

ALTERED VERSIONS:  tmean
                   tvar
                   tstd
                   tsem
                   describe

FREQUENCY STATS:  freqtable
                  itemfreq
                  scoreatpercentile
                  percentileofscore
                  histogram
                  cumfreq
                  relfreq

VARIABILITY:  obrientransform
              samplevar
              samplestd
              signaltonoise (for arrays only)
              var
              std
              stderr
              sem
              z
              zs

TRIMMING FCNS:  threshold (for arrays only)
                trimboth
                trim1
                around (round all vals to 'n' decimals)

CORRELATION FCNS:  paired
                   pearsonr
                   spearmanr
                   pointbiserialr
                   kendalltau
                   linregress

INFERENTIAL STATS:  ttest_1samp
                    ttest_ind
                    ttest_rel
                    chisquare
                    ks_2samp
                    mannwhitneyu
                    ranksums
                    wilcoxon
                    kruskal
                    friedmanchisquare

PROBABILITY CALCS:  chisqprob
                    erfcc
                    zprob
                    fprob
                    betai

## Note that scipy.stats.distributions has many more statistical probability
## functions defined.


ANOVA FUNCTIONS:  f_oneway
                  f_value

SUPPORT FUNCTIONS:  ss
                    square_of_sums
                    shellsort
                    rankdata

References
----------
[CRCProbStat2000] Zwillinger, D. and Kokoska, S. _CRC Standard Probablity and
Statistics Tables and Formulae_. Chapman & Hall: New York. 2000.
"""
## CHANGE LOG:
## ===========
## since 2001-06-25 ... see scipy SVN changelog
## 05-11-29 ... fixed default axis to be 0 for consistency with scipy;
##              cleanup of redundant imports, dead code, {0,1} -> booleans
## 02-02-10 ... require Numeric, eliminate "list-only" functions
##              (only 1 set of functions now and no Dispatch class),
##              removed all references to aXXXX functions.
## 00-04-13 ... pulled all "global" statements, except from aanova()
##              added/fixed lots of documentation, removed io.py dependency
##              changed to version 0.5
## 99-11-13 ... added asign() function
## 99-11-01 ... changed version to 0.4 ... enough incremental changes now
## 99-10-25 ... added acovariance and acorrelation functions
## 99-10-10 ... fixed askew/akurtosis to avoid divide-by-zero errors
##              added aglm function (crude, but will be improved)
## 99-10-04 ... upgraded acumsum, ass, asummult, asamplevar, var, etc. to
##                   all handle lists of 'dimension's and keepdims
##              REMOVED ar0, ar2, ar3, ar4 and replaced them with around
##              reinserted fixes for abetai to avoid math overflows
## 99-09-05 ... rewrote achisqprob/aerfcc/aksprob/afprob/abetacf/abetai to
##                   handle multi-dimensional arrays (whew!)
## 99-08-30 ... fixed l/amoment, l/askew, l/akurtosis per D'Agostino (1990)
##              added anormaltest per same reference
##              re-wrote azprob to calc arrays of probs all at once
## 99-08-22 ... edited attest_ind printing section so arrays could be rounded
## 99-08-19 ... fixed amean and aharmonicmean for non-error(!) overflow on
##                   short/byte arrays (mean of #s btw 100-300 = -150??)
## 99-08-09 ... fixed asum so that the None case works for Byte arrays
## 99-08-08 ... fixed 7/3 'improvement' to handle t-calcs on N-D arrays
## 99-07-03 ... improved attest_ind, attest_rel (zero-division errortrap)
## 99-06-24 ... fixed bug(?) in attest_ind (n1=a.shape[0])
## 04/11/99 ... added asignaltonoise, athreshold functions, changed all
##                   max/min in array section to maximum/minimum,
##                   fixed square_of_sums to prevent integer overflow
## 04/10/99 ... !!! Changed function name ... sumsquared ==> square_of_sums
## 03/18/99 ... Added ar0, ar2, ar3 and ar4 rounding functions
## 02/28/99 ... Fixed aobrientransform to return an array rather than a list
## 01/15/99 ... Essentially ceased updating list-versions of functions (!!!)
## 01/13/99 ... CHANGED TO VERSION 0.3
##              fixed bug in a/lmannwhitneyu p-value calculation
## 12/31/98 ... fixed variable-name bug in ldescribe
## 12/19/98 ... fixed bug in findwithin (fcns needed pstat. prefix)
## 12/16/98 ... changed amedianscore to return float (not array) for 1 score
## 12/14/98 ... added atmin and atmax functions
##              removed umath from import line (not needed)
##              l/ageometricmean modified to reduce chance of overflows (take
##                   nth root first, then multiply)
## 12/07/98 ... added __version__variable (now 0.2)
##              removed all 'stats.' from anova() fcn
## 12/06/98 ... changed those functions (except shellsort) that altered
##                   arguments in-place ... cumsum, ranksort, ...
##              updated (and fixed some) doc-strings
## 12/01/98 ... added anova() function (requires NumPy)
##              incorporated Dispatch class
## 11/12/98 ... added functionality to amean, aharmonicmean, ageometricmean
##              added 'asum' function (added functionality to add.reduce)
##              fixed both moment and amoment (two errors)
##              changed name of skewness and askewness to skew and askew
##              fixed (a)histogram (which sometimes counted points <lowerlimit)

# Standard library imports.
import warnings
import math

# Scipy imports.
from numpy import array, asarray, dot, ma, zeros, sum
import numpy as np

# Local imports.

__all__ = ['gmean', 'hmean', 'mean', 'cmedian', 'median', 'mode',
           'tmean', 'tvar', 'tmin', 'tmax', 'tstd', 'tsem',
           'moment', 'variation', 'skew', 'kurtosis', 'describe',
           'skewtest', 'kurtosistest', 'normaltest',
           'itemfreq', 'scoreatpercentile', 'percentileofscore',
           'histogram', 'histogram2', 'cumfreq', 'relfreq',
           'obrientransform', 'samplevar', 'samplestd', 'signaltonoise',
           'var', 'std', 'stderr', 'sem', 'z', 'zs', 'zmap',
           'threshold', 'trimboth', 'trim1', 'trim_mean',
           'cov', 'corrcoef', 'f_oneway', 'pearsonr', 'spearmanr',
           'pointbiserialr', 'kendalltau', 'linregress',
           'ttest_1samp', 'ttest_ind', 'ttest_rel',
           'kstest', 'chisquare', 'ks_2samp', 'mannwhitneyu',
           'tiecorrect', 'ranksums', 'kruskal', 'friedmanchisquare',
           'zprob', 'erfc', 'chisqprob', 'ksprob', 'fprob', 'betai',
           'glm', 'f_value_wilks_lambda',
           'f_value', 'f_value_multivariate',
           'ss', 'square_of_sums',
           'fastsort', 'rankdata',
          ]


def _chk_asarray(a, axis):
    if axis is None:
        a = np.ravel(a)
        outaxis = 0
    else:
        a = np.asarray(a)
        outaxis = axis
    return a, outaxis

#######
### NAN friendly functions
########

def nanmean(x, axis=0):
    """Compute the mean over the given axis ignoring nans.

    :Parameters:
        x : ndarray
            input array
        axis : int
            axis along which the mean is computed.

    :Results:
        m : float
            the mean."""
    x, axis = _chk_asarray(x,axis)
    x = x.copy()
    Norig = x.shape[axis]
    factor = 1.0-np.sum(np.isnan(x),axis)*1.0/Norig

    x[np.isnan(x)] = 0
    return np.mean(x,axis)/factor

def nanstd(x, axis=0, bias=False):
    """Compute the standard deviation over the given axis ignoring nans

    :Parameters:
        x : ndarray
            input array
        axis : int
            axis along which the standard deviation is computed.
        bias : boolean
            If true, the biased (normalized by N) definition is used. If false,
            the unbiased is used (the default).

    :Results:
        s : float
            the standard deviation."""
    x, axis = _chk_asarray(x,axis)
    x = x.copy()
    Norig = x.shape[axis]

    Nnan = np.sum(np.isnan(x),axis)*1.0
    n = Norig - Nnan

    x[np.isnan(x)] = 0.
    m1 = np.sum(x,axis)/n

    # Kludge to subtract m1 from the correct axis
    if axis!=0:
        shape = np.arange(x.ndim).tolist()
        shape.remove(axis)
        shape.insert(0,axis)
        x = x.transpose(tuple(shape))
        d = (x-m1)**2.0
        shape = tuple(array(shape).argsort())
        d = d.transpose(shape)
    else:
        d = (x-m1)**2.0
    m2 = np.sum(d,axis)-(m1*m1)*Nnan
    if bias:
        m2c = m2 / n
    else:
        m2c = m2 / (n - 1.)
    return np.sqrt(m2c)

def _nanmedian(arr1d):  # This only works on 1d arrays
    """Private function for rank a arrays. Compute the median ignoring Nan.

    :Parameters:
        arr1d : rank 1 ndarray
            input array

    :Results:
        m : float
            the median."""
    cond = 1-np.isnan(arr1d)
    x = np.sort(np.compress(cond,arr1d,axis=-1))
    if x.size == 0:
        return np.nan
    return median(x)

def nanmedian(x, axis=0):
    """ Compute the median along the given axis ignoring nan values

    :Parameters:
        x : ndarray
            input array
        axis : int
            axis along which the median is computed.

    :Results:
        m : float
            the median."""
    x, axis = _chk_asarray(x,axis)
    x = x.copy()
    return np.apply_along_axis(_nanmedian,axis,x)


#####################################
########  CENTRAL TENDENCY  ########
#####################################

def mean(a, axis=0):
    # fixme: This seems to be redundant with numpy.mean(,axis=0) or even
    # the ndarray.mean() method.
    """Returns the arithmetic mean of m along the given dimension.

    That is: (x1 + x2 + .. + xn) / n

    Parameters
    ----------
    a : array
    axis : int or None

    Returns
    -------
    The arithmetic mean computed over a single dimension of the input array or
    all values in the array if axis=None. The return value will have a floating
    point dtype even if the input data are integers.
    """
    a, axis = _chk_asarray(a, axis)
    return a.mean(axis)

def median(a, axis=0):
    # fixme: This would be redundant with numpy.median() except that the latter
    # does not deal with arbitrary axes.
    """Returns the median of the passed array along the given axis.

    If there is an even number of entries, the mean of the
    2 middle values is returned.

    Parameters
    ----------
    a : array
    axis=0 : int

    Returns
    -------
    The median of each remaining axis, or of all of the values in the array
    if axis is None.
    """
    a, axis = _chk_asarray(a, axis)
    if axis != 0:
        a = np.rollaxis(a, axis, 0)
    return np.median(a)

def mode(a, axis=0):
    """Returns an array of the modal (most common) value in the passed array.

    If there is more than one such value, only the first is returned.
    The bin-count for the modal bins is also returned.

    Parameters
    ----------
    a : array
    axis=0 : int

    Returns
    -------
    (array of modal values, array of counts for each mode)
    """
    a, axis = _chk_asarray(a, axis)
    scores = np.unique(np.ravel(a))       # get ALL unique values
    testshape = list(a.shape)
    testshape[axis] = 1
    oldmostfreq = np.zeros(testshape)
    oldcounts = np.zeros(testshape)
    for score in scores:
        template = (a == score)
        counts = np.expand_dims(np.sum(template, axis),axis)
        mostfrequent = np.where(counts > oldcounts, score, oldmostfreq)
        oldcounts = np.maximum(counts, oldcounts)
        oldmostfreq = mostfrequent
    return mostfrequent, oldcounts

#####################################
############  MOMENTS  #############
#####################################

def moment(a, moment=1, axis=0):
    """Calculates the nth moment about the mean for a sample.

    Generally used to calculate coefficients of skewness and
    kurtosis.

    Parameters
    ----------
    a : array
    moment : int
    axis : int or None

    Returns
    -------
    The appropriate moment along the given axis or over all values if axis is
    None.
    """
    a, axis = _chk_asarray(a, axis)
    if moment == 1:
        # By definition the first moment about the mean is 0.
        shape = list(a.shape)
        del shape[axis]
        if shape:
            # return an actual array of the appropriate shape
            return np.zeros(shape, dtype=float)
        else:
            # the input was 1D, so return a scalar instead of a rank-0 array
            return np.float64(0.0)
    else:
        mn = np.expand_dims(np.mean(a,axis), axis)
        s = np.power((a-mn), moment)
        return np.mean(s, axis)


def skew(a, axis=0, bias=True):
    """Computes the skewness of a data set.

    For normally distributed data, the skewness should be about 0. A skewness
    value > 0 means that there is more weight in the left tail of the
    distribution. The function skewtest() can be used to determine if the
    skewness value is close enough to 0, statistically speaking.

    Parameters
    ----------
    a : array
    axis : int or None
    bias : bool
        If False, then the calculations are corrected for statistical bias.

    Returns
    -------
    The skewness of values along an axis, returning 0 where all values are
    equal.

    References
    ----------
    [CRCProbStat2000] section 2.2.24.1
    """
    a, axis = _chk_asarray(a,axis)
    n = a.shape[axis]
    m2 = moment(a, 2, axis)
    m3 = moment(a, 3, axis)
    zero = (m2 == 0)
    vals = np.where(zero, 0, m3 / m2**1.5)
    if not bias:
        can_correct = (n > 2) & (m2 > 0)
        if np.any(can_correct):
            m2 = np.extract(can_correct, m2)
            m3 = np.extract(can_correct, m3)
            nval = np.sqrt((n-1.0)*n)/(n-2.0)*m3/m2**1.5
            np.place(vals, can_correct, nval)
    return vals

def kurtosis(a, axis=0, fisher=True, bias=True):
    """Computes the kurtosis (Fisher or Pearson) of a dataset.

    Kurtosis is the fourth central moment divided by the square of the variance.
    If Fisher's definition is used, then 3.0 is subtracted from the result to
    give 0.0 for a normal distribution.

    If bias is False then the kurtosis is calculated using k statistics to
    eliminate bias comming from biased moment estimators

    Use kurtosistest() to see if result is close enough to normal.

    Parameters
    ----------
    a : array
    axis : int or None
    fisher : bool
        If True, Fisher's definition is used (normal ==> 0.0). If False,
        Pearson's definition is used (normal ==> 3.0).
    bias : bool
        If False, then the calculations are corrected for statistical bias.

    Returns
    -------
    The kurtosis of values along an axis, returning 0 where all values are
    equal.

    References
    ----------
    [CRCProbStat2000] section 2.2.25
    """
    a, axis = _chk_asarray(a, axis)
    n = a.shape[axis]
    m2 = moment(a,2,axis)
    m4 = moment(a,4,axis)
    zero = (m2 == 0)
    vals = np.where(zero, 0, m4/ m2**2.0)
    if not bias:
        can_correct = (n > 3) & (m2 > 0)
        if can_correct.any():
            m2 = np.extract(can_correct, m2)
            m4 = np.extract(can_correct, m4)
            nval = 1.0/(n-2)/(n-3)*((n*n-1.0)*m4/m2**2.0-3*(n-1)**2.0)
            np.place(vals, can_correct, nval+3.0)
    if fisher:
        return vals - 3
    else:
        return vals

def describe(a, axis=0):
    """Computes several descriptive statistics of the passed array.

    Parameters
    ----------
    a : array
    axis : int or None

    Returns
    -------
    (size of the data,
     (min, max),
     arithmetic mean,
     unbiased variance,
     biased skewness,
     biased kurtosis)
    """
    a, axis = _chk_asarray(a, axis)
    n = a.shape[axis]
    mm = (np.minimum.reduce(a), np.maximum.reduce(a))
    m = mean(a, axis)
    v = var(a, axis)
    sk = skew(a, axis)
    kurt = kurtosis(a, axis)
    return n, mm, m, v, sk, kurt

#####################################
######  VARIABILITY FUNCTIONS  #####
#####################################

def var(a, axis=0, bias=False):
    """
Returns the estimated population variance of the values in the passed
array (i.e., N-1).  Axis can equal None (ravel array first), or an
integer (the axis over which to operate).
"""
    a, axis = _chk_asarray(a, axis)
    mn = np.expand_dims(mean(a,axis),axis)
    deviations = a - mn
    n = a.shape[axis]
    vals = ss(deviations,axis)/(n-1.0)
    if bias:
        return vals * (n-1.0)/n
    else:
        return vals

def std(a, axis=0, bias=False):
    """
Returns the estimated population standard deviation of the values in
the passed array (i.e., N-1).  Axis can equal None (ravel array
first), or an integer (the axis over which to operate).
"""
    return np.sqrt(var(a,axis,bias))


def stderr(a, axis=0):
    """
Returns the estimated population standard error of the values in the
passed array (i.e., N-1).  Axis can equal None (ravel array
first), or an integer (the axis over which to operate).
"""
    a, axis = _chk_asarray(a, axis)
    return std(a,axis) / float(np.sqrt(a.shape[axis]))

#####################################
#######  SUPPORT FUNCTIONS  ########
#####################################

def ss(a, axis=0):
    """Squares each value in the passed array, adds these squares, and
    returns the result.

    Parameters
    ----------
    a : array
    axis : int or None

    Returns
    -------
    The sum along the given axis for (a*a).
    """
    a, axis = _chk_asarray(a, axis)
    return np.sum(a*a, axis)


