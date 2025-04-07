"""
Helper functions for testing purposes.
"""
import inspect
import traceback
from fastapi import HTTPException
from unittest.mock import patch


def print_mock_calls(mock_obj, indent=0):
    """
    Print all calls made to a mock object for debugging.
    """
    prefix = ' ' * indent
    print(f"{prefix}Mock calls for {mock_obj._extract_mock_name()}:")

    if not mock_obj.call_args_list:
        print(f"{prefix}  No calls were made.")
        return

    for i, call in enumerate(mock_obj.call_args_list):
        args = ', '.join([repr(arg) for arg in call[0]])
        kwargs = ', '.join([f"{k}={repr(v)}" for k, v in call[1].items()])

        call_str = f"{args}"
        if kwargs:
            if args:
                call_str += f", {kwargs}"
            else:
                call_str = kwargs

        print(f"{prefix}  Call {i+1}: {call_str}")


def debug_exception(exception):
    """
    Print detailed information about an exception.
    """
    print(f"Exception type: {type(exception).__name__}")
    print(f"Exception message: {str(exception)}")
    print(f"Traceback:")
    traceback.print_tb(exception.__traceback__)

    if isinstance(exception, HTTPException):
        print(f"HTTP status code: {exception.status_code}")
        print(f"HTTP detail: {exception.detail}")


def print_route_info(app, route_path):
    """
    Print information about a specific route in a FastAPI app.
    """
    for route in app.routes:
        if hasattr(route, 'path') and route.path == route_path:
            print(f"Route: {route.path}")
            print(f"Methods: {route.methods}")
            print(f"Endpoint function: {route.endpoint.__name__}")
            print(f"Function source:")
            try:
                source = inspect.getsource(route.endpoint)
                print(source)
            except Exception as e:
                print(f"Could not get source code: {e}")

            return

    print(f"No route found for path: {route_path}")


class MockWithLogging:
    """
    A utility class to create mocks that log their calls.
    """
    @staticmethod
    def patch(target, **kwargs):
        """
        Create a patched mock that logs all calls made to it.
        """
        original_mock = patch(target, **kwargs)

        class LoggingPatchContextManager:
            def __enter__(self):
                self.mock = original_mock.__enter__()
                original_side_effect = self.mock.side_effect

                def logging_side_effect(*args, **kwargs):
                    print(
                        f"Called {target} with args: {args}, kwargs: {kwargs}")
                    if callable(original_side_effect):
                        return original_side_effect(*args, **kwargs)
                    elif original_side_effect is not None:
                        return original_side_effect
                    return self.mock.return_value

                self.mock.side_effect = logging_side_effect
                return self.mock

            def __exit__(self, *args):
                return original_mock.__exit__(*args)

        return LoggingPatchContextManager()
