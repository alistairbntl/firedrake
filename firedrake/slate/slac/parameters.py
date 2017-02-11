from __future__ import absolute_import, print_function, division

parameters = {

    # TODO: Add documentation about the various eigen
    # parameters
    "inverse_factor": None,
    "local_solve": "colPivHouseholderQr"
}


def default_parameters():
    return parameters.copy()
