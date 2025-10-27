# Copyright (c) kerem.ai. All Rights Reserved.


def is_notebook() -> bool:
    """
    Check if the code is running in a Jupyter notebook or IPython environment.

    Returns
    -------
    bool:
        True if running in a notebook/IPython, False otherwise.
    """
    try:
        # Check if we're in IPython/Jupyter environment
        from IPython import get_ipython

        ipython = get_ipython()

        # If we have an IPython instance, check if it's a notebook
        if ipython is not None:
            # Check if we're in a notebook by looking at the class name
            if "IPKernelApp" in str(type(ipython)):
                return True
            # Alternative check for notebook environment
            if hasattr(ipython, "kernel") and ipython.kernel is not None:
                return True
        return False
    except BaseException:
        return False


__all__ = [
    "is_notebook",
]
