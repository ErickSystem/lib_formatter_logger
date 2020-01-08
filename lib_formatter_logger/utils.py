import json
from os import environ, path
from shutil import which

from jsonschema import Draft3Validator, ValidationError

from . import log
from .exceptions import InvalidConfig

LOG_NAME = environ.get("LOG_NAME", None)
logger = log.getLogger(LOG_NAME)

_BOOLEANS = {
    "1": True,
    "yes": True,
    "true": True,
    "on": True,
    "True": True,
    "0": False,
    "no": False,
    "false": False,
    "off": False,
    "False": False,
}


def __environ_get(env_var, t="str", default=None, dynaconf=False):
    """Internal function to get a value from an environment variable and checks its type

    Arguments:
        env_var {str} -- The environment variable to get value from

    Keyword Arguments:
        t {str} -- The environment variable value type (int|str|bool) (default: {'str'})
        default {int|str|bool} -- A default value to be returned in case of the environment
                                variable is Null (default: {None})

    Returns:
        [int|str|bool] -- The environment variable value
    """
    if dynaconf:
        if t == "int":
            try:
                value = int(default)
            except Exception:
                value = default
        elif t == "bool":
            value = _cast_boolean(default)
        else:
            value = default
    else:
        if t == "int":
            try:
                value = int(environ.get(env_var, default))
            except Exception:
                value = default
        elif t == "bool":
            value = _cast_boolean(environ.get(env_var, default))
        else:
            value = environ.get(env_var, default)

    logger.debug("{}={}".format(env_var, value))

    return value


def _cast_boolean(value):
    """
        Helper to convert string to boolean using a booleans dictionary(_BOOLEANS).
        """
    value = str(value)
    if value.lower() not in _BOOLEANS:
        raise InvalidConfig()

    return _BOOLEANS[value.lower()]


def config_validator(variables):
    """This function checks if the config is ok and ready to work
    [Deprecated] use `config` instead

    Arguments:
        variables {list} -- List of variables that must have a value

    Returns:
        bool -- Returns if configuration is valid or not
    """
    values = []

    for env_var in variables:
        try:
            name = env_var["name"]
        except Exception:
            logger.debug("Key 'name' must be defined in variables parameter")
            raise

        required = env_var.get("required", True)
        is_file = env_var.get("is_file", False)
        is_exe = env_var.get("is_exe", False)
        var_type = env_var.get("type", "str")
        default = env_var.get("default", None)
        dynaconf = env_var.get("dynaconf", False)

        if default:
            required = False

        try:
            value = __environ_get(env_var=name, t=var_type, default=default, dynaconf=dynaconf)
        except InvalidConfig:
            logger.error(
                "Configuration invalid: The following environment variable is value isn't valid: {}".format(name)
            )
            raise

        if (required) and (not value):
            logger.error("Configuration invalid: The following environment variable is required: {}".format(name))
            raise InvalidConfig()
        elif is_file:
            if not path.isfile(value):
                msg = (
                    "Configuration invalid: The following environment variable value isn't a valid "
                    + f"file or the file itself doesn't exists: {name}"
                )
                logger.error(msg)
                raise InvalidConfig()
        elif is_exe:
            if not which(value):
                msg = (
                    "Configuration invalid: The following environment variable value isn't a valid "
                    + f"file or the file itself doesn't exists: {name}"
                )
                logger.error(msg)
                raise InvalidConfig()

        values.append(value)

    return values


def validate_json(event, schema):
    """Function to validate json format

    Arguments:
        event {str} -- Whole message content
        schema {dict} -- The json schema to use for validation
    """
    logger.debug("Validating message {}".format(event))

    try:
        Draft3Validator(json.loads(schema)).validate(event)
    except ValidationError:
        logger.exception("Error in JSON data")
        raise


undefined = object()


def config(key, default=undefined, cast=str, args=None):
    """Load a config from environment variable

    Arguments:
        key {str} -- The name of the variable to be loaded

    Keyword Arguments:
        default {any} -- The default value in case the variable is not defined (default: {undefined})
        cast {callable} -- The function to convert and valid config (default: {str})
        args {list} -- A list of extra arguments to pass to cast (default: {None})

    Raises:
        InvalidConfig -- In case the config is invalid

    Returns:
        any -- The config value validated and converted or the default
    """

    if args is None:
        args = []

    value = environ.get(key, default=undefined)

    if default is undefined and value is undefined:
        raise InvalidConfig("Environment variable is required: {}".format(key))

    if value is undefined:
        logger.debug("{}={}".format(key, default))
        return default

    try:
        logger.debug("{}={}".format(key, value))
        return cast(value, *args)
    except ValueError as ex:
        raise InvalidConfig("Environment variable is invalid: {}: {}".format(key, ex)) from None
    except InvalidConfig:
        raise


def valid_file(value):
    """Test if a path is a regular file"""

    if not path.isfile(value):
        raise ValueError("The path is not a regular file")
    return value


def valid_dir(value):
    """Test if a path is a directory"""

    if not path.isdir(value):
        raise ValueError("The path is not a directory")
    return value


def valid_executable(value):
    """Test if a path is a executable file"""

    if not which(value):
        raise ValueError("The path is not a executable file")
    return value


def boolean(value):
    """Convert a english word to boolean"""

    if value.lower() not in _BOOLEANS:
        raise ValueError("A boolean string must be one of {}".format(", ".join(_BOOLEANS.keys())))
    return _BOOLEANS[value.lower()]


def one_of(value, *alternatives):
    """Test if the value is one of alternatives"""

    if value not in alternatives:
        raise ValueError("Must be one of {}".format(", ".join(alternatives)))
    return value
