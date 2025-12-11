"""Helpers module for the klx package.

This module automatically chooses between the full kluisz kanvas implementation
(when available) and the klx implementation (when standalone).
"""

from klx.utils.langflow_utils import has_kluisz_memory

# Import the appropriate implementation
if has_kluisz_memory():
    try:
        # Import full kluisz kanvas implementation
        # Base Model
        from kluisz.helpers.base_model import (
            BaseModel,
            SchemaField,
            build_model_from_schema,
            coalesce_bool,
        )

        # Custom
        from kluisz.helpers.custom import (
            format_type,
        )

        # Data
        from kluisz.helpers.data import (
            clean_string,
            data_to_text,
            data_to_text_list,
            docs_to_data,
            safe_convert,
        )

        # Flow
        from kluisz.helpers.flow import (
            build_schema_from_inputs,
            get_arg_names,
            get_flow_by_id_or_name,
            get_flow_inputs,
            list_flows,
            list_flows_by_flow_folder,
            list_flows_by_folder_id,
            load_flow,
            run_flow,
        )
    except ImportError:
        # Fallback to klx implementation if kluisz import fails
        # Base Model
        from klx.helpers.base_model import (
            BaseModel,
            SchemaField,
            build_model_from_schema,
            coalesce_bool,
        )

        # Custom
        from klx.helpers.custom import (
            format_type,
        )

        # Data
        from klx.helpers.data import (
            clean_string,
            data_to_text,
            data_to_text_list,
            docs_to_data,
            safe_convert,
        )

        # Flow
        from klx.helpers.flow import (
            build_schema_from_inputs,
            get_arg_names,
            get_flow_by_id_or_name,
            get_flow_inputs,
            list_flows,
            list_flows_by_flow_folder,
            list_flows_by_folder_id,
            load_flow,
            run_flow,
        )
else:
    # Use klx implementation
    # Base Model
    from klx.helpers.base_model import (
        BaseModel,
        SchemaField,
        build_model_from_schema,
        coalesce_bool,
    )

    # Custom
    from klx.helpers.custom import (
        format_type,
    )

    # Data
    from klx.helpers.data import (
        clean_string,
        data_to_text,
        data_to_text_list,
        docs_to_data,
        safe_convert,
    )

    # Flow
    from klx.helpers.flow import (
        build_schema_from_inputs,
        get_arg_names,
        get_flow_by_id_or_name,
        get_flow_inputs,
        list_flows,
        list_flows_by_flow_folder,
        list_flows_by_folder_id,
        load_flow,
        run_flow,
    )

# Export the available functions
__all__ = [
    "BaseModel",
    "SchemaField",
    "build_model_from_schema",
    "build_schema_from_inputs",
    "clean_string",
    "coalesce_bool",
    "data_to_text",
    "data_to_text_list",
    "docs_to_data",
    "format_type",
    "get_arg_names",
    "get_flow_by_id_or_name",
    "get_flow_inputs",
    "list_flows",
    "list_flows_by_flow_folder",
    "list_flows_by_folder_id",
    "load_flow",
    "run_flow",
    "safe_convert",
]
