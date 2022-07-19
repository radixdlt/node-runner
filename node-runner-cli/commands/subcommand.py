def get_decorator(args, parent):
    def decorator(func):
        parser = parent.add_parser(func.__name__.replace("_", "-"), description=func.__doc__)
        required_args = parser.add_argument_group('required arguments')
        optional_args = parser.add_argument_group('optional arguments')

        if len(args) > 0:
            for arg in args:
                if "required" in arg[1]:
                    required_args.add_argument(*arg[0], **arg[1])
                else:
                    optional_args.add_argument(*arg[0], **arg[1])

        parser.set_defaults(func=func)

    return decorator


def argument(*name_or_flags, **kwargs):
    return list(name_or_flags), kwargs
