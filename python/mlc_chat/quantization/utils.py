"""Common utilities for quantization"""

from typing import List, Optional

from tvm import te, tir
from tvm import DataType


def convert_uint_to_float(  # pylint: disable=too-many-arguments
    weight: te.Tensor,
    bits: int,
    num_elem_per_storage: int,
    storage_dtype: str,
    model_dtype: str,
    axis: int = -1,
    out_shape: Optional[List[tir.PrimExpr]] = None,
    ft_reorder: Optional[bool] = False,
) -> te.Tensor:
    """Convert a quantized uint weight to an unquantized float weight."""
    tir_bin_mask = tir.const((1 << bits) - 1, storage_dtype)
    if out_shape is None:
        out_shape = weight.shape
        out_shape[axis] *= num_elem_per_storage
    axis = axis if axis >= 0 else len(out_shape) + axis
    return te.compute(
        shape=out_shape,
        fcompute=lambda *idx: tir.bitwise_and(
            tir.shift_right(
                weight(*idx[:axis], idx[axis] // num_elem_per_storage, *idx[axis + 1 :]),
                (
                    (
                        (idx[axis] % num_elem_per_storage) % 2 * 4
                        + (idx[axis] % num_elem_per_storage) // 2
                    )
                    * bits
                    if ft_reorder
                    else (idx[axis] % num_elem_per_storage) * bits
                ).astype(storage_dtype),
            ),
            tir_bin_mask,
        ).astype(model_dtype),
    )

def convert_uint_packed_fp8_to_float(  # pylint: disable=too-many-arguments
    weight: te.Tensor,
    bits: int,
    num_elem_per_storage: int,
    storage_dtype: str,
    model_dtype: str,
    quant_dtype: str,
    axis: int = -1,
    out_shape: Optional[List[tir.PrimExpr]] = None,
    ft_reorder: Optional[bool] = False,
) -> te.Tensor:
    """Convert a quantized uint weight tensor to an unquantized e4m3_float8 weight tensor."""
    # Does *not* have FT reoder support right now, can add back in (need to verify bit-match for fp8)
    if ft_reorder:
        raise NotImplementedError()
    assert quant_dtype in ["e4m3_float8", "e5m2_float8"]
    tir_bin_mask = tir.const((1 << bits) - 1, storage_dtype)
    if out_shape is None:
        out_shape = weight.shape
        out_shape[axis] *= num_elem_per_storage
    axis = axis if axis >= 0 else len(out_shape) + axis
    return te.compute(
        shape=out_shape,
        fcompute=lambda *idx: tir.reinterpret(
            DataType(quant_dtype),
            tir.bitwise_and(
                tir.shift_right(
                    weight(*idx[:axis], idx[axis] // num_elem_per_storage, *idx[axis + 1 :]),
                    (
                        (idx[axis] % num_elem_per_storage) * bits
                    ).astype(storage_dtype),
                ),
                tir_bin_mask,
            )
        ).astype(model_dtype),
    )

def is_final_fc(name: str) -> bool:
    """Determines whether the parameter is the last layer based on its name."""
    # TODO: use more specious condition to determine final fc  # pylint: disable=fixme
    return name in ["head", "lm_head"]
