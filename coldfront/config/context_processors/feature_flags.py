from coldfront.config.feature_flag_service import FeatureFlagService

def get_feature_flag_service(request):
    return {

        'feature_flag_service': FeatureFlagService()

    }