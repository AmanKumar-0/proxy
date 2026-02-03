from providers.base import BaseProvider


class ProviderRegistry:
    
    def __init__(self):
        self.providers = {}
        self.model_capabilities = {}
        self.auto_register_providers()

    def register(self, name, provider_class, model_capabilities=None):
        self.providers[name] = provider_class
        if model_capabilities:
            self.model_capabilities[name] = model_capabilities
    
    def get(self, name):
        if name not in self.providers:
            raise ValueError(f"Provider '{name}' not supported")
        return self.providers[name]
    
    def list_providers(self):
        return list(self.providers.keys())
    
    def auto_register_providers(self):
        from providers.openai import OpenAIProvider
        from providers.claude import ClaudeProvider

        self.register('openai', OpenAIProvider)
        self.register('claude', ClaudeProvider)


# provider_registry = ProviderRegistry()
