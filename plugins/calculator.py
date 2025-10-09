def run(*args):
    try:
        expr = ' '.join(args)
        result = eval(expr)
        return f"Result: {result}"
    except Exception as e:
        return f"Error: {e}"