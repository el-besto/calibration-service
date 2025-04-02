# from typing import Any
#
# from sqlalchemy import types
# from sqlalchemy.engine.interfaces import Dialect
# from ulid import ULID
#
#
# class ULIDType(types.TypeDecorator[Any]):
#     """
#     Custom SQLAlchemy type to store ULID as a CHAR(26) in the database.
#     """
#
#     impl = types.String(26)  # Store ULID as a CHAR(26) in the database
#
#     def process_bind_param(self, value: Any | None, dialect: Dialect) -> None | str:
#         """
#         Convert ULID to a string (CHAR) when saving to the database.
#         """
#         if isinstance(value, ULID):
#             return str(value)  # Convert ULID to string
#         if isinstance(value, str):
#             return value  # Already a string
#         if value is None:
#             return None  # Handle None
#         raise ValueError(f"Cannot store non-ULID value: {value}")
#
#     def process_result_value(self, value: Any | None, dialect: Dialect) -> ULID | None:
#         """
#         Convert database value (CHAR) back to a ULID when loading from the database.
#         """
#         if value is not None:
#             return ULID.from_str(value)  # Convert string back to ULID
#         return None
