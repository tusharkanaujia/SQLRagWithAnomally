"""Anomaly Detection Configuration Manager"""
import json
import os
from typing import Dict, List, Any, Optional


class AnomalyConfigManager:
    """Manages anomaly detection configuration from JSON"""

    def __init__(self, config_path: str = None):
        """
        Initialize anomaly config manager

        Args:
            config_path: Path to anomaly_config.json. If None, uses default location.
        """
        if config_path is None:
            current_dir = os.path.dirname(__file__)
            config_path = os.path.join(current_dir, 'anomaly_config.json')

        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)

        self.anomaly_config = self.config.get('anomaly_detection', {})

    def is_enabled(self) -> bool:
        """Check if anomaly detection is globally enabled"""
        return self.anomaly_config.get('enabled', True)

    # Time Series Methods
    def is_time_series_enabled(self) -> bool:
        """Check if time series detection is enabled"""
        return self.anomaly_config.get('time_series', {}).get('enabled', True)

    def get_time_series_configs(self) -> List[Dict[str, Any]]:
        """Get all enabled time series configurations"""
        configs = self.anomaly_config.get('time_series', {}).get('configurations', [])
        return [c for c in configs if c.get('enabled', True)]

    def get_time_series_config(self, name: str) -> Optional[Dict[str, Any]]:
        """Get specific time series configuration by name"""
        configs = self.anomaly_config.get('time_series', {}).get('configurations', [])
        for config in configs:
            if config.get('name') == name:
                return config
        return None

    # Statistical Methods
    def is_statistical_enabled(self) -> bool:
        """Check if statistical detection is enabled"""
        return self.anomaly_config.get('statistical', {}).get('enabled', True)

    def get_statistical_configs(self) -> List[Dict[str, Any]]:
        """Get all enabled statistical configurations"""
        configs = self.anomaly_config.get('statistical', {}).get('configurations', [])
        return [c for c in configs if c.get('enabled', True)]

    def get_statistical_config(self, name: str) -> Optional[Dict[str, Any]]:
        """Get specific statistical configuration by name"""
        configs = self.anomaly_config.get('statistical', {}).get('configurations', [])
        for config in configs:
            if config.get('name') == name:
                return config
        return None

    def get_statistical_configs_by_dimension(self, dimension: str) -> List[Dict[str, Any]]:
        """Get statistical configs for a specific dimension"""
        configs = self.get_statistical_configs()
        return [c for c in configs if c.get('dimension') == dimension]

    # Comparative Methods
    def is_comparative_enabled(self) -> bool:
        """Check if comparative detection is enabled"""
        return self.anomaly_config.get('comparative', {}).get('enabled', True)

    def get_comparative_configs(self) -> List[Dict[str, Any]]:
        """Get all enabled comparative configurations"""
        configs = self.anomaly_config.get('comparative', {}).get('configurations', [])
        return [c for c in configs if c.get('enabled', True)]

    def get_comparative_config(self, comparison_type: str) -> Optional[Dict[str, Any]]:
        """Get comparative configuration by type (yoy, mom, qoq)"""
        configs = self.get_comparative_configs()
        for config in configs:
            if config.get('comparison_type') == comparison_type:
                return config
        return None

    # Day-on-Day Methods
    def is_day_on_day_enabled(self) -> bool:
        """Check if day-on-day detection is enabled"""
        return self.anomaly_config.get('day_on_day', {}).get('enabled', True)

    def get_day_on_day_configs(self) -> List[Dict[str, Any]]:
        """Get all enabled day-on-day configurations"""
        configs = self.anomaly_config.get('day_on_day', {}).get('configurations', [])
        return [c for c in configs if c.get('enabled', True)]

    def get_day_on_day_config(self, dimension: str) -> Optional[Dict[str, Any]]:
        """Get day-on-day configuration for specific dimension"""
        configs = self.get_day_on_day_configs()
        for config in configs:
            if config.get('dimension') == dimension:
                return config
        return None

    def get_day_on_day_dimensions(self) -> List[str]:
        """Get list of dimensions configured for day-on-day analysis"""
        configs = self.get_day_on_day_configs()
        return [c.get('dimension') for c in configs if c.get('dimension')]

    # Custom Rules Methods
    def is_custom_rules_enabled(self) -> bool:
        """Check if custom rules are enabled"""
        return self.anomaly_config.get('custom_rules', {}).get('enabled', True)

    def get_custom_rules(self) -> List[Dict[str, Any]]:
        """Get all enabled custom rules"""
        rules = self.anomaly_config.get('custom_rules', {}).get('rules', [])
        return [r for r in rules if r.get('enabled', True)]

    def get_custom_rule(self, name: str) -> Optional[Dict[str, Any]]:
        """Get specific custom rule by name"""
        rules = self.get_custom_rules()
        for rule in rules:
            if rule.get('name') == name:
                return rule
        return None

    # Global Filters
    def get_global_filters(self) -> Dict[str, Any]:
        """Get global filters that apply to all detections"""
        return self.config.get('global_filters', {})

    def get_date_range_filter(self) -> Optional[Dict[str, str]]:
        """Get global date range filter if enabled"""
        date_filter = self.get_global_filters().get('date_range', {})
        if date_filter.get('enabled'):
            return {
                'start_date': date_filter.get('start_date'),
                'end_date': date_filter.get('end_date')
            }
        return None

    # Notification Settings
    def get_notification_settings(self) -> Dict[str, Any]:
        """Get notification configuration"""
        return self.config.get('notification_settings', {})

    def should_notify(self, severity: str) -> bool:
        """Check if notifications are enabled for a severity level"""
        thresholds = self.get_notification_settings().get('severity_thresholds', {})
        return thresholds.get(severity, {}).get('enabled', False)

    def get_notification_channels(self) -> List[str]:
        """Get list of enabled notification channels"""
        channels = self.get_notification_settings().get('channels', {})
        return [name for name, config in channels.items() if config.get('enabled', False)]

    # Performance Settings
    def get_performance_settings(self) -> Dict[str, Any]:
        """Get performance configuration"""
        return self.config.get('performance_settings', {})

    def get_batch_size(self) -> int:
        """Get batch size for processing"""
        return self.get_performance_settings().get('batch_size', 1000)

    def is_caching_enabled(self) -> bool:
        """Check if result caching is enabled"""
        return self.get_performance_settings().get('cache_results', True)

    # Utility Methods
    def get_all_enabled_detections(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get all enabled detection configurations grouped by type"""
        result = {}

        if self.is_time_series_enabled():
            result['time_series'] = self.get_time_series_configs()

        if self.is_statistical_enabled():
            result['statistical'] = self.get_statistical_configs()

        if self.is_comparative_enabled():
            result['comparative'] = self.get_comparative_configs()

        if self.is_day_on_day_enabled():
            result['day_on_day'] = self.get_day_on_day_configs()

        if self.is_custom_rules_enabled():
            result['custom_rules'] = self.get_custom_rules()

        return result

    def get_dimensions_to_analyze(self) -> Dict[str, List[str]]:
        """Get list of dimensions configured for each detection type"""
        dimensions = {}

        # Statistical dimensions
        statistical = self.get_statistical_configs()
        dimensions['statistical'] = list(set([c.get('dimension') for c in statistical if c.get('dimension')]))

        # Day-on-day dimensions
        day_on_day = self.get_day_on_day_configs()
        dimensions['day_on_day'] = list(set([c.get('dimension') for c in day_on_day if c.get('dimension')]))

        return dimensions

    def export_active_config(self) -> Dict[str, Any]:
        """Export only the active/enabled configurations"""
        return {
            'enabled': self.is_enabled(),
            'detections': self.get_all_enabled_detections(),
            'global_filters': self.get_global_filters(),
            'notification_settings': self.get_notification_settings(),
            'performance_settings': self.get_performance_settings()
        }

    def validate_config(self) -> List[str]:
        """
        Validate configuration and return list of warnings/errors

        Returns:
            List of validation messages (empty if all valid)
        """
        messages = []

        # Check if at least one detection method is enabled
        if not any([
            self.is_time_series_enabled(),
            self.is_statistical_enabled(),
            self.is_comparative_enabled(),
            self.is_day_on_day_enabled(),
            self.is_custom_rules_enabled()
        ]):
            messages.append("WARNING: No detection methods are enabled")

        # Check for configs with required fields
        for config in self.get_day_on_day_configs():
            if not config.get('dimension'):
                messages.append(f"ERROR: Day-on-day config '{config.get('name')}' missing dimension")
            if not config.get('metric'):
                messages.append(f"ERROR: Day-on-day config '{config.get('name')}' missing metric")

        for config in self.get_statistical_configs():
            if not config.get('dimension'):
                messages.append(f"ERROR: Statistical config '{config.get('name')}' missing dimension")
            if not config.get('method'):
                messages.append(f"ERROR: Statistical config '{config.get('name')}' missing method")

        return messages


# Global instance
_anomaly_config_manager = None


def get_anomaly_config_manager() -> AnomalyConfigManager:
    """Get singleton anomaly config manager instance"""
    global _anomaly_config_manager
    if _anomaly_config_manager is None:
        _anomaly_config_manager = AnomalyConfigManager()
    return _anomaly_config_manager


# Convenience functions
def get_enabled_detections() -> Dict[str, List[Dict[str, Any]]]:
    """Get all enabled detection configurations"""
    return get_anomaly_config_manager().get_all_enabled_detections()


def get_day_on_day_config(dimension: str) -> Optional[Dict[str, Any]]:
    """Get day-on-day configuration for a dimension"""
    return get_anomaly_config_manager().get_day_on_day_config(dimension)


def validate_anomaly_config() -> List[str]:
    """Validate anomaly configuration"""
    return get_anomaly_config_manager().validate_config()
