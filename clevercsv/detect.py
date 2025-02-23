# -*- coding: utf-8 -*-

"""
Drop-in replacement for Python Sniffer object.

Author: Gertjan van den Burg

"""

from io import StringIO

from .consistency import ConsistencyDetector
from .normal_form import detect_dialect_normal
from .read import reader


class Detector:
    """
    Detect the Dialect of CSV files with normal forms or the data consistency
    measure. This class provides a drop-in replacement for the Python dialect
    Sniffer from the standard library.

    Note
    ----
    We call the object ``Detector`` just to mark the difference in the
    implementation and avoid naming issues. You can import it as ``from ccsv
    import Sniffer`` nonetheless.

    """

    def __init__(self):
        pass

    def sniff(self, sample, delimiters=None, verbose=False):
        # Compatibility method for Python
        return self.detect(sample, delimiters=delimiters, verbose=verbose)

    def detect(
        self,
        sample,
        delimiters=None,
        verbose=False,
        method="auto",
        skip=True,
    ):
        """Detect the dialect of a CSV file

        This method detects the dialect of the CSV file using the specified
        detection method.

        Parameters
        ----------
        sample : str
            A sample of text from the CSV file. For best results and if time
            allows, use the entire contents of the CSV file as the sample.

        delimiters : Optional[Iterable[str]]
            Set of delimiters to consider for dialect detection. The potential
            dialects will be constructed by analyzing the sample and these
            delimiters. If omitted, the set of potential delimiters will be
            constructed from the sample.

        verbose : bool
            Enable verbose mode.

        method : str
            The method to use for dialect detection. Valid options are `"auto"`
            (the default), `"normal"`, or `"consistency"`. The `"auto"` option
            first attempts to detect the dialect using normal-form detection,
            and uses the consistency measure if normal-form detection is
            inconclusive. The `"normal"` method uses normal-form detection
            excllusively, and the `"consistency"` method uses the consistency
            measure exclusively.

        skip : bool
            Whether to skip potential dialects that have too low a pattern
            score in the consistency detection. See
            :func:`ConsistencyDetector.compute_consistency_scores` for more
            details.

        Returns
        -------
        dialect : Optional[SimpleDialect]
            The detected dialect. Can be `None` if dialect detection was
            inconclusive.

        """
        if method not in ("auto", "normal", "consistency"):
            raise ValueError(f"Unknown detection method: {method}")

        if method == "normal" or method == "auto":
            if verbose:
                print("Running normal form detection ...", flush=True)
            dialect = detect_dialect_normal(
                sample, delimiters=delimiters, verbose=verbose
            )
            if dialect is not None:
                self.method_ = "normal"
                return dialect

        self.method_ = "consistency"
        consistency_detector = ConsistencyDetector(skip=skip, verbose=verbose)
        if verbose:
            print("Running data consistency measure ...", flush=True)
        return consistency_detector.detect(sample, delimiters=delimiters)

    def has_header(self, sample):
        """Detect if a file has a header from a sample.

        This function is copied from CPython! The only change we've made is to
        use our dialect detection method.

        """

        # Creates a dictionary of types of data in each column. If any
        # column is of a single type (say, integers), *except* for the first
        # row, then the first row is presumed to be labels. If the type
        # can't be determined, it is assumed to be a string in which case
        # the length of the string is the determining factor: if all of the
        # rows except for the first are the same length, it's a header.
        # Finally, a 'vote' is taken at the end for each column, adding or
        # subtracting from the likelihood of the first row being a header.

        rdr = reader(StringIO(sample), self.sniff(sample))

        header = next(rdr)  # assume first row is header

        columns = len(header)
        columnTypes = {}
        for i in range(columns):
            columnTypes[i] = None

        checked = 0
        for row in rdr:
            # arbitrary number of rows to check, to keep it sane
            if checked > 20:
                break
            checked += 1

            if len(row) != columns:
                continue  # skip rows that have irregular number of columns

            for col in list(columnTypes.keys()):
                for thisType in [int, float, complex]:
                    try:
                        thisType(row[col])
                        break
                    except (ValueError, OverflowError):
                        pass
                else:
                    # fallback to length of string
                    thisType = len(row[col])

                if thisType != columnTypes[col]:
                    if columnTypes[col] is None:  # add new column type
                        columnTypes[col] = thisType
                    else:
                        # type is inconsistent, remove column from
                        # consideration
                        del columnTypes[col]

        # finally, compare results against first row and "vote"
        # on whether it's a header
        hasHeader = 0
        for col, colType in columnTypes.items():
            if isinstance(colType, int):  # it's a length
                if len(header[col]) != colType:
                    hasHeader += 1
                else:
                    hasHeader -= 1
            else:  # attempt typecast
                try:
                    colType(header[col])
                except (ValueError, TypeError):
                    hasHeader += 1
                else:
                    hasHeader -= 1

        return hasHeader > 0
