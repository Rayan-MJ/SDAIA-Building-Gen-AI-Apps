import functools
import time
import uuid
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import List, Optional, Any

@dataclass
class Span:
    id: str
    name: str
    start_time: float
    level: int
    parent: Optional['Span'] = None
    children: List['Span'] = field(default_factory=list)
    end_time: Optional[float] = None
    input: Any = None
    output: Any = None
    metadata: dict = field(default_factory=dict)

_current_span: ContextVar[Optional[Span]] = ContextVar("current_span", default=None)

class SimpleObserver:
    @staticmethod
    def print_tree(span: Span):
        duration = (span.end_time - span.start_time) * 1000
        indent = "  " * span.level
        
        # Determine tree character
        if span.level == 0:
            prefix = "=== TRACE: "
            suffix = " ==="
        else:
            # ASCII equivalent for child spans
            prefix = "|-- "
            suffix = ""

        print(f"{indent}{prefix}{span.name}{suffix} ({duration:.2f}ms)")
        
        # Recursively print children
        for child in span.children:
            SimpleObserver.print_tree(child)

def observe(name=None):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            parent = _current_span.get()
            level = parent.level + 1 if parent else 0
            
            span_name = name or func.__name__
            new_span = Span(
                id=str(uuid.uuid4())[:8], 
                name=span_name, 
                start_time=time.time(), 
                level=level, 
                parent=parent
            )
            
            if parent:
                parent.children.append(new_span)
            
            # Capture input (simplified)
            # If it's a class method, skip 'self' in args
            captured_args = args[1:] if args and hasattr(args[0], '__class__') and func.__name__ in dir(args[0].__class__) else args
            new_span.input = {"args": captured_args, "kwargs": kwargs}

            token = _current_span.set(new_span)
            
            try:
                result = func(*args, **kwargs)
                new_span.output = result
                return result
            except Exception as e:
                new_span.output = f"Error: {str(e)}"
                raise e
            finally:
                new_span.end_time = time.time()
                _current_span.reset(token)
                
                # If this is the root span, print the whole tree
                if level == 0:
                    print("\n" + "-"*60)
                    SimpleObserver.print_tree(new_span)
                    print("-"*60 + "\n")
        return wrapper

    # Handle both @observe and @observe()
    if callable(name):
        f = name
        name = None
        return decorator(f)
    return decorator

class LangfuseContext:
    def update_current_observation(self, **kwargs):
        span = _current_span.get()
        if span:
            span.metadata.update(kwargs)
            if 'input' in kwargs: span.input = kwargs['input']
            if 'output' in kwargs: span.output = kwargs['output']

langfuse_context = LangfuseContext()
