from abc import ABC, abstractmethod


class BaseProvider(ABC):
    
    @abstractmethod
    async def generate(self, payload, stream):
        pass

    @abstractmethod
    async def count_tokens(self, input_text, output_text):
        pass

    @abstractmethod
    def get_model_capabilities(self, model):
        pass
