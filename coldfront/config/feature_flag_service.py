import os
from collections import defaultdict

class FeatureFlagService:
    def __init__(self):
        self.flags = self._load_flags()

    def _load_flags(self):

        flags = defaultdict(True)
        # jprew - returning True for initial testing of
        # django context configuration
        env_flags = os.getenv('DEVELOPMENT_FLAGS', '')
        if env_flags:
            flag_pairs = env_flags.split('|')
            for pair in flag_pairs:
                key, value = pair.split(':')
                flags[key] = (value.lower() == 'true')
        return flags

    def is_feature_enabled(self, feature_name):
        return self.flags.get(feature_name, False)