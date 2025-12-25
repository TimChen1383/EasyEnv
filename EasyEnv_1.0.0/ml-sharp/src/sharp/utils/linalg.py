"""Contains linear algebra related utility functions.

For licensing see accompanying LICENSE file.
Copyright (C) 2025 Apple Inc. All Rights Reserved.
"""

from __future__ import annotations

import torch
import torch.nn.functional as F
from scipy.spatial.transform import Rotation


def rotation_matrices_from_quaternions(quaternions: torch.Tensor) -> torch.Tensor:
    """Convert batch of quaternions into rotations matrices.

    Args:
        quaternions: The quaternions convert to matrices.

    Returns:
        The rotations matrices corresponding to the (normalized) quaternions.
    """
    device = quaternions.device
    shape = quaternions.shape[:-1]

    quaternions = quaternions / torch.linalg.norm(quaternions, dim=-1, keepdim=True)
    real_part = quaternions[..., 0]
    vector_part = quaternions[..., 1:]

    vector_cross = get_cross_product_matrix(vector_part)
    real_part = real_part[..., None, None]

    matrix_outer = vector_part[..., :, None] * vector_part[..., None, :]
    matrix_diag = real_part.square() * eyes(3, shape=shape, device=device)
    matrix_cross_1 = 2 * real_part * vector_cross
    matrix_cross_2 = vector_cross @ vector_cross

    return matrix_outer + matrix_diag + matrix_cross_1 + matrix_cross_2


def quaternions_from_rotation_matrices(matrices: torch.Tensor) -> torch.Tensor:
    """Convert batch of rotation matrices to quaternions.

    Args:
        matrices: The matrices to convert to quaternions.

    Returns:
        The quaternions corresponding to the rotation matrices.

    Note: this operation is not differentiable and will be performed on the CPU.
    """
    if not matrices.shape[-2:] == (3, 3):
        raise ValueError(f"matrices have invalid shape {matrices.shape}")
    matrices_np = matrices.detach().cpu().numpy()
    quaternions_np = Rotation.from_matrix(matrices_np.reshape(-1, 3, 3)).as_quat()
    # We use a convention where the w component is at the start of the quaternion.
    quaternions_np = quaternions_np[:, [3, 0, 1, 2]]
    quaternions_np = quaternions_np.reshape(matrices_np.shape[:-2] + (4,))
    return torch.as_tensor(quaternions_np, device=matrices.device, dtype=matrices.dtype)


def get_cross_product_matrix(vectors: torch.Tensor) -> torch.Tensor:
    """Generate cross product matrix for vector exterior product."""
    if not vectors.shape[-1] == 3:
        raise ValueError("Only 3-dimensional vectors are supported")
    device = vectors.device
    shape = vectors.shape[:-1]
    unit_basis = eyes(3, shape=shape, device=device)
    # We compute the matrix by multiplying each column of unit_basis with the
    # corresponding vector.
    return torch.cross(vectors[..., :, None], unit_basis, dim=-2)


def eyes(
    dim: int, shape: tuple[int, ...], device: torch.device | str | None = None
) -> torch.Tensor:
    """Create batch of identity matrices."""
    return torch.eye(dim, device=device).broadcast_to(shape + (dim, dim)).clone()


def quaternion_product(q1, q2):
    """Compute dot product between two quaternions."""
    real_1 = q1[..., :1]
    real_2 = q2[..., :1]
    vector_1 = q1[..., 1:]
    vector_2 = q2[..., 1:]

    real_out = real_1 * real_2 - (vector_1 * vector_2).sum(dim=-1, keepdim=True)
    vector_out = real_1 * vector_2 + real_2 * vector_1 + torch.cross(vector_1, vector_2)
    return torch.concatenate([real_out, vector_out], dim=-1)


def quaternion_conj(q):
    """Get conjugate of a quaternion."""
    real = q[..., :1]
    vector = q[..., 1:]
    return torch.concatenate([real, -vector], dim=-1)


def project(u: torch.Tensor, basis: torch.Tensor) -> torch.Tensor:
    """Project tensor u to unit basis a."""
    unit_u = F.normalize(u, dim=-1)
    inner_prod = (unit_u * basis).sum(dim=-1, keepdim=True)
    return inner_prod * u
