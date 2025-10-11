"""
Calculator Plugin for Auralis
Provides mathematical calculations and unit conversions
"""

import math
import re

def register_plugin():
    """Register this plugin with Auralis"""
    return {
        "name": "calculator",
        "version": "1.0.0",
        "description": "Mathematical calculations and unit conversions",
        "commands": ["calculate", "convert_units", "solve_equation"]
    }

def calculate(expression):
    """Evaluate a mathematical expression safely"""
    try:
        # Remove any dangerous characters/functions
        safe_chars = re.compile(r'[^0-9+\-*/().\s]')
        if safe_chars.search(expression):
            return "Error: Invalid characters in expression"

        # Replace common math functions
        expression = expression.replace('^', '**')  # Power operator
        expression = re.sub(r'\bsqrt\s*\(', 'math.sqrt(', expression)
        expression = re.sub(r'\bsin\s*\(', 'math.sin(', expression)
        expression = re.sub(r'\bcos\s*\(', 'math.cos(', expression)
        expression = re.sub(r'\btan\s*\(', 'math.tan(', expression)
        expression = re.sub(r'\blog\s*\(', 'math.log(', expression)
        expression = re.sub(r'\bpi\b', 'math.pi', expression)
        expression = re.sub(r'\be\b', 'math.e', expression)

        # Safe evaluation
        allowed_names = {
            "math": math,
            "__builtins__": {}
        }

        result = eval(expression, allowed_names)

        # Format result
        if isinstance(result, float):
            if result.is_integer():
                return f"Result: {int(result)}"
            else:
                return f"Result: {result:.6f}"
        else:
            return f"Result: {result}"

    except ZeroDivisionError:
        return "Error: Division by zero"
    except OverflowError:
        return "Error: Result too large"
    except Exception as e:
        return f"Error: {str(e)}"

def convert_units(value, from_unit, to_unit):
    """Convert between units"""
    try:
        value = float(value)

        # Temperature conversions
        if from_unit.lower() in ['c', 'celsius'] and to_unit.lower() in ['f', 'fahrenheit']:
            result = (value * 9/5) + 32
            return f"{value}°C = {result:.1f}°F"
        elif from_unit.lower() in ['f', 'fahrenheit'] and to_unit.lower() in ['c', 'celsius']:
            result = (value - 32) * 5/9
            return f"{value}°F = {result:.1f}°C"
        elif from_unit.lower() in ['c', 'celsius'] and to_unit.lower() in ['k', 'kelvin']:
            result = value + 273.15
            return f"{value}°C = {result:.1f}K"
        elif from_unit.lower() in ['k', 'kelvin'] and to_unit.lower() in ['c', 'celsius']:
            result = value - 273.15
            return f"{value}K = {result:.1f}°C"

        # Length conversions (metric to imperial)
        elif from_unit.lower() in ['m', 'meter', 'meters'] and to_unit.lower() in ['ft', 'feet']:
            result = value * 3.28084
            return f"{value} m = {result:.2f} ft"
        elif from_unit.lower() in ['ft', 'feet'] and to_unit.lower() in ['m', 'meter', 'meters']:
            result = value / 3.28084
            return f"{value} ft = {result:.2f} m"
        elif from_unit.lower() in ['km', 'kilometer'] and to_unit.lower() in ['mi', 'mile', 'miles']:
            result = value * 0.621371
            return f"{value} km = {result:.2f} mi"
        elif from_unit.lower() in ['mi', 'mile', 'miles'] and to_unit.lower() in ['km', 'kilometer']:
            result = value / 0.621371
            return f"{value} mi = {result:.2f} km"

        # Weight conversions
        elif from_unit.lower() in ['kg', 'kilogram'] and to_unit.lower() in ['lb', 'pound', 'pounds']:
            result = value * 2.20462
            return f"{value} kg = {result:.2f} lb"
        elif from_unit.lower() in ['lb', 'pound', 'pounds'] and to_unit.lower() in ['kg', 'kilogram']:
            result = value / 2.20462
            return f"{value} lb = {result:.2f} kg"

        else:
            return f"Unsupported conversion: {from_unit} to {to_unit}"

    except ValueError:
        return "Error: Invalid numeric value"
    except Exception as e:
        return f"Conversion error: {str(e)}"

def solve_equation(equation):
    """Solve simple algebraic equations (placeholder)"""
    # This is a simplified implementation
    # In a real plugin, you might use sympy or similar

    try:
        # Handle simple linear equations like "2x + 3 = 7"
        equation = equation.replace(' ', '').replace('=', '-(') + ')'

        # This is very basic - just a placeholder
        return "Equation solving: This is a placeholder. For advanced equation solving, consider using a symbolic math library like sympy."

    except Exception as e:
        return f"Equation solving error: {str(e)}"