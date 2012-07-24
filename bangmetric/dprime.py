"""D' (d-prime) Sensitivity Index"""

# Authors: Nicolas Pinto <nicolas.pinto@gmail.com>
#          Nicolas Poilvert <nicolas.poilvert@gmail.com>
#          Ha Hong <hahong84@gmail.com>
#
# License: BSD

__all__ = ['dprime']

import numpy as np
from scipy.stats import norm
from .utils import confusion_matrix_stats

DEFAULT_DPRIME_MODE = 'binary'


def dprime(A, B=None, mode=DEFAULT_DPRIME_MODE, max_value=np.inf,\
        min_value=-np.inf, **kwargs):
    """Computes the d-prime sensitivity index of predictions
    from various data formats.  Depending on the choice of
    `mode`, this function can take one of the following format:

    * Binary classification outputs (`mode='binary'`; default)
    * Positive and negative samples (`mode='sample'`)
    * True positive and false positive rate (`mode='rate'`)
    * Confusion matrix (`mode='confusionmat'`)

    Parameters
    ----------
    A, B:
        If `mode` is 'binary' (default):

            A: array, shape = [n_samples],
                True values, interpreted as strictly positive or not
                (i.e. converted to binary).
                Could be in {-1, +1} or {0, 1} or {False, True}.

            B: array, shape = [n_samples],
                Predicted values (real).

        If `mode` is 'sample':

            A: array-like,
                Positive sample values (e.g., raw projection values
                of the positive classifier).

            B: array-like,
                Negative sample values.

        If `mode` is 'rate':

            A: array-like, shape = [n_groupings]
                True positive rates

            B: array-like, shape = [n_groupings]
                False positive rates

        if `mode` is 'confusionmat':

            A: array-like, shape = [n_classes (true), n_classes (pred)]
                Confusion matrix, where the element M_{rc} means
                the number of times when the classifier or subject
                guesses that a test sample in the r-th class
                belongs to the c-th class.

            B: ignored

    mode: {'binary', 'sample', 'rate'}, optional
        Directs the interpretation of A and B. Default is 'binary'.

    max_value: float, optional
        Maximum possible d-prime value. Default is ``np.inf``.

    min_value: float, optional
        Minimum possible d-prime value. Default is ``-np.inf``.

    kwargs: named arguments, optional
        Passed to ``confusion_stats()`` and used only when `mode`
        is 'confusionmat'.  By assigning ``collation``,
        ``fudge_mode``, ``fudge_factor``, etc. one can
        change the behavior of d-prime computation
        (see ``confusion_stats()`` for details).

    Returns
    -------
    dp: float or array of shape = [n_groupings]
        A d-prime value or array of d-primes, where each element
        corresponds to each grouping of positives and negatives
        (when `mode` is 'rate' or 'confusionmat')

    References
    ----------
    http://en.wikipedia.org/wiki/D'
    http://en.wikipedia.org/wiki/Confusion_matrix
    """

    # -- basic checks and conversion
    if mode == 'sample':
        pos, neg = np.array(A), np.array(B)

    elif mode == 'binary':
        y_true, y_pred = A, B

        assert len(y_true) == len(y_pred)
        assert np.isfinite(y_true).all()

        y_true = np.array(y_true)
        assert y_true.ndim == 1

        y_pred = np.array(y_pred)
        assert y_pred.ndim == 1

        i_pos = y_true > 0
        i_neg = ~i_pos

        pos = y_pred[i_pos]
        neg = y_pred[i_neg]

    elif mode == 'rate':
        TPR, FPR = np.array(A), np.array(B)
        assert TPR.shape == FPR.shape

    elif mode == 'confusionmat':
        # A: confusion mat
        # row means true classes, col means predicted classes
        P, N, TP, _, FP, _ = confusion_matrix_stats(A, **kwargs)

        TPR = TP / P
        FPR = FP / N

    else:
        raise ValueError('Invalid mode')

    # -- compute d'
    if mode in ['sample', 'binary']:
        assert np.isfinite(pos).all()
        assert np.isfinite(neg).all()

        if pos.size <= 1:
            raise ValueError('Not enough positive samples'\
                    'to estimate the variance')
        if neg.size <= 1:
            raise ValueError('Not enough negative samples'\
                    'to estimate the variance')

        pos_mean = pos.mean()
        neg_mean = neg.mean()
        pos_var = pos.var(ddof=1)
        neg_var = neg.var(ddof=1)

        num = pos_mean - neg_mean
        div = np.sqrt((pos_var + neg_var) / 2.)

        dp = num / div

    else:   # mode is rate or confusionmat
        dp = norm.ppf(TPR) - norm.ppf(FPR)

    # from Dan's suggestion about clipping d' values...
    dp = np.clip(dp, min_value, max_value)

    return dp
