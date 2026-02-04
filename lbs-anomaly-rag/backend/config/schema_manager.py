"""Schema Configuration Manager - Loads and manages database schema configuration"""
import json
import os
from typing import Dict, List, Any


class SchemaManager:
    """Manages database schema configuration from JSON"""

    def __init__(self, config_path: str = None):
        """
        Initialize schema manager

        Args:
            config_path: Path to schema_config.json. If None, uses default location.
        """
        if config_path is None:
            current_dir = os.path.dirname(__file__)
            config_path = os.path.join(current_dir, 'schema_config.json')

        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)

    def get_fact_tables(self) -> List[Dict[str, Any]]:
        """Get all fact tables"""
        return self.config.get('fact_tables', [])

    def get_dimension_tables(self) -> List[Dict[str, Any]]:
        """Get all dimension tables"""
        return self.config.get('dimension_tables', [])

    def get_table_by_name(self, table_name: str) -> Dict[str, Any]:
        """Get table configuration by name"""
        for table in self.get_fact_tables() + self.get_dimension_tables():
            if table['name'] == table_name:
                return table
        return None

    def get_business_rules(self) -> List[Dict[str, str]]:
        """Get business rules"""
        return self.config.get('business_rules', [])

    def generate_schema_context_text(self) -> str:
        """
        Generate a human-readable schema context for LLM

        Returns:
            Formatted schema description text
        """
        lines = []

        # Header
        lines.append(f"# {self.config['database']} - {self.config['description']}")
        lines.append("")
        lines.append("## Overview")
        lines.append(self.config['description'])
        lines.append("")

        # Fact Tables
        lines.append("## Fact Tables")
        lines.append("")
        for fact in self.get_fact_tables():
            lines.append(f"### {fact['name']} ({fact['row_count']:,} rows)")
            lines.append(fact['description'])
            lines.append("")
            lines.append(f"**Alias:** `{fact['alias']}`")
            lines.append("")

            # Primary Keys
            if fact.get('primary_keys'):
                lines.append("**Primary Keys:**")
                for pk in fact['primary_keys']:
                    lines.append(f"- {pk['name']} ({pk['type']})")
                lines.append("")

            # Foreign Keys
            if fact.get('foreign_keys'):
                lines.append("**Foreign Keys:**")
                for fk in fact['foreign_keys']:
                    lines.append(f"- {fk['name']} ({fk['type']}) -> {fk['references']}")
                lines.append("")

            # Measures
            if fact.get('measures'):
                lines.append("**Measures (Metrics):**")
                for measure in fact['measures']:
                    desc = f"{measure['description']}"
                    if measure.get('aggregation'):
                        desc += f" [Use {measure['aggregation']}]"
                    lines.append(f"- {measure['name']} ({measure['type']}) - {desc}")
                lines.append("")

            # Attributes
            if fact.get('attributes'):
                lines.append("**Other Columns:**")
                for attr in fact['attributes']:
                    lines.append(f"- {attr['name']} ({attr['type']}) - {attr['description']}")
                lines.append("")

        # Dimension Tables
        lines.append("## Dimension Tables")
        lines.append("")
        for dim in self.get_dimension_tables():
            lines.append(f"### {dim['name']} ({dim['row_count']:,} rows)")
            lines.append(dim['description'])
            lines.append("")
            lines.append(f"**Alias:** `{dim['alias']}`")
            lines.append("")

            # Primary Key
            pk = dim.get('primary_key')
            if pk:
                pk_desc = f"**Primary Key:** {pk['name']} ({pk['type']})"
                if pk.get('format'):
                    pk_desc += f" - Format: {pk['format']}"
                lines.append(pk_desc)
                lines.append("")

            # Date Range
            if dim.get('date_range'):
                dr = dim['date_range']
                lines.append(f"**Date Range:** {dr['start']} to {dr['end']}")
                lines.append("")

            # Name Concatenation
            if dim.get('name_concatenation'):
                lines.append(f"**Full Name:** Use `{dim['name_concatenation']}`")
                lines.append("")

            # Columns
            lines.append("**Important Columns:**")
            for col in dim.get('columns', []):
                col_desc = f"- {col['name']} ({col['type']}) - {col['description']}"
                if col.get('values'):
                    col_desc += f" [{', '.join(col['values'])}]"
                if col.get('business_key'):
                    col_desc += " [Business Key]"
                lines.append(col_desc)
            lines.append("")

            # Special Notes
            if dim.get('special_notes'):
                lines.append(f"**Note:** {dim['special_notes']}")
                lines.append("")

        # Business Rules
        lines.append("## Important Business Rules")
        lines.append("")
        for rule in self.get_business_rules():
            lines.append(f"**{rule['rule'].replace('_', ' ').title()}:** {rule['description']}")
        lines.append("")

        # Common Aggregations
        if self.config.get('common_aggregations'):
            lines.append("## Common Aggregations")
            lines.append("")
            for category, aggs in self.config['common_aggregations'].items():
                lines.append(f"**{category.replace('_', ' ').title()}:**")
                for agg in aggs:
                    lines.append(f"- `{agg}`")
                lines.append("")

        # Table Aliases
        lines.append("## Table Alias Reference")
        lines.append("")
        for table in self.get_fact_tables() + self.get_dimension_tables():
            lines.append(f"- {table['name']}: `{table['alias']}`")

        return "\n".join(lines)

    def get_table_list(self) -> List[str]:
        """Get list of all table names"""
        tables = []
        for table in self.get_fact_tables() + self.get_dimension_tables():
            tables.append(table['name'])
        return tables

    def get_column_list(self, table_name: str) -> List[str]:
        """Get list of column names for a table"""
        table = self.get_table_by_name(table_name)
        if not table:
            return []

        columns = []

        # Add primary key(s)
        if table.get('primary_key'):
            columns.append(table['primary_key']['name'])
        elif table.get('primary_keys'):
            columns.extend([pk['name'] for pk in table['primary_keys']])

        # Add foreign keys
        if table.get('foreign_keys'):
            columns.extend([fk['name'] for fk in table['foreign_keys']])

        # Add measures
        if table.get('measures'):
            columns.extend([m['name'] for m in table['measures']])

        # Add attributes
        if table.get('attributes'):
            columns.extend([a['name'] for a in table['attributes']])

        # Add other columns
        if table.get('columns'):
            columns.extend([c['name'] for c in table['columns']])

        return columns

    def get_joins_text(self) -> str:
        """Generate common join patterns"""
        lines = []
        lines.append("## Common Join Patterns")
        lines.append("")

        for fact in self.get_fact_tables():
            fact_name = fact['name']
            fact_alias = fact['alias']

            for fk in fact.get('foreign_keys', []):
                dim_table = fk['references'].split('.')[0]
                dim = self.get_table_by_name(dim_table)
                if dim:
                    lines.append(f"**{fact_name} to {dim_table}:**")
                    lines.append("```sql")
                    lines.append(f"FROM {fact_name} {fact_alias}")
                    lines.append(f"INNER JOIN {dim_table} {dim['alias']} ON {dim['alias']}.{fk['references'].split('.')[1]} = {fact_alias}.{fk['name']}")
                    lines.append("```")
                    lines.append("")

        return "\n".join(lines)


# Global instance
_schema_manager = None


def get_schema_manager() -> SchemaManager:
    """Get singleton schema manager instance"""
    global _schema_manager
    if _schema_manager is None:
        _schema_manager = SchemaManager()
    return _schema_manager


# Convenience functions for backward compatibility
def get_schema_context() -> str:
    """Get schema context text for LLM"""
    manager = get_schema_manager()
    return manager.generate_schema_context_text() + "\n\n" + manager.get_joins_text()


def get_table_list() -> List[str]:
    """Get list of all table names"""
    return get_schema_manager().get_table_list()


def get_column_list(table_name: str) -> List[str]:
    """Get list of column names for a table"""
    return get_schema_manager().get_column_list(table_name)
