from .response import (
    APIBadRequest,
    APIError,
    APINotFound,
    APIRequiredParameter
)

# Type Validation
def type_string(key, value):
    if value and type(value) not in (str):
        raise APIBadRequest(
            "Invalid parameter type: '{0}' must be 'string'.".format(
                key)
        )

def type_number(key, value):
    if value and type(value) not in (int, float):
        raise APIBadRequest(
            "Invalid parameter type: '{0}' must be 'integer' or 'float'.".format(
                key)
        )

def type_array(key, value):
    if value and type(value) not in (list, str):
        raise APIBadRequest(
            "Invalid parameter type: '{0}' must be an Array.".format(
                key)
        )


def type_boolean(key, value):
    if value and type(value) != bool:
        raise APIBadRequest(
            "Invalid parameter type: '{0}' must be a 'boolean'.".format(
                key)
        )


# Length Validation
def string_length(key, string, threshold_value):
    if string and len(string) > threshold_value:
        raise APIBadRequest(
            "Invalid length: '{0}' must be less than {1} characters.".format(
                key, threshold_value)
        )

def array_length(key, array, threshold_value):
    if array and len(array) > threshold_value:
        raise APIBadRequest(
            "Invalid length: '{0}' must be less than {1} elements.".format(
                key, threshold_value)
        )


# Param Validation
def parameter_required(key, data):
    if not data.get(key):
        raise APIRequiredParameter("Parameter `{0}`, is null or was not provided.".format(key))


def parameter_immutable(key, value):
    if value:
        raise APIBadRequest(
            "Immutable Parameter: '{0}'. Remove '{0}' from your request.".format(
                key
            )
        )


# Validation Utility
def validate(data, valid_inputs, required=True):
    '''Validate user inputs against possible, valid input values.
        :data (dict) user inputs
        :possible_inputs (dict) valid inputs and validation functions
            {
                'some_key': [(some_validation_func, arg1, arg2, ...)],
                'some_other_key': [...]
            }
        :required (bool) ignore, required parameter validation?
    '''
    def _apply(func_obj):
        func = func_obj[0]
        args = func_obj[1:]

        if required is False:
            try:
                func(*args)
            except APIRequiredParameter:
                pass
        else:
            func(*args)

    def _validate(key):
        for f in valid_inputs[key]:
            _apply(f)

    for key in valid_inputs.keys():
        _validate(key)

    return data
