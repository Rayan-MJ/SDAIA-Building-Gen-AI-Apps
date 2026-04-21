"""
PathSanitizer — Prevent Directory Traversal Attacks
=====================================================
When an LLM controls file paths, you MUST validate that the
path stays within the allowed directory. An LLM could be tricked
into requesting "../../etc/passwd".

Steps:
  1. Implement validate_safe_path()
"""

import os


class SecurityError(Exception):
    """Raised when a security check fails (e.g., path traversal)."""
    pass


class PathSanitizer:
    """Validates file paths to prevent directory traversal attacks."""

    @staticmethod
    def validate_safe_path(base_dir: str, target_path: str) -> str:
        """
        Ensures target_path resolves to a location within base_dir.

        Args:
            base_dir: The allowed root directory (e.g., "./workspace")
            target_path: The path requested (e.g., "reports/q1.txt")

        Returns:
            The resolved absolute path if safe.

        Raises:
            SecurityError: If the path escapes base_dir.

        Algorithm:
          1. Resolve the absolute path of base_dir
          2. Join base_dir + target_path, then resolve absolute path
          3. If the resolved path does NOT start with base_dir → raise SecurityError
          4. Otherwise return the resolved path
        """
        # TODO: Implement path validation
        # Hint:
        # 1. base_abs = os.path.abspath(base_dir)
        # 2. target_abs = os.path.abspath(os.path.join(base_abs, target_path))
        # 3. if not target_abs.startswith(base_abs): raise SecurityError("Traversal detected")
        # 4. return target_abs
        pass


if __name__ == "__main__":
    sanitizer = PathSanitizer()

    try:
        safe = sanitizer.validate_safe_path(".", "starter/base.py")
        print(f"Safe path: {safe}")
    except SecurityError as e:
        print(f"ERROR: {e}")

    try:
        unsafe = sanitizer.validate_safe_path(".", "../../etc/passwd")
        print(f"UNSAFE path allowed (BUG!): {unsafe}")
    except SecurityError as e:
        print(f"Blocked (correct!): {e}")
