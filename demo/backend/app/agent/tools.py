"""Agent tools for the demo application."""

from __future__ import annotations

import random

from langchain_core.tools import tool


@tool
def calculator(expression: str) -> str:
    """Evaluate a mathematical expression.

    Args:
        expression: A mathematical expression to evaluate (e.g., "2 + 2", "sqrt(16)", "3 * 4 + 5")

    Returns:
        The result of the calculation as a string.
    """
    import math

    # Safe evaluation with limited scope
    allowed_names = {
        "abs": abs,
        "round": round,
        "min": min,
        "max": max,
        "sum": sum,
        "pow": pow,
        "sqrt": math.sqrt,
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "log": math.log,
        "log10": math.log10,
        "exp": math.exp,
        "pi": math.pi,
        "e": math.e,
    }

    try:
        # Clean expression
        expr = expression.strip()
        # Evaluate with restricted scope
        result = eval(expr, {"__builtins__": {}}, allowed_names)
        return f"Result: {result}"
    except Exception as e:
        return f"Error evaluating expression: {str(e)}"


@tool
def get_weather(city: str, units: str | None = "celsius") -> str:
    """Get the current weather for a city.

    This is a mock weather tool for demonstration purposes.

    Args:
        city: The name of the city to get weather for.
        units: Temperature units - "celsius" or "fahrenheit" (default: celsius)

    Returns:
        A string describing the current weather conditions.
    """
    # Mock weather data for demo
    conditions = ["sunny", "partly cloudy", "cloudy", "rainy", "windy"]
    condition = random.choice(conditions)

    # Generate realistic temperature based on city (just for demo)
    base_temp = hash(city.lower()) % 30 + 5  # 5-35 range

    if units == "fahrenheit":
        temp = int(base_temp * 9 / 5 + 32)
        unit_str = "F"
    else:
        temp = base_temp
        unit_str = "C"

    humidity = random.randint(30, 90)

    return f"Weather in {city}: {condition}, {temp}°{unit_str}, humidity {humidity}%"


# List of available tools
TOOLS = [calculator, get_weather]
