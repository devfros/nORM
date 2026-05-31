def snake_to_camel(value: str) -> str:
    components = value.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


def snake_to_pascal(value: str) -> str:
    camel = snake_to_camel(value)
    return camel[0].upper() + camel[1:]


def camel_to_snake(value: str) -> str:
    result = []

    for i, char in enumerate(value):
        if char.isupper():
            if i > 0 and (value[i - 1].islower() or value[i - 1].isdigit()):
                result.append("_")
            result.append(char.lower())
        else:
            result.append(char)

    return "".join(result)
