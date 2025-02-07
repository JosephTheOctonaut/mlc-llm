"""This file specifies how MLC's StableLM parameters are quantized using group quantization
or other formats."""
from typing import Tuple

from tvm.relax.frontend import nn

from mlc_chat.loader import QuantizeMapping
from mlc_chat.quantization import GroupQuantize, NoQuantize

from .stablelm_model import StableLMEpochConfig, StableLMEpochForCausalLM


def group_quant(
    model_config: StableLMEpochConfig,
    quantization: GroupQuantize,
) -> Tuple[nn.Module, QuantizeMapping]:
    """Quantize a StableLM-architecture model using group quantization."""
    model: nn.Module = StableLMEpochForCausalLM(model_config)
    model.to(quantization.model_dtype)
    quant_map = QuantizeMapping({}, {})
    model = quantization.quantize_model(
        model,
        quant_map,
        "",
    )
    return model, quant_map


def no_quant(
    model_config: StableLMEpochConfig,
    quantization: NoQuantize,
) -> Tuple[nn.Module, QuantizeMapping]:
    """Quantize a StableLM model without quantization."""
    model: nn.Module = StableLMEpochForCausalLM(model_config)
    model.to(quantization.model_dtype)
    quant_map = QuantizeMapping({}, {})
    return model, quant_map
