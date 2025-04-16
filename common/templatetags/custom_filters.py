from django import template

register = template.Library()


@register.filter
def dict_get(dictionary, key):
    return dictionary.get(key, None)


@register.filter
def filter_and_get_value(array, args):
    """
    Find object with key_name == key_value, return another property. Similar to array.find() in JS.

    :param array: array of objects
    :param args: comma separated string ("key_name,key_value,return_attr"), first value is the attribute name, second value is the value to match, third value is the attribute to return
    :return: value of the return_property

    Usage:
        {{ list|filter_and_get_value:"key_name,key_value,return_attr" }}
    Example:
        {{ people|filter_and_get_value:"role,editor,name" }}
        {{ people|filter_and_get_value:"role,editor,age" }}
    Description:
        Returns the value of 'return_attr' where 'key_name' == 'key_value'
    """
    try:
        key_name, key_value, return_attr = [part.strip() for part in args.split(',')]
    except ValueError:
        return None

    for obj in array:
        if obj[key_name] == key_value:
            return obj[return_attr]

    return None
