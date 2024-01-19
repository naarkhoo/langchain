from typing import Any, Dict, List, Mapping, Optional

from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.language_models.llms import LLM
from langchain_core.pydantic_v1 import Extra, SecretStr, root_validator
from langchain_core.utils import convert_to_secret_str, get_from_dict_or_env


class NLPCloud(LLM):
    """NLPCloud large language models.

    To use, you should have the ``nlpcloud`` python package installed, and the
    environment variable ``NLPCLOUD_API_KEY`` set with your API key.

    Example:
        .. code-block:: python

            from langchain_community.llms import NLPCloud
            nlpcloud = NLPCloud(model="finetuned-gpt-neox-20b")
    """

    client: Any  #: :meta private:
    model_name: str = "finetuned-gpt-neox-20b"
    """Model name to use."""
    gpu: bool = True
    """Whether to use a GPU or not"""
    lang: str = "en"
    """Language to use (multilingual addon)"""
    temperature: float = 0.7
    """What sampling temperature to use."""
    max_length: int = 256
    """The maximum number of tokens to generate in the completion."""
    length_no_input: bool = True
    """Whether min_length and max_length should include the length of the input."""
    remove_input: bool = True
    """Remove input text from API response"""
    remove_end_sequence: bool = True
    """Whether or not to remove the end sequence token."""
    bad_words: List[str] = []
    """List of tokens not allowed to be generated."""
    top_p: float = 1.0
    """Total probability mass of tokens to consider at each step."""
    top_k: int = 50
    """The number of highest probability tokens to keep for top-k filtering."""
    repetition_penalty: float = 1.0
    """Penalizes repeated tokens. 1.0 means no penalty."""
    num_beams: int = 1
    """Number of beams for beam search."""
    num_return_sequences: int = 1
    """How many completions to generate for each prompt."""

    nlpcloud_api_key: Optional[SecretStr] = None

    class Config:
        """Configuration for this pydantic object."""

        extra = Extra.forbid

    @root_validator()
    def validate_environment(cls, values: Dict) -> Dict:
        """Validate that api key and python package exists in environment."""
        values["nlpcloud_api_key"] = convert_to_secret_str(
            get_from_dict_or_env(values, "nlpcloud_api_key", "NLPCLOUD_API_KEY")
        )
        try:
            import nlpcloud

            values["client"] = nlpcloud.Client(
                values["model_name"],
                values["nlpcloud_api_key"].get_secret_value(),
                gpu=values["gpu"],
                lang=values["lang"],
            )
        except ImportError:
            raise ImportError(
                "Could not import nlpcloud python package. "
                "Please install it with `pip install nlpcloud`."
            )
        return values

    @property
    def _default_params(self) -> Mapping[str, Any]:
        """Get the default parameters for calling NLPCloud API."""
        return {
            "temperature": self.temperature,
            "max_length": self.max_length,
            "length_no_input": self.length_no_input,
            "remove_input": self.remove_input,
            "remove_end_sequence": self.remove_end_sequence,
            "bad_words": self.bad_words,
            "top_p": self.top_p,
            "top_k": self.top_k,
            "repetition_penalty": self.repetition_penalty,
            "num_beams": self.num_beams,
            "num_return_sequences": self.num_return_sequences,
        }

    @property
    def _identifying_params(self) -> Mapping[str, Any]:
        """Get the identifying parameters."""
        return {
            **{"model_name": self.model_name},
            **{"gpu": self.gpu},
            **{"lang": self.lang},
            **self._default_params,
        }

    @property
    def _llm_type(self) -> str:
        """Return type of llm."""
        return "nlpcloud"

    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        """Call out to NLPCloud's create endpoint.

        Args:
            prompt: The prompt to pass into the model.
            stop: Not supported by this interface (pass in init method)

        Returns:
            The string generated by the model.

        Example:
            .. code-block:: python

                response = nlpcloud("Tell me a joke.")
        """
        if stop and len(stop) > 1:
            raise ValueError(
                "NLPCloud only supports a single stop sequence per generation."
                "Pass in a list of length 1."
            )
        elif stop and len(stop) == 1:
            end_sequence = stop[0]
        else:
            end_sequence = None
        params = {**self._default_params, **kwargs}
        response = self.client.generation(prompt, end_sequence=end_sequence, **params)
        return response["generated_text"]
